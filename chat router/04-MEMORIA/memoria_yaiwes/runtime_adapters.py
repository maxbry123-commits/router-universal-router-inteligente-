"""Adaptadores reales de Graphiti, Graphify, Memanto y embedding compartido.

Regla: nunca devolver CONNECTED por tener codigo fuente. Cada health() hace una
comprobacion real y, si falta algo, devuelve un GAP_* especifico.
SQLite sigue siendo la verdad; todo esto es indice/replica derivada.
"""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

EMBED_MODEL = "intfloat/multilingual-e5-small"
EMBED_DIM = 384


class EmbeddingAdapter:
    """Un solo modelo local compartido (e5-small, 384). Se carga una vez."""
    name = "embedding"
    _lock = threading.Lock()
    _model: Any = None
    _err: str | None = None

    @classmethod
    def _load(cls) -> Any:
        with cls._lock:
            if cls._model is not None or cls._err:
                return cls._model
            path = os.getenv("RIU_EMBED_MODEL_DIR", "")
            if not path or not Path(path).is_dir():
                cls._err = "GAP_EMBEDDING_MODEL_NOT_AVAILABLE"
                return None
            try:
                from sentence_transformers import SentenceTransformer
            except Exception:  # noqa: BLE001
                cls._err = "GAP_SENTENCE_TRANSFORMERS_NOT_INSTALLED"
                return None
            try:
                cls._model = SentenceTransformer(path, device="cpu")
            except Exception as exc:  # noqa: BLE001
                cls._err = f"GAP_EMBEDDING_LOAD_FAILED:{type(exc).__name__}"
            return cls._model

    @classmethod
    def reset(cls) -> None:
        cls._model, cls._err = None, None

    def ready(self) -> bool:
        return self._load() is not None

    def embed(self, texts: list[str], kind: str = "passage") -> list[list[float]]:
        model = self._load()
        if model is None:
            raise RuntimeError(self._err or "GAP_EMBEDDING_MODEL_NOT_AVAILABLE")
        pref = "query: " if kind == "query" else "passage: "
        vecs = model.encode([pref + t for t in texts], normalize_embeddings=True)
        return [list(map(float, v)) for v in vecs]

    def health(self) -> dict[str, Any]:
        ok = self.ready()
        return {"status": "CONNECTED" if ok else self._err, "model": EMBED_MODEL, "dim": EMBED_DIM,
                "semantic": ok, "e2e_verified": False}


def _flat(data: Any) -> str:
    return data if isinstance(data, str) else json.dumps(data, ensure_ascii=False, sort_keys=True)


class _Base:
    name = "base"

    def _endpoint(self) -> str | None:  # la fachada solo llama si esto es truthy
        return "local" if self.health().get("status") == "CONNECTED" else None

    def load(self, scope: str, key: str) -> list[dict[str, Any]]:
        return []

    def save(self, scope: str, key: str, data: Any) -> dict[str, Any]:
        return {"adapter": self.name, "status": "SKIPPED"}

    def search(self, scope: str, query: str, k: int = 10) -> list[dict[str, Any]]:
        return []


class GraphitiAdapter(_Base):
    """Graphiti sobre FalkorDBLite embebido. LLM = cliente inyectado (el del modelo de la ficha).
    Activar con RIU_GRAPHITI_ENABLE=1 y set_llm_client(...)/set_embedder(...)."""
    name = "graphiti"

    def __init__(self, embedder: EmbeddingAdapter | None = None) -> None:
        self.embedder = embedder or EmbeddingAdapter()
        self.llm_client: Any = None
        self._g: Any = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._err: str | None = None
        self._dead_until = 0.0

    def set_llm_client(self, client: Any) -> None:
        self.llm_client = client
        self._g = None

    def _gap(self) -> str | None:
        if os.getenv("RIU_GRAPHITI_ENABLE") != "1":
            return "GAP_DISABLED"
        try:
            import graphiti_core  # noqa: F401
        except Exception:  # noqa: BLE001
            return "GAP_GRAPHITI_CORE_NOT_INSTALLED"
        try:
            import redislite  # noqa: F401
        except Exception:  # noqa: BLE001
            return "GAP_FALKORDBLITE_NOT_INSTALLED"
        if self.llm_client is None:
            return "GAP_NO_LLM_CLIENT"
        if not self.embedder.ready():
            return "GAP_EMBEDDING_MODEL_NOT_AVAILABLE"
        return None

    def health(self) -> dict[str, Any]:
        gap = self._gap() or self._err
        return {"status": gap or "CONNECTED", "e2e_verified": False, "driver": "falkordblite-embedded"}

    def _run(self, coro: Any) -> Any:
        if self._loop is None:
            self._loop = asyncio.new_event_loop()
            threading.Thread(target=self._loop.run_forever, daemon=True).start()
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result(60)

    def _graph(self) -> Any:
        if self._g is None:
            from graphiti_core import Graphiti
            from graphiti_core.driver.falkordb_driver import FalkorDriver
            from redislite.async_falkordb_client import AsyncFalkorDB
            db_path = os.getenv("RIU_GRAPHITI_DB", "riu_data/graphiti.db")
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            driver = FalkorDriver(falkor_db=AsyncFalkorDB(db_path))
            self._g = Graphiti(graph_driver=driver, llm_client=self.llm_client, embedder=_GraphitiEmbedder(self.embedder))
            self._run(self._g.build_indices_and_constraints())
        return self._g

    def save(self, scope: str, key: str, data: Any) -> dict[str, Any]:
        from datetime import datetime, timezone
        try:
            g = self._graph()
            self._run(g.add_episode(name=f"{scope}:{key}", episode_body=_flat(data), source_description="yaiwes-memory",
                                    reference_time=datetime.now(timezone.utc), group_id=scope.replace(":", "_")))
            return {"adapter": self.name, "status": "SAVED"}
        except Exception as exc:  # noqa: BLE001
            self._err = f"GAP_RUNTIME:{type(exc).__name__}"
            return {"adapter": self.name, "status": "GAP", "reason": self._err}

    def search(self, scope: str, query: str, k: int = 10) -> list[dict[str, Any]]:
        g = self._graph()
        res = self._run(g.search(query, group_ids=[scope.replace(":", "_")], num_results=k))
        return [{"source": "graphiti", "text": getattr(r, "fact", str(r)), "id": str(getattr(r, "uuid", ""))} for r in res]


