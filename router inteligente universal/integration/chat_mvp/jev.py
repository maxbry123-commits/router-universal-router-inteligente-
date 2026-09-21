"""Jev-style decision layer for the Router: Choice / Score / Noul primitives (a state plus typed questions -> a typed
answer with a probability), following TypeSafe AI's Jev interface (https://docs.typesafe.ai/api). Every call goes
through the Router's own resilient dispatch (core.call_via_router: NVIDIA -> Groq -> Cerebras -> HF, already covered by
39 passing tests), so this works TODAY without Vercel access. The Director's plan is to swap the target to the real
`typesafe-ai/jev` (Vercel AI Gateway) or a local decision model (NanoJev / Laya / Decider) once unblocked; every call
site here stays the same when that swap happens — only `model`/`base_url` changes.
"""
from __future__ import annotations

import json
import re
from typing import Any

from . import core

SYSTEM = ("Eres un evaluador de decisiones tipadas (estilo Jev/System One). Recibes un ESTADO y una PREGUNTA con su tipo. "
          "Respondes SOLO un objeto JSON, sin texto antes ni después, sin bloque de código.")


class JevError(RuntimeError):
    pass


def _ask(provider: str, key: str | None, model: str, prompt: str, max_tokens: int) -> dict[str, Any]:
    res = core.call_via_router(provider, key, model, [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}], max_tokens)
    text = (res.get("message") or {}).get("content") or ""
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise JevError("JEV_INVALID_RESPONSE: sin JSON en la respuesta")
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError as exc:
        raise JevError(f"JEV_INVALID_RESPONSE: {exc}") from exc


def choice(state: Any, instructions: str, criteria: dict[str, str], *, provider: str = "nvidia", key: str | None = None,
          model: str = "nvidia/nemotron-3-super-120b-a12b", max_tokens: int = 300) -> dict[str, Any]:
    """Pick one option from `criteria` (name -> description). Returns {"choice", "probabilities", "confidence"}."""
    if not criteria:
        raise ValueError("criteria no puede estar vacío")
    opts = "\n".join(f"- {k}: {v}" for k, v in criteria.items())
    prompt = (f"ESTADO:\n{json.dumps(state, ensure_ascii=False)}\n\nPREGUNTA (choice): {instructions}\nOPCIONES:\n{opts}\n\n"
              'Responde: {"choice": "<una de las claves de OPCIONES, exacta>", "probabilities": {"<clave>": <0..1>, ...}, "confidence": <0..1>}. '
              "Las probabilidades deben sumar 1 (aprox) entre TODAS las opciones listadas.")
    out = _ask(provider, key, model, prompt, max_tokens)
    if out.get("choice") not in criteria:
        raise JevError(f"JEV_INVALID_CHOICE: {out.get('choice')!r} no está en {list(criteria)}")
    probs = out.get("probabilities") or {}
    if set(probs) - set(criteria):
        raise JevError("JEV_INVALID_CHOICE: probabilities tiene claves fuera de criteria")
    return {"choice": out["choice"], "probabilities": {k: float(probs.get(k, 0.0)) for k in criteria}, "confidence": float(out.get("confidence", 0.0))}


def score(state: Any, instructions: str, levels: list[str], *, provider: str = "nvidia", key: str | None = None,
         model: str = "nvidia/nemotron-3-super-120b-a12b", max_tokens: int = 300) -> dict[str, Any]:
    """Rate `state` on the ordered rubric `levels` (index 0 = lowest). Returns {"score", "probabilities", "confidence"}."""
    if len(levels) < 2:
        raise ValueError("levels necesita al menos 2 niveles")
    lv = "\n".join(f"{i}: {lvl}" for i, lvl in enumerate(levels))
    prompt = (f"ESTADO:\n{json.dumps(state, ensure_ascii=False)}\n\nPREGUNTA (score): {instructions}\nNIVELES (0 a {len(levels) - 1}):\n{lv}\n\n"
              'Responde: {"score": <media ponderada por probabilidad, número real entre 0 y N-1>, "probabilities": {"0": <0..1>, ...}, "confidence": <0..1>}.')
    out = _ask(provider, key, model, prompt, max_tokens)
    sc = float(out.get("score", -1))
    if not (0 <= sc <= len(levels) - 1):
        raise JevError(f"JEV_INVALID_SCORE: {sc} fuera de [0, {len(levels) - 1}]")
    probs = {str(i): float((out.get("probabilities") or {}).get(str(i), 0.0)) for i in range(len(levels))}
    return {"score": sc, "probabilities": probs, "confidence": float(out.get("confidence", 0.0)), "legend": levels}


def noul(state: Any, instructions: str, *, provider: str = "nvidia", key: str | None = None,
        model: str = "nvidia/nemotron-3-super-120b-a12b", max_tokens: int = 200) -> dict[str, Any]:
    """Probability that `instructions` is true of `state`. Returns {"noul": 0..1}."""
    prompt = (f"ESTADO:\n{json.dumps(state, ensure_ascii=False)}\n\nPREGUNTA (noul, sí/no): {instructions}\n\n"
              'Responde: {"noul": <probabilidad de 0.0 a 1.0 de que la afirmación sea verdadera>}.')
    out = _ask(provider, key, model, prompt, max_tokens)
    p = float(out.get("noul", -1))
    if not (0.0 <= p <= 1.0):
        raise JevError(f"JEV_INVALID_NOUL: {p} fuera de [0, 1]")
    return {"noul": p}
