from __future__ import annotations

"""
Bash — persistent async shell session.

Philosophy: The agent runs until the task is DONE.
No artificial output caps. No artificial time limits.
Only catastrophic OS-destroying operations are hard-blocked.

Blocked (hard deny, unconditional — these destroy the OS itself):
  rm -rf /   rm -rf /*   fork bombs   dd to block devices   mkfs   wipefs   kill -9 -1

Permitted (everything else — no exceptions):
  sudo, apt, pip, npm, cargo, go, git, curl, wget, ssh, docker, systemctl,
  crontab, env edits, /etc edits, /usr edits, long-running compiles, training
  runs, crawlers, scrapers, batch jobs, automation pipelines, etc.

Timeouts:
  DEFAULT_TIMEOUT = 3600   (1 hour — enough for most tasks)
  MAX_TIMEOUT     = 86400  (24 hours — for overnight jobs, model training, etc.)
  The agent MAY pass any timeout up to 24h. No cap below that.

Output:
  No byte cap. Full output is always returned.
  The agent needs complete output to reason correctly — truncation is a bug.
"""

import asyncio
import re
from typing import Any, Optional

from app.logger import logger
from app.schema import ToolResult
from app.tool.base import BaseTool


# ---------------------------------------------------------------------------
# Limits — task-complete, not toy-safe
# ---------------------------------------------------------------------------

DEFAULT_TIMEOUT = 3600    # 1 hour
MAX_TIMEOUT     = 86400   # 24 hours — overnight jobs, training runs
MIN_TIMEOUT     = 1

# Catastrophic patterns — the ONLY things blocked, ever
_CATASTROPHIC = [
    r"rm\s+-[rRf]+\s+/\s*$",
    r"rm\s+-[rRf]+\s+/\*",
    r"rm\s+--no-preserve-root",
    r":\(\)\s*\{.*:\|:.*\}",
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
        f"Default timeout: {DEFAULT_TIMEOUT}s ({DEFAULT_TIMEOUT // 3600}h). "
        f"Max timeout: {MAX_TIMEOUT}s ({MAX_TIMEOUT // 3600}h) for overnight jobs. "
        "Full output always returned — no truncation. "
        "Environment, working directory, and variables persist across calls. "
        "Full system access: sudo, apt, pip, git, curl, systemctl, docker, etc. "
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
                    f"Timeout in seconds. Default {DEFAULT_TIMEOUT}s (1h). "
                    f"Max {MAX_TIMEOUT}s (24h) for long-running jobs. "
                    "Set higher for compiles, training runs, crawlers."
                ),
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
                    f"BLOCKED — catastrophic OS-destroying pattern: `{bad}`\n"
                    "This is the ONLY category of blocked commands. "
                    "Everything else (sudo, rm -rf subdirs, system edits, network, docker) "
                    "is fully permitted."
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
            return ToolResult(output=output or "(command ran successfully, no output)")

        except asyncio.TimeoutError:
            logger.warning(f"[bash] Command timed out after {timeout}s. Resetting session.")
            await self._reset_process()
            return ToolResult(
                error=(
                    f"Command timed out after {timeout}s. Shell session was reset. "
                    f"Increase timeout (max {MAX_TIMEOUT}s = 24h), "
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
