"""Puerta del Router hacia OmniRoute, que corre DENTRO de la misma máquina HF de 16 GB (127.0.0.1:20128).

GET  /omniroute/status          -> ¿OmniRoute arrancó? (no necesita clave de OmniRoute)
ANY  /omniroute/{ruta}          -> reenvía a OmniRoute (p. ej. /omniroute/v1/chat/completions, /omniroute/v1/models)
La clave de OmniRoute llega en la cabecera X-OmniRoute-Key (Authorization la usa HF para entrar al Job),
o sale de la variable OMNIROUTE_API_KEY del Router. Protegido además por X-API-Key del Router (si está configurada).
Solo librería estándar. Si OmniRoute no está listo, responde 503 con un mensaje claro.
"""
from __future__ import annotations

import os
import urllib.error
import urllib.request

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse, Response

BASE = os.getenv("OMNIROUTE_LOCAL_URL", "http://127.0.0.1:20128")


def _auth(key: str | None) -> None:
    want = os.getenv("RIU_ROUTER_API_KEY", "")
    if want and key != want:
        raise HTTPException(status_code=401, detail="X-API-Key inválida")


def build_omniroute_router() -> APIRouter:
    r = APIRouter()

    @r.get("/omniroute/status")
    def status() -> dict:
        try:
            with urllib.request.urlopen(BASE + "/", timeout=5) as resp:
                return {"omniroute": "encendido", "http": resp.status}
        except urllib.error.HTTPError as e:
            return {"omniroute": "encendido", "http": e.code}
        except Exception as e:  # noqa: BLE001
            try:
                tail = open("/tmp/omniroute.log", encoding="utf-8", errors="ignore").read()[-400:]
            except OSError:
                tail = ""
            return {"omniroute": "arrancando o caído", "detalle": type(e).__name__, "log": tail}

    @r.api_route("/omniroute/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
    async def proxy(path: str, request: Request, x_api_key: str | None = Header(None),
                    x_omniroute_key: str | None = Header(None)) -> Response:
        _auth(x_api_key)
        key = x_omniroute_key or os.getenv("OMNIROUTE_API_KEY", "")
        headers = {"Content-Type": request.headers.get("content-type", "application/json")}
        if key:
            headers["Authorization"] = f"Bearer {key}"
        qs = ("?" + request.url.query) if request.url.query else ""
        body = await request.body()
        req = urllib.request.Request(f"{BASE}/{path}{qs}", data=body or None, method=request.method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=280) as resp:
                return Response(content=resp.read(), status_code=resp.status, media_type=resp.headers.get("content-type"))
        except urllib.error.HTTPError as e:
            return Response(content=e.read(), status_code=e.code, media_type=e.headers.get("content-type"))
        except Exception as e:  # noqa: BLE001
            return JSONResponse({"error": f"OmniRoute no está listo ({type(e).__name__}). Revisa /omniroute/status."}, status_code=503)

    return r
