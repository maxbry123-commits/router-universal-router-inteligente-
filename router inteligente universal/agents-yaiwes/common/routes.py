"""Candidate endpoints for the SmolAgents runners, in the order of the route: EVERY usable key of nvidia / groq / cerebras (a dead key, e.g. 401, is
skipped instead of blocking the agent) and the Hugging Face models `deepseek_flash` / `minimax_m3` wherever they appear in the route or the fallback.
2026-09-25 Director: hasta 4 claves por proveedor (NVIDIA primero); si una no responde o está ocupada, se prueba la siguiente."""
from __future__ import annotations

from typing import Any

from common import boot  # noqa: F401  (puts the router packages on sys.path)
from integration.chat_mvp import core
from integration.chat_mvp import providers as prov
from kernel import dispatcher

MAX_KEYS = 4


def candidates(agent: dict[str, Any]) -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    hf_keys = prov.env_keys("hf")
    for p in [*agent.get("route", []), *agent.get("fallback", [])]:
        if p in dispatcher.FALLBACK:
            model = dispatcher.FALLBACK[p]
            try:
                core.hf_gate(model)
            except ValueError:
                continue
            if hf_keys:
                out.append(("hf", prov.PROVIDERS["hf"]["base"], model, hf_keys[0]))
            continue
        used = 0
        for key in prov.env_keys(p):
            if used >= MAX_KEYS:
                break
            try:
                ids = prov.list_models(p, key)
            except Exception as exc:  # noqa: BLE001
                if getattr(exc, "status", None) in (401, 403):
                    continue  # invalid key: skip it
                ids = []
            kimi = [m for m in ids if "kimi" in m.lower()] if p == "nvidia" else []
            kimi.sort(reverse=True)  # the newest Kimi (e.g. kimi-k3 > kimi-k2) goes first when NVIDIA offers it
            model = kimi[0] if kimi else next((m for m in dispatcher.PREFS[p] if m in ids), ids[0] if ids else dispatcher.PREFS[p][0])
            out.append((p, prov.PROVIDERS[p]["base"], model, key))
            used += 1
    return out
