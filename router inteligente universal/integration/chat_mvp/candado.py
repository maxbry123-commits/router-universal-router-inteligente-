"""Candado del Router (Director 2026-10-03): una sola puerta que revisa TODAS las llamadas, sin tocar cada ruta.

1. Rutas que CAMBIAN el sistema (banco, tokens, fichas, procesador, pausar, borrar, GitHub...) exigen la clave del
   Director en la cabecera X-Director-Key. Sin ella: 403 CLAVE_DIRECTOR_REQUERIDA. Los agentes solo USAN.
2. Tokens de agente (riu_...): permisos por ruta (chat, memoria, almacenamiento, fichas, computo, terminal) y limite
   por minuto propio (429), para que 1000+ agentes no se pisen.
3. Claves maestras (RIU_AGENT_API_KEYS, harness): todo el uso, pero computo y terminal solo con la clave del Director.
4. Cada llamada autenticada queda anotada en la Ventana status (ventana.registrar).
"""
from __future__ import annotations

import json
import re
from typing import Any

from . import director, ventana

# (metodo o None, patron de ruta)
PROTEGIDAS: list[tuple[str | None, re.Pattern[str]]] = [(m, re.compile(p)) for m, p in [
    ("POST", r"^/vault/(lock|credentials|rotate|import)$"),
    ("POST", r"^/control/(?!hf/invoke$)"),                 # pausar/reanudar/emergencia/ordenes, autoscale manual, prueba de carga
    ("POST", r"^/plugins/(sync|[^/]+/(enable|disable))$"),
    ("POST", r"^/chat/(fichas|agents|github/commit)$"),
    ("DELETE", r"^/"),                                     # borrar cualquier cosa (salvo el propio espacio, ver abajo)
    ("POST", r"^/(state/rebuild|groups|workflows)$"),
    ("POST", r"^/fichas$"),
    ("POST", r"^/hf/(hardware|local/serve)$"),
    ("POST", r"^/tokens"),
    ("GET", r"^/tokens$"),
    ("POST", r"^/secciones$"),
]]
LIBRES_DE_CANDADO = [re.compile(r"^/espacio/")]           # cada token borra en SU propio espacio
PERMISOS: list[tuple[str | None, re.Pattern[str], str]] = [(m, re.compile(p), perm) for m, p, perm in [
    ("POST", r"^/hf/compute/run$", "computo"),
    (None, r"^/terminal/", "terminal"),
    ("POST", r"^/(v1/router/chat/completions|chat/send|chat/route|v1/chat/completions)$", "chat"),
    (None, r"^/memoria/", "memoria"),
    (None, r"^/espacio", "almacenamiento"),
    ("POST", r"^/(secciones/[^/]+/run|secciones/probar|fichas/[^/]+/run)$", "fichas"),
]]
SOLO_DIRECTOR_O_PERMISO = {"computo", "terminal"}


def _candidato(headers: dict[str, str]) -> str | None:
    key = headers.get("x-api-key")
    if key:
        return key
    auth = headers.get("authorization", "")
    return auth[7:].strip() if auth.lower().startswith("bearer ") else None


def _match(reglas: list[Any], method: str, path: str) -> Any:
    for regla in reglas:
        m, pat = regla[0], regla[1]
        if (m is None or m == method) and pat.search(path):
            return regla
    return None


async def _rechazo(send: Any, status: int, detail: str) -> None:
    body = json.dumps({"detail": detail}).encode()
    await send({"type": "http.response.start", "status": status,
                "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())]})
    await send({"type": "http.response.body", "body": body})


class Candado:
    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        method, path = scope.get("method", "GET"), scope.get("path", "")
        headers = {k.decode("latin-1").lower(): v.decode("latin-1") for k, v in scope.get("headers", [])}
        es_director = director.verify(headers.get(director.HEADER)) if headers.get(director.HEADER) else False

        if not es_director and _match(PROTEGIDAS, method, path) and not any(p.search(path) for p in LIBRES_DE_CANDADO):
            await _rechazo(send, 403, "CLAVE_DIRECTOR_REQUERIDA (cabecera X-Director-Key)")
            return

        owner = None
        cand = _candidato(headers)
        if cand:
            from .tokens import REGISTRO, dueno

            rec = REGISTRO.buscar(cand)
            if rec is not None:
                owner = dueno(rec)
                if not REGISTRO.permitir(rec):
                    await _rechazo(send, 429, "LIMITE_POR_MINUTO_DEL_TOKEN")
                    return
                regla = _match(PERMISOS, method, path)
                if regla and regla[2] not in rec.get("permisos", []) and not es_director:
                    await _rechazo(send, 403, f"TOKEN_SIN_PERMISO:{regla[2]}")
                    return
            else:
                try:
                    from ..huggingface.api_key_auth import authenticate_api_key

                    owner = authenticate_api_key(cand)
                except Exception:  # noqa: BLE001 - the route itself answers 401
                    owner = None
                regla = _match(PERMISOS, method, path)
                if owner and regla and regla[2] in SOLO_DIRECTOR_O_PERMISO and not es_director:
                    await _rechazo(send, 403, f"CLAVE_DIRECTOR_REQUERIDA para {regla[2]} con clave maestra")
                    return
        if owner:
            ventana.registrar(owner, "mcp" if path.startswith("/mcp") else "http", path)
            scope.setdefault("state", {})["riu_owner"] = owner
        if es_director:
            scope.setdefault("state", {})["riu_director"] = True
        await self.app(scope, receive, send)
