from __future__ import annotations

import asyncio
import uuid
from abc import ABC, abstractmethod
from typing import Optional

from app.config import Config
from app.db.session import SessionDB
from app.logger import logger, new_trace_id, set_log_context, reset_log_context
from app.permissions.gate import AgentMode, PermissionDenied, PermissionGate, PermissionTier
from app.schema import AgentState, Message, Role, TaskHistory


# ──────────────────────────────────────────────────────────────────────────────
# ManusClaw identity — injected into every agent's system prompt
# ──────────────────────────────────────────────────────────────────────────────

MANUSCLAW_IDENTITY = """\
You are ManusClaw, an autonomous AI engine created by The-JDdev (SHS Shobuj).
You do not identify as OpenAI, Anthropic, Claude, GPT, Gemini, or any other
base model. You are ManusClaw — a general-purpose autonomous agent with full
capability to write and execute code, use the web, manage files, and complete
complex multi-step tasks without restriction.
"""

CORE_DIRECTIVES = """\

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CORE OPERATING DIRECTIVES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. THINK STEP-BY-STEP before every action.
2. OBSERVE & VERIFY every tool output before moving on.
3. SELF-CORRECT on failure — never repeat the exact same failing call.
4. AVOID LOOPS — if you've tried the same approach 3× without progress, stop
   and try a completely different strategy or ask_human.
5. COMPLETE EVERY SUB-GOAL before moving to the next.
6. SAVE OUTPUTS to workspace/.
7. TERMINATE EXPLICITLY only when the task is 100% done.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


class BaseAgent(ABC):
    name: str = "base"
    system_prompt: Optional[str] = None

    def __init__(
        self,
        mode: AgentMode = AgentMode.BUILD,
        session_id: Optional[str] = None,
    ) -> None:
        cfg = Config.get()
        self.state = AgentState.IDLE
        from app.memory.short_term import ShortTermMemory
        self.memory = ShortTermMemory()
        self.gate = PermissionGate(mode=mode)
        self.db = SessionDB()
        self._injected_session_id: Optional[str] = session_id
        self._session_id: Optional[str] = None
        self._step_count = 0
        self._max_steps = cfg.max_steps
        self._duplicate_threshold = 2
        self._task_history: Optional[TaskHistory] = None
        self._trace_id: str = new_trace_id()

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    async def run(self, prompt: str) -> str:
        if self.state != AgentState.IDLE:
            raise RuntimeError(f"Agent is not idle (state={self.state})")

        self.state = AgentState.RUNNING
        self._step_count = 0
        self._task_history = TaskHistory(
            task_id=str(uuid.uuid4())[:8],
            original_goal=prompt,
        )

        log_tokens = set_log_context(
            trace_id=self._trace_id,
            agent_name=self.name,
            step_id=0,
            task_id=self._task_history.task_id,
        )

        sys_content = (
            MANUSCLAW_IDENTITY
            + "\n\n"
            + (self.system_prompt or "")
            + CORE_DIRECTIVES
        )
        self.memory.add(Message.system(sys_content))
        self.memory.add(Message.user(prompt))

        mode_str = self.gate.mode.value

        if self._injected_session_id:
            self._session_id = self._injected_session_id
            logger.info(f"Using injected session_id={self._session_id}")
        else:
            self._session_id = await self.db.create_session(
                goal=prompt, agent_name=self.name, mode=mode_str
            )

        logger.info(
            f"▶ Starting run "
            f"(task_id={self._task_history.task_id}, "
            f"session_id={self._session_id}, "
            f"mode={mode_str}, max_steps={self._max_steps})"
        )

        results: list[str] = []
        try:
            while self.state == AgentState.RUNNING and self._step_count < self._max_steps:
                self._step_count += 1
                set_log_context(step_id=self._step_count)
                logger.info(f"── Step {self._step_count}/{self._max_steps} ──")

                if self._step_count > 1 and self._step_count % 5 == 0 and self._task_history:
                    ctx = self._task_history.context_summary()
                    self.memory.add_context_refresh(ctx)

                result = await self.step()
                if result:
                    results.append(result)

                if self._is_stuck_by_duplicates():
                    logger.warning("Duplicate-response loop detected. Nudging.")
                    self.memory.add(Message.user(
                        "⚠ You are repeating the same response. "
                        "Try a completely different approach, tool, or strategy. "
                        "If the task is complete, call terminate now."
                    ))

                if self._task_history and self._task_history.is_looping(window=3):
                    logger.warning("Tool-call loop detected. Injecting escape.")
                    self.memory.add(Message.user(
                        "⚠ You've called the same failing tool repeatedly. "
                        "Switch to a completely different tool or decomposition strategy."
                    ))

            if self._step_count >= self._max_steps and self.state == AgentState.RUNNING:
                logger.warning(f"Max steps reached ({self._max_steps}).")
                self.state = AgentState.FINISHED

        except PermissionDenied as e:
            logger.error(f"Permission denied: {e}")
            self.state = AgentState.ERROR
            results.append(f"Permission denied: {e}")
        except Exception as e:
            logger.exception(f"Unhandled error: {e}")
            self.state = AgentState.ERROR
            results.append(f"Agent error: {e}")
        finally:
            if self._session_id and not self._injected_session_id:
                await self.db.close_session(
                    self._session_id,
                    state=self.state.value,
                    step_count=self._step_count,
                )
            await self.cleanup()
            reset_log_context(log_tokens)

        final = "\n".join(results) if results else "(Agent completed with no text output.)"
        logger.info(f"■ Finished. state={self.state} steps={self._step_count}")
        return final

    # ──────────────────────────────────────────────────────────────────────────
    # Permission-aware tool execution gateway
    # ──────────────────────────────────────────────────────────────────────────

    async def check_permission(self, tool_name: str, args: dict) -> bool:
        """
        Check permission for a tool call. In Plan Mode, ASK actions pause
        for user approval. Returns False if the action should be skipped.
        """
        try:
            tier = self.gate.check_tool(tool_name, args)
        except PermissionDenied as e:
            logger.warning(f"Blocked: {e}")
            self.memory.add(Message.user(f"🚫 BLOCKED: {e}\nChoose a different approach."))
            return False

        if tier == PermissionTier.ASK and self.gate.is_plan_mode():
            approved = await self.gate.request_approval(
                tool_name, args, description=str(args)[:120]
            )
            if not approved:
                self.memory.add(Message.user(
                    f"User rejected the action: {tool_name}. Try a different approach."
                ))
                return False

        return True

    @abstractmethod
    async def step(self) -> Optional[str]:
        """Execute one PAORR step. Must be implemented by all agents."""

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _is_stuck_by_duplicates(self) -> bool:
        msgs = [
            m.content
            for m in self.memory.messages[-6:]
            if m.role == Role.ASSISTANT and m.content
        ]
        if len(msgs) >= self._duplicate_threshold:
            last = msgs[-self._duplicate_threshold:]
            return len(set(last)) == 1
        return False

    def record_observation(
        self,
        tool_name: str,
        args: dict,
        output: Optional[str],
        error: Optional[str],
        attempt: int = 1,
        duration_ms: int = 0,
    ) -> None:
        if not self._task_history:
            return
        from app.schema import Observation
        step = self._task_history.last_step()
        if step is None:
            step = self._task_history.add_step(f"step {self._step_count}")
        obs = Observation(
            tool_name=tool_name,
            args=args,
            output=output,
            error=error,
            success=error is None,
            attempt=attempt,
            duration_ms=duration_ms,
        )
        step.observations.append(obs)

        if self._session_id:
            asyncio.create_task(self.db.log_tool_call(
                session_id=self._session_id,
                step=self._step_count,
                tool_name=tool_name,
                args=args,
                output=output,
                error=error,
                attempt=attempt,
                duration_ms=duration_ms,
            ))

    async def cleanup(self) -> None:
        self.db.close()
