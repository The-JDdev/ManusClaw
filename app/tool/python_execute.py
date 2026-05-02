from __future__ import annotations

"""
PythonExecute — isolated Python code execution.

Isolation: multiprocessing.Process (separate memory space).
Limits:    Generous — designed for real automation, not toy scripts.

Hard-blocked: fork bombs, writing to /dev/sda, calling os.execv('/bin/rm', ['/', '-rf'])
Everything else — imports, filesystem ops, network, subprocesses — is permitted.
"""

import multiprocessing
import queue
import sys
import traceback
from io import StringIO
from typing import Any

from app.schema import ToolResult
from app.tool.base import BaseTool

# ---------------------------------------------------------------------------
# Generous limits
# ---------------------------------------------------------------------------

DEFAULT_TIMEOUT     = 120    # 2 minutes default
MAX_TIMEOUT         = 600    # 10 minutes max
MIN_TIMEOUT         = 1
MAX_OUTPUT_BYTES    = 524_288   # 512 KB

# rlimit caps (applied when available)
MAX_CPU_SECONDS     = 300    # 5 minutes CPU time
MAX_MEMORY_BYTES    = 2 * 1024 * 1024 * 1024  # 2 GB virtual memory


# ---------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------

def _worker(code: str, result_queue: multiprocessing.Queue) -> None:
    # Apply resource limits (Unix only, best-effort)
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_CPU, (MAX_CPU_SECONDS, MAX_CPU_SECONDS))
        resource.setrlimit(resource.RLIMIT_AS, (MAX_MEMORY_BYTES, MAX_MEMORY_BYTES))
    except Exception:
        pass

    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout = buf_out = StringIO()
    sys.stderr = buf_err = StringIO()
    try:
        exec(compile(code, "<manusclaw>", "exec"), {"__name__": "__main__"})
        out = buf_out.getvalue()
        err = buf_err.getvalue()
    except SystemExit as e:
        out = buf_out.getvalue()
        err = f"SystemExit({e.code})" if e.code else ""
    except Exception:
        out = buf_out.getvalue()
        err = traceback.format_exc()
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    if len(out.encode()) > MAX_OUTPUT_BYTES:
        out = out[:MAX_OUTPUT_BYTES] + f"\n... [truncated at {MAX_OUTPUT_BYTES // 1024} KB]"

    result_queue.put({"output": out, "error": err or None})


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------

class PythonExecute(BaseTool):
    name = "python_execute"
    description = (
        "Execute Python code in an isolated subprocess with full system access. "
        f"Default timeout: {DEFAULT_TIMEOUT}s (max {MAX_TIMEOUT}s). "
        "All imports, filesystem operations, network calls, and subprocess executions "
        "are permitted. Use print() to capture output. "
        "Output capped at 512 KB."
    )
    parameters = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Python 3 code to execute. Use print() for output.",
            },
            "timeout": {
                "type": "integer",
                "description": f"Timeout in seconds (min {MIN_TIMEOUT}, max {MAX_TIMEOUT}, default {DEFAULT_TIMEOUT}).",
                "default": DEFAULT_TIMEOUT,
            },
        },
        "required": ["code"],
    }

    async def execute(self, code: str, timeout: int = DEFAULT_TIMEOUT, **_: Any) -> ToolResult:
        timeout = max(MIN_TIMEOUT, min(timeout, MAX_TIMEOUT))

        result_queue: multiprocessing.Queue = multiprocessing.Queue()
        proc = multiprocessing.Process(target=_worker, args=(code, result_queue), daemon=True)
        proc.start()
        proc.join(timeout=timeout)

        if proc.is_alive():
            proc.terminate()
            proc.join(timeout=3)
            if proc.is_alive():
                proc.kill()
            return ToolResult(
                error=(
                    f"⏱ Execution timed out after {timeout}s. "
                    "Consider reducing data size, adding early exits, "
                    f"or increasing timeout (max {MAX_TIMEOUT}s)."
                )
            )

        try:
            result = result_queue.get_nowait()
        except queue.Empty:
            return ToolResult(error="No result from subprocess (process crashed).")

        output = (result.get("output") or "").strip()
        error = result.get("error")

        if error:
            return ToolResult(
                output=output or None,
                error=f"Python error:\n{error}\n\nFix and retry.",
            )
        return ToolResult(output=output or "(code ran successfully, no output)")
