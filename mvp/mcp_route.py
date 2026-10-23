"""MCP JSON-RPC 2.0 del Router MVP: un endpoint y autenticacion compartida."""
import asyncio
import json
from fastapi import Depends, HTTPException, Request, Response
from mvp import modelos
from router import mcp_puente_github as github

# Esquemas de mvp/mcp_route.py y del contrato existente
# router/mcp_puente_github.py + router/integration/chat_mvp/mcp_fichas.py.
_CHAT_FICHA = {
    'tools': {'type': 'boolean', 'default': False},
    'agente_tool': {'type': 'boolean', 'default': False},
    'llm_tool': {'type': 'boolean', 'default': False},
    'ficha_qwen': {'type': 'string'}, 'message': {'type': 'string'},
    'messages': {'type': 'array', 'items': {'type': 'object'}},
    'sesion': {'type': 'string'}, 'request_id': {'type': 'string'},
    'max_tokens': {'type': 'integer'}, 'task_type': {'type': 'string'},
    'thinking_mode': {'type': 'string'}, 'mode_request': {'type': 'string'},
    'modo': {'type': 'string'}, 'objetivo': {'type': 'string'},
    'anclados': {'type': 'array', 'items': {}},
    'instrucciones_fijas': {'type': 'string'}, 'contexto_previo': {'type': 'string'},
    'fast_reply': {'type': 'boolean'}, 'caller_id': {'type': 'string'},
    'task_id': {'type': 'string'}, 'task_token_budget': {'type': 'integer'},
}
HERRAMIENTAS = [
    {'name': 'chat', 'description': 'Chat del Router o chat asincrono de una ficha.',
     'inputSchema': {'type': 'object', 'properties': {
         'mensajes': {'type': 'array', 'items': {'type': 'object'}},
         'modelo': {'type': 'string'}, 'opciones': {'type': 'object'},
         'via': {'type': 'string'}, **_CHAT_FICHA},
         'anyOf': [{'required': ['mensajes']}, {'required': ['ficha_qwen']}]}},
    {'name': 'almacen', 'description': 'Acceder al almacenamiento autorizado',
     'inputSchema': {'type': 'object', 'properties': {
         'accion': {'type': 'string', 'enum': ['guardar', 'leer', 'computar', 'status']},
         'destino': {'type': 'string', 'enum': ['hf', 'harness']},
         'nombre': {'type': 'string'}, 'valor': {'type': 'string'},
         'tarea': {'type': 'object'}}, 'required': ['accion']}},
    {'name': 'listar_fichas', 'description': 'Lista las fichas disponibles de fichas_qwen (n, id, nombre).',
     'inputSchema': {'type': 'object', 'properties': {}}},
    {'name': 'resultado', 'description': 'Consulta el estado de un proceso de chat asincrono.',
     'inputSchema': {'type': 'object', 'properties': {
         'proceso_id': {'type': 'string'}, 'espera': {'type': 'number'}}, 'required': ['proceso_id']}},
    {'name': 'github_leer', 'description': 'Lee un archivo o lista una carpeta en GitHub.',
     'inputSchema': {'type': 'object', 'properties': {
         'repo': {'type': 'string'}, 'ruta': {'type': 'string'},
         'rama': {'type': 'string'}, 'lineas': {'type': 'string'}}, 'required': ['repo']}},
    {'name': 'github_escribir', 'description': 'Crea o actualiza un archivo con commit en GitHub.',
     'inputSchema': {'type': 'object', 'properties': {
         'repo': {'type': 'string'}, 'ruta': {'type': 'string'},
         'contenido': {'type': 'string'}, 'mensaje': {'type': 'string'},
         'rama': {'type': 'string'}}, 'required': ['repo', 'ruta', 'contenido']}},
    {'name': 'github_api', 'description': 'Llama a la API de GitHub con permisos del token configurado.',
     'inputSchema': {'type': 'object', 'properties': {
         'metodo': {'type': 'string'}, 'ruta': {'type': 'string'},
         'cuerpo': {'type': 'object'}}, 'required': ['metodo', 'ruta']}},
]
GITHUB = {'github_leer': github.github_leer, 'github_escribir': github.github_escribir,
          'github_api': github.github_api}
FICHAS = {'listar_fichas': 'fichas', 'chat': 'chat_async', 'resultado': 'resultado'}


def _error(id_, codigo, mensaje):
    return {'jsonrpc': '2.0', 'id': id_, 'error': {'code': codigo, 'message': mensaje}}


def _ok(id_, resultado):
    return {'jsonrpc': '2.0', 'id': id_, 'result': resultado}


