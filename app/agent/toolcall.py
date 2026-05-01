from __future__ import annotations

import asyncio
import json
import random
from typing import Optional

from app.agent.react import ReActAgent
from app.logger import logger
from app.schema import AgentState, Message, ToolCall
from app.tool.base import ToolCollection
from app.tool.terminate import Terminate


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_TOOL_RETRIES = 4       # Max attempts per individual tool call
TOOL_RETRY_BASE  = 1.0     # Base backoff seconds
TOOL_RETRY_MAX   = 20.0    # Cap backoff


# ---------------------------------------------------------------------------
# ToolCallAgent
# ---------------------------------------------------------------------------

class ToolCallAgent(ReActAgent):
    """
    Agent that uses structured LLM function-calling to invoke tools.

    Upgrades over v1:
    - Tool execution is wrapped in try/except with exponential backoff retry
    - Exact error text is fed back to the LLM so it can self-correct
    - Every observation is recorded in TaskHistory
    - Terminate signal is detected via ToolResult.system == "terminate"
    - Stuck-loop guard from BaseAgent is active
    """

    name = "toolcall"
    system_prompt = """\
You are a capable AI agent with structured tool access. Your job is to complete
the user's task by selecting and calling the right tool at each step.

Think out loud BEFORE each tool call. Explain:
  - What sub-goal you are targeting
  - Which tool you chose and why
  - What you expect the output to look like

After each tool result, verify that it actually solved the sub-goal before
proceeding. If it failed or returned unexpected output, analyse why and choose
a different tool or different arguments.
"""

    def __init__(self, tools: Optional[ToolCollection] = None) -> None:
        super().__init__()
        self.tools: ToolCollection = tools or ToolCollection(Terminate())
        if self.tools.get("terminate") is None:
            self.tools.add(Terminate())

    # ------------------------------------------------------------------
    # PAORR overrides
    # ------------------------------------------------------------------

    async def think(self) -> str:
        """Ask the LLM which tool to call next (function-calling mode)."""
        schemas = self.tools.to_openai_schemas()
        response = await self.llm.ask_tool(self.memory.messages, tools=schemas)
        self.memory.add(response)
        return response.content or ""

    async def act(self, thought: str) -> Optional[str]:
        """Execute all tool calls from the last LLM response, with retry logic."""
        last_msg = self.memory.messages[-1]
        if not last_msg.tool_calls:
            return thought or None

        outputs: list[str] = []

        for tc in last_msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments) if tc.function.arguments else {}
            except json.JSONDecodeError as e:
                args = {}
                logger.warning(f"[{self.name}] JSON decode error for {name} args: {e}")

            result = await self._execute_with_retry(name, args, tool_call_id=tc.id)
            outputs.append(str(result))

            # Detect terminate
            if result.system == "terminate":
                self.state = AgentState.FINISHED

        return "\n".join(outputs) if outputs else None

    async def _execute_with_retry(self, name: str, args: dict, tool_call_id: str):
        """
        Execute a tool call with up to MAX_TOOL_RETRIES attempts.
        On failure: feed the exact error back to the LLM, wait, and retry.
        """
        from app.schema import ToolResult

        last_result = ToolResult(error="Unknown error")
        wait = TOOL_RETRY_BASE

        for attempt in range(1, MAX_TOOL_RETRIES + 1):
            try:
                logger.info(f"[{self.name}] Tool call ({attempt}/{MAX_TOOL_RETRIES}): {name}({self._fmt_args(args)})")
                result = await self.tools.execute(name, **args)
                logger.info(f"[{self.name}] Tool result: {str(result)[:300]}")

                # Record in task history
                self.record_observation(
                    tool_name=name,
                    args=args,
                    output=result.output,
                    error=result.error,
                    attempt=attempt,
                )

                # Feed result back into memory
                tool_msg = Message.tool(
                    content=str(result),
                    tool_call_id=tool_call_id,
                    name=name,
                )
                self.memory.add(tool_msg)

                # If there's an error in the result, ask LLM to self-correct
                if result.error and attempt < MAX_TOOL_RETRIES:
                    retry_msg = (
                        f"⚠ Tool '{name}' returned an error on attempt {attempt}:\n"
                        f"  Error: {result.error}\n\n"
                        f"Analyse this error carefully. What caused it? "
                        f"In your NEXT response, call the appropriate tool with CORRECTED arguments "
                        f"or choose a completely different approach. "
                        f"Do NOT repeat the exact same call."
                    )
                    self.memory.add(Message.user(retry_msg))

                    # Re-ask the LLM to pick a corrected call
                    schemas = self.tools.to_openai_schemas()
                    correction = await self.llm.ask_tool(self.memory.messages, tools=schemas)
                    self.memory.add(correction)

                    if correction.tool_calls:
                        # Recursively execute the corrected call
                        corrected_tc = correction.tool_calls[0]
                        corrected_name = corrected_tc.function.name
                        try:
                            corrected_args = json.loads(corrected_tc.function.arguments or "{}")
                        except json.JSONDecodeError:
                            corrected_args = {}
                        logger.info(f"[{self.name}] LLM self-corrected to: {corrected_name}({self._fmt_args(corrected_args)})")
                        name, args = corrected_name, corrected_args
                        await asyncio.sleep(min(wait, TOOL_RETRY_MAX))
                        wait *= 2 + random.uniform(0, 0.5)
                        continue

                return result

            except Exception as exc:
                logger.error(f"[{self.name}] Tool '{name}' raised exception (attempt {attempt}): {exc}")
                last_result = ToolResult(error=str(exc))

                self.record_observation(
                    tool_name=name, args=args, output=None, error=str(exc), attempt=attempt
                )

                if attempt < MAX_TOOL_RETRIES:
                    err_msg = (
                        f"⚠ Tool '{name}' crashed with exception on attempt {attempt}:\n"
                        f"  Exception: {exc}\n\n"
                        f"This was an unexpected crash. In your NEXT response, try a different "
                        f"tool or a safer set of arguments."
                    )
                    # Add a synthetic tool result so the message chain stays valid
                    self.memory.add(Message.tool(
                        content=f"ERROR: {exc}",
                        tool_call_id=tool_call_id,
                        name=name,
                    ))
                    self.memory.add(Message.user(err_msg))
                    await asyncio.sleep(min(wait, TOOL_RETRY_MAX))
                    wait *= 2 + random.uniform(0, 0.5)

        # All retries exhausted
        logger.error(f"[{self.name}] Tool '{name}' failed after {MAX_TOOL_RETRIES} attempts.")
        self.memory.add(Message.tool(
            content=str(last_result),
            tool_call_id=tool_call_id,
            name=name,
        ))
        return last_result

    # ------------------------------------------------------------------
    # Step entry point (override ReActAgent's PAORR step)
    # ------------------------------------------------------------------

    async def step(self) -> Optional[str]:
        """One step: think (tool selection) → act (tool execution) → observe."""
        if self._task_history:
            self._task_history.add_step(f"step {self._step_count}")

        await self.think()
        result = await self.act("")

        # If we just terminated, return
        if self.state == AgentState.FINISHED:
            return result

        # Lightweight reflection: check if LLM says it's done
        last_content = ""
        for m in reversed(self.memory.messages):
            if m.role.value == "assistant" and m.content:
                last_content = m.content.lower()
                break
        if any(kw in last_content for kw in ["task complete", "all done", "finished", "done"]):
            self.state = AgentState.FINISHED

        return result

    def _fmt_args(self, args: dict) -> str:
        s = json.dumps(args, default=str)
        return s[:120] + "..." if len(s) > 120 else s

    async def cleanup(self) -> None:
        await self.tools.cleanup_all()
