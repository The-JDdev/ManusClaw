from __future__ import annotations

"""
PlanningFlow — multi-agent orchestration with PAORR-aware step dispatch.

Upgrade summary (v2):
  • LLM-generated plan is richer: includes success criteria per step
  • Each step gets a dedicated TaskHistory
  • Step failure → re-plan remaining steps before continuing
  • Blocked steps are retried once with a different agent
  • Global timeout enforced via asyncio.timeout
"""

import asyncio
import uuid
from typing import Optional

from app.config import Config
from app.logger import logger
from app.schema import Message, Plan, PlanStep, StepStatus


_PLAN_SYSTEM = """\
You are a task decomposition expert. Break down the goal into a numbered list
of concrete, independently executable steps. For each step, also provide a
one-line success criterion in parentheses.

Format (strictly follow this):
1. <action> (<success criterion>)
2. <action> (<success criterion>)
...

Respond ONLY with the numbered list. No preamble, no explanation.
"""

_REPLAN_SYSTEM = """\
You are a task re-planner. The original plan had a blocked step. Review what
has been completed so far and output a revised numbered list of REMAINING steps
(skip already-completed ones). Keep the same format as above.
"""


class PlanningFlow:
    """
    Decomposes a high-level goal into steps, dispatches each to an agent,
    and handles failures with re-planning.
    """

    def __init__(self, timeout: int = 3600) -> None:
        self._timeout = timeout

    async def run(self, goal: str) -> str:
        logger.info(f"[PlanningFlow] ▶ Goal: {goal[:120]}")
        plan = await self._create_plan(goal)
        completed: list[str] = []
        blocked: list[str] = []

        try:
            async with asyncio.timeout(self._timeout):
                step_idx = 0
                while step_idx < len(plan.steps):
                    step = plan.steps[step_idx]

                    if step.status == StepStatus.COMPLETED:
                        step_idx += 1
                        continue

                    logger.info(f"[PlanningFlow] Step {step.id + 1}/{len(plan.steps)}: {step.description}")
                    step.status = StepStatus.IN_PROGRESS

                    agent = self._select_agent(step)
                    success = False

                    # First attempt
                    try:
                        result = await agent.run(step.description)
                        step.status = StepStatus.COMPLETED
                        completed.append(f"✓ Step {step.id + 1}: {step.description[:60]}\n  → {result[:200]}")
                        success = True
                    except Exception as e:
                        logger.warning(f"[PlanningFlow] Step {step.id + 1} failed (attempt 1): {e}")

                    # Retry once with a fresh agent if failed
                    if not success:
                        logger.info(f"[PlanningFlow] Retrying step {step.id + 1} with fresh agent...")
                        retry_agent = self._select_agent(step, prefer_safe=True)
                        try:
                            result = await retry_agent.run(
                                f"RETRY: The previous attempt at this step failed. "
                                f"Please try a different approach.\n\nStep: {step.description}"
                            )
                            step.status = StepStatus.COMPLETED
                            completed.append(f"✓ Step {step.id + 1} (retry): {step.description[:60]}\n  → {result[:200]}")
                            success = True
                        except Exception as e2:
                            logger.error(f"[PlanningFlow] Step {step.id + 1} blocked after retry: {e2}")
                            step.status = StepStatus.BLOCKED
                            blocked.append(f"✗ Step {step.id + 1}: {step.description[:60]} — {e2}")

                            # Re-plan remaining steps
                            remaining = plan.steps[step_idx + 1:]
                            if remaining:
                                logger.info("[PlanningFlow] Re-planning remaining steps...")
                                ctx = "\n".join(
                                    f"✓ {s.description}" for s in plan.steps[:step_idx]
                                    if s.status == StepStatus.COMPLETED
                                )
                                new_plan = await self._replan(goal, ctx, remaining)
                                plan.steps = plan.steps[:step_idx + 1] + new_plan.steps

                    step_idx += 1

        except asyncio.TimeoutError:
            logger.warning("[PlanningFlow] Global timeout reached.")
            blocked.append("⏱ Flow timed out before all steps completed.")

        lines = ["=== PlanningFlow Result ===", ""]
        if completed:
            lines += ["Completed:"] + completed + [""]
        if blocked:
            lines += ["Blocked / Skipped:"] + blocked + [""]
        lines.append(f"Total: {len(completed)} completed, {len(blocked)} blocked.")
        summary = "\n".join(lines)
        logger.info("[PlanningFlow] ■ Complete.")
        return summary

    # ------------------------------------------------------------------
    # Plan creation / re-planning
    # ------------------------------------------------------------------

    async def _create_plan(self, goal: str) -> Plan:
        from app.llm.llm import LLM
        llm = LLM()
        response = await llm.ask([
            Message.system(_PLAN_SYSTEM),
            Message.user(f"Goal: {goal}"),
        ])
        return self._parse_plan(response.content or "", goal)

    async def _replan(self, goal: str, completed_ctx: str, remaining: list[PlanStep]) -> Plan:
        from app.llm.llm import LLM
        llm = LLM()
        prompt = (
            f"Original goal: {goal}\n\n"
            f"Completed so far:\n{completed_ctx or '(none)'}\n\n"
            f"Remaining steps (may need revision):\n"
            + "\n".join(f"- {s.description}" for s in remaining)
        )
        response = await llm.ask([
            Message.system(_REPLAN_SYSTEM),
            Message.user(prompt),
        ])
        return self._parse_plan(response.content or "", goal)

    def _parse_plan(self, raw: str, goal: str) -> Plan:
        steps: list[PlanStep] = []
        for line in raw.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            # Strip leading numbering
            for sep in (". ", ") ", "- "):
                parts = line.split(sep, 1)
                if len(parts) == 2 and parts[0].lstrip("0123456789").strip() == "":
                    line = parts[1].strip()
                    break
            if line:
                steps.append(PlanStep(id=len(steps), description=line))

        if not steps:
            steps = [PlanStep(id=0, description=goal)]

        logger.info(f"[PlanningFlow] Plan: {len(steps)} steps.")
        return Plan(id=str(uuid.uuid4())[:8], title=goal[:80], steps=steps)

    # ------------------------------------------------------------------
    # Agent selection
    # ------------------------------------------------------------------

    def _select_agent(self, step: PlanStep, prefer_safe: bool = False):
        from app.agent.manus import Manus
        from app.agent.data_analysis import DataAnalysisAgent

        cfg = Config.get()
        desc_lower = step.description.lower()

        if (
            cfg.runflow.enable_data_analysis
            and not prefer_safe
            and any(kw in desc_lower for kw in ["chart", "graph", "plot", "analysis", "visuali", "data"])
        ):
            return DataAnalysisAgent()

        return Manus()
