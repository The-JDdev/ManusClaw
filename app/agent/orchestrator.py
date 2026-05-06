from __future__ import annotations

"""
MultiAgentOrchestrator — DAG-based multi-role execution engine.

Architecture boundary
─────────────────────
Orchestrator  controls execution ORDER and session management.
              It does NOT implement task logic (that is Agent territory)
              or step planning (that is PlanningFlow territory).

Flow:
  ProductManager → Architect → Engineer → QA

Each role:
  1. Receives the accumulated context from its upstream predecessors
  2. Runs its Observe→Think→Act→Publish loop
  3. Returns a typed RoleResult written into the PipelineResult

Event hooks
───────────
Pass callables to on_stage_start / on_stage_complete / on_stage_error to
receive live events without subclassing. All hooks are async-safe (run via
asyncio.create_task) so they never block the pipeline.

Return types
────────────
run()          → str           (summary string — keeps server API stable)
run_pipeline() → PipelineResult (typed, structured)
"""

import asyncio
import time
from typing import Callable, Optional

from app.agent.roles.base_role import RoleMessage, RoleMessageBus
from app.agent.roles.product_manager import ProductManagerRole
from app.agent.roles.architect import ArchitectRole
from app.agent.roles.engineer import EngineerRole
from app.agent.roles.qa import QARole
from app.db.session import SessionDB
from app.exceptions import OrchestratorError, PipelineCycleError
from app.logger import logger
from app.permissions.gate import AgentMode, PermissionGate
from app.schema import PipelineResult, PipelineStageResult


_DEFAULT_PIPELINE: list[str] = [
    "product_manager",
    "architect",
    "engineer",
    "qa",
]

_DEFAULT_DEPS: dict[str, list[str]] = {
    "product_manager": [],
    "architect":       ["product_manager"],
    "engineer":        ["architect"],
    "qa":              ["engineer"],
}


