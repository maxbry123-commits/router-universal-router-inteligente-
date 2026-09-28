"""Heartbeat determinista para el guardián OpenClaw."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

try:
    from puente_asistentes import emit
except ImportError:  # pragma: no cover
    from .puente_asistentes import emit

MAX_STALL_MINUTES = int(os.getenv("YAIWES_HEARTBEAT_MAX_MINUTES", "30"))


def _to_dt(value) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def detectar_paradas(tareas: Iterable[dict], ahora: datetime | None = None, limite_min: int = MAX_STALL_MINUTES) -> list[dict]:
    ahora = ahora or datetime.now(timezone.utc)
    alertas = []
    for tarea in tareas:
        if str(tarea.get("status", "")).upper() in {"PASS", "DONE", "BLOCK", "CANCELLED"}:
            continue
        hb = _to_dt(tarea.get("heartbeat") or tarea.get("updated_at"))
        if hb is None:
            continue
        minutos = (ahora - hb.astimezone(timezone.utc)).total_seconds() / 60
        if minutos > limite_min:
            alertas.append({
                "type": "ALERTA",
                "task_id": tarea.get("id") or tarea.get("task_id") or "unknown",
                "stall_minutes": round(minutos, 1),
            })
    return alertas


def vigilar(tareas: Iterable[dict], ahora: datetime | None = None) -> str:
    alertas = detectar_paradas(tareas, ahora=ahora)
    if not alertas:
        return "NO_REPLY"
    for alerta in alertas:
        emit(alerta)
    ids = ",".join(a["task_id"] for a in alertas)
    return f"ALERTA:{ids}"


def leer_estado(path: str | Path) -> list[dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if isinstance(data.get("tasks"), list):
            return data["tasks"]
        return [dict({"id": key}, **value) for key, value in data.items() if isinstance(value, dict)]
    return []
