"""MCP mínimo JSON-RPC 2.0: herramientas chat y almacén autenticadas."""
import json
from fastapi import Depends, HTTPException, Response
from mvp import modelos

HERRAMIENTAS = [
    {"name": "chat", "description": "Enviar mensajes al modelo de texto autorizado",
     "inputSchema": {"type": "object", "properties": {
         "mensajes": {"type": "array", "items": {"type": "object"}},
         "modelo": {"type": "string"}, "opciones": {"type": "object"},
         "via": {"type": "string"}}, "required": ["mensajes"]}},
    {"name": "almacen", "description": "Acceder al almacenamiento autorizado",
     "inputSchema": {"type": "object", "properties": {
         "accion": {"type": "string", "enum": ["guardar", "leer", "computar", "status"]},
         "destino": {"type": "string", "enum": ["hf", "harness"]},
         "nombre": {"type": "string"}, "valor": {"type": "string"},
         "tarea": {"type": "object"}}, "required": ["accion"]}},
]


def _error(id_, codigo, mensaje):
    return {"jsonrpc": "2.0", "id": id_, "error": {"code": codigo, "message": mensaje}}


def _ok(id_, resultado):
    return {"jsonrpc": "2.0", "id": id_, "result": resultado}


async def _herramienta(id_, params, chat, almacen):
    if not isinstance(params, dict) or not isinstance(params.get("arguments", {}), dict):
        return _error(id_, -32602, "Parametros invalidos")
    nombre, args = params.get("name"), params.get("arguments", {})
    if nombre not in ("chat", "almacen"):
        return _error(id_, -32602, "Herramienta no permitida")
    if nombre == "chat":
        try:
            modelo = modelos.validar(args.get("modelo"))
        except (ValueError, TypeError) as exc:
            return _error(id_, -32602, str(exc))
        args = {**args, "modelo": modelo}
    try:
        salida = await (chat(args) if nombre == "chat" else almacen(args))
    except HTTPException as exc:
        return _error(id_, -32602 if exc.status_code == 400 else -32000, str(exc.detail))
    except (ValueError, TypeError) as exc:
        return _error(id_, -32602, str(exc))
    return _ok(id_, {"content": [{"type": "text", "text": json.dumps(salida, ensure_ascii=False)}],
                      "structuredContent": salida})


async def despachar(doc, chat, almacen):
    ident = doc.get("id") if isinstance(doc, dict) else None
    if not isinstance(doc, dict) or doc.get("jsonrpc") != "2.0":
        return _error(ident, -32600, "Solicitud JSON-RPC invalida")
    metodo = doc.get("method")
    if not isinstance(metodo, str):
        return _error(ident, -32600, "Metodo invalido")
    if metodo.startswith("notifications/"):
        return None
    if "id" not in doc:
        return _error(None, -32600, "Falta id")
    if metodo == "initialize":
        return _ok(ident, {"protocolVersion": "2025-06-18", "capabilities": {"tools": {}},
                           "serverInfo": {"name": "riu-mvp", "version": "1.0"}})
    if metodo == "ping":
        return _ok(ident, {})
    if metodo == "tools/list":
        return _ok(ident, {"tools": HERRAMIENTAS})
    if metodo == "tools/call":
        return await _herramienta(ident, doc.get("params"), chat, almacen)
    return _error(ident, -32601, "Metodo no disponible")


def montar(api, verificar, chat, almacen):
    async def endpoint(doc: dict):
        salida = await despachar(doc, chat, almacen)
        return Response(status_code=202) if salida is None else salida
    api.add_api_route("/mcp", endpoint, methods=["POST"], dependencies=[Depends(verificar)])
