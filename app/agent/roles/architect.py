from __future__ import annotations

from app.agent.roles.base_role import BaseRole, RoleMessage, RoleMessageBus


class ArchitectRole(BaseRole):
    role_name = "architect"
    role_description = "Produces system design and implementation plan from PRD"
    specialist_prompt = """\
You are the Architect agent of ManusClaw. You receive a PRD from the Product
Manager and produce a concrete system design document.

Your design MUST include:
  1. SYSTEM OVERVIEW — high-level architecture (1 paragraph)
  2. FILE STRUCTURE — exact directory tree with file purposes
  3. COMPONENT MAP — each component, its responsibility, its interface
  4. DATA FLOW — how data moves between components (numbered steps)
  5. TECHNOLOGY STACK — exact libs/versions to use
  6. IMPLEMENTATION PLAN — ordered task list for the Engineer
     Format: [TASK-N] <action> | File: <path> | Deps: [TASK-X, ...]

The implementation plan is a DAG — declare dependencies explicitly.
Be precise. The Engineer will implement each task exactly as described.
After writing the design, publish the implementation plan to the Engineer.
"""

    async def _think_act_publish(self, context: str) -> str:
        # Observe: pull PRD from bus (or use context directly)
        msgs = await self.bus.drain(self.role_name)
        prd = next((m.artefact for m in msgs if m.artefact), context)

        design = await self._ask_llm(
            f"PRD:\n{prd}\n\nWrite a complete system design and implementation plan now."
        )
        await self.bus.publish(RoleMessage(
            from_role=self.role_name,
            to_role="engineer",
            content="Design complete. Please implement each task in the plan.",
            artefact=design,
        ))
        return design
