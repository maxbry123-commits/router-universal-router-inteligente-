"""YAIWES memory facade: SQLite is the always-available writable fallback."""
from __future__ import annotations

import json
import sqlite3
import time
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
    """Descriptor for a downloaded component; source presence is not live connectivity."""

    def __init__(self, name: str) -> None:
        self.name = name

    def health(self) -> dict[str, Any]:
        item = _component(self.name)
        return {"name": self.name, "source_status": item.get("source_status", "GAP"), "runtime_status": item.get("runtime_status", "GAP"), "path": item.get("path"), "sha": item.get("sha")}

    def save(self, scope: str, key: str, data: Any) -> dict[str, Any]:
        return {"adapter": self.name, "status": "GAP", "reason": "no verified runtime contract"}

    def load(self, scope: str, key: str) -> list[dict[str, Any]]:
        return []

    def search(self, scope: str, query: str, k: int = 10) -> list[dict[str, Any]]:
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
        return {"status": "SAVED", "adapter": "sqlite", **saved}

    def load(self, scope: str, key: str) -> list[dict[str, Any]]:
        return self.sqlite.load(scope, key)

    def search(self, scope: str, query: str, k: int = 10) -> dict[str, Any]:
        return {"sqlite": self.sqlite.search(scope, query, k), "graph": self.graph.search(scope, query, k)}


def build_memory(store: Any) -> MemoryFacade:
    return MemoryFacade(store)
