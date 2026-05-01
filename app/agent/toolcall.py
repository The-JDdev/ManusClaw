from __future__ import annotations

import json
from typing import Optional

from app.agent.react import ReActAgent
from app.logger import logger
from app.schema import AgentState, Message, ToolCall
from app.tool.base import ToolCollection
from app.tool.terminate import Terminate


class ToolCallAgent(ReActAgent):
    """Agent that uses structured LLM function-calling to invoke tools."""

    name = "toolcall"
    system_prompt = (
        "You are a capable AI agent. Use the available tools to complete the task. "
        "When you are done, call the terminate tool with a reason."
    )

    def __init__(self, tools: Optional[ToolCollection] = None) -> None:
        super().__init__()
        self.tools: ToolCollection = tools or ToolCollection(Terminate())
        # Ensure terminate is always available
        if self.tools.get("terminate") is None:
            self.tools.add(Terminate())

    async def think(self) -> str:
        """Ask the LLM which tool to call next."""
        schemas = self.tools.to_openai_schemas()
        response = await self.llm.ask_tool(self.memory.messages, tools=schemas)
        self.memory.add(response)
        return response.content or ""

    async def act(self, thought: str) -> Optional[str]:
        """Execute any tool calls that came back from the LLM."""
        last_msg = self.memory.messages[-1]
        if not last_msg.tool_calls:
            return thought or None

        outputs = []
        for tc in last_msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments) if tc.function.arguments else {}
            except json.JSONDecodeError:
                args = {}

            logger.info(f"[{self.name}] Tool call: {name}({args})")
            result = await self.tools.execute(name, **args)
            logger.info(f"[{self.name}] Tool result: {str(result)[:200]}")

            # Check for terminate signal
            if result.system == "terminate":
                self.state = AgentState.FINISHED

            # Feed result back to memory
            tool_msg = Message.tool(
                content=str(result),
                tool_call_id=tc.id,
                name=name,
            )
            self.memory.add(tool_msg)
            outputs.append(str(result))

        return "\n".join(outputs) if outputs else None

    async def step(self) -> Optional[str]:
        await self.think()
        return await self.act("")

    async def cleanup(self) -> None:
        await self.tools.cleanup_all()
