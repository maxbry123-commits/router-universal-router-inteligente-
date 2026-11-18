"""long_term.py - Memoria de hechos con SQLite FTS5.
Sin embeddings: búsqueda por tokens. Determinista."""
import os
import sqlite3
import time
from pathlib import Path

DB = Path(os.getenv("LTM_DB", "state/long_term.db"))
DB.parent.mkdir(parents=True, exist_ok=True)


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB, isolation_level=None)
    c.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS facts USING fts5(
            key,
            value,
            session_id UNINDEXED,
            ts UNINDEXED
        )
    """)
    return c


def remember(key: str, value: str, session_id: str = "global") -> None:
    """Guarda un hecho. FTS5 permite búsqueda posterior por tokens."""
    try:
        with _conn() as c:
            c.execute(
                "INSERT INTO facts(key, value, session_id, ts) VALUES(?,?,?,?)",
                (key, value, session_id, time.time()),
            )
    except Exception:
        pass


def recall(key: str, limit: int = 5) -> list:
    """Recupera hechos por coincidencia exacta/token de la key."""
    try:
        with _conn() as c:
            rows = c.execute(
                "SELECT key, value, session_id, ts FROM facts "
                "WHERE key MATCH ? ORDER BY ts DESC LIMIT ?",
                (key, limit),
            ).fetchall()
        return [{"key": r[0], "value": r[1], "session_id": r[2], "ts": r[3]}
                for r in rows]
    except Exception:
        return []


def search(query: str, limit: int = 10) -> list:
    """Búsqueda full-text sobre key + value."""
    try:
        with _conn() as c:
            rows = c.execute(
                "SELECT key, value, session_id, ts FROM facts "
                "WHERE facts MATCH ? ORDER BY ts DESC LIMIT ?",
                (query, limit),
            ).fetchall()
        return [{"key": r[0], "value": r[1], "session_id": r[2], "ts": r[3]}
                for r in rows]
    except Exception:
        return []


def prune(days: int = 90) -> int:
    """Borra hechos más viejos que N días."""
    cutoff = time.time() - days * 86400
    with _conn() as c:
        cur = c.execute("DELETE FROM facts WHERE ts < ?", (str(cutoff),))
        return cur.rowcount


def count() -> int:
    """Número total de hechos almacenados."""
    try:
        with _conn() as c:
            row = c.execute("SELECT COUNT(*) FROM facts").fetchone()
        return row[0] if row else 0
    except Exception:
        return 0
