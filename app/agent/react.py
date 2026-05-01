from __future__ import annotations

from typing import Optional

from app.agent.base import BaseAgent
from app.llm.llm import LLM
from app.logger import logger
from app.schema import AgentState, Message


class ReActAgent(BaseAgent):
    """ReAct agent: Reason → Act loop."""

    name = "react"
    system_prompt = (
        "You are a helpful AI assistant. Think step by step (Reason), "
        "then take an action (Act). Continue until the task is complete."
    )

    def __init__(self) -> None:
        super().__init__()
        self.llm = LLM()

    async def think(self) -> str:
        """Generate reasoning from the LLM."""
        response = await self.llm.ask(self.memory.messages)
        self.memory.add(response)
        return response.content or ""

    async def act(self, thought: str) -> Optional[str]:
        """Default action is just the thought itself. Override in subclasses."""
        return thought

    async def step(self) -> Optional[str]:
        thought = await self.think()
        logger.debug(f"[{self.name}] Thought: {thought[:120]}")
        result = await self.act(thought)

        # Simple termination: if the LLM says it's done
        lower = (thought + (result or "")).lower()
        if any(kw in lower for kw in ["task complete", "task is complete", "finished", "done"]):
            self.state = AgentState.FINISHED

        return result
