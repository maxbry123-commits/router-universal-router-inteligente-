"""Chat MVP HTTP surface: providers, chat, agents, documents, GitHub accounts, storage, usage, DAG and graph.

Every /chat/* data endpoint requires a Router API key (env RIU_AGENT_API_KEYS or the certified MAXBRY keystore).
Provider keys and GitHub tokens come from the server environment or from per-request BYOK headers
(X-Provider-Key, X-Provider-Keys as JSON, X-GitHub-Token); they are never stored, logged or returned.
Chat turns go through the certified hot path: FastAPI -> Enchufe Gate -> RedUniversal -> provider executor.
Cost: response cache ON by default, prefix-stable prompts and a usage log (see core.py / usage.py).
"""
from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import tempfile
import threading
import time
import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field

from ..huggingface.api_key_auth import authenticate_api_key
from ..huggingface.chat_catalog import (
    cached_discovery,  # noqa: F401
    family_of,
    selector_models,
)
from . import core, dag_cli, model_pool, org_api, resilience, ui_bridge
from . import dag as dagmod
from . import github_tools as gh
from . import providers as prov
from .fables_adapter import FablesCatalog
from .memory_runtime import memory, scope_for
from .store import Store
from .usage import UsageLog, normalize_usage

_UI = Path(__file__).with_name("chat_ui.html")
_ORG_UI = Path(__file__).resolve().parents[3] / "chat router/ui/shell.html"
_store: Store | None = None
_fables_catalog: FablesCatalog | None = None


def get_store() -> Store:
    global _store
    if _store is None:
        default = Path("/data") if os.access("/data", os.W_OK) else Path.cwd() / "riu_data"
        data_dir = Path(os.getenv("RIU_DATA_DIR") or default)
        bucket = os.getenv("HF_BUCKET_ID")
        token = os.getenv("HF_WRITE_TOKEN") or os.getenv("HF_TOKEN") or ""
        if bucket and token and not (data_dir / "riu_chat.sqlite3").exists():
            try:  # permanent storage: a fresh Router starts from the last HF bucket snapshot
                restore_from_bucket(data_dir, bucket, token)
            except Exception as exc:  # never take the Router down for storage GAPs
                logging.getLogger("riu").warning("bucket restore omitido: %s", type(exc).__name__)
        _store = Store(data_dir)
    return _store


def set_store(store: Store | None) -> None:
    global _store
    _store = store


def get_fables_catalog() -> FablesCatalog:
    global _fables_catalog
    if _fables_catalog is None:
        _fables_catalog = FablesCatalog()
    return _fables_catalog


def _auth(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    authorization: str | None = Header(default=None),
) -> str:
    candidate = x_api_key
    if not candidate and authorization and authorization.lower().startswith("bearer "):
        candidate = authorization[7:].strip()
    try:
        return authenticate_api_key(candidate)
    except RuntimeError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


def restore_from_bucket(data_dir: str | Path, bucket_id: str, token: str, *, fs_factory: Callable[..., Any] | None = None) -> dict[str, Any]:
    """Inverse of sync_to_bucket: bring the SQLite snapshot and documents back from the HF bucket."""
    if fs_factory is None:
        from huggingface_hub import HfFileSystem as fs_factory
    fs = fs_factory(token=token)
    base = f"buckets/{bucket_id}/riu-chat"
    data_dir = Path(data_dir)
    if not fs.exists(f"{base}/riu_chat.sqlite3"):
        return {"bucket": bucket_id, "restored": 0}
    (data_dir / "docs").mkdir(parents=True, exist_ok=True)
    (data_dir / "riu_chat.sqlite3").write_bytes(fs.cat_file(f"{base}/riu_chat.sqlite3"))
    files = 1
    if fs.exists(f"{base}/docs"):
        for path in fs.ls(f"{base}/docs", detail=False):
            (data_dir / "docs" / Path(path).name).write_bytes(fs.cat_file(path))
            files += 1
    return {"bucket": bucket_id, "restored": files}


