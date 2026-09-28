"""Puerta del Router hacia OmniRoute (N instancias DENTRO de la misma máquina HF 16 GB).

Instancias: OMNIROUTE_PORTS (coma) o, por defecto, 10 puertos 20128, 20138, …, 20218 (ver chat router/08-OMNIROUTE/start_omniroute_x10.sh).
GET  /omniroute/status   -> estado de CADA instancia (encendida/caída) + cuántas responden. Sin clave de OmniRoute.
ANY  /omniroute/{ruta}   -> reparte en rotación entre las instancias vivas; si una falla por conexión, prueba la siguiente.
La clave de OmniRoute llega en X-OmniRoute-Key (Authorization la usa HF para entrar al Job) o sale de OMNIROUTE_API_KEY.
Protegido por X-API-Key del Router (RIU_ROUTER_API_KEY). Solo librería estándar.
"""
from __future__ import annotations

import itertools
import os
import threading
import urllib.error
import urllib.request

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse, Response

_PUERTOS = [int(p) for p in os.getenv("OMNIROUTE_PORTS", "").split(",") if p.strip().isdigit()] or [20128 + 10 * i for i in range(10)]
BASES = [f"http://127.0.0.1:{p}" for p in _PUERTOS]
_turno = itertools.cycle(range(len(BASES)))
_lock = threading.Lock()


def _auth(key: str | None) -> None:
    want = os.getenv("RIU_ROUTER_API_KEY", "")
    if want and key != want:
        raise HTTPException(status_code=401, detail="X-API-Key inválida")


def _viva(base: str) -> bool | int:
    try:
        with urllib.request.urlopen(base + "/", timeout=3) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:  # noqa: BLE001
        return False


def build_omniroute_router() -> APIRouter:
    r = APIRouter()

    @r.get("/omniroute/status")
    def status() -> dict:
        estado = {b.rsplit(":", 1)[1]: ("encendido" if _viva(b) else "caído") for b in BASES}
        vivas = sum(1 for v in estado.values() if v == "encendido")
        out = {"omniroute": "encendido" if vivas else "arrancando o caído", "vivas": vivas, "total": len(BASES), "instancias": estado}
        if not vivas:
            try:
                out["log"] = open("/tmp/omniroute.log", encoding="utf-8", errors="ignore").read()[-400:]
            except OSError:
                pass
        return out

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
        with _lock:
            inicio = next(_turno)
        ultimo = None
        for k in range(len(BASES)):
            base = BASES[(inicio + k) % len(BASES)]
            req = urllib.request.Request(f"{base}/{path}{qs}", data=body or None, method=request.method, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=280) as resp:
                    return Response(content=resp.read(), status_code=resp.status, media_type=resp.headers.get("content-type"),
                                    headers={"X-OmniRoute-Instancia": base.rsplit(":", 1)[1]})
            except urllib.error.HTTPError as e:
                return Response(content=e.read(), status_code=e.code, media_type=e.headers.get("content-type"),
                                headers={"X-OmniRoute-Instancia": base.rsplit(":", 1)[1]})
            except Exception as e:  # noqa: BLE001  instancia caída: probar la siguiente
                ultimo = type(e).__name__
        return JSONResponse({"error": f"Ninguna instancia de OmniRoute responde ({ultimo}). Revisa /omniroute/status."}, status_code=503)

    return r
