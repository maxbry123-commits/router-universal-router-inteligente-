"""Puente mínimo entre YAIWES y Hermes/OpenClaw."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib import request

ROLES = {
    "hermes": "planner_supervisor",
    "openclaw": "guardian_supervisor",
}
BASE_URL = os.getenv("YAIWES_ROUTER_URL", "https://integrate.api.nvidia.com/v1").rstrip("/")
MODEL = os.getenv("YAIWES_ASSISTANT_MODEL", "kimi-k3")
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
    """Pregunta a Hermes/OpenClaw a través del Router/NVIDIA; SIMULADO no usa red."""
    if agente not in ROLES:
        raise ValueError(f"agente desconocido: {agente}")
    if not isinstance(mensaje, str) or not mensaje.strip():
        raise ValueError("mensaje requerido")
    if _simulado():
        return f"SIMULADO:{agente}:{ROLES[agente]}:{mensaje.strip()}"

    token = os.getenv("NVIDIA_API_KEY") or os.getenv("RIU_ROUTER_API_KEY")
    if not token:
        raise RuntimeError("falta NVIDIA_API_KEY o RIU_ROUTER_API_KEY")
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": f"Actúa como {ROLES[agente]} de YAIWES."},
            {"role": "user", "content": mensaje},
        ],
        "temperature": 0.2,
    }
    result = _post_json(
        f"{BASE_URL}/chat/completions",
        payload,
        {"Authorization": f"Bearer {token}"},
    )
    try:
        return str(result["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("respuesta inválida del Router") from exc


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