def start_bucket_autosync(interval_s: float | None = None) -> threading.Thread | None:
    """Background sync to the HF bucket whenever the SQLite store changed (RIU_AUTOSYNC_SECONDS, 0 = off)."""
    interval = float(os.getenv("RIU_AUTOSYNC_SECONDS", "60") if interval_s is None else interval_s)
    bucket = os.getenv("HF_BUCKET_ID")
    token = os.getenv("HF_WRITE_TOKEN") or os.getenv("HF_TOKEN") or ""
    if interval <= 0 or not bucket or not token:
        return None

    def loop() -> None:
        last = -1
        while True:
            time.sleep(interval)
            try:
                store = get_store()
                changes = store._db.total_changes
                if changes != last:
                    sync_to_bucket(store, bucket, token)
                    last = changes
            except Exception as exc:  # keep trying; never crash the Router
                logging.getLogger("riu").warning("bucket autosync fallo: %s", type(exc).__name__)

    thread = threading.Thread(target=loop, name="riu-bucket-autosync", daemon=True)
    thread.start()
    return thread


def sync_to_bucket(store: Store, bucket_id: str, token: str, *, fs_factory: Callable[..., Any] | None = None) -> dict[str, Any]:
    """Copy the SQLite snapshot and documents into an HF storage bucket (needs a write token)."""
    if fs_factory is None:
        from huggingface_hub import HfFileSystem as fs_factory
    fs = fs_factory(token=token)
    base = f"buckets/{bucket_id}/riu-chat"
    files = 0
    with tempfile.TemporaryDirectory() as tmp:
        snap = store.snapshot(Path(tmp) / "riu_chat.sqlite3")
        fs.pipe_file(f"{base}/riu_chat.sqlite3", snap.read_bytes())
        files += 1
    for doc in store.documents():
        fs.pipe_file(f"{base}/docs/{doc['id']}", (store.dir / "docs" / doc["id"]).read_bytes())
        files += 1
    return {"bucket": bucket_id, "files": files}


class SendReq(BaseModel):
    message: str = Field(min_length=1, max_length=20000)
    provider: str = "hf"  # "auto" = the Router picks the model (chain of the "default" group in resilience.py); then `model` is ignored
    model: str = ""
    conversation_id: str | None = None
    mode: str = "direct"  # direct = sin agente, agent = con agente
    agent_id: str | None = None
    doc_ids: list[str] = []
    cache: bool = True  # exact-match response cache (skipped when temperature > 0)
    refresh: bool = False  # bypass the cache read and overwrite the entry
    max_tokens: int = Field(default=1024, ge=1, le=8192)
    temperature: float | None = None
    github: dict[str, str] | None = None  # {"account": ..., "repo": ...} provenance only


