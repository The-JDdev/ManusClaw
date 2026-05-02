from __future__ import annotations

from app.agent.roles.base_role import BaseRole, RoleMessage, RoleMessageBus


class EngineerRole(BaseRole):
    role_name = "engineer"
    role_description = "Implements code from the Architect's plan using Manus tools"
    specialist_prompt = """\
You are the Engineer agent of ManusClaw. You receive an implementation plan
from the Architect and execute each task using available tools.

Your process for EVERY task:
  1. Read the task description carefully
  2. Identify the correct tool (python_execute, bash, str_replace_editor)
  3. Write/run the code
  4. Verify the output (does it match the acceptance criterion?)
  5. If it fails: debug, fix, re-run (up to 3 attempts)
  6. Mark the task complete only when verified

Rules:
  - Always run code — never just write it and assume it works
  - Save all outputs to workspace/
  - Use str_replace_editor to write files, bash/python_execute to run them
  - After implementing all tasks, publish a summary to QA
"""

    async def _think_act_publish(self, context: str) -> str:
        from app.agent.manus import Manus

        # Observe: pull design from bus
        msgs = await self.bus.drain(self.role_name)
        design = next((m.artefact for m in msgs if m.artefact), context)

        # Delegate actual implementation to the full Manus agent
        # (which has all tools + PAORR loop + retry logic)
        engineer_agent = Manus()
        implementation_result = await engineer_agent.run(
            f"You are implementing code based on this design plan.\n\n"
            f"DESIGN PLAN:\n{design}\n\n"
            f"Implement EVERY task in the plan. Run and verify each one. "
            f"Save all outputs to workspace/. "
            f"When all tasks are done, call terminate with a summary."
        )

        await self.bus.publish(RoleMessage(
            from_role=self.role_name,
            to_role="qa",
            content="Implementation complete. Please run QA validation.",
            artefact=implementation_result,
        ))
        return implementation_result
