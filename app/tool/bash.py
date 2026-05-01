from __future__ import annotations

"""
Bash — persistent async shell session with strict guardrails.

Safety model:
  • Hard per-command timeout (default 30s, max 300s)
  • Output capped at 64 KB to prevent floods
  • Sentinel-based stdout drain — no blocking reads
  • Session restart on corruption (process death / timeout)
  • Dangerous command detection with explicit warning injected into output
"""

import asyncio
import shlex
from typing import Any, Optional

from app.logger import logger
from app.schema import ToolResult
from app.tool.base import BaseTool


# ---------------------------------------------------------------------------
# Guardrail constants
# ---------------------------------------------------------------------------

DEFAULT_TIMEOUT  = 30
MAX_TIMEOUT      = 300
MIN_TIMEOUT      = 1
MAX_OUTPUT_BYTES = 65_536   # 64 KB

# Commands that could wipe the filesystem or cause irreversible harm
_DANGEROUS_PATTERNS = [
    "rm -rf /",
    "rm -rf /*",
    ":(){ :|:& };:",   # fork bomb
    "dd if=/dev/zero of=/dev/",
    "mkfs.",
    "> /dev/sda",
]


def _is_dangerous(command: str) -> Optional[str]:
    lower = command.lower().replace("  ", " ")
    for pattern in _DANGEROUS_PATTERNS:
        if pattern in lower:
            return pattern
    return None


class Bash(BaseTool):
    name = "bash"
    description = (
        "Run shell commands in a persistent async bash session. "
        f"Default timeout: {DEFAULT_TIMEOUT}s (max {MAX_TIMEOUT}s). "
        "Environment variables and working directory are preserved across calls. "
        "Output is capped at 64 KB. Dangerous destructive commands are blocked."
    )
    parameters = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "Shell command to run.",
            },
            "timeout": {
                "type": "integer",
                "description": f"Timeout in seconds (min {MIN_TIMEOUT}, max {MAX_TIMEOUT}, default {DEFAULT_TIMEOUT}).",
                "default": DEFAULT_TIMEOUT,
            },
        },
        "required": ["command"],
    }

    def __init__(self) -> None:
        self._process: Optional[asyncio.subprocess.Process] = None
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Tool execution
    # ------------------------------------------------------------------

    async def execute(self, command: str, timeout: int = DEFAULT_TIMEOUT, **_: Any) -> ToolResult:
        timeout = max(MIN_TIMEOUT, min(timeout, MAX_TIMEOUT))

        # Safety gate
        danger = _is_dangerous(command)
        if danger:
            return ToolResult(
                error=(
                    f"🚫 BLOCKED: Command matches dangerous pattern '{danger}'. "
                    "This operation could cause irreversible damage and was rejected. "
                    "Choose a safer alternative."
                )
            )

        async with self._lock:
            return await self._run(command, timeout)

    async def _run(self, command: str, timeout: int) -> ToolResult:
        sentinel = "__MANUSCLAW_BASH_DONE_42__"
        # Wrap: run command, print exit code, then sentinel
        wrapped = f"({command}); echo \"EXIT:$?\"; echo {sentinel}\n"

        try:
            proc = await self._ensure_process()
            assert proc.stdin is not None and proc.stdout is not None

            proc.stdin.write(wrapped.encode())
            await proc.stdin.drain()

            lines: list[str] = []
            total_bytes = 0
            truncated = False
            exit_code: Optional[int] = None

            async def _read() -> None:
                nonlocal total_bytes, truncated, exit_code
                while True:
                    line_bytes = await proc.stdout.readline()
                    line = line_bytes.decode(errors="replace").rstrip("\n")
                    if line == sentinel:
                        break
                    if line.startswith("EXIT:"):
                        try:
                            exit_code = int(line[5:].strip())
                        except ValueError:
                            pass
                        continue
                    chunk = len(line.encode())
                    if total_bytes + chunk > MAX_OUTPUT_BYTES:
                        lines.append(f"... [output truncated at {MAX_OUTPUT_BYTES} bytes]")
                        truncated = True
                        # drain until sentinel
                        while True:
                            drain = await proc.stdout.readline()
                            if drain.decode(errors="replace").strip() == sentinel:
                                break
                        break
                    total_bytes += chunk
                    lines.append(line)

            await asyncio.wait_for(_read(), timeout=timeout)
            output = "\n".join(lines)

            if exit_code is not None and exit_code != 0:
                return ToolResult(
                    output=output or None,
                    error=(
                        f"Command exited with code {exit_code}.\n"
                        f"Output:\n{output}\n\n"
                        "Review the error and adjust your command."
                    ),
                )
            return ToolResult(output=output or "(command produced no output)")

        except asyncio.TimeoutError:
            logger.warning(f"[bash] Command timed out after {timeout}s. Resetting session.")
            await self._reset_process()
            return ToolResult(
                error=(
                    f"⏱ Command timed out after {timeout}s and the shell session was reset. "
                    "Consider: running shorter commands, adding background '&', "
                    f"or increasing timeout (max {MAX_TIMEOUT}s)."
                )
            )
        except BrokenPipeError:
            await self._reset_process()
            return ToolResult(error="Shell session died unexpectedly. Session restarted — please retry.")
        except Exception as e:
            return ToolResult(error=f"Bash error: {e}")

    # ------------------------------------------------------------------
    # Process lifecycle
    # ------------------------------------------------------------------

    async def _ensure_process(self) -> asyncio.subprocess.Process:
        if self._process is None or self._process.returncode is not None:
            self._process = await asyncio.create_subprocess_shell(
                "bash --norc --noprofile",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
        return self._process

    async def _reset_process(self) -> None:
        if self._process and self._process.returncode is None:
            try:
                self._process.terminate()
                await asyncio.wait_for(self._process.wait(), timeout=3)
            except Exception:
                try:
                    self._process.kill()
                except Exception:
                    pass
        self._process = None

    async def cleanup(self) -> None:
        await self._reset_process()
