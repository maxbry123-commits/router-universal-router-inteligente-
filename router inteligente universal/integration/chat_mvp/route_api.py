"""/chat/route (policy routing by group with fallback only where authorized), /chat/router/status and /chat/jev
(Choice/Score/Noul decisions, see jev.py)."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from . import core, jev, resilience
from .router import _auth, get_store
from .usage import UsageLog


class RouteReq(BaseModel):
    group: str = Field(default="default", pattern=r"^[a-z0-9_-]{1,32}$")
    message: str = Field(min_length=1, max_length=20000)
    agent_id: str | None = None
    max_tokens: int = Field(default=1024, ge=1, le=8192)
    temperature: float | None = None


class JevReq(BaseModel):
    kind: Literal["choice", "score", "noul"]
    state: Any
    instructions: str = Field(min_length=1, max_length=4000)
    criteria: dict[str, str] | None = None
    levels: list[str] | None = None
    provider: str = Field(default="nvidia", pattern=r"^[a-z_]{1,20}$")
    model: str | None = None
    max_tokens: int = Field(default=300, ge=32, le=2000)


def _call(provider: str, key: str | None, model: str, messages: list[dict[str, str]], max_tokens: int, temperature: float | None) -> dict[str, Any]:
    if provider == "hf":
        try:
            core.hf_gate(model)
        except ValueError as exc:
            raise RuntimeError(str(exc)) from exc
    return core.call_via_router(provider, key, model, messages, max_tokens, temperature)


def build_route_router() -> APIRouter:
    r = APIRouter()

    @r.post("/chat/route")
    async def route(req: RouteReq, owner: str = Depends(_auth)) -> dict[str, Any]:
        st = get_store()
        msgs: list[dict[str, str]] = []
        if req.agent_id:
            agent = st.agent(req.agent_id)
            if not agent:
                raise HTTPException(status_code=400, detail="AGENT_NOT_FOUND")
            if agent["system_prompt"]:
                msgs.append({"role": "system", "content": agent["system_prompt"]})
        msgs.append({"role": "user", "content": req.message})
        try:
            out = await asyncio.to_thread(resilience.run_policy, req.group, msgs, req.max_tokens, temperature=req.temperature, call=_call)
        except resilience.RouteFailed as exc:
            status = 409 if str(exc).startswith("NEEDS_DIRECTOR_AUTH") else 503
            raise HTTPException(status_code=status, detail={"error": str(exc), "trace": exc.trace}) from exc
        route_info = out["route"]
        UsageLog(st).record(owner=owner, provider=route_info["provider"], model=route_info["model"], usage=out.get("usage"), from_cache=False)
        return {"group": req.group, "reply": out["message"].get("content") or "", "route": route_info, "trace": out["trace"],
                "finish_reason": out.get("finish_reason"), "usage": out.get("usage")}

    @r.get("/chat/router/status")
    def status(_owner: str = Depends(_auth)) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        groups = {}
        for name in resilience.DEFAULT_POLICY:
            chain, skipped = resilience.resolve_chain(name, now)
            groups[name] = {"authorized_fallback": resilience.DEFAULT_POLICY[name]["authorized_fallback"], "chain": chain, "skipped": skipped}
        lim = resilience.ROUTER.limiter
        return {"deepseek_peak_now": resilience.is_peak_utc(now), "limiter": {"tier": lim.tier, "slots": lim.tiers[lim.tier], "tiers": list(lim.tiers)},
                "latency_seconds": {k: round(v, 2) for k, v in resilience.ROUTER.latency.items()}, "groups": groups}

    @r.post("/chat/jev")
    async def jev_decide(req: JevReq, _owner: str = Depends(_auth)) -> dict[str, Any]:
        model = req.model or "nvidia/nemotron-3-super-120b-a12b"
        try:
            if req.kind == "choice":
                if not req.criteria:
                    raise HTTPException(status_code=400, detail="criteria es obligatorio para choice")
                out = await asyncio.to_thread(jev.choice, req.state, req.instructions, req.criteria, provider=req.provider, model=model, max_tokens=req.max_tokens)
            elif req.kind == "score":
                if not req.levels:
                    raise HTTPException(status_code=400, detail="levels es obligatorio para score")
                out = await asyncio.to_thread(jev.score, req.state, req.instructions, req.levels, provider=req.provider, model=model, max_tokens=req.max_tokens)
            else:
                out = await asyncio.to_thread(jev.noul, req.state, req.instructions, provider=req.provider, model=model, max_tokens=req.max_tokens)
        except jev.JevError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return {"kind": req.kind, "provider": req.provider, "model": model, "answer": out}

    return r
