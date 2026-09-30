"""Plantilla de plugin para un SDK/API nuevo. La carpeta empieza con _ y el Plugin Host la IGNORA a proposito.
Para usarla: copiar la carpeta a plugins/<id>/, cambiar CAMBIAR en ficha.json y aqui (id = nombre de carpeta).
Acciones: status, invoke. La clave NO esta en el repo: se lee del banco secreto ya abierto (vault_hook) o de una variable de entorno.
"""
from __future__ import annotations

import os
from typing import Any

PROVIDER = "CAMBIAR_proveedor"  # prefijo del ref en el banco (proveedor/cuenta) y clave de PROVIDER_MAP en vault_bridge.py
ENV_KEY = "CAMBIAR_NOMBRE_VARIABLE_ENTORNO"  # solo respaldo; el camino normal es el banco
ENV_URL = "CAMBIAR_NOMBRE_VARIABLE_URL"


def _keys() -> list[str]:
    try:
        from integration.chat_mvp import vault_hook
        found = vault_hook.provider_keys(PROVIDER)
    except Exception:  # noqa: BLE001 - sin banco abierto se sigue con el respaldo
        found = []
    env = (os.getenv(ENV_KEY) or "").strip()
    return list(found) or ([env] if env else [])


def handle(action: str, payload: dict[str, Any] | None) -> dict[str, Any]:
    payload = payload or {}
    if action == "status":
        if not _keys():
            return {"status": "degraded", "reason": "sin clave: abrir el banco (/vault) o definir la variable"}
        return {"status": "ok", "claves_disponibles": len(_keys())}  # solo el conteo, nunca el valor
    if action == "invoke":
        if not _keys():
            return {"status": "degraded", "reason": "sin clave"}
        return {"status": "degraded", "reason": "invoke sin implementar: escribir la llamada real al SDK aqui"}
    return {"status": "error", "reason": "accion desconocida: " + str(action)}
