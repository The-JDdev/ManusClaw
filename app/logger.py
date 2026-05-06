from __future__ import annotations

"""
ManusClaw Context-Aware Logger
================================
Every log record is automatically tagged with four context fields:

  trace_id  — unique ID for the agent run (set once per run)
  agent     — agent name (manus, orchestrator, product_manager, …)
  step      — current PAORR step number within the run
  task_id   — short task UUID

Context is propagated via Python's `contextvars` module, which means it
works correctly across `async/await` boundaries without manual threading.
"""

import sys
import uuid
from contextvars import ContextVar
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger as _logger

from app.config import Config


_ctx_trace: ContextVar[str] = ContextVar("mc_trace", default="————")
_ctx_agent: ContextVar[str] = ContextVar("mc_agent", default="system")
_ctx_step: ContextVar[int] = ContextVar("mc_step", default=0)
_ctx_task: ContextVar[str] = ContextVar("mc_task", default="")


def _patcher(record: dict) -> None:
    record["extra"]["trace_id"] = _ctx_trace.get()
    record["extra"]["agent"] = _ctx_agent.get()
    record["extra"]["step"] = _ctx_step.get()
    record["extra"]["task_id"] = _ctx_task.get()


_LOG_DIR = Path("logs")
_LOG_DIR.mkdir(exist_ok=True)
_LOG_FILE = _LOG_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

_CONSOLE_FORMAT = (
    "<green>{time:HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{extra[agent]}</cyan>@<cyan>{extra[step]}</cyan> "
    "[<dim>{extra[trace_id]}</dim>] — "
    "<level>{message}</level>"
)

_FILE_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
    "agent={extra[agent]} step={extra[step]} "
    "trace={extra[trace_id]} task={extra[task_id]} | "
    "{name}:{function}:{line} — {message}"
)

_log_level = Config.get().logging.level.upper().strip() or "DEBUG"

_logger.remove()
_logger.add(
    sys.stderr,
    colorize=True,
    format=_CONSOLE_FORMAT,
    level=_log_level,
)
_logger.add(
    str(_LOG_FILE),
    rotation="50 MB",
    retention="7 days",
    compression="gz",
    format=_FILE_FORMAT,
    level=_log_level,
    encoding="utf-8",
)

logger = _logger.patch(_patcher)


def new_trace_id() -> str:
    return str(uuid.uuid4())[:12]


def set_log_context(
    trace_id: Optional[str] = None,
    agent_name: Optional[str] = None,
    step_id: Optional[int] = None,
    task_id: Optional[str] = None,
) -> dict:
    tokens: dict = {}
    if trace_id is not None:
        tokens["trace_id"] = _ctx_trace.set(trace_id)
    if agent_name is not None:
        tokens["agent_name"] = _ctx_agent.set(agent_name)
    if step_id is not None:
        tokens["step_id"] = _ctx_step.set(step_id)
    if task_id is not None:
        tokens["task_id"] = _ctx_task.set(task_id)
    return tokens


def reset_log_context(tokens: dict) -> None:
    for key, token in tokens.items():
        if key == "trace_id":
            _ctx_trace.reset(token)
        elif key == "agent_name":
            _ctx_agent.reset(token)
        elif key == "step_id":
            _ctx_step.reset(token)
        elif key == "task_id":
            _ctx_task.reset(token)


def get_current_trace_id() -> str:
    return _ctx_trace.get()


def get_current_agent() -> str:
    return _ctx_agent.get()
