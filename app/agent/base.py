from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Optional

from app.config import Config
from app.logger import logger
from app.schema import AgentState, Memory, Message


class BaseAgent(ABC):
    name: str = "base"
    system_prompt: Optional[str] = None

    def __init__(self) -> None:
        self.state = AgentState.IDLE
        self.memory = Memory()
        self._step_count = 0
        self._max_steps = Config.get().max_steps
        self._duplicate_threshold = 2
        self._last_assistant_messages: list[str] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run(self, prompt: str) -> str:
        """Run the agent on a prompt and return the final output."""
        if self.state != AgentState.IDLE:
            raise RuntimeError(f"Agent is not idle (state={self.state})")

        self.state = AgentState.RUNNING
        self._step_count = 0

        if self.system_prompt:
            self.memory.add(Message.system(self.system_prompt))
        self.memory.add(Message.user(prompt))

        logger.info(f"[{self.name}] Starting run. Max steps: {self._max_steps}")

        results: list[str] = []
        try:
            while self.state == AgentState.RUNNING and self._step_count < self._max_steps:
                self._step_count += 1
                logger.info(f"[{self.name}] Step {self._step_count}/{self._max_steps}")
                result = await self.step()
                if result:
                    results.append(result)
                if self._is_stuck():
                    logger.warning(f"[{self.name}] Stuck loop detected. Nudging agent.")
                    self.memory.add(Message.user(
                        "You seem to be repeating yourself. Please try a different approach "
                        "or call the terminate tool if the task is complete."
                    ))

            if self._step_count >= self._max_steps and self.state == AgentState.RUNNING:
                logger.warning(f"[{self.name}] Reached max steps ({self._max_steps}). Stopping.")
                self.state = AgentState.FINISHED
        except Exception as e:
            logger.exception(f"[{self.name}] Error during run: {e}")
            self.state = AgentState.ERROR
            results.append(f"Error: {e}")
        finally:
            await self.cleanup()

        final = "\n".join(results) if results else "(Agent completed with no text output.)"
        logger.info(f"[{self.name}] Finished. State={self.state}")
        return final

    @abstractmethod
    async def step(self) -> Optional[str]:
        """Execute one step of the agent loop. Return output text or None."""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _is_stuck(self) -> bool:
        msgs = self.memory.messages
        assistant_texts = [
            m.content for m in msgs[-4:] if m.role.value == "assistant" and m.content
        ]
        if len(assistant_texts) >= self._duplicate_threshold:
            if len(set(assistant_texts[-self._duplicate_threshold:])) == 1:
                return True
        return False

    async def cleanup(self) -> None:
        """Override to release resources."""
