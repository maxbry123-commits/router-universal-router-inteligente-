"""Candidate endpoints for the SmolAgents runners, in the order of the route: EVERY usable key of nvidia / groq (a dead key, e.g. 401, is
skipped instead of blocking the agent) and the Hugging Face models `deepseek_flash` / `minimax_m3` wherever they appear in the route or the fallback.
2026-09-25 Director: hasta 4 claves por proveedor (NVIDIA primero); si una no responde o está ocupada, se prueba la siguiente.
2026-09-27 Director: el Router PREGUNTA primero qué modelos responden de verdad (sonda corta por clave) y prioriza
  Kimi K3 → GLM-5 → DeepSeek V4 Flash → cualquier otro de NVIDIA que responda. Cerebras eliminado (pide pago). Groq como respaldo
  (hasta 7 claves; modelos vivos hoy: gpt-oss-120b/20b, qwen3.8-27b). La sonda envía User-Agent (Groq devuelve 403 al de urllib).
  La sonda se cachea 15 min por (proveedor, clave) para no gastar llamadas."""
from __future__ import annotations

import json
import time
import urllib.request
from typing import Any

from common import boot  # noqa: F401  (puts the router packages on sys.path)
from integration.chat_mvp import core
from integration.chat_mvp import providers as prov
from kernel import dispatcher

MAX_KEYS = {"nvidia": 4, "groq": 7}
PRIORIDAD = ["kimi-k3", "glm-5", "deepseek-v4", "kimi-k2", "qwen3", "deepseek", "gpt-oss-120b", "gpt-oss", "llama-4", "nemotron", "llama-3.3"]
NO_CHAT = ("whisper", "orpheus", "guard", "tts", "embed")
EXCLUIDOS: set = set()
_CACHE: dict[tuple[str, str], tuple[float, list[str]]] = {}
_TTL = 900


def _ranked(ids: list[str]) -> list[str]:
    ids = [i for i in ids if not any(x in i.lower() for x in NO_CHAT)]
    out: list[str] = []
    for p in PRIORIDAD:
        out += sorted([i for i in ids if p in i.lower() and i not in out], reverse=True)
    return out


def _responde(base: str, model: str, key: str) -> bool:
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": "OK"}], "max_tokens": 2}).encode()
    req = urllib.request.Request(base.rstrip("/") + "/chat/completions", data=body,
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                                          "User-Agent": "riu-chat-mvp"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status == 200
    except Exception:  # noqa: BLE001
        return False


def disponibles(p: str, key: str, limite: int = 3) -> list[str]:
    """Modelos que responden de verdad para (proveedor, clave), en orden de prioridad. Cacheado 15 min."""
    ck = (p, key[-6:])
    hit = _CACHE.get(ck)
    if hit and time.time() - hit[0] < _TTL:
        return hit[1]
    try:
        ids = prov.list_models(p, key)
    except Exception as exc:  # noqa: BLE001
        if getattr(exc, "status", None) in (401, 403):
            _CACHE[ck] = (time.time(), [])
            return []
        ids = []
    base = prov.PROVIDERS[p]["base"]
    vivos = [m for m in _ranked(ids)[:8] if _responde(base, m, key)][:limite]
    _CACHE[ck] = (time.time(), vivos)
    return vivos


def candidates(agent: dict[str, Any]) -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    hf_keys = prov.env_keys("hf")
    for p in [*agent.get("route", []), *agent.get("fallback", [])]:
        if p in EXCLUIDOS:
            continue
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
            if used >= MAX_KEYS.get(p, 4):
                break
            vivos = disponibles(p, key)
            if not vivos:
                continue  # clave muerta o ningún modelo responde: siguiente clave
            for m in vivos:
                out.append((p, prov.PROVIDERS[p]["base"], m, key))
            used += 1
    return out
