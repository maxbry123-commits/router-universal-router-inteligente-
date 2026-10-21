# -*- coding: utf-8 -*-
"""Ampliacion del MCP original /mcp con 3 herramientas de fichas_qwen.

No toca mcp_route.py ni mcp_puente_github.py: instala sobre el MCP original un envoltorio que
anade listar_fichas, chat y resultado y delega todo lo demas (github_leer, github_escribir,
github_api y la autenticacion RIU_MCP_KEY/RIU_PUBLIC_CHAT_KEY) al original.
Llama por HTTP al propio Router con router/red/http_plugins.py (sin credenciales en codigo).
"""
from __future__ import annotations

import importlib.util
import json
import os

PLUGIN = 'fichas_qwen'

_CHAT_PROPS = {
    'ficha_qwen': {'type': 'string', 'description': 'Ficha (alias o id); ver listar_fichas'},
    'message': {'type': 'string', 'description': 'Mensaje del usuario'},
    'messages': {'type': 'array', 'items': {'type': 'object'}, 'description': 'Alternativa a message: lista {role, content}; se usa el ultimo del usuario'},
    'sesion': {'type': 'string', 'description': 'Sesion de la conversacion (el plugin lleva el historial)'},
    'request_id': {'type': 'string', 'description': 'Idempotencia: mismo request_id devuelve el mismo proceso_id'},
    'modelo': {'type': 'string'},
    'max_tokens': {'type': 'integer'},
    'task_type': {'type': 'string'},
    'thinking_mode': {'type': 'string'},
    'mode_request': {'type': 'string'},
    'modo': {'type': 'string'},
    'objetivo': {'type': 'string'},
    'anclados': {'type': 'array', 'items': {}},
    'instrucciones_fijas': {'type': 'string'},
    'contexto_previo': {'type': 'string'},
    'fast_reply': {'type': 'boolean'},
    'caller_id': {'type': 'string'},
    'task_id': {'type': 'string'},
    'task_token_budget': {'type': 'integer'},
}

TOOLS_NUEVAS = [
    {'name': 'listar_fichas',
     'description': 'Lista las fichas disponibles de fichas_qwen (n, id, nombre).',
     'inputSchema': {'type': 'object', 'properties': {}}},
    {'name': 'chat',
     'description': 'Lanza un chat asincrono con una ficha de fichas_qwen. Devuelve proceso_id; consulta con la herramienta resultado.',
     'inputSchema': {'type': 'object', 'properties': _CHAT_PROPS, 'required': ['ficha_qwen']}},
    {'name': 'resultado',
     'description': 'Consulta el estado/resultado de un chat lanzado, por proceso_id.',
     'inputSchema': {'type': 'object',
                     'properties': {'proceso_id': {'type': 'string'},
                                    'espera': {'type': 'number', 'description': 'Segundos a esperar el resultado'}},
                     'required': ['proceso_id']}},
]

ACCION = {'listar_fichas': 'fichas', 'chat': 'chat_async', 'resultado': 'resultado'}
REQUERIDO = {'chat': 'ficha_qwen', 'resultado': 'proceso_id'}


def _llamar(plugin, accion, payload):
    # Llamada local al PluginHost del mismo proceso (sin HTTP a si mismo): misma ruta que POST /plugins/<id>/call/<accion>.
    from ..plugin_host.host import get_host
    out = get_host().call(plugin, accion, dict(payload or {}))
    if isinstance(out, dict) and out.get('status') == 'ok':
        return out.get('result')
    return {'error': str((out or {}).get('reason') or 'fallo'), 'status': str((out or {}).get('status') or 'degraded')}


def _es_error(res):
    return isinstance(res, dict) and bool(res.get('error'))


def ejecutar(nombre, args):
    """Devuelve (texto, es_error): resultado del plugin tal cual, o el error real si falla."""
    falta = REQUERIDO.get(nombre)
    if falta and not args.get(falta):
        return 'FALTA: %s' % falta, True
    res = _llamar(PLUGIN, ACCION[nombre], dict(args))
    return json.dumps(res, ensure_ascii=False), _es_error(res)


class _Ampliado:
    def __init__(self, mod):
        self._mod = mod
        self.TOOLS = list(mod.TOOLS) + TOOLS_NUEVAS

    def procesar_peticion(self, req):
        metodo = req.get('method')
        if metodo == 'tools/list':
            return self._mod.procesar_respuesta(req.get('id'), {'tools': self.TOOLS})
        if metodo == 'tools/call':
            p = req.get('params') or {}
            nombre = p.get('name')
            if nombre in ACCION:
                try:
                    texto, err = ejecutar(nombre, p.get('arguments') or {})
                except Exception as x:  # noqa: BLE001
                    texto, err = 'ERROR: ' + str(x)[:400], True
                return self._mod.procesar_respuesta(req.get('id'), {'content': [{'type': 'text', 'text': texto}], 'isError': err})
        return self._mod.procesar_peticion(req)

    def __getattr__(self, n):
        return getattr(self._mod, n)


def instalar(mcp_route_mod):
    """Sustituye la cache del modulo MCP de mcp_route por la version ampliada (sin editar mcp_route)."""
    mcp_route_mod._MCP = _Ampliado(mcp_route_mod._mod())
    return mcp_route_mod._MCP
