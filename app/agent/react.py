from __future__ import annotations

import json
from typing import Any, Optional

from app.agent.base import BaseAgent
from app.llm.llm import LLM
from app.logger import logger
from app.schema import AgentState, Message, Observation, Reflection, TaskStep


# ---------------------------------------------------------------------------
# Reflection prompt builder
# ---------------------------------------------------------------------------

_REFLECT_SYSTEM = """\
You are a reflection module for an AI agent. Given a goal and an observation
(the output of a tool call), determine:

1. Was the goal SOLVED by this observation? (yes/no)
2. Why? (one sentence)
3. If NOT solved: what should the agent try next?

Respond ONLY in this JSON format (no extra text):
{
  "solved": true,
  "reason": "...",
  "next_action": "..." 
}
"""


class ReActAgent(BaseAgent):
    """
    ReAct agent with Plan → Act → Observe → Reflect → Retry (PAORR) loop.

    Each step:
      1. THINK  — LLM reasons about what to do next
      2. ACT    — executes action (default: returns thought)
      3. OBSERVE — captures the result
      4. REFLECT — LLM judges if the goal was met
      5. RETRY  — if not solved and attempts remain, feed error back and retry
    """

    name = "react"
    system_prompt = """\
You are a highly capable AI assistant with access to tools. Your mission is to
complete the user's task completely and correctly.

For every action, think out loud: reason about WHY you are choosing this
approach, WHAT you expect the result to be, and HOW you will verify success.
"""

    MAX_REFLECT_RETRIES = 3  # Max retries per step when reflection says "not solved"

    def __init__(self) -> None:
        super().__init__()
        self.llm = LLM()

    # ------------------------------------------------------------------
    # PAORR core
    # ------------------------------------------------------------------

    async def think(self) -> str:
        """P — Generate a reasoned thought from the LLM."""
        response = await self.llm.ask(self.memory.messages)
        self.memory.add(response)
        return response.content or ""

    async def act(self, thought: str) -> Optional[str]:
        """A — Default action: the thought itself. Subclasses override this."""
        return thought

    async def observe(self, result: Optional[str]) -> Observation:
        """O — Wrap the action result into an Observation."""
        if self._task_history:
            step = self._task_history.last_step()
            if step is None:
                step = self._task_history.add_step(f"step {self._step_count}")
        obs = Observation(
            tool_name="think",
            args={},
            output=result,
            error=None,
            success=bool(result),
        )
        return obs

    async def reflect(self, goal: str, obs: Observation) -> Reflection:
        """R — Ask the LLM to reflect on whether the observation solved the goal."""
        prompt = (
            f"Goal: {goal}\n\n"
            f"Observation:\n{obs.summary()}\n\n"
            "Did this observation solve the goal?"
        )
        try:
            response = await self.llm.ask(
                [Message.system(_REFLECT_SYSTEM), Message.user(prompt)]
            )
            raw = (response.content or "{}").strip()
            # Strip markdown fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            data = json.loads(raw)
            return Reflection(
                step_goal=goal,
                observation_summary=obs.summary(),
                solved=bool(data.get("solved", False)),
                reason=str(data.get("reason", "Unknown")),
                next_action=data.get("next_action"),
            )
        except Exception as e:
            logger.debug(f"[{self.name}] Reflection parse error: {e}")
            # If reflection fails, assume success to avoid blocking
            return Reflection(
                step_goal=goal,
                observation_summary=obs.summary(),
                solved=True,
                reason=f"Reflection unavailable ({e}); assuming success.",
            )

    # ------------------------------------------------------------------
    # Step entry point
    # ------------------------------------------------------------------

    async def step(self) -> Optional[str]:
        """Full PAORR step."""
        if self._task_history:
            current_step = self._task_history.add_step(f"step {self._step_count}")
        else:
            current_step = None

        goal = f"step {self._step_count}"

        for attempt in range(1, self.MAX_REFLECT_RETRIES + 1):
            # PLAN / THINK
            thought = await self.think()
            logger.debug(f"[{self.name}] Thought: {thought[:160]}")

            # ACT
            result = await self.act(thought)

            # OBSERVE
            obs = await self.observe(result)
            if current_step:
                obs.attempt = attempt
                current_step.observations.append(obs)

            # Simple termination check from thought content
            lower = (thought + (result or "")).lower()
            if any(kw in lower for kw in ["task complete", "task is complete", "all done", "finished"]):
                self.state = AgentState.FINISHED
                if current_step:
                    current_step.resolved = True
                return result

            # REFLECT — only if more retries remain
            if attempt < self.MAX_REFLECT_RETRIES:
                reflection = await self.reflect(goal, obs)
                if current_step:
                    current_step.reflection = reflection
                logger.debug(f"[{self.name}] Reflect: solved={reflection.solved} — {reflection.reason}")

                if reflection.solved:
                    if current_step:
                        current_step.resolved = True
                    return result

                # RETRY — inject reflection into memory so the LLM self-corrects
                retry_msg = (
                    f"⚠ Reflection (attempt {attempt}/{self.MAX_REFLECT_RETRIES}):\n"
                    f"{reflection.to_prompt()}\n\n"
                    "The sub-goal was NOT solved. Analyse the failure and try a "
                    "different approach in your next response."
                )
                self.memory.add(Message.user(retry_msg))
                logger.info(f"[{self.name}] Retrying step (attempt {attempt+1})...")
            else:
                if current_step:
                    current_step.resolved = bool(result)
                return result

        return None
