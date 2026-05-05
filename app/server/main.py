from __future__ import annotations

"""
ManusClaw HTTP/WebSocket Server
================================
FastAPI backend that exposes the full ManusClaw agent engine via:
  • REST API   — session management, history queries, tool introspection
  • WebSocket  — real-time streaming of agent thoughts, tool calls, and outputs
  • API Key    — optional authentication via MANUSCLAW_API_KEY env var
  • CORS       — configurable via MANUSCLAW_ALLOWED_ORIGINS env var

Run with:
  python run_server.py
  # or
  uvicorn app.server.main:app --host 0.0.0.0 --port 8765 --reload
"""

import asyncio
import json
import os
import time
from typing import Any, Optional

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from app.db.session import SessionDB
from app.logger import logger
from app.permissions.gate import AgentMode

app = FastAPI(
    title="ManusClaw Agent Server",
    description="Autonomous AI agent engine by The-JDdev (SHS Shobuj)",
    version="3.0.0",
)

# ---------------------------------------------------------------------------
# CORS — explicitly configured; allow_credentials only when origins are known
# ---------------------------------------------------------------------------

_raw_origins = os.getenv("MANUSCLAW_ALLOWED_ORIGINS", "")
_allowed_origins: list[str] = (
    [o.strip() for o in _raw_origins.split(",") if o.strip()]
    if _raw_origins
    else []
)

if _allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# ---------------------------------------------------------------------------
# API Key authentication — enabled only when MANUSCLAW_API_KEY is set
# ---------------------------------------------------------------------------

_API_KEY = os.getenv("MANUSCLAW_API_KEY", "")
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(key: Optional[str] = Depends(_api_key_header)) -> None:
    if not _API_KEY:
        return
    if key != _API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")


# ---------------------------------------------------------------------------
# WebSocket manager
# ---------------------------------------------------------------------------

class ConnectionManager:
    def __init__(self):
        self.active: dict[str, WebSocket] = {}

    async def connect(self, ws: WebSocket, session_id: str) -> None:
        await ws.accept()
        self.active[session_id] = ws

    def disconnect(self, session_id: str) -> None:
        self.active.pop(session_id, None)

    async def send(self, session_id: str, data: dict) -> None:
        ws = self.active.get(session_id)
        if ws:
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                self.disconnect(session_id)

    async def broadcast(self, data: dict) -> None:
        for sid, ws in list(self.active.items()):
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                self.disconnect(sid)


manager = ConnectionManager()
db = SessionDB()


# ---------------------------------------------------------------------------
# Streaming agent wrapper — emits WebSocket events + uses unified session_id
# ---------------------------------------------------------------------------

class StreamingManus:
    """Wraps Manus agent with WebSocket event emission and unified session tracking."""

    def __init__(self, session_id: str, mode: AgentMode = AgentMode.BUILD) -> None:
        self.session_id = session_id
        self.mode = mode

    async def run(self, prompt: str) -> str:
        from app.agent.manus import Manus

        # Inject the server-minted session_id so the agent doesn't create a new one
        agent = Manus(mode=self.mode, session_id=self.session_id)

        original_step = agent.step

        async def patched_step():
            step_num = agent._step_count
            await manager.send(self.session_id, {
                "type": "step_start",
                "step": step_num,
                "ts": time.time(),
            })
            result = await original_step()
            if result:
                await manager.send(self.session_id, {
                    "type": "step_output",
                    "step": step_num,
                    "content": result[:2000],
                    "ts": time.time(),
                })
            return result

        agent.step = patched_step  # type: ignore

        try:
            final = await agent.run(prompt)
            await manager.send(self.session_id, {
                "type": "agent_done",
                "output": final[:4000],
                "state": agent.state.value,
                "ts": time.time(),
            })
            return final
        except Exception as e:
            await manager.send(self.session_id, {
                "type": "agent_error",
                "error": str(e),
                "ts": time.time(),
            })
            raise


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------

class RunRequest(BaseModel):
    prompt: str
    mode: str = "build"


class RunResponse(BaseModel):
    session_id: str
    status: str
    output: Optional[str] = None


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "version": "3.0.0", "agent": "ManusClaw"}


@app.get("/")
async def root():
    return {"message": "ManusClaw Agent Server v3.0 — connect via /ws/<session_id>"}


@app.post("/run", response_model=RunResponse, dependencies=[Depends(require_api_key)])
async def run_agent(req: RunRequest):
    """
    Fire-and-forget agent run. Returns session_id immediately.
    Connect to /ws/<session_id> for live streaming.
    """
    mode = AgentMode.PLAN if req.mode.lower() == "plan" else AgentMode.BUILD
    session_id = await db.create_session(req.prompt, mode=req.mode)

    async def _run():
        streamer = StreamingManus(session_id=session_id, mode=mode)
        try:
            await streamer.run(req.prompt)
        except Exception as e:
            logger.error(f"[Server] Agent run error: {e}")

    asyncio.create_task(_run())
    return RunResponse(session_id=session_id, status="running")


