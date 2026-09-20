"""SQLite-backed storage for the chat MVP: SQL, graph, cache and documents (stdlib only).

Four storage systems share one data directory (mounted from an HF bucket in the Space):
  sql        conversations, messages, agents      (SQLite)
  graph      provenance graph: nodes + edges with valid_at (SQLite, Graphiti-shaped, no LLM extraction)
  cache      response cache with TTL and hit counter (SQLite)
  documents  attachments on disk, deduplicated by sha256, metadata in SQLite
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
TEXT_EXT = {".md", ".txt", ".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".yml", ".yaml", ".toml", ".csv", ".html",
            ".css", ".sql", ".sh", ".ini", ".cfg", ".rs", ".go", ".java", ".c", ".h", ".cpp", ".xml", ".log"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations(id TEXT PRIMARY KEY, title TEXT, agent_id TEXT, owner TEXT, created_at REAL);
CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY AUTOINCREMENT, conv_id TEXT, role TEXT, content TEXT, provider TEXT, model TEXT, created_at REAL);
CREATE TABLE IF NOT EXISTS documents(id TEXT PRIMARY KEY, name TEXT, mime TEXT, size INTEGER, path TEXT, conv_id TEXT, is_text INTEGER, created_at REAL);
CREATE TABLE IF NOT EXISTS cache(key TEXT PRIMARY KEY, value TEXT, expires_at REAL, hits INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS graph_nodes(id TEXT PRIMARY KEY, kind TEXT, label TEXT, props TEXT, created_at REAL);
CREATE TABLE IF NOT EXISTS graph_edges(id INTEGER PRIMARY KEY AUTOINCREMENT, src TEXT, dst TEXT, rel TEXT, valid_at REAL, props TEXT);
CREATE TABLE IF NOT EXISTS agents(id TEXT PRIMARY KEY, name TEXT, role TEXT, system_prompt TEXT, models TEXT, created_at REAL);
"""

DEFAULT_AGENTS = (
    ("orquestador-g0", "Orquestador (Grupo 0)", "orquestacion",
     "Eres el orquestador del Grupo 0. Descompones la tarea, decides qué agente o herramienta interviene y respondes con un plan breve y accionable."),
    ("seals-team-yaiwes-001", "Seals Team YAIWES 001", "code",
     "Eres un agente Seals Team YAIWES especializado en código. Produces parches mínimos y verificables, explicas solo lo necesario y señalas cualquier GAP."),
)


