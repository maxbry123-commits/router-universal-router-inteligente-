"""Model dispatcher for the micro-agents.
Order set by the Director: the route (NVIDIA / Groq / Cerebras) first; only if the whole route fails, DeepSeek V4 Flash or
MiniMax M3 through the Hugging Face router. Every call goes through the Router core (Enchufe Gate -> RedUniversal ->
adaptive limiter + per-key circuit breaker + key pool). Keys come from the unlocked bank (never from files).
"""
from __future__ import annotations

from typing import Any

from integration.chat_mvp import core
from integration.chat_mvp import providers as prov

PREFS = {
    "nvidia": ["nvidia/nemotron-3-super-120b-a12b"],
    "groq": ["openai/gpt-oss-120b", "llama-3.3-70b-versatile", "qwen/qwen3-32b", "openai/gpt-oss-20b"],
    "cerebras": ["gpt-oss-120b", "qwen-3.8-27b"],
}
FALLBACK = {"deepseek_flash": "deepseek-ai/DeepSeek-V4-Flash", "minimax_m3": "MiniMaxAI/MiniMax-M3"}


def pick_model(provider: str, key: str) -> str:
    try:
        ids = prov.list_models(provider, key)
    except Exception:  # noqa: BLE001 - catalog failure: use the first preference
        return PREFS[provider][0]
    for pref in PREFS[provider]:
        if pref in ids:
            return pref
    return ids[0] if ids else PREFS[provider][0]


def _text(res: dict[str, Any]) -> str:
    return (res.get("message") or {}).get("content") or ""


def call(cfg: dict[str, Any], messages: list[dict[str, str]], max_tokens: int = 1500) -> dict[str, Any]:
    trace: list[str] = []
    for provider in cfg.get("route", []):
        keys = prov.env_keys(provider)
        if not keys:
            trace.append(f"{provider}:SIN_CLAVE")
            continue
        model = pick_model(provider, keys[0])
        try:
            text = _text(core.call_via_router(provider, keys[0], model, messages, max_tokens))
        except RuntimeError as exc:
            trace.append(f"{provider}/{model}:{str(exc)[:100]}")
            continue
        if not text.strip():
            trace.append(f"{provider}/{model}:VACIO")
            continue
        return {"text": text, "provider": provider, "model": model, "via": "route", "trace": trace}
    for fb in cfg.get("fallback", []):
        model, keys = FALLBACK[fb], prov.env_keys("hf")
        if not keys:
            trace.append("hf:SIN_CLAVE")
            continue
        try:
            core.hf_gate(model)
            text = _text(core.call_via_router("hf", keys[0], model, messages, max_tokens))
        except (RuntimeError, ValueError) as exc:
            trace.append(f"hf/{model}:{str(exc)[:100]}")
            continue
        if not text.strip():
            trace.append(f"hf/{model}:VACIO")
            continue
        return {"text": text, "provider": "hf", "model": model, "via": "fallback", "trace": trace}
    raise RuntimeError("SIN_RUTA: " + " | ".join(trace))
