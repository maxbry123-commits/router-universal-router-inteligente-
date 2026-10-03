"""OpenAI-compatible door to the Router's model chains: POST /v1/router/chat/completions and GET /v1/router/models.

Why: Hermes, OpenClaw, the DeepSeek Harness (llm-pi-ai, api: openai-completions) and any OpenAI-style client only need
`base_url = <Router>/v1/router` and `model = "auto"` (or a group name) to use the ONE Router: the chain, key rotation, cooling
and NVIDIA -> Groq fallback stay in resilience.run_policy, never in the client.
model: "auto" = group `default`; a group of resilience.DEFAULT_POLICY (default, assistants, code, minor, g2, ...);
or a direct route "provider:model" (e.g. "nvidia:moonshotai/kimi-k3") used by the fichas/selector.
Tool calling: `tools` / `tool_choice` and the `tool` / assistant `tool_calls` messages pass through to the provider (agents).
Streaming: `stream: true` answers Server-Sent Events (OpenAI chunk format, one content chunk + tool_call chunks + [DONE]);
the provider call itself is not streamed. Auth: X-API-Key or Authorization: Bearer <router key> (same as the other /chat routes).
Elastic pool: when this Router is >= 85% busy and a worker Job runs, the request is served by the worker (same code).
2026-09-29 (Director: agentes Hermes/OpenClaw por el Router; regla 02:06 NVIDIA -> Groq).
2026-10-03 (Director: el Harness usa el Router como proveedor, sin DeepSeek API): tools, roles tool/developer, SSE, rutas directas."""
from __future__ import annotations

import asyncio
import json
import time
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from . import model_pool, resilience
from . import providers as prov
from .route_api import _call
from .router import _auth, get_store
from .usage import UsageLog

ROLES = {"system", "user", "assistant", "tool", "developer"}
PASS_FIELDS = ("tools", "tool_choice", "parallel_tool_calls", "response_format", "stop", "top_p", "seed", "reasoning_effort")


class OAChatReq(BaseModel):
    model_config = ConfigDict(extra="allow")
    model: str = Field(default="auto", pattern=r"^[A-Za-z0-9_.:/@-]{1,128}$")
    messages: list[dict[str, Any]] = Field(min_length=1, max_length=400)
    max_tokens: int | None = Field(default=None, ge=1, le=65536)
    max_completion_tokens: int | None = Field(default=None, ge=1, le=65536)
    temperature: float | None = None
    stream: bool | None = None


def _text(content: Any) -> str:
    """OpenAI allows content as a list of parts; keep only the text ones."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(str(p.get("text", "")) for p in content if isinstance(p, dict) and p.get("type", "text") == "text")
    return str(content or "")


def clean_messages(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep the OpenAI fields providers understand; developer -> system (routers that reject the developer role)."""
    out: list[dict[str, Any]] = []
    for m in raw:
        role = str(m.get("role") or "")
        if role not in ROLES:
            raise HTTPException(status_code=422, detail=f"ROLE_UNKNOWN:{role[:20]}")
        msg: dict[str, Any] = {"role": "system" if role == "developer" else role, "content": _text(m.get("content"))}
        if role == "assistant" and m.get("tool_calls"):
            msg["tool_calls"] = m["tool_calls"]
            if not msg["content"]:
                msg["content"] = None
        if role == "tool":
            msg["tool_call_id"] = str(m.get("tool_call_id") or "")
            if m.get("name"):
                msg["name"] = m["name"]
        out.append(msg)
    return out


def group_for(model: str) -> str | None:
    if model == "auto":
        return "default"
    return model if model in resilience.DEFAULT_POLICY else None


def direct_route(model: str) -> tuple[str, str] | None:
    """"provider:model" -> (provider, model) when the provider exists in the registry (built-in or Secret Bank)."""
    if ":" not in model:
        return None
    provider, _, mid = model.partition(":")
    return (provider, mid) if provider in prov.registry() and mid else None


def run_chat(model: str, messages: list[dict[str, Any]], max_tokens: int, temperature: float | None,
             extra: dict[str, Any] | None) -> dict[str, Any]:
    """Blocking: one request through a group chain or a direct provider:model route. Used by the HTTP door, fichas and MCP."""
    token = prov.EXTRA_PAYLOAD.set(extra or None)
    try:
        direct = direct_route(model)
        if direct:
            provider, mid = direct
            keys = prov.env_keys(provider) or [None]
            out = _call(provider, keys[0], mid, messages, max_tokens, temperature)
            return {**out, "route": {"provider": provider, "model": mid, "attempt": 1}, "trace": [], "group": None}
        group = group_for(model)
        if group is None:
            raise HTTPException(status_code=400, detail=f"MODEL_UNKNOWN:{model} (use auto, provider:model or one of {sorted(resilience.DEFAULT_POLICY)})")
        out = resilience.run_policy(group, messages, max_tokens, temperature=temperature, call=_call, pool=model_pool.POOL)
        return {**out, "group": group}
    finally:
        prov.EXTRA_PAYLOAD.reset(token)


def wants_sse(req: OAChatReq, accept: str) -> bool:
    """SSE only for real streaming clients (OpenAI SDKs send stream_options or Accept: text/event-stream; RIU_OPENAI_SSE=1 forces it).
    A bare `stream: true` keeps the old JSON answer (Hermes/OpenClaw and the existing contract tests)."""
    if not req.stream:
        return False
    import os

    return bool((req.model_extra or {}).get("stream_options")) or "text/event-stream" in accept.lower() or os.getenv("RIU_OPENAI_SSE") == "1"


