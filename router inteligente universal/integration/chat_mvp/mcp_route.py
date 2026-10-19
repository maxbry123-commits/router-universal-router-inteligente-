# -*- coding: utf-8 -*-
"""Puerta MCP (streamable-HTTP, JSON-RPC) para clientes tipo Claude.ai connector.

URL: POST /mcp?key=<RIU_PUBLIC_CHAT_KEY>
Habla el mismo protocolo que mcp_puente_github.py (tools GitHub del Router)
pero por HTTPS dentro del Space — sin Vercel ni servicio nuevo.
"""
from __future__ import annotations

import importlib.util
import json
import os

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

_MCP = None


def _mod():
    global _MCP
    if _MCP is None:
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        spec = importlib.util.spec_from_file_location('mcp_puente_github', os.path.join(base, 'mcp_puente_github.py'))
        _MCP = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_MCP)
    return _MCP


def build_mcp_router() -> APIRouter:
    r = APIRouter()

    @r.post('/mcp')
    async def mcp_http(request: Request):
        key_esperada = os.getenv('RIU_PUBLIC_CHAT_KEY')
        if not key_esperada or request.query_params.get('key') != key_esperada:
            return JSONResponse({'jsonrpc': '2.0', 'id': None,
                                 'error': {'code': -32001, 'message': 'key invalida'}}, status_code=401)
        try:
            cuerpo = await request.json()
        except Exception:  # noqa: BLE001
            return JSONResponse({'jsonrpc': '2.0', 'id': None,
                                 'error': {'code': -32700, 'message': 'JSON invalido'}}, status_code=400)
        mod = _mod()
        reqs = cuerpo if isinstance(cuerpo, list) else [cuerpo]
        respuestas = [r2 for r2 in (mod.procesar_peticion(req) for req in reqs) if r2 is not None]
        if not respuestas:
            return JSONResponse(None, status_code=202)  # solo notificaciones
        return JSONResponse(respuestas if isinstance(cuerpo, list) else respuestas[0],
                            headers={'MCP-Protocol-Version': '2025-03-26'})

    @r.get('/mcp')
    async def mcp_info(request: Request):
        return JSONResponse({'ok': True, 'servidor': 'riu-mcp-puente-github',
                             'uso': 'POST JSON-RPC con ?key=<clave>'})

    return r
