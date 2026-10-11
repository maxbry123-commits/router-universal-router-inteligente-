"""YAIWES memory facade: SQLite is the always-available writable fallback."""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import socket
import threading
import time
import uuid
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
    evidence = ROOT / "router inteligente universal" / "Componentes del Router" / "router inteligente software" / "componentes todos" / "componentes descargados" / "RDC_ADDITIONAL_COMPONENTS_EVIDENCE.json"
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


class QdrantLocalAdapter(ComponentAdapter):
    """Indice DERIVADO y reconstruible: Qdrant en modo local (sin servidor), el cliente viene del motor de descarga.
    SQLite sigue siendo la verdad. Embedding determinista LEXICAL_HASH: busca por palabras en comun, NO es semantico."""

    COLLECTION = "memoria_yaiwes"
    DIM = 256
    EMBEDDING = "LEXICAL_HASH_256"

    def __init__(self) -> None:
        super().__init__("qdrant")
        self._client: Any = None
        self._error: str | None = None
        self._down_until = 0.0
        self._lock = threading.Lock()

    @staticmethod
    def _enabled() -> bool:
        return os.getenv("RIU_QDRANT_LOCAL", "1") != "0"

    @staticmethod
    def _path() -> str:
        return os.getenv("RIU_QDRANT_PATH") or str(ROOT / "chat router" / "04-MEMORIA" / "indices" / "qdrant_local")

    def _ready(self) -> bool:
        if not self._enabled():
            self._error = "GAP_DISABLED"
            return False
        if self._client is not None:
            return time.time() >= self._down_until
        if time.time() < self._down_until:
            return False
        with self._lock:
            if self._client is not None:
                return True
            try:
                from qdrant_client import QdrantClient, models
                Path(self._path()).mkdir(parents=True, exist_ok=True)
                client = QdrantClient(path=self._path())
                if not client.collection_exists(self.COLLECTION):
                    client.create_collection(collection_name=self.COLLECTION, vectors_config=models.VectorParams(size=self.DIM, distance=models.Distance.COSINE))
                self._client = client
                self._error = None
                return True
            except ImportError:
                self._error = "GAP_CLIENT_NOT_INSTALLED"
            except Exception as exc:  # noqa: BLE001 - un indice derivado nunca tumba la memoria
                self._error = "GAP_" + type(exc).__name__
            self._down_until = time.time() + 60
            return False

    def _fail(self, exc: Exception) -> None:
        self._error = "GAP_" + type(exc).__name__
        self._down_until = time.time() + 60

    def _endpoint(self) -> str | None:
        return "local" if self._ready() else None

    @classmethod
    def embed(cls, text: Any) -> list[float]:
        vec = [0.0] * cls.DIM
        for token in re.findall(r"\w+", str(text).lower()):
            n = int.from_bytes(hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest(), "big")
            vec[n % cls.DIM] += 1.0 if (n >> 63) & 1 else -1.0
        norm = sum(v * v for v in vec) ** 0.5
        return [v / norm for v in vec] if norm else vec

    @staticmethod
    def _pid(scope: str, key: str) -> str:
        return str(uuid.uuid5(uuid.NAMESPACE_URL, scope + "\x1f" + key))

    def health(self) -> dict[str, Any]:
        item = _component("qdrant")
        downloaded = _downloaded("qdrant-client") or _downloaded("qdrant")
        source_status = "PRESENT_DOWNLOADED" if downloaded.get("status") in {"EXTRACTED_VERIFIED", "VERIFIED_EXISTING"} else item.get("source_status", "GAP")
        ready = self._ready()
        records = None
        if ready:
            try:
                records = self._client.count(collection_name=self.COLLECTION, exact=True).count
            except Exception as exc:  # noqa: BLE001
                self._fail(exc)
                ready = False
        return {"name": self.name, "source_status": source_status, "runtime_status": "CONNECTED" if ready else (self._error or "GAP"), "configured": self._enabled(),
                "mode": "derived-local-index", "truth": "sqlite", "embedding": self.EMBEDDING, "semantic": False, "records": records, "path": self._path()}

    def save(self, scope: str, key: str, data: Any) -> dict[str, Any]:
        if not self._ready():
            return {"adapter": self.name, "status": "GAP", "reason": self._error or "not ready"}
        try:
            from qdrant_client import models
            vec = self.embed(key + " " + json.dumps(data, ensure_ascii=False)[:4000])
            if not any(vec):
                return {"adapter": self.name, "status": "GAP", "reason": "empty vector"}
            self._client.upsert(collection_name=self.COLLECTION, points=[models.PointStruct(id=self._pid(scope, key), vector=vec, payload={"scope": scope, "key": key, "data": data, "ts": time.time()})])
            return {"adapter": self.name, "status": "SAVED", "mode": "derived-index", "embedding": self.EMBEDDING}
        except Exception as exc:  # noqa: BLE001
            self._fail(exc)
            return {"adapter": self.name, "status": "GAP", "reason": type(exc).__name__}

    def load(self, scope: str, key: str) -> list[dict[str, Any]]:
        return []  # indice derivado: la verdad se carga de SQLite, no se duplica aqui

    def search(self, scope: str, query: str, k: int = 10) -> list[dict[str, Any]]:
        if not str(query).strip() or not self._ready():
            return []
        try:
            from qdrant_client import models
            vec = self.embed(query)
            if not any(vec):
                return []
            flt = models.Filter(must=[models.FieldCondition(key="scope", match=models.MatchValue(value=scope))])
            res = self._client.query_points(collection_name=self.COLLECTION, query=vec, query_filter=flt, limit=k, with_payload=True)
            return [{"scope": p.payload.get("scope"), "key": p.payload.get("key"), "data": p.payload.get("data"), "score": p.score} for p in res.points]
        except Exception as exc:  # noqa: BLE001
            self._fail(exc)
            return []

    def rebuild(self, sqlite_adapter: Any) -> dict[str, Any]:
        rows = sqlite_adapter.db.execute("SELECT scope,key,data FROM memoria_yaiwes ORDER BY id").fetchall()
        done = sum(1 for r in rows if self.save(r["scope"], r["key"], json.loads(r["data"])).get("status") == "SAVED")
        return {"indexed": done, "total": len(rows)}