def _sse(body: dict[str, Any]) -> StreamingResponse:
    """Emulated OpenAI stream: role, content, tool_calls, finish (+usage), [DONE]."""
    msg = body["choices"][0]["message"]
    base = {"id": body["id"], "object": "chat.completion.chunk", "created": body["created"], "model": body["model"]}

    def chunks():
        yield {**base, "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}]}
        if msg.get("content"):
            yield {**base, "choices": [{"index": 0, "delta": {"content": msg["content"]}, "finish_reason": None}]}
        for i, tc in enumerate(msg.get("tool_calls") or []):
            fn = tc.get("function") or {}
            yield {**base, "choices": [{"index": 0, "delta": {"tool_calls": [{"index": i, "id": tc.get("id"), "type": "function",
                   "function": {"name": fn.get("name"), "arguments": fn.get("arguments") or ""}}]}, "finish_reason": None}]}
        yield {**base, "choices": [{"index": 0, "delta": {}, "finish_reason": body["choices"][0]["finish_reason"]}], "usage": body["usage"]}

    async def gen():
        for c in chunks():
            yield f"data: {json.dumps(c, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})


async def _offload(req: OAChatReq) -> dict[str, Any] | None:
    """Elastic pool: when this Router is >= 85% busy and a worker Job is running, the request is served there (same code)."""
    try:
        from ..hf_worker_pool import POOL
    except Exception:  # noqa: BLE001
        return None
    worker = POOL.offload_target()
    if worker is None:
        return None
    import httpx

    payload = req.model_dump(exclude_none=True) | dict(req.model_extra or {})
    payload["stream"] = False
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(worker.url.rstrip("/") + "/v1/router/chat/completions", json=payload, headers=POOL._headers())  # noqa: SLF001
        if resp.status_code < 400:
            body = resp.json()
            body.setdefault("riu", {})["worker"] = worker.job_id
            return body
    except Exception:  # noqa: BLE001 - a dead worker never fails the request: serve it here
        return None
    return None


def _ficha_amarrada(owner: str) -> str | None:
    if not owner.startswith("tok:"):
        return None
    from .tokens import registro_de_dueno

    rec = registro_de_dueno(owner)
    return (rec or {}).get("ficha") or None


def build_openai_router() -> APIRouter:
    r = APIRouter()

    @r.get("/v1/router/models")
    def models(_owner: str = Depends(_auth)) -> dict[str, Any]:
        ids = ["auto", *resilience.DEFAULT_POLICY]
        return {"object": "list", "data": [{"id": i, "object": "model", "owned_by": "riu-router"} for i in ids]}

    @r.post("/v1/router/chat/completions")
    async def completions(req: OAChatReq, request: Request, owner: str = Depends(_auth)) -> Any:
        sse = wants_sse(req, request.headers.get("accept", ""))
        msgs = clean_messages(req.messages)
        extra = {k: v for k, v in (req.model_extra or {}).items() if k in PASS_FIELDS and v is not None}
        max_tokens = min(req.max_tokens or req.max_completion_tokens or 1024, 32768)
        amarrada = _ficha_amarrada(owner)
        if amarrada:
            from .secciones import ejecutar

            texto = next((m["content"] for m in reversed(msgs) if m["role"] == "user" and m.get("content")), "")
            res = await asyncio.to_thread(ejecutar, amarrada, texto, owner)
            body = {"id": "chatcmpl-" + uuid.uuid4().hex[:24], "object": "chat.completion", "created": int(time.time()),
                    "model": f"seccion/{res['seccion']}",
                    "choices": [{"index": 0, "message": {"role": "assistant", "content": res.get("final") or ""}, "finish_reason": "stop"}],
                    "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                    "riu": {"seccion": res["seccion"], "pasos": [{k: s.get(k) for k in ("paso", "model", "ok", "ms")} for s in res["steps"]]}}
            return _sse(body) if sse else body
        offloaded = await _offload(req)
        if offloaded is not None:
            return _sse(offloaded) if sse else offloaded
        try:
            out = await asyncio.to_thread(run_chat, req.model, msgs, max_tokens, req.temperature, extra)
        except resilience.RouteFailed as exc:
            busy = str(exc).startswith("ROUTER_SATURATED")
            trace = getattr(exc, "trace", None) or []
            raise HTTPException(status_code=503 if busy or not str(exc).startswith("NEEDS_DIRECTOR_AUTH") else 409,
                                detail=(f"{exc} | " + " ; ".join(trace))[:900]) from exc
        except HTTPException:
            raise
        except Exception as exc:  # direct route failure
            raise HTTPException(status_code=502, detail=f"ROUTE_FAILED:{str(exc)[:300]}") from exc
        route = out["route"]
        UsageLog(get_store()).record(owner=owner, provider=route["provider"], model=route["model"], usage=out.get("usage"), from_cache=False)
        usage = out.get("usage") or {}
        message = {"role": "assistant", "content": out["message"].get("content") or ""}
        finish = out.get("finish_reason") or "stop"
        if out["message"].get("tool_calls"):
            message["tool_calls"] = out["message"]["tool_calls"]
            finish = "tool_calls"
        body = {"id": "chatcmpl-" + uuid.uuid4().hex[:24], "object": "chat.completion", "created": int(time.time()),
                "model": f"{route['provider']}/{route['model']}",
                "choices": [{"index": 0, "message": message, "finish_reason": finish}],
                "usage": {"prompt_tokens": usage.get("prompt_tokens", 0), "completion_tokens": usage.get("completion_tokens", 0),
                          "total_tokens": usage.get("total_tokens", 0)},
                "riu": {"group": out.get("group"), "trace": out.get("trace", [])}}
        return _sse(body) if sse else body

    return r
