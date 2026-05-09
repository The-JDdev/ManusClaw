from __future__ import annotations

"""
SessionDB — SQLite WAL-mode session store with FTS5 cross-session search,
session branching (fork), and context compression.

New features vs original:
- FTS5 virtual table over messages for full-text search across sessions
- Jittered retries at app level to avoid SQLite convoy under concurrent readers
- branch_session() — fork with parent_session_id
- compress_session() — summarize context when approaching token limits
- fts_search() — search messages and tool calls across all sessions
"""

import asyncio
import json
import random
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any, Optional

from app.logger import logger

_DB_PATH = Path("workspace/.sessions/manusclaw.db")

_SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS sessions (
    id                TEXT PRIMARY KEY,
    goal              TEXT,
    agent_name        TEXT,
    mode              TEXT DEFAULT 'build',
    parent_session_id TEXT,
    started_at        REAL,
    ended_at          REAL,
    state             TEXT DEFAULT 'running',
    step_count        INTEGER DEFAULT 0,
    compressed        INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT REFERENCES sessions(id),
    role        TEXT,
    content     TEXT,
    ts          REAL
);

CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts
    USING fts5(content, session_id UNINDEXED, role UNINDEXED, content='messages', content_rowid='id');

CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
    INSERT INTO messages_fts(rowid, content, session_id, role)
        VALUES (new.id, new.content, new.session_id, new.role);
END;

CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, content, session_id, role)
        VALUES ('delete', old.id, old.content, old.session_id, old.role);
END;

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

CREATE VIRTUAL TABLE IF NOT EXISTS tool_calls_fts
    USING fts5(output, tool_name UNINDEXED, session_id UNINDEXED, content='tool_calls', content_rowid='id');

CREATE TRIGGER IF NOT EXISTS tool_calls_ai AFTER INSERT ON tool_calls BEGIN
    INSERT INTO tool_calls_fts(rowid, output, tool_name, session_id)
        VALUES (new.id, COALESCE(new.output, ''), new.tool_name, new.session_id);
END;

CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_tool_calls_session ON tool_calls(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_parent ON sessions(parent_session_id);
"""

_MAX_RETRIES = 5
_RETRY_BASE  = 0.05


async def _with_retry(fn, *args, **kwargs):
    """Jittered retry wrapper for SQLite operations (avoids convoy effect)."""
    wait = _RETRY_BASE
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            return await asyncio.to_thread(fn, *args, **kwargs)
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower() and attempt < _MAX_RETRIES:
                jitter = random.uniform(0, wait * 0.5)
                await asyncio.sleep(wait + jitter)
                wait = min(wait * 2, 2.0)
                continue
            raise


class SessionDB:
    """
    Thread-safe async wrapper around the SQLite audit DB with FTS5 and branching.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or _DB_PATH
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None

    def _ensure(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
            self._conn.executescript(_SCHEMA)
            self._conn.commit()
        return self._conn

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    async def create_session(self, goal: str, agent_name: str = "manus",
                              mode: str = "build", parent_session_id: Optional[str] = None) -> str:
        sid = str(uuid.uuid4())[:12]

        def _create():
            conn = self._ensure()
            conn.execute(
                "INSERT INTO sessions (id, goal, agent_name, mode, parent_session_id, started_at) "
                "VALUES (?,?,?,?,?,?)",
                (sid, goal, agent_name, mode, parent_session_id, time.time()),
            )
            conn.commit()
        await _with_retry(_create)
        return sid

    async def branch_session(self, parent_session_id: str, new_goal: Optional[str] = None) -> str:
        """Fork an existing session with a new parent_session_id link."""
        def _get_parent():
            conn = self._ensure()
            row = conn.execute("SELECT goal, agent_name, mode FROM sessions WHERE id=?",
                               (parent_session_id,)).fetchone()
            return row

        row = await _with_retry(_get_parent)
        if not row:
            raise ValueError(f"Parent session not found: {parent_session_id}")
        goal = new_goal or f"[Branch of {parent_session_id}] {row[0]}"
        return await self.create_session(goal, row[1], row[2], parent_session_id=parent_session_id)

    async def close_session(self, session_id: str, state: str = "finished", step_count: int = 0) -> None:
        def _close():
            conn = self._ensure()
            conn.execute("UPDATE sessions SET ended_at=?, state=?, step_count=? WHERE id=?",
                         (time.time(), state, step_count, session_id))
            conn.commit()
        await _with_retry(_close)

    async def compress_session(self, session_id: str, summary: str) -> None:
        """
        Replace all non-system messages with a single compressed summary.
        Sets compressed=1 on the session record.
        """
        def _compress():
            conn = self._ensure()
            conn.execute("DELETE FROM messages WHERE session_id=? AND role != 'system'", (session_id,))
            conn.execute(
                "INSERT INTO messages (session_id, role, content, ts) VALUES (?,?,?,?)",
                (session_id, "user", f"[COMPRESSED CONTEXT]\n{summary}", time.time()),
            )
            conn.execute("UPDATE sessions SET compressed=1 WHERE id=?", (session_id,))
            conn.commit()
        await _with_retry(_compress)
        logger.info(f"[SessionDB] Compressed session {session_id}")

    # ------------------------------------------------------------------
    # Message logging
    # ------------------------------------------------------------------

    async def log_message(self, session_id: str, role: str, content: Optional[str]) -> None:
        if not content:
            return
        def _log():
            conn = self._ensure()
            conn.execute(
                "INSERT INTO messages (session_id, role, content, ts) VALUES (?,?,?,?)",
                (session_id, role, content[:4096], time.time()),
            )
            conn.commit()
        await _with_retry(_log)

    # ------------------------------------------------------------------
    # Tool call logging
    # ------------------------------------------------------------------

    async def log_tool_call(self, session_id: str, step: int, tool_name: str,
                             args: dict, output: Optional[str], error: Optional[str],
                             attempt: int = 1, duration_ms: int = 0) -> None:
        def _log():
            conn = self._ensure()
            conn.execute(
                """INSERT INTO tool_calls
                   (session_id, step, tool_name, args, output, error, success, attempt, duration_ms, ts)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (session_id, step, tool_name,
                 json.dumps(args, default=str)[:2048],
                 (output or "")[:4096], (error or "")[:2048],
                 1 if error is None else 0, attempt, duration_ms, time.time()),
            )
            conn.commit()
        await _with_retry(_log)

    # ------------------------------------------------------------------
    # FTS5 cross-session search
    # ------------------------------------------------------------------

    async def fts_search(self, query: str, limit: int = 10, search_in: str = "both") -> list[dict]:
        """Full-text search across messages and/or tool_calls."""
        results: list[dict] = []
        safe_q = self._fts_safe(query)

        def _search():
            conn = self._ensure()
            rows: list[dict] = []
            if search_in in ("messages", "both"):
                try:
                    r = conn.execute(
                        """SELECT m.id, m.session_id, m.role, m.content, m.ts,
                                  snippet(messages_fts, 0, '>>>', '<<<', '...', 20) as snippet
                           FROM messages_fts
                           JOIN messages m ON m.id = messages_fts.rowid
                           WHERE messages_fts MATCH ?
                           ORDER BY rank LIMIT ?""",
                        (safe_q, limit),
                    ).fetchall()
                    for row in r:
                        rows.append({
                            "type": "message", "id": row[0], "session_id": row[1],
                            "role": row[2], "content": row[3][:300],
                            "ts": row[4], "snippet": row[5],
                        })
                except Exception:
                    pass
            if search_in in ("tool_calls", "both"):
                try:
                    r = conn.execute(
                        """SELECT tc.id, tc.session_id, tc.tool_name, tc.output, tc.ts,
                                  snippet(tool_calls_fts, 0, '>>>', '<<<', '...', 20) as snippet
                           FROM tool_calls_fts
                           JOIN tool_calls tc ON tc.id = tool_calls_fts.rowid
                           WHERE tool_calls_fts MATCH ?
                           ORDER BY rank LIMIT ?""",
                        (safe_q, limit),
                    ).fetchall()
                    for row in r:
                        rows.append({
                            "type": "tool_call", "id": row[0], "session_id": row[1],
                            "role": row[2], "content": (row[3] or "")[:300],
                            "ts": row[4], "snippet": row[5],
                        })
                except Exception:
                    pass
            return rows

        results = await _with_retry(_search)
        return results[:limit]

    @staticmethod
    def _fts_safe(query: str) -> str:
        import re
        words = re.findall(r"\w+", query)
        return " OR ".join(words[:8]) if words else query

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    async def get_sessions(self, limit: int = 20) -> list[dict]:
        def _get():
            conn = self._ensure()
            rows = conn.execute(
                "SELECT id, goal, agent_name, mode, parent_session_id, started_at, ended_at, state, step_count "
                "FROM sessions ORDER BY started_at DESC LIMIT ?", (limit,)
            ).fetchall()
            cols = ["id","goal","agent_name","mode","parent_session_id","started_at","ended_at","state","step_count"]
            return [dict(zip(cols, r)) for r in rows]
        return await _with_retry(_get)

    async def get_session_tool_calls(self, session_id: str) -> list[dict]:
        def _get():
            conn = self._ensure()
            rows = conn.execute(
                "SELECT step, tool_name, args, output, error, success, attempt, duration_ms, ts "
                "FROM tool_calls WHERE session_id=? ORDER BY id", (session_id,)
            ).fetchall()
            cols = ["step","tool_name","args","output","error","success","attempt","duration_ms","ts"]
            return [dict(zip(cols, r)) for r in rows]
        return await _with_retry(_get)

    async def get_session_messages(self, session_id: str) -> list[dict]:
        def _get():
            conn = self._ensure()
            rows = conn.execute(
                "SELECT role, content, ts FROM messages WHERE session_id=? ORDER BY id", (session_id,)
            ).fetchall()
            return [{"role": r[0], "content": r[1], "ts": r[2]} for r in rows]
        return await _with_retry(_get)

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