class DocReq(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    mime: str = "application/octet-stream"
    data_b64: str
    conversation_id: str | None = None


class AgentReq(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{1,63}$")
    name: str = Field(min_length=1, max_length=120)
    role: str = "general"
    system_prompt: str = ""
    models: list[str] = []


class CommitReq(BaseModel):
    account: str
    repo: str = Field(pattern=r"^[\w.-]+/[\w.-]+$")
    path: str = Field(min_length=1, max_length=300)
    content: str
    message: str = Field(default="chat: update from RIU chat", max_length=200)
    branch: str | None = None


class DagReq(BaseModel):
    dag: dict[str, Any]


class FichaReq(BaseModel):
    ficha: dict[str, Any]


def _gh_token(account: str, byok: str | None) -> str:
    token = gh.token_for(account, byok)
    if not token:
        raise HTTPException(status_code=400, detail="GITHUB_ACCOUNT_NOT_CONFIGURED")
    return token


def _gh(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    try:
        return fn(*args, **kwargs)
    except gh.GitHubError as exc:
        raise HTTPException(status_code=404 if str(exc.status) == "404" else 502, detail=str(exc)) from exc


def build_router() -> APIRouter:
    r = APIRouter()
    r.include_router(org_api.build_org_router(_auth, get_store, get_fables_catalog))

    @r.get("/chat/organization", response_class=HTMLResponse)
    def organization() -> HTMLResponse:
        return HTMLResponse(_ORG_UI.read_text(encoding="utf-8"))

    @r.get("/chat/fichas")
    def fichas(_owner: str = Depends(_auth)) -> dict[str, Any]:
        return {"fichas": get_fables_catalog().list()}

    @r.get("/chat/fichas/{artifact_id}")
    def ficha(artifact_id: str, _owner: str = Depends(_auth)) -> dict[str, Any]:
        entry = get_fables_catalog().get(artifact_id)
        if entry is None:
            raise HTTPException(status_code=404, detail="FICHA_NOT_FOUND")
        return {"ficha": entry}

    @r.post("/chat/fichas")
    def register_ficha(req: FichaReq, _owner: str = Depends(_auth)) -> dict[str, Any]:
        try:
            return {"ficha": get_fables_catalog().register(req.ficha)}
        except ValueError as exc:
            detail = str(exc)
            raise HTTPException(status_code=409 if detail == "FICHA_ALREADY_REGISTERED" else 422, detail=detail) from exc

    @r.get("/chat", response_class=HTMLResponse)
    def page() -> HTMLResponse:
        return HTMLResponse(_UI.read_text(encoding="utf-8"))

    @r.get("/chat/providers")
    def providers() -> dict[str, Any]:
        chain, _skipped = resilience.resolve_chain("default", datetime.now(timezone.utc))
        auto = {"id": "auto", "label": "Automático (el Router elige el modelo y pasa al siguiente si uno falla)", "configured": bool(chain)}
        return {"live_provider_inference": core.live_enabled(),
                "providers": [auto] + [{"id": k, "label": v["label"], "configured": prov.configured(k)} for k, v in prov.registry().items()]}

    @r.get("/chat/providers/{provider}/models")
    def provider_models(provider: str, _owner: str = Depends(_auth),
                        x_provider_key: str | None = Header(default=None, alias="X-Provider-Key")) -> dict[str, Any]:
        if provider == "auto":  # one pseudo-model: the model is chosen by the chain of the "default" group on every turn
            return {"provider": "auto", "models": [{"label": "Automático", "model_id": "auto", "state": "ROUTER_CHAIN", "certified": False,
                                                    "selectable": True, "suggested": True}]}
        if provider not in prov.registry():
            raise HTTPException(status_code=404, detail="PROVIDER_UNKNOWN")
        if provider == "hf":
            rows = selector_models(discovered=core.cached_discovery(), live_enabled=core.live_enabled())["models"]
            return {"provider": "hf", "models": rows}
        key = prov.resolve_key(provider, x_provider_key)
        if not key and provider != "local":
            raise HTTPException(status_code=400, detail="PROVIDER_KEY_MISSING")
        try:
            ids = prov.list_models(provider, key)
        except prov.ProviderError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        ids = sorted(ids, key=lambda i: (family_of(i) is None, i))
        return {"provider": provider, "models": [{"label": i, "model_id": i, "state": "PROVIDER_CATALOG", "certified": False,
                                                  "selectable": True, "suggested": family_of(i) is not None} for i in ids]}

    @r.post("/chat/send")
    async def send(req: SendReq, owner: str = Depends(_auth),
                   x_provider_key: str | None = Header(default=None, alias="X-Provider-Key")) -> dict[str, Any]:
        st = get_store()
        auto = req.provider == "auto"  # 2026-09-29: Kimi K3 -> GLM 5.3 -> DeepSeek V4 -> Qwen 3.8 (Groq) -> Nemotron, falls to the next by itself
        if not auto and req.provider not in prov.registry():
            raise HTTPException(status_code=400, detail="PROVIDER_UNKNOWN")
        if not auto and not req.model:
            raise HTTPException(status_code=400, detail="MODEL_REQUIRED")
        if req.mode not in {"direct", "agent"}:
            raise HTTPException(status_code=400, detail="MODE_INVALID")
        agent = None
        if req.mode == "agent":
            agent = st.agent(req.agent_id or "")
            if not agent:
                raise HTTPException(status_code=400, detail="AGENT_NOT_FOUND")
        key = None if auto else prov.resolve_key(req.provider, x_provider_key)
        if not auto and not key and req.provider != "local":
            raise HTTPException(status_code=400, detail=f"PROVIDER_KEY_MISSING:{req.provider}")
        certified = False
        if auto:
            pass  # every option of the chain is checked by its own gate / provider list (resilience.run_policy + model_pool)
        elif req.provider == "hf":
            try:
                certified = core.hf_gate(req.model)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
        else:
            try:
                if req.model not in prov.list_models(req.provider, key):
                    raise HTTPException(status_code=400, detail="MODEL_NOT_IN_PROVIDER_CATALOG")
            except prov.ProviderError as exc:
                raise HTTPException(status_code=502, detail=str(exc)) from exc
        conv = req.conversation_id
        if conv:
            row = st.conversation(conv)
            if not row or row["owner"] != owner:
                raise HTTPException(status_code=404, detail="CONVERSATION_NOT_FOUND")
        # Prefix-stable order (provider prompt caching): agent prompt, documents sorted by id, history, new turn.
        msgs: list[dict[str, str]] = []
        if agent and agent["system_prompt"]:
            msgs.append({"role": "system", "content": agent["system_prompt"]})
        used_docs: list[str] = []
        for did in sorted(set(req.doc_ids)):
            doc, text = st.document(did), st.document_text(did)
            if not doc or text is None:
                raise HTTPException(status_code=404, detail=f"DOCUMENT_NOT_READABLE:{did}")
            msgs.append({"role": "system", "content": f"Documento adjunto «{doc['name']}»:\n{text}"})
            used_docs.append(did)
        if conv:
            msgs += core.trim_history([{"role": m["role"], "content": m["content"]} for m in st.messages(conv, limit=40)])
        msgs.append({"role": "user", "content": req.message})
        used_provider, used_model, route_trace = req.provider, req.model, None
        try:
            if auto:
                from .route_api import _call as route_call

                out = await asyncio.to_thread(resilience.run_policy, "default", msgs, req.max_tokens, temperature=req.temperature,
                                              call=route_call, pool=model_pool.POOL)
                used_provider, used_model, route_trace = out["route"]["provider"], out["route"]["model"], out["trace"]
                result = {"message": out["message"], "finish_reason": out.get("finish_reason"), "usage": out.get("usage"), "cached": False}
                UsageLog(st).record(owner=owner, provider=used_provider, model=used_model, usage=result["usage"], from_cache=False)
            else:
                result = await asyncio.to_thread(core.run_completion, st, owner, req.provider, key, req.model, msgs, req.max_tokens,
                                                 req.temperature, use_cache=req.cache, refresh=req.refresh)
        except RuntimeError as exc:
            trace = getattr(exc, "trace", None)
            # A plain string on purpose: the current chat page writes `detail` into a sentence (an object would show as [object Object]).
            detail = f"{exc} | " + " ; ".join(trace) if (auto and trace) else str(exc)
            busy = str(exc).startswith("ROUTER_SATURATED")  # the Router is busy, no model failed: 503 like /chat/route
            raise HTTPException(status_code=503 if busy else 502, detail=detail[:900]) from exc
        reply = result["message"].get("content") or ""
        if reply:
            if not conv:
                conv = st.new_conversation(req.message, agent["id"] if agent else None, owner)
            st.add_message(conv, "user", req.message)
            st.add_message(conv, "assistant", reply, used_provider, used_model)
            st.record_turn(conv_id=conv, owner=owner, provider=used_provider, model=used_model,
                           agent_id=agent["id"] if agent else None, doc_ids=used_docs,
                           repo=(req.github or {}).get("repo"))
        body = {"conversation_id": conv, "reply": reply, "empty": not reply, "provider": used_provider, "model": used_model,
                "certified": certified, "cached": result["cached"], "finish_reason": result.get("finish_reason"),
                "usage": result.get("usage"), "usage_normalized": normalize_usage(result.get("usage")),
                "docs_used": used_docs, "agent_id": agent["id"] if agent else None}
        if auto:
            body["auto"] = True
            body["trace"] = route_trace  # why earlier options were skipped / failed (NOT_LISTED, COOLING, provider errors)
        if reply:
            memory_key = f"turn:{conv}:{uuid.uuid4().hex}"
            payload = {"conversation_id": conv, "message": req.message, "reply": reply,
                       "provider": used_provider, "model": used_model, "agent_id": body["agent_id"],
                       "doc_ids": used_docs}
            try:
                facade = memory(st)
                result = await asyncio.to_thread(facade.save, scope_for(owner, "chat"), memory_key, payload)
                rows = await asyncio.to_thread(facade.load, scope_for(owner, "chat"), memory_key)
                if not any(row.get("data") == payload for row in rows):
                    raise RuntimeError("MEMORY_READBACK_FAILED")
                replicas = result.get("replicas", {})
                status = "PARTIAL" if any(row.get("status") == "GAP" for row in replicas.values()) else "SAVED"
                body["memory"] = {"status": status, "key": memory_key, "adapter": "sqlite"}
            except Exception as exc:  # noqa: BLE001 - Store already persisted the conversation
                body["memory"] = {"status": "🚩 PENDIENTE", "reason": type(exc).__name__}
        return body

    @r.get("/chat/usage")
    def usage(_owner: str = Depends(_auth)) -> dict[str, Any]:
        return UsageLog(get_store()).summary()

    @r.post("/chat/dag/run")
    async def dag_run(req: DagReq, owner: str = Depends(_auth),
                      x_provider_keys: str | None = Header(default=None, alias="X-Provider-Keys")) -> dict[str, Any]:
        keys: dict[str, str] = {}
        if x_provider_keys:
            try:
                parsed = json.loads(x_provider_keys)
            except json.JSONDecodeError as exc:
                raise HTTPException(status_code=400, detail="X_PROVIDER_KEYS_INVALID_JSON") from exc
            keys = {str(k): str(v) for k, v in parsed.items()} if isinstance(parsed, dict) else {}
        st = get_store()
        agents = {a["id"]: a["system_prompt"] for a in st.agents()}
        try:
            return await asyncio.to_thread(dagmod.run_dag, req.dag, dag_cli.build_executor(st, owner, keys),
                                           agents=agents, known_providers=set(prov.registry()),
                                           state_emit=ui_bridge._emit_state_event if any(
                                               n.get("type") == "agent" for n in req.dag.get("nodes", [])
                                               if isinstance(n, dict)) else None)
        except dagmod.DagError as exc:
            raise HTTPException(status_code=400, detail=f"DAG_INVALID:{exc}") from exc

    @r.get("/chat/conversations")
    def conversations(owner: str = Depends(_auth)) -> dict[str, Any]:
        return {"conversations": get_store().conversations(owner)}

    @r.get("/chat/conversations/{cid}")
    def conversation(cid: str, owner: str = Depends(_auth)) -> dict[str, Any]:
        st = get_store()
        row = st.conversation(cid)
        if not row or row["owner"] != owner:
            raise HTTPException(status_code=404, detail="CONVERSATION_NOT_FOUND")
        return {"conversation": row, "messages": st.messages(cid, limit=200)}

    @r.get("/chat/agents")
    def agents(_owner: str = Depends(_auth)) -> dict[str, Any]:
        return {"agents": get_store().agents()}

    @r.post("/chat/agents")
    def upsert_agent(req: AgentReq, _owner: str = Depends(_auth)) -> dict[str, Any]:
        get_store().upsert_agent(req.id, req.name, req.role, req.system_prompt, req.models)
        return {"agent": get_store().agent(req.id)}

    @r.delete("/chat/agents/{agent_id}")
    def delete_agent(agent_id: str, _owner: str = Depends(_auth)) -> dict[str, Any]:
        if not get_store().delete_agent(agent_id):
            raise HTTPException(status_code=404, detail="AGENT_NOT_FOUND")
        return {"deleted": agent_id}

    @r.post("/chat/documents")
    def upload(req: DocReq, _owner: str = Depends(_auth)) -> dict[str, Any]:
        try:
            data = base64.b64decode(req.data_b64, validate=True)
        except Exception as exc:
            raise HTTPException(status_code=400, detail="DOCUMENT_BASE64_INVALID") from exc
        st = get_store()
        try:
            doc = st.put_document(req.name, req.mime, data, req.conversation_id)
        except ValueError as exc:
            raise HTTPException(status_code=413 if "LARGE" in str(exc) else 400, detail=str(exc)) from exc
        st.graph_node(f"doc:{doc['id']}", "document", doc["name"])
        return {"document": doc}

    @r.get("/chat/documents")
    def documents(_owner: str = Depends(_auth)) -> dict[str, Any]:
        return {"documents": get_store().documents()}

    @r.get("/chat/documents/{did}")
    def document(did: str, _owner: str = Depends(_auth)) -> dict[str, Any]:
        st = get_store()
        doc = st.document(did)
        if not doc:
            raise HTTPException(status_code=404, detail="DOCUMENT_NOT_FOUND")
        return {"document": doc, "preview": st.document_text(did, limit=4000)}

    @r.get("/chat/media/{did}")
    def media(did: str, _owner: str = Depends(_auth)) -> FileResponse:
        st = get_store()
        doc = st.document(did)
        allowed = {"image/png", "image/jpeg", "image/gif", "image/webp", "video/mp4", "video/webm"}
        if not doc or doc["mime"] not in allowed:
            raise HTTPException(status_code=404, detail="MEDIA_NOT_FOUND")
        path = st.dir / "docs" / doc["id"]
        if not path.is_file():
            raise HTTPException(status_code=404, detail="MEDIA_NOT_FOUND")
        return FileResponse(path, media_type=doc["mime"], headers={"X-Content-Type-Options": "nosniff"})

    @r.delete("/chat/documents/{did}")
    def delete_document(did: str, _owner: str = Depends(_auth)) -> dict[str, Any]:
        if not get_store().delete_document(did):
            raise HTTPException(status_code=404, detail="DOCUMENT_NOT_FOUND")
        return {"deleted": did}

    @r.get("/chat/graph")
    def graph(_owner: str = Depends(_auth)) -> dict[str, Any]:
        return get_store().graph_view()

    @r.get("/chat/storage")
    def storage(_owner: str = Depends(_auth)) -> dict[str, Any]:
        st = get_store()
        bucket = os.getenv("HF_BUCKET_ID") or ""
        return {**st.stats(), "data_dir": str(st.dir),
                "hf_bucket": {"configured": bool(bucket), "id": bucket or None,
                              "write_token": bool(os.getenv("HF_WRITE_TOKEN") or os.getenv("HF_TOKEN"))}}

    @r.post("/chat/storage/sync")
    def storage_sync(_owner: str = Depends(_auth)) -> dict[str, Any]:
        bucket = os.getenv("HF_BUCKET_ID")
        token = os.getenv("HF_WRITE_TOKEN") or os.getenv("HF_TOKEN") or ""
        if not bucket:
            raise HTTPException(status_code=400, detail="HF_BUCKET_ID_NOT_SET")
        if not token:
            raise HTTPException(status_code=400, detail="HF_BUCKET_WRITE_TOKEN_NOT_SET")
        try:
            return sync_to_bucket(get_store(), bucket, token)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"BUCKET_SYNC_FAILED:{type(exc).__name__}") from exc

    @r.get("/chat/github/accounts")
    def gh_accounts(_owner: str = Depends(_auth),
                    x_github_token: str | None = Header(default=None, alias="X-GitHub-Token")) -> dict[str, Any]:
        rows = [{"account": label, "configured": bool(os.getenv(var)), "source": "env"} for label, var in gh.accounts_from_env().items()]
        if x_github_token:
            rows.append({"account": "byok", "configured": True, "source": "header"})
        return {"accounts": rows}

    @r.get("/chat/github/whoami")
    def gh_whoami(account: str, _owner: str = Depends(_auth),
                  x_github_token: str | None = Header(default=None, alias="X-GitHub-Token")) -> dict[str, Any]:
        return {"account": account, "login": _gh(gh.whoami, _gh_token(account, x_github_token))}

    @r.get("/chat/github/repos")
    def gh_repos(account: str, _owner: str = Depends(_auth),
                 x_github_token: str | None = Header(default=None, alias="X-GitHub-Token")) -> dict[str, Any]:
        return {"repos": _gh(gh.list_repos, _gh_token(account, x_github_token))}

    @r.get("/chat/github/file")
    def gh_file(account: str, repo: str, path: str, ref: str | None = None, attach: bool = False,
                _owner: str = Depends(_auth), x_github_token: str | None = Header(default=None, alias="X-GitHub-Token")) -> dict[str, Any]:
        data = _gh(gh.get_file, _gh_token(account, x_github_token), repo, path, ref)
        out: dict[str, Any] = {"path": data["path"], "sha": data["sha"], "size": data["size"], "text": data["text"]}
        if attach:
            name = f"{repo.split('/')[-1]}_{Path(path).name}"
            doc = get_store().put_document(name, "text/plain", data["text"].encode("utf-8"))
            out["document"] = doc
        return out

    @r.post("/chat/github/commit")
    def gh_commit(req: CommitReq, _owner: str = Depends(_auth),
                  x_github_token: str | None = Header(default=None, alias="X-GitHub-Token")) -> dict[str, Any]:
        return _gh(gh.put_file, _gh_token(req.account, x_github_token), req.repo, req.path, req.content, req.message, req.branch)

    return r
