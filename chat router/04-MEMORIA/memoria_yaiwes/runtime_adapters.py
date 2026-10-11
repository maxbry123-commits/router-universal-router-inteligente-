"""Adaptadores de Graphiti (memoria) y Graphify (codigo) para memoria_yaiwes.

Regla: CONNECTED solo si el contrato real se cumple; si falta algo, GAP_* especifico.
SQLite sigue siendo la verdad; Graphiti/Graphify son indices derivados.
Sin modelos nuevos: el vector de Graphiti es QdrantLocalAdapter.embed (256, NO semantico).
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import threading
import types
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.request import Request, urlopen

EMBED_DIM = 256


def _data_dir() -> Path:
    return Path(os.getenv("RIU_DATA_DIR") or (Path.cwd() / "riu_data"))


def _flat(data: Any) -> str:
    return data if isinstance(data, str) else json.dumps(data, ensure_ascii=False, sort_keys=True)


class _Base:
    name = "base"
    IN_SAVE = True  # False = fuera del guardado de memoria

    def health(self) -> dict[str, Any]:
        return {"status": "GAP"}

    def _endpoint(self) -> str | None:  # la fachada solo llama si esto es truthy
        return "local" if self.health().get("status") == "CONNECTED" else None

    def load(self, scope: str, key: str) -> list[dict[str, Any]]:
        return []

    def save(self, scope: str, key: str, data: Any) -> dict[str, Any]:
        return {"adapter": self.name, "status": "SKIPPED"}

    def search(self, scope: str, query: str, k: int = 10) -> list[dict[str, Any]]:
        return []


class YaiwesGraphitiEmbedder:
    """Puente al vector tecnico existente (QdrantLocalAdapter.embed). NO es semantico."""
    dimension = EMBED_DIM
    semantic = False

    def __init__(self, embed_fn: Callable[[Any], list[float]]) -> None:
        self._embed = embed_fn

    async def create(self, input_data: Any) -> list[float]:
        text = input_data if isinstance(input_data, str) else " ".join(map(str, input_data))
        return [float(x) for x in self._embed(text)]

    async def create_batch(self, input_data_list: list[str]) -> list[list[float]]:
        return [[float(x) for x in self._embed(t)] for t in input_data_list]


class YaiwesPassthroughCrossEncoder:
    """Sin modelo ni API: devuelve los mismos pasajes en orden estable (evita el reranker OpenAI por defecto)."""

    async def rank(self, query: str, passages: list[str]) -> list[tuple[str, float]]:
        n = len(passages)
        return [(p, float(n - i)) for i, p in enumerate(passages)]


def _extract_json(text: str) -> dict[str, Any]:
    m = re.search(r"\{.*\}", text or "", re.S)
    return json.loads(m.group(0)) if m else {}


def build_llm_client(call: Callable[[list[dict[str, str]], int], str]) -> Any:
    """YaiwesGraphitiLLM: LLMClient de Graphiti que delega en la llamada del modelo YA elegido por la ficha."""
    from graphiti_core.llm_client.client import LLMClient
    from graphiti_core.llm_client.config import LLMConfig

    class YaiwesGraphitiLLM(LLMClient):
        def __init__(self) -> None:
            super().__init__(LLMConfig(api_key="ficha", model="ficha"), cache=False)

        async def _generate_response(self, messages, response_model=None, max_tokens=8192, model_size=None):  # noqa: ANN001
            msgs = [{"role": m.role, "content": m.content} for m in messages]
            if response_model is not None:
                schema = json.dumps(response_model.model_json_schema(), ensure_ascii=False)
                msgs[-1]["content"] += "\n\nResponde SOLO con JSON valido que cumpla este esquema:\n" + schema
            text = await asyncio.to_thread(call, msgs, max_tokens)
            return _extract_json(text) if response_model is not None else {"content": text}

    return YaiwesGraphitiLLM()


class GraphitiAdapter(_Base):
    """Graphiti 0.30.2 -> FalkorDriver -> FalkorDBLite en <RIU_DATA_DIR>/indices/graphiti/graphiti.db.
    LLM = el de la ficha (set_llm_client); embedder = QdrantLocalAdapter.embed; cross-encoder sin modelo."""
    name = "graphiti"

    def __init__(self, embed_fn: Callable[[Any], list[float]] | None = None) -> None:
        self._embed_fn = embed_fn
        self._call_ref: dict[str, Any] = {"call": None}
        self._g: Any = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._verified = False
        self._err: str | None = None

    def set_llm_client(self, call: Callable[[list[dict[str, str]], int], str]) -> None:
        """Recibe la llamada al modelo que ya ejecuta la ficha: call(messages, max_tokens) -> texto."""
        self._call_ref["call"] = call

    @staticmethod
    def db_path() -> Path:
        return _data_dir() / "indices" / "graphiti" / "graphiti.db"

    def health(self) -> dict[str, Any]:
        if os.getenv("RIU_GRAPHITI_ENABLE") != "1":
            return {"status": "GAP_DISABLED"}
        try:
            import graphiti_core  # noqa: F401
        except ImportError as exc:
            return {"status": "GAP_IMPORT", "missing": getattr(exc, "name", None)}
        try:
            from redislite.async_falkordb_client import AsyncFalkorDB  # noqa: F401
        except ImportError as exc:
            return {"status": "GAP_GRAPH_BACKEND", "missing": getattr(exc, "name", "falkordblite")}
        if self._call_ref["call"] is None:
            return {"status": "GAP_LLM", "reason": "la ficha aun no entrego su modelo"}
        if self._embed_fn is None:
            return {"status": "GAP_EMBEDDER"}
        return {"status": self._err or "CONNECTED", "backend": "falkordblite", "db": str(self.db_path()),
                "embedding": {"dim": EMBED_DIM, "semantic": False, "source": "QdrantLocalAdapter.embed"},
                "e2e_verified": self._verified}

    def _run(self, coro: Any, timeout: float = 300) -> Any:
        if self._loop is None:
            self._loop = asyncio.new_event_loop()
            threading.Thread(target=self._loop.run_forever, daemon=True, name="graphiti-loop").start()
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result(timeout)

    def _graph(self) -> Any:
        if self._g is not None:
            return self._g
        os.environ.setdefault("EMBEDDING_DIM", str(EMBED_DIM))  # antes de importar graphiti_core
        from graphiti_core import Graphiti
        from graphiti_core.cross_encoder.client import CrossEncoderClient
        from graphiti_core.driver.falkordb_driver import FalkorDriver
        from graphiti_core.embedder.client import EmbedderClient
        from redislite.async_falkordb_client import AsyncFalkorDB
        self.db_path().parent.mkdir(parents=True, exist_ok=True)
        driver = FalkorDriver(falkor_db=AsyncFalkorDB(str(self.db_path())))
        emb = types.new_class("YaiwesGraphitiEmbedder", (YaiwesGraphitiEmbedder, EmbedderClient))(self._embed_fn)
        ce = types.new_class("YaiwesPassthroughCrossEncoder", (YaiwesPassthroughCrossEncoder, CrossEncoderClient))()
        llm = build_llm_client(lambda msgs, mt: self._call_ref["call"](msgs, mt))
        g = Graphiti(graph_driver=driver, llm_client=llm, embedder=emb, cross_encoder=ce)
        self._run(g.build_indices_and_constraints())
        self._g = g
        return g

    @staticmethod
    def _gid(scope: str) -> str:
        return re.sub(r"[^A-Za-z0-9_-]", "_", scope) or "default"

    def save(self, scope: str, key: str, data: Any) -> dict[str, Any]:
        try:
            from graphiti_core.nodes import EpisodeType
            body = json.dumps(data if isinstance(data, (dict, list)) else {"text": str(data)}, ensure_ascii=False, sort_keys=True)
            self._run(self._graph().add_episode(name=f"{scope}:{key}", episode_body=body, source_description="yaiwes-memory",
                                                reference_time=datetime.now(timezone.utc), source=EpisodeType.json,
                                                group_id=self._gid(scope)))
            return {"adapter": self.name, "status": "SAVED"}
        except Exception as exc:  # noqa: BLE001 - SQLite ya guardo; Graphiti nunca tumba el chat
            self._err = f"GAP_WRITE:{type(exc).__name__}"
            return {"adapter": self.name, "status": "GAP", "reason": self._err}

    def search(self, scope: str, query: str, k: int = 10) -> list[dict[str, Any]]:
        gid = self._gid(scope)
        res = self._run(self._graph().search(query, group_ids=[gid], num_results=k))
        self._verified = True
        out = []
        for r in res:
            fact = str(getattr(r, "fact", r))
            out.append({"source": "graphiti", "scope": scope, "id": str(getattr(r, "uuid", "")), "text": fact, "content": fact,
                        "score": None, "provenance": {"group_id": gid, "episodes": [str(e) for e in (getattr(r, "episodes", None) or [])]}})
        return out

    def close(self) -> None:
        if self._g is not None:
            try:
                self._run(self._g.close(), 60)
            finally:
                self._g = None


class GraphifyCodeAdapter(_Base):
    """Graphify 0.1.14 sobre CODIGO, via modulos Python (sin CLI, sin LLM, sin embeddings).
    SOURCE de solo lectura -> OUTPUT escribible (<RIU_DATA_DIR>/indices/graphify/graph.json)."""
    name = "graphify"
    IN_SAVE = False

    def __init__(self, source_root: str | Path | None = None, output_dir: str | Path | None = None) -> None:
        self._src, self._out = source_root, output_dir

    def source_root(self) -> Path | None:
        r = self._src or os.getenv("RIU_GRAPHIFY_SOURCE_ROOT") or os.getenv("RIU_GRAPHIFY_ROOT")
        return Path(r) if r else None

    def output_dir(self) -> Path:
        return Path(self._out or os.getenv("RIU_GRAPHIFY_OUTPUT") or (_data_dir() / "indices" / "graphify"))

    def graph_path(self) -> Path:
        return self.output_dir() / "graph.json"

    def _gap_io(self) -> dict[str, Any] | None:
        s = self.source_root()
        if s is None or not s.is_dir() or not os.access(s, os.R_OK):
            return {"status": "GAP_SOURCE"}
        o = self.output_dir()
        try:
            o.mkdir(parents=True, exist_ok=True)
        except OSError:
            return {"status": "GAP_OUTPUT"}
        return None if os.access(o, os.W_OK) else {"status": "GAP_OUTPUT"}

    def health(self) -> dict[str, Any]:
        gap = self._gap_io()
        if gap:
            return gap
        g = self.graph_path()
        if not g.exists():
            return {"status": "GAP_GRAPH_NOT_BUILT"}
        try:
            nodes = json.loads(g.read_text(encoding="utf-8")).get("nodes") or []
        except Exception:  # noqa: BLE001
            return {"status": "GAP_QUERY", "reason": "graph.json invalido"}
        if not nodes:
            return {"status": "GAP_QUERY", "reason": "graph.json vacio"}
        return {"status": "CONNECTED", "nodes": len(nodes), "graph_json": str(g), "e2e_verified": False}

    def build(self) -> dict[str, Any]:
        gap = self._gap_io()
        if gap:
            return gap
        try:
            from graphify.build import build_from_json
            from graphify.cluster import cluster
            from graphify.detect import detect
            from graphify.export import to_json
            from graphify.extract import collect_files, extract
        except ImportError as exc:
            return {"status": "GAP_GRAPHIFY_DEPS", "missing": getattr(exc, "name", str(exc))}
        src = self.source_root()
        code = (detect(src).get("files") or {}).get("code") or []
        files: list[Path] = []
        for p in code:
            p = Path(p)
            files.extend(collect_files(p if p.is_absolute() else src / p))
        if not files:
            return {"status": "GAP_NO_CODE_FILES"}
        graph = build_from_json(extract(files))  # solo AST de codigo: sin extraccion semantica/LLM
        try:
            comunidades = cluster(graph)
        except ImportError:  # sin graspologic: una sola comunidad (to_json solo necesita grafo + mapa de comunidades)
            comunidades = {0: list(graph.nodes())}
        to_json(graph, comunidades, str(self.graph_path()))
        return {"status": "BUILT", "files": len(files), "graph_json": str(self.graph_path())}

    def save(self, scope: str, key: str, data: Any) -> dict[str, Any]:
        return {"adapter": self.name, "status": "SKIPPED", "reason": "code-graph-not-memory"}

    def search(self, scope: str, query: str, k: int = 10) -> list[dict[str, Any]]:
        g = self.graph_path()
        if not g.exists():
            return []
        data = json.loads(g.read_text(encoding="utf-8"))
        links = data.get("links") or data.get("edges") or []
        terms = [t for t in query.lower().split() if t]
        scored = []
        for n in data.get("nodes", []):
            hay = " ".join(str(n.get(f, "")) for f in ("id", "label", "source_file", "file")).lower()
            s = sum(t in hay for t in terms)
            if s:
                scored.append((s, n))
        scored.sort(key=lambda x: -x[0])
        out = []
        for _, n in scored[:k]:
            nid = n.get("id")
            edges = [{"source": e.get("source"), "target": e.get("target"), "relation": e.get("relation") or e.get("type")}
                     for e in links if nid in (e.get("source"), e.get("target"))][:20]
            out.append({"source": "graphify", "id": nid, "label": n.get("label"), "file": n.get("source_file") or n.get("file"),
                        "text": str(n.get("label") or nid), "edges": edges})
        return out


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