@app.post("/run/sync", response_model=RunResponse, dependencies=[Depends(require_api_key)])
async def run_agent_sync(req: RunRequest):
    """Synchronous run — waits for completion (no streaming)."""
    from app.agent.manus import Manus
    mode = AgentMode.PLAN if req.mode.lower() == "plan" else AgentMode.BUILD
    session_id = await db.create_session(req.prompt, mode=req.mode)
    try:
        agent = Manus(mode=mode, session_id=session_id)
        output = await agent.run(req.prompt)
        await db.close_session(session_id, state="finished")
        return RunResponse(session_id=session_id, status="finished", output=output)
    except Exception as e:
        await db.close_session(session_id, state="error")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions", dependencies=[Depends(require_api_key)])
async def list_sessions(limit: int = 20):
    sessions = await db.get_sessions(limit=limit)
    return {"sessions": sessions}


@app.get("/sessions/{session_id}/messages", dependencies=[Depends(require_api_key)])
async def get_messages(session_id: str):
    msgs = await db.get_session_messages(session_id)
    return {"session_id": session_id, "messages": msgs}


@app.get("/sessions/{session_id}/tool_calls", dependencies=[Depends(require_api_key)])
async def get_tool_calls(session_id: str):
    calls = await db.get_session_tool_calls(session_id)
    return {"session_id": session_id, "tool_calls": calls}


@app.get("/tools")
async def list_tools():
    from app.tool.base import ToolCollection
    from app.tool.python_execute import PythonExecute
    from app.tool.bash import Bash
    from app.tool.web_search import WebSearch
    from app.tool.str_replace_editor import StrReplaceEditor
    from app.tool.terminate import Terminate
    tools = ToolCollection(PythonExecute(), Bash(), WebSearch(), StrReplaceEditor(), Terminate())
    schemas = tools.to_openai_schemas()
    return {"tools": [{"name": s["function"]["name"], "description": s["function"]["description"]} for s in schemas]}


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    # API key check for WebSocket via query param or header
    if _API_KEY:
        token = (
            websocket.query_params.get("api_key")
            or websocket.headers.get("x-api-key", "")
        )
        if token != _API_KEY:
            await websocket.close(code=4001)
            return

    await manager.connect(websocket, session_id)
    logger.info(f"[Server] WebSocket connected: {session_id}")
    try:
        await websocket.send_text(json.dumps({
            "type": "connected",
            "session_id": session_id,
            "message": "ManusClaw WebSocket ready. Send {\"prompt\": \"...\"} to start.",
        }))
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"type": "error", "message": "Invalid JSON"}))
                continue

            if msg.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
                continue

            prompt = msg.get("prompt", "").strip()
            if not prompt:
                await websocket.send_text(json.dumps({"type": "error", "message": "No prompt provided"}))
                continue

            mode_str = msg.get("mode", "build")
            mode = AgentMode.PLAN if mode_str == "plan" else AgentMode.BUILD

            await websocket.send_text(json.dumps({"type": "agent_start", "prompt": prompt[:200]}))

            streamer = StreamingManus(session_id=session_id, mode=mode)
            try:
                await streamer.run(prompt)
            except Exception as e:
                await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))

    except WebSocketDisconnect:
        manager.disconnect(session_id)
        logger.info(f"[Server] WebSocket disconnected: {session_id}")


# ---------------------------------------------------------------------------
# Multi-agent endpoint
# ---------------------------------------------------------------------------

class MultiAgentRequest(BaseModel):
    goal: str
    mode: str = "build"
    roles: Optional[list[str]] = None


@app.post("/multi-agent", dependencies=[Depends(require_api_key)])
async def run_multi_agent(req: MultiAgentRequest):
    """Run the full ProductManager → Architect → Engineer → QA pipeline."""
    from app.agent.orchestrator import MultiAgentOrchestrator
    mode = AgentMode.PLAN if req.mode.lower() == "plan" else AgentMode.BUILD
    orchestrator = MultiAgentOrchestrator(mode=mode)
    result = await orchestrator.run(req.goal)
    return {"result": result}


# ---------------------------------------------------------------------------
# Packaged entry point (used by pyproject.toml script)
# ---------------------------------------------------------------------------

def serve() -> None:
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser(description="ManusClaw Agent Server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    uvicorn.run(
        "app.server.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
