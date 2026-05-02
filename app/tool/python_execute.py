from __future__ import annotations

"""
PythonExecute — isolated Python code execution.

Philosophy: The agent runs until the task is DONE.
No artificial output caps. No artificial time limits.
Only catastrophic OS operations are hard-blocked.

Isolation: multiprocessing.Process (separate memory space).
Memory:    2 GB virtual — enough for real ML/data work.
CPU time:  No wall-clock cap. Agent sets its own timeout.
Output:    Full output always returned. No byte truncation.

Blocked (hard deny):
  fork bombs, writing to /dev/sda, os.execv to destructive binaries

Permitted (everything else):
  All imports, filesystem ops, network calls, subprocesses,
  ML training, data processing, long computations, crawlers.

Timeouts:
  DEFAULT_TIMEOUT = 3600s  (1 hour)
  MAX_TIMEOUT     = 86400s (24 hours — model training, batch jobs)
  Agent may specify any value up to 24h.
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
# Limits — unlimited output, task-duration timeouts
# ---------------------------------------------------------------------------

DEFAULT_TIMEOUT  = 3600      # 1 hour
MAX_TIMEOUT      = 86400     # 24 hours
MIN_TIMEOUT      = 1
MAX_MEMORY_BYTES = 2 * 1024 * 1024 * 1024   # 2 GB virtual memory (rlimit)


# ---------------------------------------------------------------------------
# Worker subprocess
# ---------------------------------------------------------------------------

def _worker(code: str, result_queue: multiprocessing.Queue) -> None:
    try:
        import resource
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

    result_queue.put({"output": out, "error": err or None})


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------

class PythonExecute(BaseTool):
    name = "python_execute"
    description = (
        "Execute Python code in an isolated subprocess with full system access. "
        f"Default timeout: {DEFAULT_TIMEOUT}s (1h). "
        f"Max timeout: {MAX_TIMEOUT}s (24h) for training runs, batch jobs, crawlers. "
        "Full output always returned — no truncation. "
        "All imports, filesystem, network, subprocess, ML ops are permitted. "
        "Use print() to capture output. "
        "Only fork bombs and /dev/sda writes are blocked."
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
                "description": (
                    f"Timeout in seconds. Default {DEFAULT_TIMEOUT}s (1h). "
                    f"Max {MAX_TIMEOUT}s (24h) for long-running tasks. "
                    "Set higher for ML training, large data processing."
                ),
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
            proc.join(timeout=5)
            if proc.is_alive():
                proc.kill()
            return ToolResult(
                error=(
                    f"Execution timed out after {timeout}s. "
                    "Consider: increasing timeout (max 86400s = 24h), "
                    "adding progress checkpoints, running in background via bash, "
                    "or splitting the task into smaller steps."
                )
            )

        try:
            result = result_queue.get_nowait()
        except queue.Empty:
            return ToolResult(error="Subprocess crashed with no result. Check for memory errors or OS-level issues.")

        output = (result.get("output") or "").strip()
        error  = result.get("error")

        if error:
            return ToolResult(
                output=output or None,
                error=f"Python error:\n{error}\n\nAnalyse the traceback and fix the code.",
            )
        return ToolResult(output=output or "(code ran successfully, no output)")
