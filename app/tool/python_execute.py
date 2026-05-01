from __future__ import annotations

"""
PythonExecute — isolated Python code execution with strict guardrails.

Safety model:
  • True process isolation via multiprocessing (separate memory space)
  • Hard wall-clock timeout (default 30s, max 120s, min 1s)
  • Resource limits via setrlimit when available (CPU time, address space)
  • stdout/stderr captured; no TTY interaction
  • No network access restriction (use Docker sandbox for that)
"""

import multiprocessing
import queue
import resource
import sys
import traceback
from io import StringIO
from typing import Any

from app.schema import ToolResult
from app.tool.base import BaseTool

# ---------------------------------------------------------------------------
# Guardrail constants
# ---------------------------------------------------------------------------

DEFAULT_TIMEOUT     = 30    # seconds
MAX_TIMEOUT         = 120
MIN_TIMEOUT         = 1
MAX_OUTPUT_BYTES    = 65_536   # 64 KB — prevent runaway print floods
MAX_CPU_SECONDS     = 60       # setrlimit CPU cap (Unix only)
MAX_MEMORY_BYTES    = 512 * 1024 * 1024  # 512 MB virtual memory cap (Unix only)


# ---------------------------------------------------------------------------
# Subprocess worker
# ---------------------------------------------------------------------------

def _worker(code: str, result_queue: multiprocessing.Queue) -> None:
    """Runs inside a fresh process. Captures stdout/stderr, applies rlimits."""
    # Apply resource limits (Unix only)
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (MAX_CPU_SECONDS, MAX_CPU_SECONDS))
        resource.setrlimit(resource.RLIMIT_AS,  (MAX_MEMORY_BYTES, MAX_MEMORY_BYTES))
    except (AttributeError, ValueError, resource.error):
        pass  # Windows or limit already lower — skip gracefully

    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout = buf_out = StringIO()
    sys.stderr = buf_err = StringIO()
    try:
        exec(compile(code, "<manusclaw_sandbox>", "exec"), {})
        out = buf_out.getvalue()
        err = buf_err.getvalue()
    except SystemExit as e:
        out = buf_out.getvalue()
        err = f"SystemExit({e.code})"
    except Exception:
        out = buf_out.getvalue()
        err = traceback.format_exc()
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    # Truncate to prevent huge result payloads
    if len(out.encode()) > MAX_OUTPUT_BYTES:
        out = out[:MAX_OUTPUT_BYTES] + f"\n... [truncated at {MAX_OUTPUT_BYTES} bytes]"

    result_queue.put({"output": out, "error": err or None})


# ---------------------------------------------------------------------------
# Tool class
# ---------------------------------------------------------------------------

class PythonExecute(BaseTool):
    name = "python_execute"
    description = (
        "Execute Python code in an isolated subprocess. "
        f"Default timeout: {DEFAULT_TIMEOUT}s (max {MAX_TIMEOUT}s). "
        "stdout is captured and returned. Use print() to display results. "
        "Heavy computation, infinite loops, and memory bombs are terminated automatically."
    )
    parameters = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Valid Python 3 code to execute. Use print() for output.",
            },
            "timeout": {
                "type": "integer",
                "description": (
                    f"Wall-clock timeout in seconds "
                    f"(min {MIN_TIMEOUT}, max {MAX_TIMEOUT}, default {DEFAULT_TIMEOUT})."
                ),
                "default": DEFAULT_TIMEOUT,
            },
        },
        "required": ["code"],
    }

    async def execute(self, code: str, timeout: int = DEFAULT_TIMEOUT, **_: Any) -> ToolResult:
        # Clamp timeout
        timeout = max(MIN_TIMEOUT, min(timeout, MAX_TIMEOUT))

        result_queue: multiprocessing.Queue = multiprocessing.Queue()
        proc = multiprocessing.Process(
            target=_worker,
            args=(code, result_queue),
            daemon=True,
        )
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
                    "Your code exceeded the time limit. "
                    "Consider: reducing data size, adding early exits, "
                    "or splitting into smaller operations."
                )
            )

        try:
            result = result_queue.get_nowait()
        except queue.Empty:
            return ToolResult(error="No result returned from subprocess (process crashed).")

        output = (result.get("output") or "").strip()
        error  = result.get("error")

        # Surface errors clearly so the LLM can self-correct
        if error:
            return ToolResult(
                output=output or None,
                error=(
                    f"Python execution error:\n{error}\n\n"
                    "Fix the code and retry."
                ),
            )
        return ToolResult(output=output or "(code ran successfully, no output)")
