from __future__ import annotations

"""
FastAPI-based MCP server that exposes local ManusClaw tools to external MCP clients.
"""

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.tool.base import ToolCollection
from app.tool.bash import Bash
from app.tool.browser_use_tool import BrowserUseTool
from app.tool.str_replace_editor import StrReplaceEditor
from app.tool.terminate import Terminate


def build_mcp_server() -> FastAPI:
    app = FastAPI(title="ManusClaw MCP Server", version="1.0.0")

    _tools = ToolCollection(
        Bash(),
        BrowserUseTool(),
        StrReplaceEditor(),
        Terminate(),
    )

    class CallRequest(BaseModel):
        name: str
        arguments: dict[str, Any] = {}

    @app.get("/tools/list")
    async def list_tools() -> dict:
        return {
            "tools": [
                {
                    "name": t.name,
                    "description": t.description,
                    "inputSchema": t.parameters,
                }
                for t in _tools
            ]
        }

    @app.post("/tools/call")
    async def call_tool(req: CallRequest) -> dict:
        tool = _tools.get(req.name)
        if tool is None:
            raise HTTPException(status_code=404, detail=f"Tool '{req.name}' not found.")
        result = await tool(**req.arguments)
        return {"content": [{"type": "text", "text": str(result)}]}

    @app.get("/healthz")
    async def health() -> dict:
        return {"status": "ok", "tools": len(_tools)}

    return app