def _contenido(salida, error=False):
    if isinstance(salida, dict):
        return {'content': [{'type': 'text', 'text': json.dumps(salida, ensure_ascii=False)}],
                'structuredContent': salida, 'isError': error}
    return {'content': [{'type': 'text', 'text': str(salida)}], 'isError': error}


async def _herramienta(id_, params, chat, almacen, plugin_call):
    if not isinstance(params, dict) or not isinstance(params.get('arguments', {}), dict):
        return _error(id_, -32602, 'Parametros invalidos')
    nombre, args = params.get('name'), params.get('arguments', {})
    if nombre not in {t['name'] for t in HERRAMIENTAS}:
        return _error(id_, -32602, 'Herramienta no permitida')
    esquema = next(t['inputSchema'] for t in HERRAMIENTAS if t['name'] == nombre)
    for campo in esquema.get('required', []):
        if campo not in args or args[campo] is None:
            return _error(id_, -32602, 'Falta parametro: ' + campo)
    if nombre == 'chat':
        if args.get('ficha_qwen'):
            if args.get('modelo'):
                try:
                    modelos.validar(args['modelo'])
                except (ValueError, TypeError) as exc:
                    return _error(id_, -32602, str(exc))
            if not isinstance(args['ficha_qwen'], str):
                return _error(id_, -32602, 'ficha_qwen invalida')
        elif not isinstance(args.get('mensajes'), list) or not args['mensajes']:
            return _error(id_, -32602, 'mensajes debe ser lista no vacia')
    if nombre == 'resultado' and not isinstance(args.get('proceso_id'), str):
        return _error(id_, -32602, 'proceso_id invalido')
    if nombre in GITHUB and any(not isinstance(args.get(c), str) for c in esquema.get('required', [])):
        return _error(id_, -32602, 'Parametros invalidos')
    try:
        if nombre in GITHUB:
            texto = await asyncio.to_thread(GITHUB[nombre], args)
            return _ok(id_, _contenido(texto, str(texto).startswith(('ERROR', 'FALTA'))))
        if nombre in FICHAS and (nombre != 'chat' or args.get('ficha_qwen')):
            if plugin_call is None:
                return _error(id_, -32602, 'Servicio de fichas no disponible')
            respuesta = await plugin_call('fichas_qwen', FICHAS[nombre], args)
            salida = respuesta.get('result', respuesta) if isinstance(respuesta, dict) else respuesta
        else:
            if nombre == 'chat':
                args = {**args, 'modelo': modelos.validar(args.get('modelo'))}
            salida = await (chat(args) if nombre == 'chat' else almacen(args))
    except HTTPException as exc:
        return _error(id_, -32602 if exc.status_code == 400 else -32000, str(exc.detail))
    except (ValueError, TypeError) as exc:
        return _error(id_, -32602, str(exc))
    except RuntimeError as exc:
        return _ok(id_, _contenido('ERROR: ' + str(exc), True))
    return _ok(id_, _contenido(salida, isinstance(salida, dict) and bool(salida.get('error'))))


async def despachar(doc, chat, almacen, plugin_call=None):
    ident = doc.get('id') if isinstance(doc, dict) else None
    if not isinstance(doc, dict) or doc.get('jsonrpc') != '2.0':
        return _error(ident, -32600, 'Solicitud JSON-RPC invalida')
    metodo = doc.get('method')
    if not isinstance(metodo, str):
        return _error(ident, -32600, 'Metodo invalido')
    if metodo.startswith('notifications/'):
        return None
    if 'id' not in doc:
        return _error(None, -32600, 'Falta id')
    if metodo == 'initialize':
        return _ok(ident, {'protocolVersion': '2025-06-18', 'capabilities': {'tools': {}},
                           'serverInfo': {'name': 'riu-mvp', 'version': '1.0'}})
    if metodo == 'ping':
        return _ok(ident, {})
    if metodo == 'tools/list':
        return _ok(ident, {'tools': HERRAMIENTAS})
    if metodo == 'tools/call':
        return await _herramienta(ident, doc.get('params'), chat, almacen, plugin_call)
    return _error(ident, -32601, 'Metodo no disponible')


def montar(api, verificar, chat, almacen):
    # Reutilizar el handler del mismo FastAPI, sin peticiones HTTP al propio Router.
    plugin_call = next((ruta.endpoint for ruta in api.routes
                        if getattr(ruta, 'path', '') == '/plugins/{plugin}/call/{accion}'), None)

    async def endpoint(request: Request):
        try:
            doc = await request.json()
        except ValueError:
            return _error(None, -32700, 'JSON invalido')
        salida = await despachar(doc, chat, almacen, plugin_call)
        return Response(status_code=202) if salida is None else salida
    api.add_api_route('/mcp', endpoint, methods=['POST'], dependencies=[Depends(verificar)])
