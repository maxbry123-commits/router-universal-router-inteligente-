"""loop_engine.py — Motor del loop (MINIMAX 4) que invoca api/loop.js.

CONTRATO (api/loop.js):
    python3 -m router_llm_hf.loop_engine '<json>'
    -> imprime UN objeto JSON por stdout.
    claves que usa el llamante: "done" (bool) y "iteration" (int).

Determinista y fail-closed: si el payload no es JSON valido sale con codigo 2 y
un JSON de error (nunca texto libre: el llamante hace JSON.parse y reventaria).
Ejecucion con el repo como PYTHONPATH (CWD=raiz del repo o PYTHONPATH=<raiz>).

El motor NO llama a proveedores: resuelve el plan (modo + adapter) y decide si
la iteracion termina. La ejecucion real la hace el proxy del Data Plane.
"""
from __future__ import annotations

import json
import os
import sys

MAX_ITER = int(os.getenv("LOOP_MAX_ITER", "8"))


def _text_of(payload):
    """Extrae el texto del usuario del payload (str o dict con messages)."""
    if isinstance(payload, str):
        return payload
    if not isinstance(payload, dict):
        return ""
    text = payload.get("input") or payload.get("text") or ""
    if isinstance(text, str) and text.strip():
        return text
    for msg in payload.get("messages") or []:
        if isinstance(msg, dict) and msg.get("role") == "user":
            content = msg.get("content")
            if isinstance(content, str):
                return content
    return text if isinstance(text, str) else ""


def _plan(text):
    """Modo + adapter del plan. Fail-soft: si HF no responde, plan minimo."""
    from .mode_detector import detect_mode, detect_service_route
    from .service_routes import SERVICE_MODES

    service = detect_service_route(text)
    mode = service or detect_mode(text)
    adapter = {}
    try:
        from .mode_router import get_adapter_config
        adapter = get_adapter_config(mode) or {}
    except Exception as exc:  # sin red o sin registry: plan minimo, no crash
        adapter = {"_error": str(exc)[:200]}
    plan = {
        "mode": mode,
        "service_mode": service,
        "base_model": adapter.get("base_model"),
        "lora": adapter.get("lora"),
        "dataset": adapter.get("dataset"),
    }
    if service and service in SERVICE_MODES:
        cfg = SERVICE_MODES[service]
        plan["route"] = cfg["route"]
        plan["local_first"] = cfg["local_first"]
        plan["space"] = cfg["space"]
    return plan


def main(argv):
    raw = argv[1] if len(argv) > 1 else "{}"
    try:
        payload = json.loads(raw)
    except Exception as exc:
        json.dump(
            {"done": True, "iteration": 0, "error": "payload no JSON: {}".format(exc)},
            sys.stdout,
        )
        sys.stdout.write("\n")
        return 2

    iteration = int(payload.get("iteration") or 0) if isinstance(payload, dict) else 0
    text = _text_of(payload)
    plan = _plan(text)

    resolved = bool(plan.get("base_model") or plan.get("mode"))
    last = iteration >= MAX_ITER
    done = bool(resolved and (last or not text.strip()))

    out = {
        "done": done,
        "iteration": iteration,
        "mode": plan["mode"],
        "service_mode": plan.get("service_mode"),
        "plan": plan,
    }
    if not done:
        out["next"] = "reintentar con mas contexto"
    json.dump(out, sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
