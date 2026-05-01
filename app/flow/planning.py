from __future__ import annotations

import asyncio
import uuid
from typing import Optional

from app.agent.manus import Manus
from app.agent.data_analysis import DataAnalysisAgent
from app.config import Config
from app.logger import logger
from app.schema import Message, Plan, PlanStep, StepStatus
from app.tool.planning import PlanningTool


class PlanningFlow:
    """
    Decomposes a high-level task into steps, then dispatches each step to
    an appropriate agent.
    """

    def __init__(self, timeout: int = 3600) -> None:
        self._timeout = timeout
        self._planner_tool = PlanningTool()
        self._plan: Optional[Plan] = None

    async def run(self, goal: str) -> str:
        cfg = Config.get()
        logger.info(f"[PlanningFlow] Starting goal: {goal[:100]}")

        plan = await self._create_plan(goal)
        self._plan = plan

        results: list[str] = []
        try:
            async with asyncio.timeout(self._timeout):
                for step in plan.steps:
                    if plan.is_complete():
                        break
                    logger.info(f"[PlanningFlow] Executing step {step.id}: {step.description}")
                    step.status = StepStatus.IN_PROGRESS

                    agent = self._select_agent(step, cfg)
                    try:
                        result = await agent.run(step.description)
                        step.status = StepStatus.COMPLETED
                        results.append(f"Step {step.id} completed: {result[:300]}")
                    except Exception as e:
                        logger.error(f"[PlanningFlow] Step {step.id} failed: {e}")
                        step.status = StepStatus.BLOCKED
                        results.append(f"Step {step.id} blocked: {e}")
        except asyncio.TimeoutError:
            logger.warning("[PlanningFlow] Global timeout reached.")
            results.append("Flow timed out.")

        summary = "\n".join(results)
        logger.info("[PlanningFlow] Complete.")
        return summary

    async def _create_plan(self, goal: str) -> Plan:
        from app.llm.llm import LLM
        llm = LLM()
        prompt = (
            f"Break down this goal into 3-6 concrete, actionable steps:\n\n{goal}\n\n"
            "Respond with ONLY a numbered list, one step per line, nothing else."
        )
        response = await llm.ask([Message.user(prompt)])
        raw = response.content or ""
        steps = []
        for line in raw.strip().splitlines():
            line = line.strip().lstrip("0123456789.-) ").strip()
            if line:
                steps.append(line)

        if not steps:
            steps = [goal]  # fallback: single step

        plan_id = str(uuid.uuid4())[:8]
        plan = Plan(
            id=plan_id,
            title=goal[:80],
            steps=[PlanStep(id=i, description=s) for i, s in enumerate(steps)],
        )
        logger.info(f"[PlanningFlow] Plan created with {len(plan.steps)} steps.")
        return plan

    def _select_agent(self, step: PlanStep, cfg: "Config") -> "BaseAgent":  # type: ignore[name-defined]
        desc_lower = step.description.lower()
        if cfg.runflow.enable_data_analysis and any(
            kw in desc_lower for kw in ["chart", "graph", "plot", "data", "analysis", "visuali"]
        ):
            return DataAnalysisAgent()
        return Manus()
