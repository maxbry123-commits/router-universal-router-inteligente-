"""Ventana status router inteligente universal (Director 2026-10-03): handoff JSON vivo que se escribe solo.

Cada conexion (HTTP o MCP) queda anotada en memoria por candado.py; cada RIU_VENTANA_S (30 s) se escriben, solo si
cambiaron, estos archivos en router-inteligente-universal/Ventana status router inteligente universal/:
  conectados.json    quien esta conectado, por que via, cuantas llamadas, ultima ruta
  banco.json         que hay en el banco (numerado N01.., proveedor, cuenta, huella; nunca la clave)
  laboratorio.json   ultimo informe del laboratorio (estado de cada API)
  secciones.json     fichas montadas como secciones (y las que tienen error)
  tokens.json        cuantos tokens hay por instancia, activos/apagados (sin huellas)
  handoff-vivo.json  resumen general: Router vigente, puerta, rutas, conteos, guias
GET /ventana devuelve lo mismo en vivo.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import time
from typing import Any

from fastapi import APIRouter, Depends

from . import rutas

log = logging.getLogger("riu")
INTERVALO = float(os.getenv("RIU_VENTANA_S", "30"))
PUERTA = os.getenv("RIU_PUERTA_URL", "https://comand-center-1-claude-github-mcp-backup.hf.space")
MAX_CONEXIONES = 20000
_lock = threading.Lock()
_conexiones: dict[str, dict[str, Any]] = {}
_huellas: dict[str, str] = {}
_inicio = time.time()


def registrar(owner: str, via: str, path: str) -> None:
    now = time.time()
    with _lock:
        c = _conexiones.get(owner)
        if c is None:
            if len(_conexiones) >= MAX_CONEXIONES:
                return
            c = _conexiones[owner] = {"primera": now, "ultima": now, "llamadas": 0, "via": {}, "ultima_ruta": ""}
        c["ultima"] = now
        c["llamadas"] += 1
        c["via"][via] = c["via"].get(via, 0) + 1
        c["ultima_ruta"] = path[:120]


def _seguro(fn: Any, default: Any) -> Any:
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001 - a broken source never stops the window
        return {**default, "error": type(exc).__name__} if isinstance(default, dict) else default


def conectados() -> dict[str, Any]:
    now = time.time()
    with _lock:
        rows = {k: {**v, "activo_ultimos_5_min": now - v["ultima"] < 300} for k, v in _conexiones.items()}
    return {"total": len(rows), "activos_5_min": sum(1 for v in rows.values() if v["activo_ultimos_5_min"]), "conexiones": rows}


def banco() -> dict[str, Any]:
    from .control_plane import _credentials

    creds = _credentials()
    porprov: dict[str, int] = {}
    for c in creds:
        porprov[c["provider"]] = porprov.get(c["provider"], 0) + 1
    return {"total": len(creds), "por_proveedor": porprov,
            "credenciales": [{k: c.get(k) for k in ("n", "provider", "account", "source", "fp")} for c in creds],
            "nota": "sin claves: solo numero, proveedor, cuenta y huella"}


def laboratorio() -> dict[str, Any]:
    from .control_plane import lab_last

    rep = lab_last() or {}
    return {"run_id": rep.get("run_id"), "ts": rep.get("ts"), "resumen": rep.get("resumen"),
            "apis": [{k: a.get(k) for k in ("n", "provider", "account", "status", "passed")} for a in rep.get("apis") or []],
            "sdks": rep.get("sdks")}


def secciones() -> dict[str, Any]:
    from .secciones import SECCIONES

    return {"carpeta": rutas.FICHAS, "secciones": SECCIONES.lista()}


def tokens() -> dict[str, Any]:
    from .tokens import REGISTRO

    por: dict[str, dict[str, int]] = {}
    for rec in list(REGISTRO.data.values()):
        d = por.setdefault(rec.get("instancia") or "?", {"activos": 0, "apagados": 0})
        d["activos" if rec.get("activo", True) else "apagados"] += 1
    return {"total": len(REGISTRO.data), "por_instancia": por}


def handoff() -> dict[str, Any]:
    return {
        "router": {"job_id": os.getenv("JOB_ID") or os.getenv("RIU_JOB_ID"), "arranque": _inicio, "puerta": PUERTA},
        "raiz_almacenamiento": f"{rutas.bucket()}/{rutas.ROOT}",
        "como_conectarse": {
            "http_openai": f"{PUERTA}/v1/router  (model=auto, Authorization: Bearer <token>)",
            "mcp": f"{PUERTA}/mcp/  (Authorization: Bearer <token>)",
            "memoria": "/memoria/save|load|search", "almacenamiento_propio": "/espacio/<ruta>",
            "secciones": "/secciones y /secciones/<nombre>/run", "computo": "/hf/compute/run (permiso computo)",
            "terminal": "/terminal/run (permiso terminal; reemplaza SSH)", "quien_soy": "/tokens/yo",
        },
        "candado": "cambios (banco, tokens, fichas, procesador, pausar) solo con X-Director-Key",
        "guias": ["router inteligente universal/HANDOFF-ROUTER-UNIVERSAL-OPUS.md",
                  "router inteligente universal/MANUAL-AGENTES.md"],
        "conteos": {"conexiones": len(_conexiones)},
    }


FUENTES = {"conectados.json": (conectados, {}), "banco.json": (banco, {}), "laboratorio.json": (laboratorio, {}),
           "secciones.json": (secciones, {}), "tokens.json": (tokens, {}), "handoff-vivo.json": (handoff, {})}


def todo() -> dict[str, Any]:
    return {nombre: _seguro(fn, d) for nombre, (fn, d) in FUENTES.items()}


def escribir() -> int:
    from .control_plane import bucket_write_json

    escritos = 0
    for nombre, data in todo().items():
        cuerpo = json.dumps(data, sort_keys=True, default=str)
        h = hashlib.sha256(cuerpo.encode()).hexdigest()
        if _huellas.get(nombre) == h:
            continue
        if bucket_write_json(f"{rutas.VENTANA}/{nombre}", {"actualizado": time.time(), **data}):
            _huellas[nombre] = h
            escritos += 1
    return escritos


def iniciar() -> None:
    def bucle() -> None:
        while True:
            time.sleep(INTERVALO)
            try:
                escribir()
            except Exception as exc:  # noqa: BLE001
                log.warning("ventana: %s", type(exc).__name__)

    threading.Thread(target=bucle, name="riu-ventana", daemon=True).start()


def build_ventana_router(auth: Any) -> APIRouter:
    r = APIRouter()

    @r.get("/ventana")
    def ventana(_owner: str = Depends(auth)) -> dict[str, Any]:
        return {"carpeta": f"{rutas.bucket()}/{rutas.VENTANA}", **todo()}

    return r
