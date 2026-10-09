"""Puente mínimo entre YAIWES y Hermes/OpenClaw."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
import sys
from urllib import request

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "colmena"))
from router_cliente import RouterCliente  # noqa: E402  (helper único hacia el Router)

ROLES = {
    "hermes": "planner_supervisor",
    "openclaw": "guardian_supervisor",
}
GROUP = os.getenv("YAIWES_ASSISTANT_GROUP", "assistants")  # grupo de política del Router; el Router elige modelo/clave
STATE_HUB_URL = os.getenv("YAIWES_STATE_HUB_URL", "").rstrip("/")
BITACORA = Path(__file__).resolve().parents[2] / "03-ESTADO" / "BITACORA.jsonl"


def _simulado() -> bool:
    return os.getenv("SIMULADO", "0") == "1"


def _post_json(url: str, payload: dict, headers: dict[str, str] | None = None) -> dict:
    data = json.dumps(payload).encode("utf-8")
    hdrs = {"Content-Type": "application/json", **(headers or {})}
    req = request.Request(url, data=data, headers=hdrs, method="POST")
    with request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def preguntar(agente: str, mensaje: str) -> str:
    """Pregunta a Hermes/OpenClaw a través del grupo `assistants` del Router; SIMULADO no usa red."""
    if agente not in ROLES:
        raise ValueError(f"agente desconocido: {agente}")
    if not isinstance(mensaje, str) or not mensaje.strip():
        raise ValueError("mensaje requerido")
    if _simulado():
        return f"SIMULADO:{agente}:{ROLES[agente]}:{mensaje.strip()}"

    # El Router (grupo `assistants`) elige modelo y rota claves; el puente no llama a ningún proveedor directo.
    return RouterCliente(max_tokens=1024).chat(mensaje.strip(), ROLES[agente], group=GROUP)


def emit(evento: dict) -> dict:
    """Emite al State Hub; fallback JSONL. En SIMULADO no escribe ni usa red."""
    if not isinstance(evento, dict) or not evento:
        raise ValueError("evento debe ser dict no vacío")
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        **evento,
    }
    if _simulado():
        return {"status": "SIMULADO", "event": record}

    if STATE_HUB_URL:
        response = _post_json(f"{STATE_HUB_URL}/events", record)
        return {"status": "STATE_HUB", "response": response, "event": record}

    BITACORA.parent.mkdir(parents=True, exist_ok=True)
    with BITACORA.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return {"status": "BITACORA", "path": str(BITACORA), "event": record}
