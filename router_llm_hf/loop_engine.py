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

MERGE MINIMAX 2E (sobre la version de los modos de servicio):
  · El plan ya NO depende de la red: el adapter se resuelve con la tabla local
    de alias (mismos 4 modos con adapter GAP confirmado). Antes el motor hacia
    una llamada a HF por iteracion: eso rompia la determinismo y hacia fallar
    el loop entero sin conexion.
  · Acepta task_id y max_iterations, y guarda un checkpoint del estado: asi
    /v1/loop/resume del proxy tiene algo real que reanudar (antes la lista de
    checkpoints salia siempre vacia).
"""
from __future__ import annotations

import json
import os
import sys

MAX_ITER = int(os.getenv("LOOP_MAX_ITER", "8"))

# Modos con adapter GAP confirmado en COMAND-CENTER-1/swe-code-adapters.
VALID_MODES = ("python", "backend", "architecture", "agentic_tool")

# Alias detector -> modo de adapter (tabla local, sin red).
MODE_ALIAS = {
    "code_generate": "python",
    "tool_call": "agentic_tool",
    "architecture": "architecture",
    "backend": "backend",
    "python": "python",
}


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
    """Modo + adapter del plan. SIN RED: tabla local de alias."""
    from .mode_detector import detect_mode, detect_service_route
    from .service_routes import SERVICE_MODES

    service = detect_service_route(text)
    mode = service or detect_mode(text)
    adapter_mode = mode if mode in VALID_MODES else MODE_ALIAS.get(mode)
    plan = {
        "mode": mode,
        "service_mode": service,
        "adapter_mode": adapter_mode,
        "base_model": None,
        "lora": None,
        "dataset": None,
    }
    if service and service in SERVICE_MODES:
        cfg = SERVICE_MODES[service]
        plan["route"] = cfg["route"]
        plan["local_first"] = cfg["local_first"]
        plan["space"] = cfg["space"]
        plan["base_model"] = cfg.get("model")
    return plan


def _save_checkpoint(task_id, state, input_sha256):
    """Guarda el checkpoint del loop (para /v1/loop/resume). Nunca revienta."""
    try:
        import hashlib

        from .checkpoint_manager import CheckpointManager

        cm = CheckpointManager()
        path = cm.save(task_id, state, input_sha256)
        return True, path
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def _sha256(text):
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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

    if not isinstance(payload, dict):
        payload = {"input": str(payload)}

    iteration = int(payload.get("iteration") or 0)
    max_iterations = int(payload.get("max_iterations") or MAX_ITER)
    task_id = str(payload.get("task_id") or payload.get("taskId") or "default")
    text = _text_of(payload)
    plan = _plan(text)

    resolved = bool(plan.get("mode"))
    last = iteration >= max_iterations
    done = bool(resolved and (last or not text.strip()))

    out = {
        "done": done,
        "iteration": iteration,
        "max_iterations": max_iterations,
        "task_id": task_id,
        "mode": plan["mode"],
        "service_mode": plan.get("service_mode"),
        "adapter_mode": plan.get("adapter_mode"),
        "plan": plan,
        "input_sha256": _sha256(text),
        "deterministic": True,
    }
    if not done:
        out["next"] = "reintentar con mas contexto"

    ok, detail = _save_checkpoint(
        task_id,
        {
            "iteration": iteration,
            "status": "done" if done else "running",
            "mode": plan["mode"],
            "adapter_mode": plan.get("adapter_mode"),
            "steps": plan,
        },
        out["input_sha256"],
    )
    out["checkpoint"] = ok
    if not ok:
        out["checkpoint_error"] = detail

    json.dump(out, sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
