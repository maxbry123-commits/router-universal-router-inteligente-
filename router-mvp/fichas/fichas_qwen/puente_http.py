"""Edificio 1 -> edificio 2 solo por HTTP: puente_chat y hf_storage via red.http_plugins.llamar (sin importar plugins/)."""
from __future__ import annotations

from red.http_plugins import llamar


def capacidad_de(texto):
    """Puerta CAP unica (puente_chat.capacidad_de). Sin respuesta valida: 'none' (falla cerrado: sin tools)."""
    r = llamar("puente_chat", "capacidad", {"texto": texto})
    return r.get("capacidad") if isinstance(r, dict) and r.get("status") == "ok" and r.get("capacidad") else "none"


class _HfStorage:
    """Misma superficie que el modulo hf_storage.plugin: handle(accion, payload) -> dict."""

    def handle(self, accion, payload=None):
        r = llamar("hf_storage", accion, payload or {})
        return r if isinstance(r, dict) else {"status": "degraded", "error": "respuesta invalida"}


HFS = _HfStorage()
