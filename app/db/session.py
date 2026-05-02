from __future__ import annotations

"""
SessionDB — SQLite-backed session, message, and tool-call audit log.

Every agent run creates a Session record. Every message and tool call
is appended atomically so that any execution is fully recoverable.
"""

import asyncio
import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any, Optional

_DB_PATH = Path("workspace/.sessions/manusclaw.db")

_SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS sessions (
    id          TEXT PRIMARY KEY,
    goal        TEXT,
    agent_name  TEXT,
    mode        TEXT DEFAULT 'build',
    started_at  REAL,
    ended_at    REAL,
    state       TEXT DEFAULT 'running',
    step_count  INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT REFERENCES sessions(id),
    role        TEXT,
    content     TEXT,
    ts          REAL
);

CREATE TABLE IF NOT EXISTS tool_calls (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT REFERENCES sessions(id),
    step        INTEGER,
    tool_name   TEXT,
    args        TEXT,
    output      TEXT,
    error       TEXT,
    success     INTEGER,
    attempt     INTEGER DEFAULT 1,
    duration_ms INTEGER,
    ts          REAL
);

CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_tool_calls_session ON tool_calls(session_id);
"""


class SessionDB:
    """
    Thread-safe async wrapper around the SQLite audit DB.
    Safe to share across coroutines — all writes go through asyncio.to_thread.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or _DB_PATH
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None

    def _ensure(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(
                str(self._db_path),
                check_same_thread=False,
            )
            self._conn.executescript(_SCHEMA)
            self._conn.commit()
        return self._conn

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    async def create_session(
        self,
        goal: str,
        agent_name: str = "manus",
        mode: str = "build",
    ) -> str:
        sid = str(uuid.uuid4())[:12]
        conn = await asyncio.to_thread(self._ensure)
        await asyncio.to_thread(
            conn.execute,
            "INSERT INTO sessions (id, goal, agent_name, mode, started_at) VALUES (?,?,?,?,?)",
            (sid, goal, agent_name, mode, time.time()),
        )
        await asyncio.to_thread(conn.commit)
        return sid

    async def close_session(self, session_id: str, state: str = "finished", step_count: int = 0) -> None:
        conn = await asyncio.to_thread(self._ensure)
        await asyncio.to_thread(
            conn.execute,
            "UPDATE sessions SET ended_at=?, state=?, step_count=? WHERE id=?",
            (time.time(), state, step_count, session_id),
        )
        await asyncio.to_thread(conn.commit)

    # ------------------------------------------------------------------
    # Message logging
    # ------------------------------------------------------------------

    async def log_message(self, session_id: str, role: str, content: Optional[str]) -> None:
        if not content:
            return
        conn = await asyncio.to_thread(self._ensure)
        await asyncio.to_thread(
            conn.execute,
            "INSERT INTO messages (session_id, role, content, ts) VALUES (?,?,?,?)",
            (session_id, role, content[:4096], time.time()),
        )
        await asyncio.to_thread(conn.commit)

    # ------------------------------------------------------------------
    # Tool call logging
    # ------------------------------------------------------------------

    async def log_tool_call(
        self,
        session_id: str,
        step: int,
        tool_name: str,
        args: dict,
        output: Optional[str],
        error: Optional[str],
        attempt: int = 1,
        duration_ms: int = 0,
    ) -> None:
        conn = await asyncio.to_thread(self._ensure)
        await asyncio.to_thread(
            conn.execute,
            """INSERT INTO tool_calls
               (session_id, step, tool_name, args, output, error, success, attempt, duration_ms, ts)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                session_id,
                step,
                tool_name,
                json.dumps(args, default=str)[:2048],
                (output or "")[:4096],
                (error or "")[:2048],
                1 if error is None else 0,
                attempt,
                duration_ms,
                time.time(),
            ),
        )
        await asyncio.to_thread(conn.commit)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    async def get_sessions(self, limit: int = 20) -> list[dict]:
        conn = await asyncio.to_thread(self._ensure)
        rows = await asyncio.to_thread(
            lambda: conn.execute(
                "SELECT id, goal, agent_name, mode, started_at, ended_at, state, step_count "
                "FROM sessions ORDER BY started_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        )
        cols = ["id", "goal", "agent_name", "mode", "started_at", "ended_at", "state", "step_count"]
        return [dict(zip(cols, r)) for r in rows]

    async def get_session_tool_calls(self, session_id: str) -> list[dict]:
        conn = await asyncio.to_thread(self._ensure)
        rows = await asyncio.to_thread(
            lambda: conn.execute(
                "SELECT step, tool_name, args, output, error, success, attempt, duration_ms, ts "
                "FROM tool_calls WHERE session_id=? ORDER BY id",
                (session_id,),
            ).fetchall()
        )
        cols = ["step", "tool_name", "args", "output", "error", "success", "attempt", "duration_ms", "ts"]
        return [dict(zip(cols, r)) for r in rows]

    async def get_session_messages(self, session_id: str) -> list[dict]:
        conn = await asyncio.to_thread(self._ensure)
        rows = await asyncio.to_thread(
            lambda: conn.execute(
                "SELECT role, content, ts FROM messages WHERE session_id=? ORDER BY id",
                (session_id,),
            ).fetchall()
        )
        return [{"role": r[0], "content": r[1], "ts": r[2]} for r in rows]

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
