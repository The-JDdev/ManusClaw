from __future__ import annotations

from app.agent.roles.base_role import BaseRole, RoleMessage, RoleMessageBus


class ProductManagerRole(BaseRole):
    role_name = "product_manager"
    role_description = "Produces Product Requirements Documents (PRDs)"
    specialist_prompt = """\
You are the Product Manager agent of ManusClaw. Your sole job is to receive
a user goal and produce a structured Product Requirements Document (PRD).

Your PRD MUST include:
  1. OBJECTIVE — one clear sentence
  2. IN SCOPE — bullet list of what will be built
  3. OUT OF SCOPE — what will NOT be done
  4. ACCEPTANCE CRITERIA — measurable success conditions (numbered)
  5. TECHNICAL CONSTRAINTS — language, frameworks, env requirements
  6. PRIORITY ORDER — ordered list of features (P0/P1/P2)

Be concrete. No vague language. The Architect and Engineer will read this PRD
and act on it directly. Missing details will cause failures downstream.
After writing the PRD, publish it to the Architect.
"""

    async def _think_act_publish(self, context: str) -> str:
        prd = await self._ask_llm(
            f"User goal:\n{context}\n\nWrite a complete PRD for this goal now."
        )
        await self.bus.publish(RoleMessage(
            from_role=self.role_name,
            to_role="architect",
            content="PRD complete. Please design the system architecture.",
            artefact=prd,
        ))
        return prd