class Store:
    def __init__(self, data_dir: str | Path) -> None:
        self.dir = Path(data_dir)
        (self.dir / "docs").mkdir(parents=True, exist_ok=True)
        self.db_path = self.dir / "riu_chat.sqlite3"
        self._lock = threading.RLock()
        self._db = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        with self._lock:
            self._db.executescript(SCHEMA)
            self._db.commit()
        if not self.agents():
            for aid, name, role, prompt in DEFAULT_AGENTS:
                self.upsert_agent(aid, name, role, prompt, [])

    # -- low level -----------------------------------------------------------------
    def _all(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(r) for r in self._db.execute(sql, params).fetchall()]

    def _exec(self, sql: str, params: tuple = ()) -> int:
        with self._lock:
            cur = self._db.execute(sql, params)
            self._db.commit()
            return cur.lastrowid or 0

    # -- sql: conversations / messages ---------------------------------------------
    def new_conversation(self, title: str, agent_id: str | None, owner: str) -> str:
        cid = uuid.uuid4().hex[:16]
        self._exec("INSERT INTO conversations VALUES(?,?,?,?,?)", (cid, title[:80], agent_id, owner, time.time()))
        return cid

    def conversation(self, cid: str) -> dict[str, Any] | None:
        rows = self._all("SELECT * FROM conversations WHERE id=?", (cid,))
        return rows[0] if rows else None

    def conversations(self, owner: str, limit: int = 50) -> list[dict[str, Any]]:
        return self._all("SELECT * FROM conversations WHERE owner=? ORDER BY created_at DESC LIMIT ?", (owner, limit))

    def add_message(self, cid: str, role: str, content: str, provider: str | None = None, model: str | None = None) -> None:
        self._exec("INSERT INTO messages(conv_id,role,content,provider,model,created_at) VALUES(?,?,?,?,?,?)",
                   (cid, role, content, provider, model, time.time()))

    def messages(self, cid: str, limit: int = 40) -> list[dict[str, Any]]:
        rows = self._all("SELECT role,content,provider,model,created_at FROM messages WHERE conv_id=? ORDER BY id DESC LIMIT ?", (cid, limit))
        return list(reversed(rows))

    # -- documents -----------------------------------------------------------------
    def put_document(self, name: str, mime: str, data: bytes, conv_id: str | None = None) -> dict[str, Any]:
        if not data:
            raise ValueError("DOCUMENT_EMPTY")
        if len(data) > MAX_UPLOAD_BYTES:
            raise ValueError("DOCUMENT_TOO_LARGE")
        did = hashlib.sha256(data).hexdigest()[:24]
        safe_name = Path(name).name[:120] or "documento"
        is_text = int(mime.startswith("text/") or mime in {"application/json", "application/xml", "application/x-yaml"}
                      or Path(safe_name).suffix.lower() in TEXT_EXT)
        path = self.dir / "docs" / did
        if not path.exists():
            path.write_bytes(data)
        self._exec("INSERT OR REPLACE INTO documents VALUES(?,?,?,?,?,?,?,?)",
                   (did, safe_name, mime[:100], len(data), str(path), conv_id, is_text, time.time()))
        return self.document(did) or {}

    def document(self, did: str) -> dict[str, Any] | None:
        rows = self._all("SELECT id,name,mime,size,conv_id,is_text,created_at FROM documents WHERE id=?", (did,))
        return rows[0] if rows else None

    def documents(self) -> list[dict[str, Any]]:
        return self._all("SELECT id,name,mime,size,conv_id,is_text,created_at FROM documents ORDER BY created_at DESC")

    def document_text(self, did: str, limit: int = 12000) -> str | None:
        rows = self._all("SELECT path,is_text FROM documents WHERE id=?", (did,))
        if not rows or not rows[0]["is_text"]:
            return None
        text = Path(rows[0]["path"]).read_bytes().decode("utf-8", errors="replace")
        return text if len(text) <= limit else text[:limit] + "\n[... truncado]"

    def delete_document(self, did: str) -> bool:
        rows = self._all("SELECT path FROM documents WHERE id=?", (did,))
        if not rows:
            return False
        Path(rows[0]["path"]).unlink(missing_ok=True)
        self._exec("DELETE FROM documents WHERE id=?", (did,))
        return True

    # -- cache ---------------------------------------------------------------------
    def cache_get(self, key: str) -> Any | None:
        rows = self._all("SELECT value,expires_at FROM cache WHERE key=?", (key,))
        if not rows or rows[0]["expires_at"] < time.time():
            return None
        self._exec("UPDATE cache SET hits=hits+1 WHERE key=?", (key,))
        return json.loads(rows[0]["value"])

    def cache_put(self, key: str, value: Any, ttl: float = 3600.0) -> None:
        self._exec("INSERT OR REPLACE INTO cache(key,value,expires_at,hits) VALUES(?,?,?,0)", (key, json.dumps(value), time.time() + ttl))

    # -- graph ---------------------------------------------------------------------
    def graph_node(self, node_id: str, kind: str, label: str, **props: Any) -> None:
        self._exec("INSERT INTO graph_nodes VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET label=excluded.label, props=excluded.props",
                   (node_id, kind, label[:120], json.dumps(props), time.time()))

    def graph_link(self, src: str, dst: str, rel: str, **props: Any) -> None:
        self._exec("INSERT INTO graph_edges(src,dst,rel,valid_at,props) VALUES(?,?,?,?,?)", (src, dst, rel, time.time(), json.dumps(props)))

    def graph_view(self, limit: int = 200) -> dict[str, Any]:
        edges = self._all("SELECT src,dst,rel,valid_at FROM graph_edges ORDER BY id DESC LIMIT ?", (limit,))
        ids = {e["src"] for e in edges} | {e["dst"] for e in edges}
        nodes = [n for n in self._all("SELECT id,kind,label FROM graph_nodes ORDER BY created_at DESC LIMIT ?", (limit * 2,)) if n["id"] in ids]
        return {"nodes": nodes, "edges": edges}

    def record_turn(self, *, conv_id: str, owner: str, provider: str, model: str, agent_id: str | None,
                    doc_ids: list[str], repo: str | None = None) -> None:
        self.graph_node(f"owner:{owner}", "owner", owner)
        self.graph_node(f"conv:{conv_id}", "conversation", conv_id)
        self.graph_node(f"model:{provider}/{model}", "model", f"{provider}/{model}")
        self.graph_link(f"owner:{owner}", f"conv:{conv_id}", "started")
        self.graph_link(f"conv:{conv_id}", f"model:{provider}/{model}", "used_model")
        if agent_id:
            self.graph_node(f"agent:{agent_id}", "agent", agent_id)
            self.graph_link(f"conv:{conv_id}", f"agent:{agent_id}", "ran_agent")
        for did in doc_ids:
            doc = self.document(did)
            if doc:
                self.graph_node(f"doc:{did}", "document", doc["name"])
                self.graph_link(f"conv:{conv_id}", f"doc:{did}", "attached")
        if repo:
            self.graph_node(f"repo:{repo}", "repo", repo)
            self.graph_link(f"conv:{conv_id}", f"repo:{repo}", "linked_repo")

    # -- agents --------------------------------------------------------------------
    def upsert_agent(self, agent_id: str, name: str, role: str, system_prompt: str, models: list[str]) -> None:
        self._exec("INSERT INTO agents VALUES(?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name, role=excluded.role, system_prompt=excluded.system_prompt, models=excluded.models",
                   (agent_id, name, role, system_prompt, json.dumps(models), time.time()))

    def agents(self) -> list[dict[str, Any]]:
        rows = self._all("SELECT * FROM agents ORDER BY id")
        for r in rows:
            r["models"] = json.loads(r["models"] or "[]")
        return rows

    def agent(self, agent_id: str) -> dict[str, Any] | None:
        return next((a for a in self.agents() if a["id"] == agent_id), None)

    def delete_agent(self, agent_id: str) -> bool:
        exists = self.agent(agent_id) is not None
        self._exec("DELETE FROM agents WHERE id=?", (agent_id,))
        return exists

    # -- stats / snapshot ----------------------------------------------------------
    def stats(self) -> dict[str, Any]:
        one = lambda sql: (self._all(sql) or [{"n": 0}])[0]["n"] or 0  # noqa: E731
        return {
            "sql": {"path": str(self.db_path), "conversations": one("SELECT COUNT(*) n FROM conversations"),
                    "messages": one("SELECT COUNT(*) n FROM messages"), "agents": one("SELECT COUNT(*) n FROM agents")},
            "graph": {"nodes": one("SELECT COUNT(*) n FROM graph_nodes"), "edges": one("SELECT COUNT(*) n FROM graph_edges")},
            "cache": {"entries": one("SELECT COUNT(*) n FROM cache"), "hits": one("SELECT SUM(hits) n FROM cache")},
            "documents": {"count": one("SELECT COUNT(*) n FROM documents"), "bytes": one("SELECT SUM(size) n FROM documents")},
        }

    def snapshot(self, dest: str | Path) -> Path:
        dest = Path(dest)
        target = sqlite3.connect(str(dest))
        with self._lock:
            self._db.backup(target)
        target.close()
        return dest
