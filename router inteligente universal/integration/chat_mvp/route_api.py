"""/chat/route (policy routing by group with fallback only where authorized) and /chat/router/status."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from . import core, resilience
from .router import _auth, get_store
from .usage import UsageLog


class RouteReq(BaseModel):
    group: str = Field(default="default", pattern=r"^[a-z0-9_-]{1,32}$")
    message: str = Field(min_length=1, max_length=20000)
    agent_id: str | None = None
    max_tokens: int = Field(default=1024, ge=1, le=8192)
    temperature: float | None = None


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

    return r
