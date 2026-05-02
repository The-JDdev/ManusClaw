from __future__ import annotations

"""
Bash — persistent async shell session.

Runtime philosophy: TASK-COMPLETE, NOT TIME-BOXED.
  The agent runs until the work is done — period.
  If a task needs 2 minutes, it runs 2 minutes.
  If it needs 3 hours, it runs 3 hours.
  There is no DEFAULT timeout and no MAX cap.
  Pass timeout=None (or omit it) → runs until completion, no kill.
  Pass timeout=N   → kills after exactly N seconds if still running.

Blocked (hard deny — OS-destroying operations only):
  rm -rf /   rm -rf /*   fork bombs   dd to block devices
  mkfs       wipefs      kill -9 -1   shred /bin|/usr|/boot

Everything else is permitted with zero restriction:
  sudo, apt, pip, npm, cargo, git, curl, wget, ssh, docker,
  systemctl, crontab, /etc edits, compiles, crawlers, ML jobs,
  batch pipelines, overnight automation — all fully allowed.
"""

import asyncio
import re
from typing import Any, Optional

from app.logger import logger
from app.schema import ToolResult
from app.tool.base import BaseTool


# ---------------------------------------------------------------------------
# Catastrophic blacklist — the ONLY restriction in this tool
# ---------------------------------------------------------------------------

_CATASTROPHIC = [
    r"rm\s+-[rRf]+\s+/\s*$",
    r"rm\s+-[rRf]+\s+/\*",
    r"rm\s+--no-preserve-root",
    r":\(\)\s*\{.*:\|:.*\}",                      # fork bomb
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
        "Runs until completion — no artificial time limit. "
        "Optionally pass timeout=N (seconds) to kill after exactly N seconds. "
        "Full output always returned — no byte truncation, ever. "
        "Environment, working directory, and shell variables persist across calls. "
        "Full system access: sudo, apt, pip, git, curl, docker, systemctl, etc. "
        "Only OS-destroying commands (rm -rf /, fork bombs, mkfs) are blocked."
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
                "description": (
                    "Optional. Kill after this many seconds if still running. "
                    "Omit (or pass null) to run until the task naturally completes — "
                    "2 min tasks run 2 min, 3 hour jobs run 3 hours. "
                    "Only set this if you explicitly need a deadline."
                ),
            },
        },
        "required": ["command"],
    }

    def __init__(self) -> None:
        self._process: Optional[asyncio.subprocess.Process] = None
        self._lock = asyncio.Lock()

    async def execute(
        self,
        command: str,
        timeout: Optional[int] = None,
        **_: Any,
    ) -> ToolResult:
        bad = _is_catastrophic(command)
        if bad:
            return ToolResult(
                error=(
                    f"BLOCKED — catastrophic OS-destroying pattern matched: `{bad}`\n"
                    "This is the ONLY category of blocked commands. "
                    "All other system operations (sudo, rm -rf subdirs, network, "
                    "docker, /etc edits) are fully permitted."
                )
            )

        async with self._lock:
            return await self._run(command, timeout)

    async def _run(self, command: str, timeout: Optional[int]) -> ToolResult:
        sentinel = "__MC_DONE_9742__"
        wrapped  = f"({command}); echo \"EXIT:$?\"; echo {sentinel}\n"

        try:
            proc = await self._ensure_process()
            assert proc.stdin is not None and proc.stdout is not None

            proc.stdin.write(wrapped.encode())
            await proc.stdin.drain()

            lines: list[str] = []
            exit_code: Optional[int] = None

            async def _read() -> None:
                nonlocal exit_code
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
                    lines.append(line)

            # timeout=None → asyncio.wait_for waits forever (task-complete behaviour)
            await asyncio.wait_for(_read(), timeout=timeout)
            output = "\n".join(lines)

            if exit_code is not None and exit_code != 0:
                return ToolResult(
                    output=output or None,
                    error=(
                        f"Command exited with code {exit_code}.\n"
                        f"Output:\n{output}\n\n"
                        "Review the error above and adjust your command."
                    ),
                )
            return ToolResult(output=output or "(command completed successfully, no output)")

        except asyncio.TimeoutError:
            logger.warning(f"[bash] Deadline reached after {timeout}s — resetting session.")
            await self._reset_process()
            return ToolResult(
                error=(
                    f"Deadline reached after {timeout}s. Shell session was reset. "
                    "Options: omit timeout to run until done, "
                    "use background execution ('nohup ... &'), "
                    "or split into smaller steps."
                )
            )
        except BrokenPipeError:
            await self._reset_process()
            return ToolResult(error="Shell session died unexpectedly. Session restarted — retry.")
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
