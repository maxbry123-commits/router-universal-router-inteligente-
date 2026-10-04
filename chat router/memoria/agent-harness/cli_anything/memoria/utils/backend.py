'''Backend del harness de memoria: habla con los motores por HTTP (contrato de ComponentAdapter) o TCP. Solo libreria estandar.'''
from __future__ import annotations

import json
import os
import socket
import urllib.parse
import urllib.request

# motor -> (variable de entorno, tipo, solo_lectura, detalle si no esta conectado)
MOTORES = {
    'agentdb': ('RIU_AGENTDB_URL', 'http', False, 'sin servicio: arrancar memoria/motores/levantar_motores.sh'),
    'graphiti': ('RIU_GRAPHITI_URL', 'http', False, 'sin servicio: arrancar memoria/motores/levantar_motores.sh'),
    'graphify': ('RIU_GRAPHIFY_URL', 'http', True, 'sin servicio: arrancar memoria/motores/levantar_motores.sh'),
    'memanto': ('RIU_MEMANTO_URL', 'http', False, 'GAP: su motor es el servidor Moorcheh (nube o Docker+Ollama); sin ese servidor no hay motor'),
    'falkordb': ('RIU_FALKORDB_HTTP_URL', 'http', False, 'sin servicio: memoria/motores/compilar_motores.sh y levantar_motores.sh'),
    'postgresql': ('RIU_POSTGRESQL_HTTP_URL', 'http', False, 'sin servicio: memoria/motores/compilar_motores.sh y levantar_motores.sh'),
}
ORDEN = ['agentdb', 'graphiti', 'graphify', 'memanto', 'falkordb', 'postgresql']  # prioridad fija: hace el resultado determinista


def url(motor: str) -> str:
    return os.environ.get(MOTORES[motor][0], '')


def http(motor: str, method: str, path: str, payload=None, params=None, timeout: float = 15):
    base = url(motor)
    if not base:
        raise RuntimeError('sin URL')
    q = ('?' + urllib.parse.urlencode(params)) if params else ''
    data = json.dumps(payload).encode('utf-8') if payload is not None else None
    req = urllib.request.Request(base.rstrip('/') + path + q, data=data, method=method, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 URL de un motor local configurado por el operador
        return json.loads(r.read().decode('utf-8') or 'null')


def tcp_probe(u: str, timeout: float = 3) -> None:
    p = urllib.parse.urlparse(u)
    socket.create_connection((p.hostname or '127.0.0.1', p.port or 0), timeout=timeout).close()


def estado(motor: str) -> dict:
    env, tipo, solo_lectura, detalle = MOTORES[motor]
    u = os.environ.get(env, '')
    if not u:
        return {'motor': motor, 'estado': 'GAP', 'solo_lectura': solo_lectura, 'detalle': detalle}
    try:
        if tipo == 'http':
            h = http(motor, 'GET', '/')
            info = (h.get('modo') or h.get('engine') or 'http') if isinstance(h, dict) else 'http'
        else:
            tcp_probe(u)
            info = 'tcp'
        return {'motor': motor, 'estado': 'CONNECTED', 'solo_lectura': solo_lectura, 'detalle': info}
    except Exception as exc:  # noqa: BLE001
        return {'motor': motor, 'estado': 'GAP', 'solo_lectura': solo_lectura, 'detalle': 'inalcanzable: ' + type(exc).__name__}
