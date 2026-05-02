from __future__ import annotations

"""
MultiAgentOrchestrator — DAG-based multi-role execution engine.

Roles execute in topological order based on declared dependencies.
Each role Observes → Thinks → Acts → Publishes via the async message bus.

Default pipeline:
  ProductManager → Architect → Engineer → QA

Custom pipelines can be injected by passing a roles_order list and
a dependency_graph dict.
"""

import asyncio
from typing import Optional

from app.agent.roles.base_role import RoleMessage, RoleMessageBus
from app.agent.roles.product_manager import ProductManagerRole
from app.agent.roles.architect import ArchitectRole
from app.agent.roles.engineer import EngineerRole
from app.agent.roles.qa import QARole
from app.db.session import SessionDB
from app.logger import logger
from app.permissions.gate import AgentMode, PermissionGate


_DEFAULT_PIPELINE = [
    "product_manager",
    "architect",
    "engineer",
    "qa",
]

_DEFAULT_DEPS: dict[str, list[str]] = {
    "product_manager": [],
    "architect": ["product_manager"],
    "engineer": ["architect"],
    "qa": ["engineer"],
}


class MultiAgentOrchestrator:
    """
    Runs a set of specialist roles in dependency order (topological sort).
    Each role receives the accumulated context from all predecessors.
    """

    def __init__(
        self,
        mode: AgentMode = AgentMode.BUILD,
        pipeline: Optional[list[str]] = None,
        deps: Optional[dict[str, list[str]]] = None,
        timeout: int = 7200,
    ) -> None:
        self.mode = mode
        self.pipeline = pipeline or _DEFAULT_PIPELINE
        self.deps = deps or _DEFAULT_DEPS
        self.timeout = timeout
        self.bus = RoleMessageBus()
        self.db = SessionDB()
        self.gate = PermissionGate(mode=mode)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run(self, goal: str) -> str:
        logger.info(f"[Orchestrator] ▶ Multi-agent run | mode={self.mode} | goal={goal[:80]}")
        session_id = await self.db.create_session(goal, agent_name="orchestrator", mode=self.mode.value)

        order = self._topological_sort()
        logger.info(f"[Orchestrator] Execution order: {' → '.join(order)}")

        results: dict[str, str] = {}
        context = goal

        try:
            async with asyncio.timeout(self.timeout):
                for role_name in order:
                    logger.info(f"[Orchestrator] ── Role: {role_name} ──")
                    role = self._build_role(role_name)

                    # Inject accumulated context from upstream roles
                    role_input = self._build_role_input(goal, role_name, results)

                    try:
                        result = await role.run(role_input)
                        results[role_name] = result
                        logger.info(f"[Orchestrator] {role_name} ✓ ({len(result)} chars)")
                        await self.db.log_message(session_id, role_name, result[:2048])
                    except Exception as e:
                        logger.error(f"[Orchestrator] {role_name} failed: {e}")
                        results[role_name] = f"ERROR: {e}"
                        await self.db.log_message(session_id, role_name, f"ERROR: {e}")

        except asyncio.TimeoutError:
            logger.warning("[Orchestrator] Global timeout reached.")
            results["_timeout"] = "⏱ Orchestrator timed out."

        await self.db.close_session(session_id, state="finished", step_count=len(order))

        return self._build_summary(goal, results, order)

    # ------------------------------------------------------------------
    # Topological sort (Kahn's algorithm)
    # ------------------------------------------------------------------

    def _topological_sort(self) -> list[str]:
        in_degree = {r: len(self.deps.get(r, [])) for r in self.pipeline}
        queue = [r for r in self.pipeline if in_degree[r] == 0]
        order: list[str] = []
        dependents: dict[str, list[str]] = {r: [] for r in self.pipeline}
        for r, d_list in self.deps.items():
            for d in d_list:
                dependents[d].append(r)

        while queue:
            role = queue.pop(0)
            order.append(role)
            for dep in dependents.get(role, []):
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    queue.append(dep)

        if len(order) != len(self.pipeline):
            logger.warning("[Orchestrator] Cycle detected in DAG — falling back to linear order.")
            return self.pipeline[:]

        return order

    # ------------------------------------------------------------------
    # Role factory
    # ------------------------------------------------------------------

    def _build_role(self, role_name: str):
        role_map = {
            "product_manager": ProductManagerRole,
            "architect": ArchitectRole,
            "engineer": EngineerRole,
            "qa": QARole,
        }
        cls = role_map.get(role_name)
        if cls is None:
            raise ValueError(f"Unknown role: {role_name}")
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

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def _build_summary(self, goal: str, results: dict[str, str], order: list[str]) -> str:
        lines = [
            "═══════════════════════════════════════════════════",
            "  ManusClaw Multi-Agent Pipeline — Final Report",
            "═══════════════════════════════════════════════════",
            f"  Goal: {goal[:80]}",
            "",
        ]
        for r in order:
            res = results.get(r, "(no output)")
            status = "✓" if not res.startswith("ERROR") else "✗"
            lines.append(f"  {status} {r.replace('_', ' ').title()}: {res[:120]}...")
        if "_timeout" in results:
            lines.append(f"\n  ⏱ {results['_timeout']}")
        lines.append("═══════════════════════════════════════════════════")
        return "\n".join(lines)
