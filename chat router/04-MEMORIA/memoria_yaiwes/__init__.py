"""YAIWES memory facade: SQLite is the always-available writable fallback."""
from __future__ import annotations

import json
import os
import sqlite3
import socket
import time
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
INVENTORY = ROOT / "chat router" / "03-ESTADO" / "MEMORIA-INVENTARIO.json"


def _load_inventory() -> dict[str, Any]:
    try:
        return json.loads(INVENTORY.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {"components": []}


def _component(name: str) -> dict[str, Any]:
    return next((item for item in _load_inventory().get("components", []) if item.get("name") == name), {})


def _downloaded(name: str) -> dict[str, Any]:
    evidence = ROOT / "router inteligente software" / "componentes todos" / "componentes descargados" / "RDC_ADDITIONAL_COMPONENTS_EVIDENCE.json"
    try:
        rows = json.loads(evidence.read_text(encoding="utf-8")).get("components", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return next((row for row in rows if str(row.get("slug", "")).lower() == name.lower()), {})


def _http_probe(url: str) -> bool:
    try:
        with urlopen(url, timeout=1.5) as response:
            return 200 <= response.status < 500
    except Exception:  # noqa: BLE001 - health must never take down the Router
        return False


def _tcp_probe(url: str) -> bool:
    try:
        parsed = urlparse(url)
        with socket.create_connection((parsed.hostname or "127.0.0.1", parsed.port or 6379), timeout=1.5) as sock:
            if parsed.scheme in {"redis", "rediss"}:
                sock.sendall(b"*1\r\n$4\r\nPING\r\n")
                return b"PONG" in sock.recv(64)
            return True
    except Exception:  # noqa: BLE001
        return False


class SQLiteAdapter:
    name = "sqlite"

    def __init__(self, store: Any) -> None:
        self.store = store
        self.db_path = Path(store.db_path)
        self.db = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute("CREATE TABLE IF NOT EXISTS memoria_yaiwes (id INTEGER PRIMARY KEY AUTOINCREMENT, scope TEXT NOT NULL, key TEXT NOT NULL, data TEXT NOT NULL, created_at REAL NOT NULL)")
        self.db.commit()

    def health(self) -> dict[str, Any]:
        count = self.db.execute("SELECT COUNT(*) FROM memoria_yaiwes").fetchone()[0]
        return {"name": self.name, "status": "CONNECTED", "mode": "primary", "records": count, "db": str(self.db_path)}

    def save(self, scope: str, key: str, data: Any) -> dict[str, Any]:
        cur = self.db.execute("INSERT INTO memoria_yaiwes(scope,key,data,created_at) VALUES(?,?,?,?)", (scope, key, json.dumps(data, ensure_ascii=False), time.time()))
        self.db.commit()
        return {"adapter": self.name, "id": cur.lastrowid, "scope": scope, "key": key}

    def load(self, scope: str, key: str) -> list[dict[str, Any]]:
        rows = self.db.execute("SELECT id,scope,key,data FROM memoria_yaiwes WHERE scope=? AND key=? ORDER BY id DESC", (scope, key)).fetchall()
        return [{"id": row["id"], "scope": row["scope"], "key": row["key"], "data": json.loads(row["data"])} for row in rows]

    def search(self, scope: str, query: str, k: int = 10) -> list[dict[str, Any]]:
        rows = self.db.execute("SELECT id,scope,key,data FROM memoria_yaiwes WHERE scope=? AND (key LIKE ? OR data LIKE ?) ORDER BY id DESC LIMIT ?", (scope, f"%{query}%", f"%{query}%", k)).fetchall()
        return [{"id": row["id"], "scope": row["scope"], "key": row["key"], "data": json.loads(row["data"])} for row in rows]


class GraphSQLiteAdapter:
    name = "graph-sqlite-fallback"

    def __init__(self, store: Any) -> None:
        self.store = store

    def health(self) -> dict[str, Any]:
        return {"name": self.name, "status": "CONNECTED", "mode": "fallback", "stats": self.store.stats().get("graph", {})}

    def save(self, scope: str, key: str, data: Any) -> dict[str, Any]:
        node_id = f"memory:{scope}:{key}"
        scope_id = f"scope:{scope}"
        self.store.graph_node(scope_id, "memory_scope", scope)
        self.store.graph_node(node_id, "memory", key, scope=scope, data=data)
        self.store.graph_link(scope_id, node_id, "contains")
        return {"adapter": self.name, "id": node_id}

    def load(self, scope: str, key: str) -> list[dict[str, Any]]:
        needle = f"memory:{scope}:{key}"
        return [node for node in self.store.graph_view().get("nodes", []) if node.get("id") == needle]

    def search(self, scope: str, query: str, k: int = 10) -> list[dict[str, Any]]:
        q = str(query).lower()
        return [node for node in self.store.graph_view(limit=max(k, 10)).get("nodes", []) if q in str(node.get("label", "")).lower()][:k]


class ComponentAdapter:
    """Optional runtime connector; downloaded source alone never means CONNECTED."""

    def __init__(self, name: str) -> None:
        self.name = name

    def _endpoint(self) -> str | None:
        env_name = {"graphiti": "RIU_GRAPHITI_URL", "memanto": "RIU_MEMANTO_URL", "graphify": "RIU_GRAPHIFY_URL", "agentdb": "RIU_AGENTDB_URL"}.get(self.name)
        return os.getenv(env_name) if env_name else None

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        endpoint = (self._endpoint() or "").rstrip("/") + path
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(endpoint, data=body, method=method, headers={"Content-Type": "application/json"})
        with urlopen(request, timeout=3) as response:
            return json.loads(response.read().decode("utf-8"))

    def health(self) -> dict[str, Any]:
        item = _component(self.name)
        downloaded = _downloaded(self.name)
        source_status = "PRESENT_DOWNLOADED" if downloaded.get("status") in {"EXTRACTED_VERIFIED", "VERIFIED_EXISTING"} else item.get("source_status", "GAP")
        runtime_status = item.get("runtime_status", "GAP")
        endpoint_env = {"falkordb": "RIU_FALKORDB_URL", "redis": "RIU_REDIS_URL", "graphiti": "RIU_GRAPHITI_URL", "memanto": "RIU_MEMANTO_URL", "graphify": "RIU_GRAPHIFY_URL", "agentdb": "RIU_AGENTDB_URL", "postgresql": "RIU_POSTGRES_DSN"}.get(self.name)
        configured = bool(endpoint_env and os.getenv(endpoint_env))
        if configured:
            endpoint = os.environ[endpoint_env]
            if self.name in {"falkordb", "redis"}:
                live = _tcp_probe(endpoint)
            elif self.name == "postgresql":
                live = False
                try:
                    import psycopg
                    with psycopg.connect(endpoint, connect_timeout=2) as conn:
                        conn.execute("SELECT 1")
                    live = True
                except Exception:  # noqa: BLE001
                    live = False
            else:
                live = _http_probe(endpoint)
            runtime_status = "CONNECTED" if live else "GAP_UNREACHABLE"
        return {"name": self.name, "source_status": source_status, "runtime_status": runtime_status, "configured": configured, "path": downloaded.get("target") or item.get("path"), "sha": downloaded.get("tree_sha256") or item.get("sha")}

    def save(self, scope: str, key: str, data: Any) -> dict[str, Any]:
        if self._endpoint():
            try:
                return {"adapter": self.name, "status": "SAVED", "response": self._request("POST", "/save", {"scope": scope, "key": key, "data": data})}
            except Exception:  # noqa: BLE001
                pass
        return {"adapter": self.name, "status": "GAP", "reason": "no verified runtime contract"}

    def load(self, scope: str, key: str) -> list[dict[str, Any]]:
        if self._endpoint():
            try:
                response = self._request("GET", "/load?" + urlencode({"scope": scope, "key": key}))
                return response.get("records", response if isinstance(response, list) else [])
            except Exception:  # noqa: BLE001
                pass
        return []

    def search(self, scope: str, query: str, k: int = 10) -> list[dict[str, Any]]:
        if self._endpoint():
            try:
                response = self._request("GET", "/search?" + urlencode({"scope": scope, "query": query, "k": k}))
                return response.get("records", response if isinstance(response, list) else [])
            except Exception:  # noqa: BLE001
                pass
        return []


class MemoryFacade:
    def __init__(self, store: Any) -> None:
        self.sqlite = SQLiteAdapter(store)
        self.graph = GraphSQLiteAdapter(store)
        self.components = {name: ComponentAdapter(name) for name in ("state-hub", "dataset-yaiwes", "graphiti", "falkordb", "memanto", "graphify", "agentdb", "postgresql", "redis", "hf-storage-bucket", "chroma", "qdrant")}

    def health(self) -> dict[str, Any]:
        adapters = {"sqlite": self.sqlite.health(), "graph": self.graph.health()}
        adapters.update({name: adapter.health() for name, adapter in self.components.items()})
        return {"schema": "yaiwes.memory/v1", "adapters": adapters, "fallback": "sqlite"}

    def save(self, scope: str, key: str, data: Any) -> dict[str, Any]:
        saved = self.sqlite.save(scope, key, data)
        self.graph.save(scope, key, data)
        replicas = {name: adapter.save(scope, key, data) for name, adapter in self.components.items() if adapter._endpoint()}
        return {"status": "SAVED", "adapter": "sqlite", "replicas": replicas, **saved}

    def load(self, scope: str, key: str) -> list[dict[str, Any]]:
        records = list(self.sqlite.load(scope, key))
        for adapter in self.components.values():
            records.extend(adapter.load(scope, key))
        return records

    def search(self, scope: str, query: str, k: int = 10) -> dict[str, Any]:
        results = {"sqlite": self.sqlite.search(scope, query, k), "graph": self.graph.search(scope, query, k)}
        for name, adapter in self.components.items():
            if adapter._endpoint():
                results[name] = adapter.search(scope, query, k)
        return results


def build_memory(store: Any) -> MemoryFacade:
    return MemoryFacade(store)
