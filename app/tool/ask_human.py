from __future__ import annotations

import asyncio
from typing import Any

from app.schema import ToolResult
from app.tool.base import BaseTool


class AskHuman(BaseTool):
    name = "ask_human"
    description = "Ask the user a question and wait for their response via stdin."
    parameters = {
        "type": "object",
        "properties": {
            "question": {"type": "string", "description": "Question to ask the user."},
        },
        "required": ["question"],
    }

    async def execute(self, question: str, **_: Any) -> ToolResult:
        print(f"\n[ManusClaw asks]: {question}")
        loop = asyncio.get_event_loop()
        answer = await loop.run_in_executor(None, input, "Your answer: ")
        return ToolResult(output=f"User said: {answer}")
