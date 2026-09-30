"""OpenAI-compatible door to the Router's model chains: POST /v1/router/chat/completions and GET /v1/router/models.

Why: Hermes, OpenClaw and any OpenAI-style client only need `base_url = <Router>/v1/router` and `model = "auto"` (or a group name) to use the ONE
Router: the chain, key rotation, cooling and NVIDIA -> Groq fallback stay in resilience.run_policy, never in the client.
model: "auto" = group `default`; otherwise a group of resilience.DEFAULT_POLICY (default, assistants, code, minor, g2).
Not streamed (stream is ignored and a normal JSON answer is returned). Same X-API-Key auth as the other /chat routes.
2026-09-29 (Director: agentes Hermes/OpenClaw por el Router; regla 02:06 NVIDIA -> Groq)."""
from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from . import model_pool, resilience
from .route_api import _call
from .router import _auth, get_store
from .usage import UsageLog


class OAMessage(BaseModel):
    role: str = Field(pattern=r"^(system|user|assistant)$")
    content: Any = ""


class OAChatReq(BaseModel):
    model: str = Field(default="auto", pattern=r"^[A-Za-z0-9_.:-]{1,64}$")
    messages: list[OAMessage] = Field(min_length=1, max_length=200)
    max_tokens: int = Field(default=1024, ge=1, le=8192)
    temperature: float | None = None
    stream: bool | None = None  # accepted and ignored: the answer is never streamed


def _text(content: Any) -> str:
    """OpenAI allows content as a list of parts; keep only the text ones."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(str(p.get("text", "")) for p in content if isinstance(p, dict) and p.get("type", "text") == "text")
    return str(content or "")


def group_for(model: str) -> str | None:
    if model == "auto":
        return "default"
    return model if model in resilience.DEFAULT_POLICY else None


def build_openai_router() -> APIRouter:
    r = APIRouter()

    @r.get("/v1/router/models")
    def models(_owner: str = Depends(_auth)) -> dict[str, Any]:
        ids = ["auto", *resilience.DEFAULT_POLICY]
        return {"object": "list", "data": [{"id": i, "object": "model", "owned_by": "riu-router"} for i in ids]}

    @r.post("/v1/router/chat/completions")
    async def completions(req: OAChatReq, owner: str = Depends(_auth)) -> dict[str, Any]:
        group = group_for(req.model)
        if group is None:
            raise HTTPException(status_code=400, detail=f"MODEL_UNKNOWN:{req.model} (use auto or one of {sorted(resilience.DEFAULT_POLICY)})")
        msgs = [{"role": m.role, "content": _text(m.content)} for m in req.messages]
        try:
            out = await asyncio.to_thread(resilience.run_policy, group, msgs, req.max_tokens, temperature=req.temperature, call=_call,
                                          pool=model_pool.POOL)
        except resilience.RouteFailed as exc:
            busy = str(exc).startswith("ROUTER_SATURATED")
            trace = getattr(exc, "trace", None) or []
            raise HTTPException(status_code=503 if busy or not str(exc).startswith("NEEDS_DIRECTOR_AUTH") else 409,
                                detail=(f"{exc} | " + " ; ".join(trace))[:900]) from exc
        route = out["route"]
        UsageLog(get_store()).record(owner=owner, provider=route["provider"], model=route["model"], usage=out.get("usage"), from_cache=False)
        usage = out.get("usage") or {}
        return {"id": "chatcmpl-" + uuid.uuid4().hex[:24], "object": "chat.completion", "created": int(time.time()),
                "model": f"{route['provider']}/{route['model']}",
                "choices": [{"index": 0, "message": {"role": "assistant", "content": out["message"].get("content") or ""},
                             "finish_reason": out.get("finish_reason") or "stop"}],
                "usage": {"prompt_tokens": usage.get("prompt_tokens", 0), "completion_tokens": usage.get("completion_tokens", 0),
                          "total_tokens": usage.get("total_tokens", 0)},
                "riu": {"group": group, "trace": out["trace"]}}

    return r
