"""Chat MVP HTTP surface: providers, chat, agents, documents, GitHub accounts, storage and graph.

Every /chat/* data endpoint requires a Router API key (env RIU_AGENT_API_KEYS or the certified MAXBRY keystore).
Provider keys and GitHub tokens come from the server environment or from per-request BYOK headers
(X-Provider-Key, X-GitHub-Token); they are never stored, logged or returned.
Chat turns go through the certified hot path: FastAPI -> Enchufe Gate -> RedUniversal -> provider executor.
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Callable

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from ..huggingface.api_key_auth import authenticate_api_key
from ..huggingface.chat_catalog import cached_discovery, family_of, selectable_live_ids, selector_models
from ..huggingface.huggingface_openai_chat import allowed_model_ids
from ..huggingface.router_hot_path import route_chat_completion
from . import github_tools as gh
from . import providers as prov
from .store import Store

_UI = Path(__file__).with_name("chat_ui.html")
_store: Store | None = None


def get_store() -> Store:
    global _store
    if _store is None:
        default = Path("/data") if os.access("/data", os.W_OK) else Path.cwd() / "riu_data"
        _store = Store(os.getenv("RIU_DATA_DIR") or default)
    return _store


def set_store(store: Store | None) -> None:
    global _store
    _store = store


def _live() -> bool:
    return os.getenv("RIU_CHAT_ALLOW_PROVIDER_LIVE", "") == "1"


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


def sync_to_bucket(store: Store, bucket_id: str, token: str, *, fs_factory: Callable[..., Any] | None = None) -> dict[str, Any]:
    """Copy the SQLite snapshot and documents into an HF storage bucket (needs a write token)."""
    if fs_factory is None:
        from huggingface_hub import HfFileSystem as fs_factory  # noqa: N813
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
    provider: str = "hf"
    model: str
    conversation_id: str | None = None
    mode: str = "direct"  # direct = sin agente, agent = con agente
    agent_id: str | None = None
    doc_ids: list[str] = []
    cache: bool = False
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

    @r.get("/chat", response_class=HTMLResponse)
    def page() -> HTMLResponse:
        return HTMLResponse(_UI.read_text(encoding="utf-8"))

    @r.get("/chat/providers")
    def providers() -> dict[str, Any]:
        return {"live_provider_inference": _live(),
                "providers": [{"id": k, "label": v["label"], "configured": prov.configured(k)} for k, v in prov.PROVIDERS.items()]}

    @r.get("/chat/providers/{provider}/models")
    def provider_models(provider: str, _owner: str = Depends(_auth),
                        x_provider_key: str | None = Header(default=None, alias="X-Provider-Key")) -> dict[str, Any]:
        if provider not in prov.PROVIDERS:
            raise HTTPException(status_code=404, detail="PROVIDER_UNKNOWN")
        if provider == "hf":
            rows = selector_models(discovered=cached_discovery(), live_enabled=_live())["models"]
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
        if req.provider not in prov.PROVIDERS:
            raise HTTPException(status_code=400, detail="PROVIDER_UNKNOWN")
        if req.mode not in {"direct", "agent"}:
            raise HTTPException(status_code=400, detail="MODE_INVALID")
        agent = None
        if req.mode == "agent":
            agent = st.agent(req.agent_id or "")
            if not agent:
                raise HTTPException(status_code=400, detail="AGENT_NOT_FOUND")
        key = prov.resolve_key(req.provider, x_provider_key)
        if not key and req.provider != "local":
            raise HTTPException(status_code=400, detail=f"PROVIDER_KEY_MISSING:{req.provider}")
        certified = False
        if req.provider == "hf":
            if req.model in allowed_model_ids():
                certified = True
            elif not (_live() and req.model in selectable_live_ids(discovered=cached_discovery())):
                raise HTTPException(status_code=400, detail="MODEL_NOT_SELECTABLE")
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
        msgs: list[dict[str, str]] = []
        if agent and agent["system_prompt"]:
            msgs.append({"role": "system", "content": agent["system_prompt"]})
        used_docs: list[str] = []
        for did in req.doc_ids:
            doc, text = st.document(did), st.document_text(did)
            if not doc or text is None:
                raise HTTPException(status_code=404, detail=f"DOCUMENT_NOT_READABLE:{did}")
            msgs.append({"role": "system", "content": f"Documento adjunto «{doc['name']}»:\n{text}"})
            used_docs.append(did)
        if conv:
            msgs += [{"role": m["role"], "content": m["content"]} for m in st.messages(conv, limit=20)]
        msgs.append({"role": "user", "content": req.message})

        ckey = hashlib.sha256(json.dumps([req.provider, req.model, msgs, req.max_tokens, req.temperature], sort_keys=True).encode()).hexdigest()
        result = st.cache_get(ckey) if req.cache else None
        cached = result is not None
        if not cached:
            errbox: dict[str, str] = {}

            def executor(*, model_id: str, messages: list[dict[str, str]], max_tokens: int = 256) -> dict[str, Any]:
                try:
                    return prov.chat(req.provider, key, model_id, messages, max_tokens, temperature=req.temperature)
                except prov.ProviderError as exc:
                    errbox["e"] = str(exc)
                    raise

            def run() -> dict[str, Any]:
                return asyncio.run(route_chat_completion(model_id=req.model, messages=msgs, max_tokens=req.max_tokens, executor=executor))

            try:
                result = await asyncio.to_thread(run)
            except RuntimeError as exc:
                raise HTTPException(status_code=502, detail=errbox.get("e") or str(exc)) from exc
        reply = (result["message"].get("content") or "") if result else ""
        if reply and not cached and req.cache:
            st.cache_put(ckey, {"message": result["message"], "finish_reason": result.get("finish_reason"), "usage": result.get("usage")})
        if reply:
            if not conv:
                conv = st.new_conversation(req.message, agent["id"] if agent else None, owner)
            st.add_message(conv, "user", req.message)
            st.add_message(conv, "assistant", reply, req.provider, req.model)
            st.record_turn(conv_id=conv, owner=owner, provider=req.provider, model=req.model,
                           agent_id=agent["id"] if agent else None, doc_ids=used_docs,
                           repo=(req.github or {}).get("repo"))
        return {"conversation_id": conv, "reply": reply, "empty": not reply, "provider": req.provider, "model": req.model,
                "certified": certified, "cached": cached, "finish_reason": result.get("finish_reason"),
                "usage": result.get("usage"), "docs_used": used_docs, "agent_id": agent["id"] if agent else None}

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
        except Exception as exc:  # noqa: BLE001
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
                              "write_token": bool(os.getenv("HF_WRITE_TOKEN"))}}

    @r.post("/chat/storage/sync")
    def storage_sync(_owner: str = Depends(_auth)) -> dict[str, Any]:
        bucket = os.getenv("HF_BUCKET_ID")
        token = os.getenv("HF_WRITE_TOKEN") or os.getenv("HF_TOKEN") or ""
        if not bucket:
            raise HTTPException(status_code=400, detail="HF_BUCKET_ID_NOT_SET")
        try:
            return sync_to_bucket(get_store(), bucket, token)
        except Exception as exc:  # noqa: BLE001
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
