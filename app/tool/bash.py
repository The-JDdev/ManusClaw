from __future__ import annotations

"""
Bash — persistent async shell session.

Safety: Only catastrophic OS-destroying operations are blocked.
Everything else — system edits, package installs, network ops,
config changes, automation scripts — is fully permitted.

Blocked (hard deny, unconditional):
  rm -rf / | rm -rf /* | fork bombs | dd to block devices | mkfs | kill -9 -1
  
Permitted (everything else):
  sudo, apt, pip, npm, git, curl, wget, ssh, docker, systemctl,
  crontab, env edits, /etc edits, /usr edits, complex scripts, etc.
"""

import asyncio
import re
from typing import Any, Optional

from app.logger import logger
from app.schema import ToolResult
from app.tool.base import BaseTool


# ---------------------------------------------------------------------------
# Limits — generous, not artificial
# ---------------------------------------------------------------------------

DEFAULT_TIMEOUT  = 120
MAX_TIMEOUT      = 600
MIN_TIMEOUT      = 1
MAX_OUTPUT_BYTES = 524_288   # 512 KB

# Catastrophic patterns — the ONLY things blocked
_CATASTROPHIC = [
    r"rm\s+-[rRf]+\s+/\s*$",
    r"rm\s+-[rRf]+\s+/\*",
    r"rm\s+--no-preserve-root",
    r":\(\)\s*\{.*:\|:.*\}",               # fork bomb
    r"dd\s+if=/dev/zero\s+of=/dev/(s|h|v|xv)d\b",
    r">\s*/dev/(s|h|v|xv)d[a-z]\b",
    r"mkfs\.",
    r"wipefs\s",
    r"kill\s+-9\s+-1\b",
    r"killall\s+-9\b",
    r"shred\s+.*/(bin|sbin|lib|usr|boot)/",
]


def _is_catastrophic(command: str) -> Optional[str]:
    for p in _CATASTROPHIC:
        if re.search(p, command, re.IGNORECASE | re.DOTALL):
            return p
    return None


class Bash(BaseTool):
    name = "bash"
    description = (
        "Execute shell commands in a persistent bash session. "
        f"Default timeout: {DEFAULT_TIMEOUT}s (max {MAX_TIMEOUT}s). "
        "Environment, working directory, and variables persist across calls. "
        "Full system access: sudo, apt, pip, git, curl, systemctl, etc. "
        "Only catastrophic OS-destroying commands are blocked."
    )
    parameters = {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Shell command to run."},
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

    async def execute(self, command: str, timeout: int = DEFAULT_TIMEOUT, **_: Any) -> ToolResult:
        timeout = max(MIN_TIMEOUT, min(timeout, MAX_TIMEOUT))

        bad = _is_catastrophic(command)
        if bad:
            return ToolResult(
                error=(
                    f"🚫 BLOCKED — catastrophic pattern matched: `{bad}`\n"
                    "This operation would permanently damage the OS and is the ONLY type "
                    "of command that is blocked. All other system operations are permitted."
                )
            )

        async with self._lock:
            return await self._run(command, timeout)

    async def _run(self, command: str, timeout: int) -> ToolResult:
        sentinel = "__MC_DONE_9742__"
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
                    chunk_bytes = len(line.encode())
                    if total_bytes + chunk_bytes > MAX_OUTPUT_BYTES:
                        lines.append(f"\n... [output truncated at {MAX_OUTPUT_BYTES // 1024} KB]")
                        truncated = True
                        while True:
                            drain = await proc.stdout.readline()
                            if drain.decode(errors="replace").strip() == sentinel:
                                break
                        break
                    total_bytes += chunk_bytes
                    lines.append(line)

            await asyncio.wait_for(_read(), timeout=timeout)
            output = "\n".join(lines)

            if exit_code is not None and exit_code != 0:
                return ToolResult(
                    output=output or None,
                    error=(
                        f"Command exited with code {exit_code}.\n"
                        f"Output:\n{output}\n\nReview the error and adjust your command."
                    ),
                )
            return ToolResult(output=output or "(command ran, no output)")

        except asyncio.TimeoutError:
            logger.warning(f"[bash] Command timed out after {timeout}s. Resetting session.")
            await self._reset_process()
            return ToolResult(
                error=(
                    f"⏱ Command timed out after {timeout}s. Shell session was reset. "
                    f"Consider background execution ('&'), increased timeout (max {MAX_TIMEOUT}s), "
                    "or splitting into smaller steps."
                )
            )
        except BrokenPipeError:
            await self._reset_process()
            return ToolResult(error="Shell session died. Session restarted — please retry.")
        except Exception as e:
            return ToolResult(error=f"Bash error: {e}")

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
