from __future__ import annotations

import multiprocessing
import queue
import sys
import traceback
from io import StringIO
from typing import Any

from app.schema import ToolResult
from app.tool.base import BaseTool


def _run_in_process(code: str, result_queue: multiprocessing.Queue) -> None:
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = buf_out = StringIO()
    sys.stderr = buf_err = StringIO()
    try:
        local_vars: dict[str, Any] = {}
        exec(compile(code, "<manusclaw>", "exec"), local_vars)
        output = buf_out.getvalue()
        err = buf_err.getvalue()
        result_queue.put({"output": output, "error": err or None})
    except Exception:
        result_queue.put({"output": buf_out.getvalue(), "error": traceback.format_exc()})
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr


class PythonExecute(BaseTool):
    name = "python_execute"
    description = (
        "Execute Python code in an isolated subprocess with a 5-second timeout. "
        "Returns stdout output and any errors."
    )
    parameters = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Python code to execute.",
            },
            "timeout": {
                "type": "integer",
                "description": "Timeout in seconds (default 5, max 60).",
                "default": 5,
            },
        },
        "required": ["code"],
    }

    async def execute(self, code: str, timeout: int = 5, **_: Any) -> ToolResult:
        timeout = min(max(1, timeout), 60)
        result_queue: multiprocessing.Queue = multiprocessing.Queue()
        proc = multiprocessing.Process(target=_run_in_process, args=(code, result_queue))
        proc.start()
        proc.join(timeout=timeout)

        if proc.is_alive():
            proc.terminate()
            proc.join(2)
            return ToolResult(error=f"Execution timed out after {timeout}s.")

        try:
            result = result_queue.get_nowait()
        except queue.Empty:
            return ToolResult(error="No result returned from subprocess.")

        output = result.get("output") or ""
        error = result.get("error")
        return ToolResult(output=output.strip() if output else None, error=error)
