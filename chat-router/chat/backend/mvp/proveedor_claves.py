"""Adaptador HTTP del plugin banco_proveedores. Punto unico del Router MVP.

Las claves son datos de control sensibles: no se entregan a la inferencia del Harness.
El chat autorizado invoca POST /plugins/banco_proveedores/call/{catalogo|anadir}.
SWE CODE lee el MISMO banco cifrado ya respaldado; no se crean nuevos servicios.
"""
import os
import re

import httpx
from fastapi import HTTPException


async def llamar(accion, cuerpo):
    if accion not in ("catalogo", "anadir"):
        raise HTTPException(status_code=404, detail="ACCION_NO_DISPONIBLE")
    if not isinstance(cuerpo, dict):
        raise HTTPException(status_code=400, detail="CUERPO_INVALIDO")
    if accion == "anadir":
        secreto = cuerpo.get("secret")
        provider = str(cuerpo.get("proveedor") or "auto")
        tipo = cuerpo.get("tipo") or "api_key"
        if (not isinstance(secreto, str) or not 8 <= len(secreto) <= 300
                or any(ch.isspace() for ch in secreto)
                or not re.fullmatch(r"auto|[a-z][a-z0-9_-]{1,31}", provider)
                or tipo not in ("api_key", "sdk")):
            raise HTTPException(status_code=400, detail="REGISTRO_INVALIDO")
    # Nunca recibir URL arbitraria del cliente (evitar SSRF): solo loopback del bridge existente.
    port = os.environ.get("BRIDGE_PORT") or "7870"
    if not port.isdigit() or not 1 <= int(port) <= 65535:
        raise HTTPException(status_code=503, detail="BRIDGE_NO_CONFIGURADO")
    key = os.environ.get("RIU_API_KEY") or ""
    if not key:
        raise HTTPException(status_code=503, detail="CREDENCIAL_INTERNA_AUSENTE")
    try:
        async with httpx.AsyncClient(timeout=25, trust_env=False) as cliente:
            respuesta = await cliente.request("POST" if accion == "anadir" else "GET",
                "http://127.0.0.1:" + port + "/v1/credenciales",
                headers={"X-API-Key": key}, json=cuerpo if accion == "anadir" else None)
            if respuesta.status_code != 200:
                raise HTTPException(status_code=respuesta.status_code,
                                    detail="BANCO_NO_DISPONIBLE" if respuesta.status_code >= 500 else "REGISTRO_INVALIDO")
            salida = respuesta.json()
    except HTTPException:
        raise
    except (httpx.HTTPError, ValueError):
        raise HTTPException(status_code=503, detail="BANCO_NO_DISPONIBLE") from None
    if not isinstance(salida, dict) or salida.get("ok") is not True:
        raise HTTPException(status_code=503, detail="BANCO_NO_DISPONIBLE")
    return salida
