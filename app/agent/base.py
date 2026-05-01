from __future__ import annotations

import asyncio
import uuid
from abc import ABC, abstractmethod
from typing import Optional

from app.config import Config
from app.logger import logger
from app.schema import AgentState, Memory, Message, Role, TaskHistory


# ---------------------------------------------------------------------------
# Hardcoded core directives — injected into every agent
# ---------------------------------------------------------------------------

CORE_DIRECTIVES = """\

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CORE OPERATING DIRECTIVES (non-negotiable)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. THINK STEP-BY-STEP: Before every action, reason explicitly about what
   you know, what you need, and which tool will best advance the task.

2. OBSERVE & VERIFY: After every tool call, read the output carefully.
   Confirm that it actually solved the intended sub-goal before moving on.

3. SELF-CORRECT ON FAILURE: If a tool returns an error, an empty result,
   or unexpected output — do NOT repeat the same call. Analyze the failure,
   identify the root cause, and choose a different tool or a different
   argument set.

4. AVOID LOOPS: If you notice you have called the same tool with the same
   arguments more than twice without progress, STOP. Either ask the user
   for clarification (ask_human) or terminate with an honest explanation.

5. COMPLETE EVERY SUB-GOAL BEFORE MOVING ON: Do not skip steps. Do not
   assume a step is done without evidence in the tool output.

6. SAVE IMPORTANT OUTPUTS: Write files, charts, and results to workspace/.

7. TERMINATE EXPLICITLY: When the task is fully done — and not before —
   call the terminate tool with a precise explanation of what was achieved.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


class BaseAgent(ABC):
    name: str = "base"
    system_prompt: Optional[str] = None

    def __init__(self) -> None:
        self.state = AgentState.IDLE
        self.memory = Memory()
        self._step_count = 0
        self._max_steps = Config.get().max_steps
        self._duplicate_threshold = 2
        self._task_history: Optional[TaskHistory] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run(self, prompt: str) -> str:
        if self.state != AgentState.IDLE:
            raise RuntimeError(f"Agent is not idle (state={self.state})")

        self.state = AgentState.RUNNING
        self._step_count = 0
        self._task_history = TaskHistory(
            task_id=str(uuid.uuid4())[:8],
            original_goal=prompt,
        )

        # Build system message: base prompt + core directives
        sys_content = (self.system_prompt or "") + CORE_DIRECTIVES
        self.memory.add(Message.system(sys_content))
        self.memory.add(Message.user(prompt))

        logger.info(f"[{self.name}] ▶ Starting run (task_id={self._task_history.task_id}). max_steps={self._max_steps}")

        results: list[str] = []
        try:
            while self.state == AgentState.RUNNING and self._step_count < self._max_steps:
                self._step_count += 1
                logger.info(f"[{self.name}] ── Step {self._step_count}/{self._max_steps} ──")

                # Inject task history summary every 5 steps so the agent remembers
                if self._step_count > 1 and self._step_count % 5 == 0 and self._task_history:
                    ctx = self._task_history.context_summary()
                    self.memory.add(Message.user(
                        f"[Context refresh — your task history so far]\n{ctx}\n"
                        "Continue from where you left off."
                    ))

                result = await self.step()
                if result:
                    results.append(result)

                # Stuck-loop detection
                if self._is_stuck_by_duplicates():
                    logger.warning(f"[{self.name}] Duplicate-response loop detected. Nudging.")
                    self.memory.add(Message.user(
                        "⚠ You appear to be repeating the same response. "
                        "You MUST try a completely different approach, tool, or strategy. "
                        "If the task is already complete, call terminate now."
                    ))

                if self._task_history and self._task_history.is_looping(window=3):
                    logger.warning(f"[{self.name}] Tool-call loop detected. Injecting escape prompt.")
                    self.memory.add(Message.user(
                        "⚠ You have been calling the same tool repeatedly without making progress. "
                        "Change your strategy immediately. Consider: "
                        "(a) using a different tool, "
                        "(b) decomposing the problem differently, or "
                        "(c) calling ask_human if you need clarification."
                    ))

            if self._step_count >= self._max_steps and self.state == AgentState.RUNNING:
                logger.warning(f"[{self.name}] Reached max steps ({self._max_steps}). Forcing stop.")
                self.state = AgentState.FINISHED

        except Exception as e:
            logger.exception(f"[{self.name}] Unhandled error: {e}")
            self.state = AgentState.ERROR
            results.append(f"Agent error: {e}")
        finally:
            await self.cleanup()

        final = "\n".join(results) if results else "(Agent completed with no text output.)"
        logger.info(f"[{self.name}] ■ Finished. state={self.state} steps={self._step_count}")
        return final

    @abstractmethod
    async def step(self) -> Optional[str]:
        """Execute one PAORR step. Return output text or None."""

    # ------------------------------------------------------------------
    # Loop-detection helpers
    # ------------------------------------------------------------------

    def _is_stuck_by_duplicates(self) -> bool:
        """True if the last N assistant messages are identical."""
        msgs = [
            m.content
            for m in self.memory.messages[-6:]
            if m.role == Role.ASSISTANT and m.content
        ]
        if len(msgs) >= self._duplicate_threshold:
            last = msgs[-self._duplicate_threshold:]
            if len(set(last)) == 1:
                return True
        return False

    def record_observation(
        self,
        tool_name: str,
        args: dict,
        output: Optional[str],
        error: Optional[str],
        attempt: int = 1,
    ) -> None:
        """Record a tool observation in the task history."""
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
        )
        step.observations.append(obs)

    async def cleanup(self) -> None:
        """Override to release resources."""
