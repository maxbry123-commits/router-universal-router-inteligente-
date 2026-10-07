"""Tres mecanismos de recuperación de estado para el sentinela."""
from __future__ import annotations

import json
import time
from copy import deepcopy


def checkpoint_local(cache, sesion, mensajes=None):
    """Motor 1: snapshot de proceso, independiente por sesión."""
    if mensajes is not None:
        cache[sesion] = deepcopy(mensajes)
    valor = cache.get(sesion)
    return deepcopy(valor) if valor else None


def checkpoint_persistente(mem, scope, sesion, mensajes=None):
    """Motor 2: read-back de la memoria del Router; no inventa un checkpoint."""
    clave = 'checkpoint'
    if mensajes is not None:
        mem.save(scope, clave, {'mensajes': deepcopy(mensajes), 'guardado_ns': time.time_ns()})
        return deepcopy(mensajes)
    res = mem.search(scope, clave, 5)
    filas = res if isinstance(res, list) else next((v for v in (res or {}).values() if isinstance(v, list)), [])
    validos = [(f.get('data', f) if isinstance(f, dict) else f) for f in filas]
    validos = [d for d in validos if isinstance(d, dict) and isinstance(d.get('mensajes'), list)]
    if validos:
        ultimo = max(enumerate(validos), key=lambda par: (par[1].get('guardado_ns', 0), par[0]))[1]
        return deepcopy(ultimo['mensajes'])
    return None


def reconstruir_herramientas(mensajes):
    """Motor 3: rehidrata resultados de herramientas ya confirmados en el diálogo."""
    solicitudes = {}
    resultados = {}
    for m in mensajes:
        if m.get('role') == 'assistant':
            for call in m.get('tool_calls') or []:
                f = call.get('function') or {}
                try:
                    args = json.loads(f.get('arguments') or '{}')
                except (ValueError, TypeError):
                    args = {}
                solicitudes[call.get('id')] = (f.get('name', ''), json.dumps(args, sort_keys=True, default=str))
        if m.get('role') == 'tool' and m.get('tool_call_id') in solicitudes:
            resultados[solicitudes[m['tool_call_id']]] = m.get('content') or ''
    return resultados
