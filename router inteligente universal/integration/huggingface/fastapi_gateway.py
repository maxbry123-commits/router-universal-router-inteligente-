"""Single FastAPI gateway for Hugging Face models: certified path + chat MVP.

Routes stay thin: authentication is enforced at the HTTP boundary and valid
requests continue through the persisted Enchufe Gate + RedUniversal.

RIU_CHAT_ALLOW_PROVIDER_LIVE=1 lets the chat ATTEMPT provider-live selector
models (Kimi K3, MiniMax, DeepSeek V4 Flash/Pro). They are returned with
`certified: false` until their gates close in model_registry.json.
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from .api_key_auth import authenticate_api_key
from .chat_catalog import cached_discovery, selectable_live_ids, selector_models
from .chat_executor import make_executor
from .huggingface_openai_chat import allowed_model_ids
from .router_hot_path import route_chat_completion

LIVE_ENV = "RIU_CHAT_ALLOW_PROVIDER_LIVE"
_CHAT_UI = Path(__file__).with_name("chat_ui.html")

app = FastAPI(title="Router Inteligente Universal HF Gateway", version="0.4.1")


def live_enabled() -> bool:
    return os.getenv(LIVE_ENV, "") == "1"


def _require_selectable(model_id: str) -> None:
    """Fail closed at the HTTP boundary so a rejected model is a 400, not a routing 503."""
    if model_id in allowed_model_ids():
        return
    if not live_enabled():
        raise ValueError("MODEL_NOT_IN_CERTIFIED_REGISTRY")
    if model_id not in selectable_live_ids(discovered=cached_discovery()):
        raise ValueError("MODEL_NOT_SELECTABLE")


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    max_tokens: int = Field(default=256, ge=1, le=4096)


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "registry_count": len(allowed_model_ids()),
        "route": "FastAPI->EnchufeGate->RedUniversal->HFAdapter",
        "auth": "RIU_AGENT_API_KEYS",
        "chat": "/chat",
        "live_provider_inference": live_enabled(),
    }


@app.get("/v1/models")
def models() -> dict[str, object]:
    return {
        "object": "list",
        "data": [{"id": model_id, "object": "model"} for model_id in sorted(allowed_model_ids())],
    }


@app.get("/chat", response_class=HTMLResponse)
def chat_page() -> HTMLResponse:
    return HTMLResponse(_CHAT_UI.read_text(encoding="utf-8"))


@app.get("/chat/models")
def chat_models() -> dict[str, object]:
    return selector_models(discovered=cached_discovery(), live_enabled=live_enabled())


@app.post("/v1/chat/completions")
async def chat(
    req: ChatRequest,
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> dict[str, object]:
    candidate = x_api_key
    if not candidate and authorization and authorization.lower().startswith("bearer "):
        candidate = authorization[7:].strip()
    try:
        agent_id = authenticate_api_key(candidate)
        _require_selectable(req.model)
        result = await route_chat_completion(
            model_id=req.model,
            messages=[m.model_dump() for m in req.messages],
            max_tokens=req.max_tokens,
            executor=make_executor(allow_provider_live=live_enabled()),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        detail = str(exc)
        status = 401 if detail.startswith("RIU_API_KEY_") else 503
        raise HTTPException(status_code=status, detail=detail) from exc
    return {
        "object": "chat.completion",
        "model": result["model"],
        "agent_id": agent_id,
        "certified": bool(result.get("certified", True)),
        "choices": [
            {
                "index": 0,
                "message": result["message"],
                "finish_reason": result["finish_reason"],
            }
        ],
    }