class MultiAgentOrchestrator:
    """
    Runs specialist roles in dependency order (topological sort via Kahn's algorithm).
    Each role receives the accumulated context from all its upstream predecessors.
    """

    def __init__(
        self,
        mode:                AgentMode                              = AgentMode.BUILD,
        pipeline:            Optional[list[str]]                   = None,
        deps:                Optional[dict[str, list[str]]]        = None,
        timeout:             int                                    = 7200,
        on_stage_start:      Optional[Callable[..., object]]       = None,
        on_stage_complete:   Optional[Callable[..., object]]       = None,
        on_stage_error:      Optional[Callable[..., object]]       = None,
    ) -> None:
        self.mode      = mode
        self.pipeline  = pipeline or _DEFAULT_PIPELINE
        self.deps      = deps     or _DEFAULT_DEPS
        self.timeout   = timeout
        self.bus       = RoleMessageBus()
        self.db        = SessionDB()
        self.gate      = PermissionGate(mode=mode)
        self._on_stage_start    = on_stage_start
        self._on_stage_complete = on_stage_complete
        self._on_stage_error    = on_stage_error

    async def run(self, goal: str) -> str:
        result = await self.run_pipeline(goal)
        return result.to_summary()

    async def run_pipeline(self, goal: str) -> PipelineResult:
        import uuid
        pipeline_id = str(uuid.uuid4())[:8]

        logger.info(
            f"[Orchestrator:{pipeline_id}] ▶ Multi-agent run "
            f"| mode={self.mode.value} | goal={goal[:80]}"
        )

        session_id = await self.db.create_session(
            goal, agent_name="orchestrator", mode=self.mode.value
        )

        try:
            order = self._topological_sort()
        except PipelineCycleError as e:
            raise OrchestratorError(str(e), pipeline=self.pipeline) from e

        logger.info(
            f"[Orchestrator:{pipeline_id}] Execution order: {' → '.join(order)}"
        )

        pipeline_result = PipelineResult(pipeline_id=pipeline_id, goal=goal)
        results: dict[str, str] = {}
        t_pipeline = time.monotonic()

        try:
            async with asyncio.timeout(self.timeout):
                for role_name in order:
                    logger.info(f"[Orchestrator:{pipeline_id}] ── Role: {role_name} ──")
                    await self._fire_hook(self._on_stage_start, role_name)

                    role = self._build_role(role_name)
                    role_input = self._build_role_input(goal, role_name, results)
                    t0 = time.monotonic()

                    try:
                        output = await role.run(role_input)
                        results[role_name] = output
                        elapsed = time.monotonic() - t0

                        logger.info(
                            f"[Orchestrator:{pipeline_id}] "
                            f"{role_name} ✓ ({len(output)} chars, {elapsed:.1f}s)"
                        )
                        await self.db.log_message(session_id, role_name, output[:2048])

                        pipeline_result.stages.append(PipelineStageResult(
                            role_name=role_name,
                            status="completed",
                            output=output,
                            duration_s=round(elapsed, 2),
                        ))
                        await self._fire_hook(self._on_stage_complete, role_name, output)

                    except Exception as e:
                        elapsed = time.monotonic() - t0
                        err_msg = f"ERROR: {e}"
                        logger.error(f"[Orchestrator:{pipeline_id}] {role_name} ✗ {err_msg}")
                        results[role_name] = err_msg
                        await self.db.log_message(session_id, role_name, err_msg)

                        pipeline_result.stages.append(PipelineStageResult(
                            role_name=role_name,
                            status="error",
                            output=err_msg,
                            duration_s=round(elapsed, 2),
                        ))
                        await self._fire_hook(self._on_stage_error, role_name, err_msg)

        except asyncio.TimeoutError:
            logger.warning(f"[Orchestrator:{pipeline_id}] Global timeout reached.")
            pipeline_result.timed_out = True

        pipeline_result.total_duration_s = round(time.monotonic() - t_pipeline, 2)
        pipeline_result.verdict = self._derive_verdict(results, pipeline_result.timed_out)

        final_state = "timeout" if pipeline_result.timed_out else "finished"
        await self.db.close_session(session_id, state=final_state, step_count=len(order))

        logger.info(
            f"[Orchestrator:{pipeline_id}] ■ Pipeline complete. "
            f"verdict={pipeline_result.verdict} "
            f"duration={pipeline_result.total_duration_s:.1f}s"
        )
        return pipeline_result

    def _topological_sort(self) -> list[str]:
        in_degree = {r: len(self.deps.get(r, [])) for r in self.pipeline}
        queue = [r for r in self.pipeline if in_degree[r] == 0]
        order: list[str] = []
        dependents: dict[str, list[str]] = {r: [] for r in self.pipeline}

        for r, d_list in self.deps.items():
            for d in d_list:
                if d in dependents:
                    dependents[d].append(r)

        while queue:
            role = queue.pop(0)
            order.append(role)
            for dep in dependents.get(role, []):
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    queue.append(dep)

        if len(order) != len(self.pipeline):
            raise PipelineCycleError(
                "Dependency graph contains a cycle — cannot determine execution order.",
                pipeline=self.pipeline,
            )

        return order

    def _build_role(self, role_name: str):
        role_map = {
            "product_manager": ProductManagerRole,
            "architect":       ArchitectRole,
            "engineer":        EngineerRole,
            "qa":              QARole,
        }
        cls = role_map.get(role_name)
        if cls is None:
            raise OrchestratorError(f"Unknown role: '{role_name}'", pipeline=self.pipeline)
        return cls(self.bus)

    def _build_role_input(self, goal: str, role_name: str, results: dict[str, str]) -> str:
        upstream = self.deps.get(role_name, [])
        if not upstream:
            return goal
        parts = [f"ORIGINAL GOAL:\n{goal}"]
        for up in upstream:
            if up in results:
                parts.append(f"\n{up.upper().replace('_', ' ')} OUTPUT:\n{results[up][:3000]}")
        return "\n\n".join(parts)

    @staticmethod
    def _derive_verdict(results: dict[str, str], timed_out: bool) -> str:
        if timed_out:
            return "timeout"
        qa_out = results.get("qa", "").upper()
        if "APPROVED" in qa_out:
            return "approved"
        if "REWORK" in qa_out:
            return "rework"
        any_error = any(v.startswith("ERROR:") for v in results.values())
        if any_error:
            return "error"
        return "unknown"

    @staticmethod
    async def _fire_hook(hook: Optional[Callable], *args: object) -> None:
        if hook is None:
            return
        try:
            coro = hook(*args)
            if asyncio.iscoroutine(coro):
                asyncio.create_task(coro)
        except Exception as e:
            logger.debug(f"[Orchestrator] Hook error (non-fatal): {e}")