class _GraphitiEmbedder:
    """Puente duck-typed al EmbedderClient de Graphiti usando el embedding compartido."""
    def __init__(self, emb: EmbeddingAdapter) -> None:
        self.emb = emb

    async def create(self, input_data: Any) -> list[float]:
        text = input_data if isinstance(input_data, str) else " ".join(map(str, input_data))
        return self.emb.embed([text])[0]

    async def create_batch(self, input_data_list: list[str]) -> list[list[float]]:
        return self.emb.embed(list(input_data_list))


class GraphifyCodeAdapter(_Base):
    """Grafo del CODIGO (no de la memoria). Lee graphify-out/graph.json; solo busqueda, no es parte de save."""
    name = "graphify"

    @staticmethod
    def _graph_path() -> Path | None:
        root = os.getenv("RIU_GRAPHIFY_ROOT")
        return Path(root) / "graphify-out" / "graph.json" if root else None

    def health(self) -> dict[str, Any]:
        p = self._graph_path()
        if p is None:
            return {"status": "GAP_DISABLED"}
        if not p.exists():
            return {"status": "GAP_GRAPH_NOT_BUILT", "hint": "graphify <root>"}
        return {"status": "CONNECTED", "graph_json_bytes": p.stat().st_size, "age_s": int(time.time() - p.stat().st_mtime), "e2e_verified": False}

    def build(self) -> dict[str, Any]:
        root = os.getenv("RIU_GRAPHIFY_ROOT")
        if not root:
            return {"status": "GAP_DISABLED"}
        try:
            r = subprocess.run(["graphify", root], capture_output=True, timeout=600)
        except FileNotFoundError:
            return {"status": "GAP_GRAPHIFY_NOT_INSTALLED"}
        return {"status": "BUILT" if r.returncode == 0 else "GAP_BUILD_FAILED", "rc": r.returncode}

    def save(self, scope: str, key: str, data: Any) -> dict[str, Any]:
        return {"adapter": self.name, "status": "SKIPPED", "reason": "code-graph-not-memory"}

    def search(self, scope: str, query: str, k: int = 10) -> list[dict[str, Any]]:
        p = self._graph_path()
        if p is None or not p.exists():
            return []
        g = json.loads(p.read_text(encoding="utf-8"))
        nodes = g.get("nodes", [])
        terms = [t for t in query.lower().split() if t]
        out = []
        for n in nodes:
            text = json.dumps(n, ensure_ascii=False).lower()
            score = sum(t in text for t in terms)
            if score:
                out.append((score, n))
        out.sort(key=lambda x: -x[0])
        return [{"source": "graphify", "text": str(n.get("label") or n.get("id")), "node": n.get("id")} for _, n in out[:k]]


class MemantoAdapter(_Base):
    """Memanto via REST v2 (RIU_MEMANTO_URL). Agente estable yaiwes-router; token solo en RAM."""
    name = "memanto"
    AGENT = "yaiwes-router"

    def __init__(self) -> None:
        self._token: str | None = None

    def _base(self) -> str:
        return (os.getenv("RIU_MEMANTO_URL") or "").rstrip("/")

    def _req(self, method: str, path: str, body: dict | None = None, auth: bool = True) -> Any:
        h = {"Content-Type": "application/json"}
        if auth and self._token:
            h["X-Session-Token"] = self._token
        rq = Request(self._base() + path, method=method, headers=h, data=json.dumps(body).encode() if body is not None else None)
        with urlopen(rq, timeout=5) as r:
            return json.loads(r.read().decode() or "{}")

    def _activate(self) -> None:
        out = self._req("POST", f"/api/v2/agents/{self.AGENT}/activate", {}, auth=False)
        self._token = out.get("session_token")
        if not self._token:
            raise RuntimeError("NO_SESSION_TOKEN")

    def health(self) -> dict[str, Any]:
        if not self._base():
            return {"status": "GAP_DISABLED"}
        try:
            self._activate()
            return {"status": "CONNECTED", "agent": self.AGENT, "e2e_verified": False}
        except Exception as exc:  # noqa: BLE001
            return {"status": f"GAP_SERVICE_UNREACHABLE:{type(exc).__name__}"}

    def _ensure(self) -> None:
        if not self._token:
            self._activate()

    def save(self, scope: str, key: str, data: Any) -> dict[str, Any]:
        self._ensure()
        self._req("POST", f"/api/v2/agents/{self.AGENT}/remember", {"content": _flat(data), "tags": [scope, key]})
        return {"adapter": self.name, "status": "SAVED"}

    def search(self, scope: str, query: str, k: int = 10) -> list[dict[str, Any]]:
        self._ensure()
        out = self._req("POST", f"/api/v2/agents/{self.AGENT}/recall", {"query": query, "limit": k})
        items = out.get("memories") or out.get("results") or []
        return [{"source": "memanto", "text": str(i.get("content", i))} for i in items if scope in json.dumps(i)][:k]
