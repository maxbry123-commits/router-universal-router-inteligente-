"""conversation_store.py - Persistencia de conversaciones en SQLite.
Schema: (id, session_id, role, content, ts). Índice por sesión."""
import os
import sqlite3
import time
from pathlib import Path

DB = Path(os.getenv("CONV_DB", "state/conversations.db"))
DB.parent.mkdir(parents=True, exist_ok=True)


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB, isolation_level=None)
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            ts REAL NOT NULL
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_sess ON messages(session_id, ts)")
    return c


def append(session_id: str, role: str, content: str) -> int:
    """Añade mensaje. Devuelve el id."""
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO messages(session_id, role, content, ts) VALUES(?,?,?,?)",
            (session_id, role, content, time.time()),
        )
        return cur.lastrowid


def history(session_id: str, limit: int = 100) -> list:
    """Devuelve los últimos N mensajes ordenados por ts ascendente."""
    with _conn() as c:
        rows = c.execute(
            "SELECT role, content, ts FROM messages "
            "WHERE session_id=? ORDER BY ts ASC LIMIT ?",
            (session_id, limit),
        ).fetchall()
    return [{"role": r[0], "content": r[1], "ts": r[2]} for r in rows]


def sessions() -> list:
    """Lista de session_id conocidas."""
    with _conn() as c:
        rows = c.execute(
            "SELECT DISTINCT session_id FROM messages ORDER BY session_id"
        ).fetchall()
    return [r[0] for r in rows]


def prune(days: int = 30) -> int:
    """Borra mensajes más viejos que N días. Devuelve cuántos eliminó."""
    cutoff = time.time() - days * 86400
    with _conn() as c:
        cur = c.execute("DELETE FROM messages WHERE ts < ?", (cutoff,))
        return cur.rowcount


def count(session_id: str | None = None) -> int:
    """Cuenta mensajes en una sesión o globales."""
    with _conn() as c:
        if session_id:
            row = c.execute(
                "SELECT COUNT(*) FROM messages WHERE session_id=?",
                (session_id,),
            ).fetchone()
        else:
            row = c.execute("SELECT COUNT(*) FROM messages").fetchone()
        return row[0] if row else 0
