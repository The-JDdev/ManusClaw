from __future__ import annotations

import asyncio
from typing import Any, Optional

from app.schema import ToolResult
from app.tool.base import BaseTool


class Bash(BaseTool):
    name = "bash"
    description = (
        "Run shell commands in a persistent async bash session. "
        "State (env vars, cwd) is preserved across calls."
    )
    parameters = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "Shell command to execute.",
            },
            "timeout": {
                "type": "integer",
                "description": "Timeout in seconds (default 30).",
                "default": 30,
            },
        },
        "required": ["command"],
    }

    def __init__(self) -> None:
        self._process: Optional[asyncio.subprocess.Process] = None

    async def _ensure_process(self) -> asyncio.subprocess.Process:
        if self._process is None or self._process.returncode is not None:
            self._process = await asyncio.create_subprocess_shell(
                "bash",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
        return self._process

    async def execute(self, command: str, timeout: int = 30, **_: Any) -> ToolResult:
        timeout = min(max(1, timeout), 300)
        sentinel = "__MANUSCLAW_DONE__"
        full_cmd = f"{command}\necho {sentinel}\n"
        try:
            proc = await self._ensure_process()
            assert proc.stdin is not None and proc.stdout is not None
            proc.stdin.write(full_cmd.encode())
            await proc.stdin.drain()

            output_lines = []
            async def read_until_sentinel() -> None:
                while True:
                    line = await proc.stdout.readline()
                    decoded = line.decode(errors="replace").rstrip("\n")
                    if decoded == sentinel:
                        break
                    output_lines.append(decoded)

            await asyncio.wait_for(read_until_sentinel(), timeout=timeout)
            output = "\n".join(output_lines)
            return ToolResult(output=output or "(no output)")
        except asyncio.TimeoutError:
            await self.cleanup()
            return ToolResult(error=f"Command timed out after {timeout}s.")
        except Exception as e:
            return ToolResult(error=str(e))

    async def cleanup(self) -> None:
        if self._process and self._process.returncode is None:
            try:
                self._process.terminate()
                await asyncio.wait_for(self._process.wait(), timeout=5)
            except Exception:
                pass
        self._process = None
