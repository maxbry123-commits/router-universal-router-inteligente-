"""MCP JSON-RPC 2.0 del Router MVP: un endpoint y autenticacion compartida."""
import asyncio
import json
from fastapi import Depends, HTTPException, Request, Response
from mvp import control as permisos, mcp_cliente, modelos
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
# Herramientas del chat que solo existen con estado de servidor (mvp/control.py); se exponen cuando montar() recibe el control.
HERRAMIENTAS_CONTROL = [
    {'name': 'pendientes', 'description': 'Checklist de pendientes: listar, agregar, marcar, ordenar o quitar.',
     'inputSchema': {'type': 'object', 'properties': {
         'accion': {'type': 'string', 'enum': ['listar', 'agregar', 'marcar', 'ordenar', 'quitar']},
         'id': {'type': 'string'}, 'texto': {'type': 'string'}, 'hecho': {'type': 'boolean'},
         'ids': {'type': 'array', 'items': {'type': 'string'}}}, 'required': ['accion']}},
    {'name': 'sala', 'description': 'ROOM CONFERENCIAS: salas compartidas con participantes, mensajes, contexto y permisos de acceso.',
     'inputSchema': {'type': 'object', 'properties': {
         'accion': {'type': 'string', 'enum': ['crear', 'listar', 'leer', 'enviar', 'contexto', 'permiso']},
         'id': {'type': 'string'}, 'nombre': {'type': 'string'}, 'texto': {'type': 'string'},
         'participante': {'type': 'string'}, 'nivel': {'type': 'string', 'enum': ['lectura', 'escritura', 'admin']},
         'participantes': {'type': 'object'}}, 'required': ['accion']}},
]
HERRAMIENTAS_CONTROL += [
    {'name': 'agente', 'description': 'Delegar una tarea en un agente conectado (cada llamada es una sesion de chat nueva con su modelo y sus instrucciones).',
     'inputSchema': {'type': 'object', 'properties': {'nombre': {'type': 'string'}, 'mensaje': {'type': 'string'}}, 'required': ['nombre', 'mensaje']}},
    {'name': 'llm', 'description': 'Preguntar a otro modelo de texto del plan y recibir su respuesta.',
     'inputSchema': {'type': 'object', 'properties': {'modelo': {'type': 'string'}, 'mensaje': {'type': 'string'}}, 'required': ['modelo', 'mensaje']}},
]
HERRAMIENTAS_CONTROL.append({'name': 'yaiwes_md', 'description': 'yaiwes.md: informacion del proyecto compartida entre el Director y los modelos. accion leer o escribir (reemplaza el texto completo).',
     'inputSchema': {'type': 'object', 'properties': {'accion': {'type': 'string', 'enum': ['leer', 'escribir']}, 'texto': {'type': 'string'}}, 'required': ['accion']}})
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


def _gestionada(nombre):
    return nombre in permisos.TOOLS or nombre.startswith('mcp__')


def _catalogo(control):
    if control is None:
        return HERRAMIENTAS
    visibles = set(control.visibles())  # solo las encendidas y con conexion activa
    externas = [{'name': permisos.MCP_NOMBRE(c, h), 'description': '[' + c['etiqueta'] + '] ' + h['descripcion'], 'inputSchema': h['esquema']}
                for c in control.d['conexiones']['mcp'] for h in c.get('herramientas', [])]
    return [t for t in [*HERRAMIENTAS, *HERRAMIENTAS_CONTROL, *externas] if t['name'] in visibles or not _gestionada(t['name'])]


async def _herramienta(id_, params, chat, almacen, plugin_call, control=None, banco=None, delegar=None):
    if not isinstance(params, dict) or not isinstance(params.get('arguments', {}), dict):
        return _error(id_, -32602, 'Parametros invalidos')
    nombre, args = params.get('name'), params.get('arguments', {})
    catalogo = _catalogo(control)
    if nombre not in {t['name'] for t in catalogo}:
        motivo = control.decidir(nombre)[1] if control and isinstance(nombre, str) else ''
        return _error(id_, -32000 if motivo else -32602, 'Herramienta bloqueada: ' + motivo if motivo else 'Herramienta no permitida')
    if control is not None and _gestionada(nombre):  # vuelve a comprobar el permiso al ejecutar
        permitido, motivo = control.decidir(nombre)
        if not permitido:
            return _error(id_, -32000, 'Herramienta bloqueada: ' + motivo)
    esquema = next(t['inputSchema'] for t in catalogo if t['name'] == nombre)
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
        if nombre in ('pendientes', 'sala', 'yaiwes_md'):
            salida = await control.aplicar({'pendientes': 'checklist', 'sala': 'salas', 'yaiwes_md': 'handoff_texto'}[nombre], args, banco, 'modelo')
            return _ok(id_, _contenido(salida))
        if nombre in ('agente', 'llm'):
            return _ok(id_, _contenido(await delegar(nombre, args)))
        if nombre.startswith('mcp__'):
            con = next(c for c in control.d['conexiones']['mcp'] if c['id'] == nombre[5:13])
            respuesta = await asyncio.to_thread(mcp_cliente.llamar, con['url'], banco.leer(permisos._clave_banco('mcp', con['id'])) if banco else None, nombre[15:], args)
            return _ok(id_, _contenido(respuesta['texto'], respuesta['error']))
        if nombre in ("github_leer", "github_escribir") and "/" in args["repo"]:
            dueno, repo = args["repo"].split("/", 1)
            if dueno != github.OWNER or not repo or "/" in repo:
                return _error(id_, -32602, "Repositorio fuera de la cuenta GitHub configurada")
            args = {**args, "repo": repo}
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
    except PermissionError as exc:
        return _ok(id_, _contenido('ERROR: ' + str(exc), True))
    except HTTPException as exc:
        return _error(id_, -32602 if exc.status_code == 400 else -32000, str(exc.detail))
    except (ValueError, TypeError) as exc:
        return _error(id_, -32602, str(exc))
    except RuntimeError as exc:
        return _ok(id_, _contenido('ERROR: ' + str(exc), True))
    return _ok(id_, _contenido(salida, isinstance(salida, dict) and bool(salida.get('error'))))


async def despachar(doc, chat, almacen, plugin_call=None, control=None, banco=None, delegar=None):
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
        return _ok(ident, {'tools': _catalogo(control)})
    if metodo == 'tools/call':
        return await _herramienta(ident, doc.get('params'), chat, almacen, plugin_call, control, banco, delegar)
    return _error(ident, -32601, 'Metodo no disponible')


def montar(api, verificar, chat, almacen, control=None, delegar=None):
    def token_github():
        banco = getattr(api.state, 'banco', None)
        if control is not None:
            return control.credencial('github', banco)  # primera conexion GitHub ON
        token = banco.leer('GITHUB_TOKEN') if banco else None
        if not token:
            raise RuntimeError('GITHUB_TOKEN no disponible en banco')
        return token
    github._token = token_github
    # Reutilizar el handler del mismo FastAPI, sin peticiones HTTP al propio Router.
    plugin_call = next((ruta.endpoint for ruta in api.routes
                        if getattr(ruta, 'path', '') == '/plugins/{plugin}/call/{accion}'), None)

    async def endpoint(request: Request):
        try:
            doc = await request.json()
        except ValueError:
            return _error(None, -32700, 'JSON invalido')
        salida = await despachar(doc, chat, almacen, plugin_call, control, getattr(api.state, 'banco', None), delegar)
        return Response(status_code=202) if salida is None else salida
    api.add_api_route('/mcp', endpoint, methods=['POST'], dependencies=[Depends(verificar)])
