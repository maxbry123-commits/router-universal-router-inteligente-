"""Proxy /web/* al bridge EXISTENTE del mismo Space; no crea infraestructura nueva.

Se reenvian exclusivamente las credenciales de la llamada autenticada; el puerto de
destino es loopback fijo. Admite SSE real, cancelacion y respuestas JSON.
"""
import os
import httpx
from fastapi import Request
from fastapi.responses import JSONResponse, Response, StreamingResponse

# El bridge debe estar unido solo a loopback en este Space.
_BRIDGE = "http://127.0.0.1:" + str(int(os.getenv("BRIDGE_PORT") or "7870"))
_ENTRADA = {"authorization", "x-api-key", "x-bridge-key", "x-operador", "x-operator-token",
            "content-type", "accept", "last-event-id"}
_SALIDA = {"content-type", "cache-control", "x-request-id"}


def montar(app):
    @app.api_route("/web/{ruta:path}", methods=["GET", "POST", "DELETE", "PUT", "PATCH"], include_in_schema=False)
    async def web_bridge(ruta: str, request: Request):
        # Un proxy de rutas, NO un cliente HTTP arbitrario ni un proveedor nuevo.
        if ruta != "health" and not ruta.startswith("v1/"):
            return JSONResponse(status_code=404, content={"error": {"code": "RUTA_BRIDGE_INVALIDA"}})
        if len(ruta) > 256 or ".." in ruta or "\\" in ruta:
            return JSONResponse(status_code=400, content={"error": {"code": "RUTA_BRIDGE_INVALIDA"}})
        headers = {k: v for k, v in request.headers.items() if k.lower() in _ENTRADA}
        headers["accept-encoding"] = "identity"  # SSE se reenvia crudo, sin comprimir ni corromper el navegador
        client = httpx.AsyncClient(timeout=httpx.Timeout(connect=4, read=None, write=20, pool=4), trust_env=False)
        try:
            req = client.build_request(request.method, _BRIDGE + "/" + ruta,
                                       params=request.query_params, headers=headers,
                                       content=await request.body())
            upstream = await client.send(req, stream=True)
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.PoolTimeout, OSError):
            await client.aclose()
            return JSONResponse(status_code=503, content={"error": {"code": "BRIDGE_NO_DISPONIBLE"}})
        except Exception:
            await client.aclose()
            return JSONResponse(status_code=502, content={"error": {"code": "BRIDGE_TRANSPORTE_ERROR"}})
        response_headers = {k: v for k, v in upstream.headers.items() if k.lower() in _SALIDA}
        if "text/event-stream" in upstream.headers.get("content-type", "").lower():
            async def chunks():
                try:
                    async for item in upstream.aiter_raw():
                        if item:
                            yield item
                finally:
                    await upstream.aclose()
                    await client.aclose()
            return StreamingResponse(chunks(), status_code=upstream.status_code,
                                     headers=response_headers)
        try:
            body = await upstream.aread()
            return Response(content=body, status_code=upstream.status_code,
                            headers=response_headers)
        finally:
            await upstream.aclose()
            await client.aclose()
