"""Shared chat core: HF gate, response cache, history budget, Router hot-path call and usage accounting.

Cost levers implemented here:
  1. Exact-match response cache (default ON, TTL RIU_CACHE_TTL, skipped when temperature > 0 or refresh=True).
  2. Prefix-stable prompts (system + sorted documents first, history append-only, new turn last) so providers with
     native prompt caching (DeepSeek, Moonshot, OpenAI-style) bill the repeated prefix as cached input.
  3. History budget: old turns are dropped in one large step (to 60 %) instead of one by one, so the cached prefix stays stable.
  4. Usage log with cached-token accounting (see usage.py) to measure real savings.
Availability: when the key comes from the server environment, the provider's other environment keys form a POOL;
a slow or failing key (timeout, 401/402/403/429/5xx) falls over to the next one. Request errors (400/404/410/422) do not.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
from typing import Any

from ..huggingface.chat_catalog import cached_discovery, selectable_live_ids
from . import providers as prov
from .store import Store
from .usage import UsageLog

CACHE_TTL_ENV = "RIU_CACHE_TTL"
DEFAULT_CACHE_TTL = 86400.0
HISTORY_BUDGET_CHARS = 24000
NO_FAILOVER_STATUS = {400, 404, 410, 422}


def live_enabled() -> bool:
    return os.getenv("RIU_CHAT_ALLOW_PROVIDER_LIVE", "") == "1"


def hf_gate(model: str) -> bool:
    """True when the model is certified; False when allowed as live attempt; raises ValueError otherwise."""
    from ..huggingface.huggingface_openai_chat import allowed_model_ids

    if model in allowed_model_ids():
        return True
    if live_enabled() and model in selectable_live_ids(discovered=cached_discovery()):
        return False
    raise ValueError("MODEL_NOT_SELECTABLE")


def cache_key(provider: str, model: str, messages: list[dict[str, str]], max_tokens: int, temperature: float | None) -> str:
    return hashlib.sha256(json.dumps([provider, model, messages, max_tokens, temperature], sort_keys=True).encode()).hexdigest()


def trim_history(history: list[dict[str, str]], budget: int = HISTORY_BUDGET_CHARS) -> list[dict[str, str]]:
    if sum(len(m["content"]) for m in history) <= budget:
        return history
    out = list(history)
    target = int(budget * 0.6)
    while out and sum(len(m["content"]) for m in out) > target:
        out.pop(0)
    while out and out[0]["role"] != "user":
        out.pop(0)
    return out


def key_pool(provider: str, key: str | None) -> list[str | None]:
    """Keys to try, in order. Only an environment key expands to the provider's pool; a BYOK key is used alone."""
    env = prov.env_keys(provider)
    if key and key in env:
        return [key] + [k for k in env if k != key]
    return [key]


def call_via_router(provider: str, key: str | None, model: str, messages: list[dict[str, str]], max_tokens: int,
                    temperature: float | None = None) -> dict[str, Any]:
    """FastAPI-side call: Enchufe Gate -> RedUniversal -> provider executor (blocking; run it in a thread)."""
    from ..huggingface.router_hot_path import route_chat_completion

    errbox: dict[str, str] = {}
    pool = key_pool(provider, key)

    def executor(*, model_id: str, messages: list[dict[str, str]], max_tokens: int = 256) -> dict[str, Any]:
        last: prov.ProviderError | None = None
        for k in pool:
            try:
                return prov.chat(provider, k, model_id, messages, max_tokens, temperature=temperature)
            except prov.ProviderError as exc:
                last = exc
                errbox["e"] = str(exc)
                if exc.status in NO_FAILOVER_STATUS:
                    raise
        assert last is not None
        raise last

    try:
        return asyncio.run(route_chat_completion(model_id=model, messages=messages, max_tokens=max_tokens, executor=executor))
    except RuntimeError as exc:
        raise RuntimeError(errbox.get("e") or str(exc)) from exc


def run_completion(store: Store, owner: str, provider: str, key: str | None, model: str, messages: list[dict[str, str]],
                   max_tokens: int, temperature: float | None = None, *, use_cache: bool = True, refresh: bool = False) -> dict[str, Any]:
    log = UsageLog(store)
    cacheable = use_cache and temperature in (None, 0)
    ck = cache_key(provider, model, messages, max_tokens, temperature)
    if cacheable and not refresh:
        hit = store.cache_get(ck)
        if hit:
            log.record(owner=owner, provider=provider, model=model, usage=hit.get("usage"), from_cache=True)
            return {**hit, "cached": True}
    result = call_via_router(provider, key, model, messages, max_tokens, temperature)
    out = {"message": result["message"], "finish_reason": result.get("finish_reason"), "usage": result.get("usage")}
    if cacheable and (out["message"].get("content") or ""):
        store.cache_put(ck, out, ttl=float(os.getenv(CACHE_TTL_ENV) or DEFAULT_CACHE_TTL))
    log.record(owner=owner, provider=provider, model=model, usage=out["usage"], from_cache=False)
    return {**out, "cached": False}
