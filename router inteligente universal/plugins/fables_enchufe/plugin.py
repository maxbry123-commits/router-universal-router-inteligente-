"""fables_enchufe: envoltura del unico tramo cableado de Fables (enchufe/validator_v2.py). Solo lo ya existente.

Acciones: status, validate (payload {"ficha": {...}}). Reutiliza repo_validator() del host (carga por ruta, sin duplicar).
"""
from __future__ import annotations

from typing import Any


def _validator():
    from integration.plugin_host.host import repo_validator

    return repo_validator()


def handle(action: str, payload: dict[str, Any] | None) -> dict[str, Any]:
    v = _validator()
    if action == "status":
        return {"status": "ok" if v else "degraded", "validator_v2_cargado": bool(v), **({} if v else {"reason": "enchufe/validator_v2.py no se pudo cargar"})}
    if action != "validate":
        return {"status": "degraded", "reason": "accion desconocida"}
    if v is None:
        return {"status": "degraded", "reason": "enchufe/validator_v2.py no se pudo cargar"}
    ficha = (payload or {}).get("ficha")
    if not isinstance(ficha, dict):
        return {"status": "degraded", "reason": "payload.ficha debe ser un objeto"}
    verdict = v(ficha)
    return {"status": "ok", "valido": bool(verdict.valido), "errores": list(verdict.errores), "ficha_normalizada": verdict.ficha_normalizada}
