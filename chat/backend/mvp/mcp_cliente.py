"""Cliente MCP (JSON-RPC 2.0 sobre HTTP) para servidores externos; sin dependencias. El token se usa solo aqui, en el servidor."""
import ipaddress
import json
import os
import socket
from urllib import error, parse, request

PROTOCOLO = "2025-06-18"


def _validar(url):
    p = parse.urlsplit(url if isinstance(url, str) else "")
    local = os.environ.get("MVP_MCP_LOCAL") == "1" and p.scheme == "http" and p.hostname in ("127.0.0.1", "localhost")
    if not local:
        if p.scheme != "https" or not p.hostname:
            raise ValueError("URL MCP requiere HTTPS")
        try:
            ips = {ipaddress.ip_address(i[4][0]) for i in socket.getaddrinfo(p.hostname, p.port or 443)}
        except OSError:
            raise RuntimeError("Servidor MCP no disponible") from None
        if any(i.is_private or i.is_loopback or i.is_link_local or i.is_reserved for i in ips):
            raise ValueError("URL MCP apunta a una red privada")
    return url


def _rpc(url, token, metodo, params=None, ident=1):
    cabeceras = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    if token:
        cabeceras["Authorization"] = "Bearer " + token
    cuerpo = json.dumps({"jsonrpc": "2.0", "id": ident, "method": metodo, "params": params or {}}).encode()
    solicitud = request.Request(_validar(url), data=cuerpo, headers=cabeceras, method="POST")
    try:
        with request.urlopen(solicitud, timeout=30) as r:
            crudo = r.read(2_000_000).decode("utf-8", "replace")
            if "text/event-stream" in r.headers.get("Content-Type", ""):
                crudo = next((l[5:].strip() for l in crudo.splitlines() if l.startswith("data:")), "{}")
            doc = json.loads(crudo)
    except error.HTTPError as exc:
        raise RuntimeError("Servidor MCP HTTP " + str(exc.code)) from None
    except (error.URLError, TimeoutError, OSError):
        raise RuntimeError("Servidor MCP no disponible") from None
    except ValueError:
        raise RuntimeError("Servidor MCP respuesta invalida") from None
    if not isinstance(doc, dict) or doc.get("error"):
        raise RuntimeError("Servidor MCP error: " + str((doc.get("error") or {}).get("message") if isinstance(doc, dict) else "invalido")[:120])
    return doc.get("result") or {}


def listar(url, token=None):
    _rpc(url, token, "initialize", {"protocolVersion": PROTOCOLO, "capabilities": {}, "clientInfo": {"name": "riu-mvp", "version": "1.0"}})
    return [{"nombre": t["name"], "descripcion": t.get("description", ""), "esquema": t.get("inputSchema") or {"type": "object"}}
            for t in _rpc(url, token, "tools/list", ident=2).get("tools", []) if isinstance(t, dict) and isinstance(t.get("name"), str)]


def llamar(url, token, nombre, argumentos):
    resultado = _rpc(url, token, "tools/call", {"name": nombre, "arguments": argumentos or {}}, ident=3)
    texto = "\n".join(c.get("text", "") for c in resultado.get("content", []) if isinstance(c, dict) and c.get("type") == "text")
    return {"texto": texto[:20000], "error": bool(resultado.get("isError"))}
