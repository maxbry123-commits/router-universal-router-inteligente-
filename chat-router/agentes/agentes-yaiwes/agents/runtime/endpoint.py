"""Picks the model endpoint for SmolAgents (which talks to an OpenAI-compatible URL itself).
Order set by the Director: NVIDIA / Groq / Cerebras first; only if the whole route has no usable key, DeepSeek V4 Flash / MiniMax M3
through the Hugging Face router. Keys come from the unlocked bank (never from files)."""
from __future__ import annotations

from typing import Any

from kernel import dispatcher
from integration.chat_mvp import providers as prov


def pick(cfg: dict[str, Any]) -> dict[str, Any]:
    trace: list[str] = []
    for provider in cfg.get("route", []):
        keys = prov.env_keys(provider)
        if not keys:
            trace.append(f"{provider}:SIN_CLAVE")
            continue
        for key in keys[:3]:
            try:
                ids = prov.list_models(provider, key)
            except Exception as exc:  # noqa: BLE001
                trace.append(f"{provider}:{type(exc).__name__}")
                continue
            model = next((m for m in dispatcher.PREFS[provider] if m in ids), ids[0] if ids else dispatcher.PREFS[provider][0])
            return {"provider": provider, "model": model, "base": prov.base_url(provider), "key": key, "via": "route", "trace": trace}
    for fb in cfg.get("fallback", []):
        keys = prov.env_keys("hf")
        if keys:
            return {"provider": "hf", "model": dispatcher.FALLBACK[fb], "base": prov.base_url("hf"), "key": keys[0], "via": "fallback", "trace": trace}
    raise RuntimeError("SIN_RUTA: " + " | ".join(trace))
