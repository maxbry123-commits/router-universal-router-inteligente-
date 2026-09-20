"""Token usage log and cost/saving accounting for the chat MVP (stdlib only).

Provider-side prompt caching (DeepSeek, Moonshot, OpenAI-style) shows up as cached input tokens in `usage`;
response-cache hits cost nothing and are logged as `from_cache` with the tokens they avoided.
Optional prices (USD per 1M tokens): RIU_PRICES_JSON='{"deepseek/deepseek-v4-flash": {"in": 0.14, "cached_in": 0.014, "out": 0.28}}'
"""
from __future__ import annotations

import json
import os
import time
from typing import Any

from .store import Store


def normalize_usage(usage: dict[str, Any] | None) -> dict[str, int]:
    u = usage or {}
    cached = u.get("prompt_cache_hit_tokens")  # DeepSeek
    if cached is None:
        cached = (u.get("prompt_tokens_details") or {}).get("cached_tokens")  # OpenAI-style
    if cached is None:
        cached = u.get("cached_tokens")  # Moonshot
    return {"input": int(u.get("prompt_tokens") or 0), "output": int(u.get("completion_tokens") or 0), "cached": int(cached or 0)}


def _prices() -> dict[str, dict[str, float]]:
    try:
        parsed = json.loads(os.getenv("RIU_PRICES_JSON", "") or "{}")
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


class UsageLog:
    def __init__(self, store: Store) -> None:
        self.s = store
        store._exec("CREATE TABLE IF NOT EXISTS usage(id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, owner TEXT, provider TEXT, model TEXT, "
                    "input INTEGER, output INTEGER, cached INTEGER, from_cache INTEGER)")

    def record(self, *, owner: str, provider: str, model: str, usage: dict[str, Any] | None, from_cache: bool) -> None:
        n = normalize_usage(usage)
        self.s._exec("INSERT INTO usage(ts,owner,provider,model,input,output,cached,from_cache) VALUES(?,?,?,?,?,?,?,?)",
                     (time.time(), owner, provider, model, n["input"], n["output"], n["cached"], int(from_cache)))

    def summary(self) -> dict[str, Any]:
        prices = _prices()
        rows = self.s._all("SELECT provider, model, from_cache, COUNT(*) calls, SUM(input) input, SUM(output) output, SUM(cached) cached "
                           "FROM usage GROUP BY provider, model, from_cache")
        per: dict[str, dict[str, Any]] = {}
        for r in rows:
            key = f"{r['provider']}/{r['model']}"
            d = per.setdefault(key, {"model": key, "calls": 0, "input": 0, "output": 0, "cached_input": 0, "response_cache_hits": 0,
                                     "tokens_avoided_by_response_cache": 0, "est_cost_usd": None, "est_saved_usd": None})
            price = prices.get(key)

            def cost(inp: int, cached: int, out: int) -> float | None:
                if not price:
                    return None
                return ((inp - cached) * price.get("in", 0) + cached * price.get("cached_in", price.get("in", 0)) + out * price.get("out", 0)) / 1e6

            if r["from_cache"]:
                d["response_cache_hits"] += r["calls"]
                d["tokens_avoided_by_response_cache"] += (r["input"] or 0) + (r["output"] or 0)
                saved = cost(r["input"] or 0, r["cached"] or 0, r["output"] or 0)
                if saved is not None:
                    d["est_saved_usd"] = (d["est_saved_usd"] or 0.0) + saved
            else:
                d["calls"] += r["calls"]
                d["input"] += r["input"] or 0
                d["output"] += r["output"] or 0
                d["cached_input"] += r["cached"] or 0
                spent = cost(r["input"] or 0, r["cached"] or 0, r["output"] or 0)
                if spent is not None:
                    d["est_cost_usd"] = (d["est_cost_usd"] or 0.0) + spent
        models = sorted(per.values(), key=lambda x: x["model"])
        tot_in = sum(m["input"] for m in models)
        totals = {"calls": sum(m["calls"] for m in models), "input": tot_in, "output": sum(m["output"] for m in models),
                  "cached_input": sum(m["cached_input"] for m in models),
                  "provider_cache_hit_ratio": round(sum(m["cached_input"] for m in models) / tot_in, 4) if tot_in else 0.0,
                  "response_cache_hits": sum(m["response_cache_hits"] for m in models),
                  "tokens_avoided_by_response_cache": sum(m["tokens_avoided_by_response_cache"] for m in models)}
        return {"totals": totals, "models": models, "prices_configured": bool(prices)}
