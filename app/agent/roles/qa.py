from __future__ import annotations

from app.agent.roles.base_role import BaseRole, RoleMessage, RoleMessageBus


class QARole(BaseRole):
    role_name = "qa"
    role_description = "Validates implementation against acceptance criteria"
    specialist_prompt = """\
You are the QA agent of ManusClaw. You receive implementation output from the
Engineer and validate it against the acceptance criteria in the PRD.

Your QA process:
  1. Read each acceptance criterion from the PRD
  2. For each criterion: run a test (bash, python_execute, or manual check)
  3. Record: PASS / FAIL / PARTIAL with evidence
  4. For any FAIL: describe the exact defect and which file/function is wrong
  5. If critical failures exist (P0 criteria): publish a REWORK request to Engineer
  6. If all P0 criteria pass: publish a RELEASE APPROVED signal

Your output MUST include:
  - QA REPORT header
  - Per-criterion result (numbered, matching PRD)
  - Summary table: PASS / FAIL / PARTIAL counts
  - Verdict: APPROVED / REWORK REQUIRED
  - If REWORK: list exact defects with file paths
"""

    async def _think_act_publish(self, context: str) -> str:
        from app.agent.manus import Manus

        # Observe: pull implementation from bus
        msgs = await self.bus.drain(self.role_name)
        impl = next((m.artefact for m in msgs if m.artefact), context)

        # Delegate QA checks to Manus (it can run code, check files, etc.)
        qa_agent = Manus()
        qa_result = await qa_agent.run(
            f"You are a QA engineer. Validate the following implementation:\n\n"
            f"{impl}\n\n"
            f"For each stated feature or function: run a test, check the output, "
            f"and record PASS/FAIL with evidence. Save the QA report to workspace/qa_report.md. "
            f"Terminate with the final QA verdict."
        )

        verdict = "APPROVED" if "fail" not in qa_result.lower() else "REWORK REQUIRED"
        await self.bus.publish(RoleMessage(
            from_role=self.role_name,
            to_role="*",
            content=f"QA Verdict: {verdict}",
            artefact=qa_result,
        ))
        return qa_result