class MemoryFacade:
    def __init__(self, store: Any) -> None:
        self.sqlite = SQLiteAdapter(store)
        self.graph = GraphSQLiteAdapter(store)
        self.components = {name: ComponentAdapter(name) for name in ("state-hub", "dataset-yaiwes", "graphiti", "falkordb", "memanto", "graphify", "agentdb", "postgresql", "redis", "hf-storage-bucket", "chroma")}
        qd = QdrantLocalAdapter()  # primero: su embed() (256d, NO semantico) alimenta a Graphiti
        self.components["qdrant"] = qd  # indice derivado local; SQLite sigue siendo la verdad
        try:  # adaptadores reales (health estricto); si el modulo falla, queda el generico
            from . import runtime_adapters as _ra
            self.components["graphiti"] = _ra.GraphitiAdapter(QdrantLocalAdapter.embed)
            self.components["graphify"] = _ra.GraphifyCodeAdapter()
            self.components["memanto"] = _ra.MemantoAdapter()
        except Exception:  # noqa: BLE001
            pass

    def health(self) -> dict[str, Any]:
        adapters = {"sqlite": self.sqlite.health(), "graph": self.graph.health()}
        adapters.update({name: adapter.health() for name, adapter in self.components.items()})
        return {"schema": "yaiwes.memory/v1", "adapters": adapters, "fallback": "sqlite"}

    def save(self, scope: str, key: str, data: Any) -> dict[str, Any]:
        saved = self.sqlite.save(scope, key, data)  # SQLite es la verdad: si esto no falla, el dato esta guardado
        gaps: list[dict[str, Any]] = []
        try:
            self.graph.save(scope, key, data)
        except Exception as exc:  # noqa: BLE001 - la replica de grafo nunca invalida el guardado
            gaps.append({"adapter": self.graph.name, "error": type(exc).__name__})
        replicas: dict[str, Any] = {}
        solo_sqlite = ":gov:" in scope or ":snapanc:" in scope or key in ("gov-registro", "snapshot-anclados")
        for name, adapter in ({} if solo_sqlite else self.components).items():
            try:
                if getattr(adapter, "IN_SAVE", True) is False:
                    continue
                if adapter._endpoint():
                    replicas[name] = adapter.save(scope, key, data)
            except Exception as exc:  # noqa: BLE001
                replicas[name] = {"adapter": name, "status": "GAP", "reason": type(exc).__name__}
        out = {"status": "SAVED", "adapter": "sqlite", "replicas": replicas, **saved}
        if gaps:
            out["replica_gaps"] = gaps
        return out

    def load(self, scope: str, key: str) -> list[dict[str, Any]]:
        records = list(self.sqlite.load(scope, key))
        for adapter in self.components.values():
            try:
                records.extend(adapter.load(scope, key))
            except Exception:  # noqa: BLE001
                pass
        return records

    def search(self, scope: str, query: str, k: int = 10) -> dict[str, Any]:
        results: dict[str, Any] = {"sqlite": self.sqlite.search(scope, query, k)}
        try:
            results["graph"] = self.graph.search(scope, query, k)
        except Exception:  # noqa: BLE001
            results["graph"] = []
        for name, adapter in self.components.items():
            try:
                if adapter._endpoint():
                    results[name] = adapter.search(scope, query, k)
            except Exception:  # noqa: BLE001
                results[name] = []
        return results

    def rebuild_index(self) -> dict[str, Any]:
        qd = self.components.get("qdrant")
        if qd is None or not qd._endpoint():
            return {"status": "GAP", "reason": getattr(qd, "_error", None) or "qdrant no disponible"}
        return {"status": "REBUILT", **qd.rebuild(self.sqlite)}


def build_memory(store: Any) -> MemoryFacade:
    return MemoryFacade(store)
