"""Runtime nativo XRAY-V2.

El DSL/DAG ya no se envia al modelo como prompt. Este modulo ejecuta en Python
los estados y compuertas basicas del workflow de cada nodo. La tarea del usuario
se conserva verbatim en memoria del runtime y el modelo recibe solo tarea/rol/
dependencias desde FichaOS.
"""
from __future__ import annotations

from threading import local
from time import time

_CTX = local()

TERMINALES = {'CLOSED', 'BLOCKED'}
TRANSICIONES = {
    'PENDING': {'RESEARCHING', 'EXECUTING', 'VALIDATING', 'BLOCKED'},
    'RESEARCHING': {'RESEARCH_PASS', 'BLOCKED'},
    'RESEARCH_PASS': {'CLOSED', 'BLOCKED'},
    'EXECUTING': {'EXECUTION_PASS', 'BLOCKED'},
    'EXECUTION_PASS': {'CLOSED', 'BLOCKED'},
    'VALIDATING': {'STABLE', 'GAP', 'BLOCKED'},
    'GAP': {'FIXING', 'BLOCKED'},
    'FIXING': {'RETESTING', 'BLOCKED'},
    'RETESTING': {'VALIDATING', 'BLOCKED'},
    'STABLE': {'CLOSED'},
    'CLOSED': set(),
    'BLOCKED': set(),
}


class RuntimeXrayError(RuntimeError):
    pass


def _fase(rol: str) -> str:
    r = (rol or '').lower()
    if any(x in r for x in ('revisa', 'valida', 'refactor')):
        return 'VALIDATING'
    if any(x in r for x in ('ejecuta', 'ejecutor', 'responde la tarea')):
        return 'EXECUTING'
    return 'RESEARCHING'


def _mover(nuevo: str) -> None:
    ctx = getattr(_CTX, 'nodo', None)
    if not ctx:
        return
    actual = ctx['estado']
    if nuevo not in TRANSICIONES.get(actual, set()):
        raise RuntimeXrayError('TRANSICION_XRAY_INVALIDA:%s->%s' % (actual, nuevo))
    ctx['estado'] = nuevo
    ctx['historial'].append({'estado': nuevo, 'ts': time()})


def bind_node(nodo: dict, task_id: str, raw_input: str, paso: int, rutas: list[str]) -> dict:
    """CAPTURE -> FREEZE_VERBATIM -> BIND_AS_TASK, sin transformar el input."""
    if raw_input is None:
        raise RuntimeXrayError('INPUT_AUSENTE')
    ctx = {
        'nodo': str(nodo.get('id') or ''),
        'task_id': str(task_id),
        'paso': int(paso),
        'rol': str(nodo.get('rol') or ''),
        'raw_input': raw_input,  # referencia exacta; no trim, no slice, no rewrite
        'read_paths': tuple(nodo.get('read_paths') or ()),
        'write_paths': tuple(rutas or ()),
        'fase': _fase(str(nodo.get('rol') or '')),
        'estado': 'PENDING',
        'historial': [{'estado': 'PENDING', 'ts': time()}],
        'llamadas': 0,
        'gap': None,
    }
    _CTX.nodo = ctx
    return ctx


def iniciar_modelo() -> None:
    """Compuerta nativa antes de entregar la tarea al modelo."""
    ctx = getattr(_CTX, 'nodo', None)
    if not ctx:
        return
    if ctx['estado'] in TERMINALES:
        raise RuntimeXrayError('NODO_TERMINAL:' + ctx['estado'])
    if ctx['estado'] == 'PENDING':
        _mover(ctx['fase'])
    ctx['llamadas'] += 1


def cerrar_modelo(ok: bool, motivo: str = '') -> None:
    """Cierra la fase del nodo. FAIL-CLOSED: error => BLOCKED."""
    ctx = getattr(_CTX, 'nodo', None)
    if not ctx:
        return
    if not ok:
        ctx['gap'] = str(motivo or 'MODELO_NO_COMPLETO')
        if ctx['estado'] not in TERMINALES:
            _mover('BLOCKED')
        return
    estado = ctx['estado']
    if estado == 'RESEARCHING':
        _mover('RESEARCH_PASS')
        _mover('CLOSED')
    elif estado == 'EXECUTING':
        _mover('EXECUTION_PASS')
        _mover('CLOSED')
    elif estado == 'VALIDATING':
        _mover('STABLE')
        _mover('CLOSED')


def snapshot() -> dict:
    ctx = getattr(_CTX, 'nodo', None)
    if not ctx:
        return {}
    return {k: v for k, v in ctx.items() if k != 'raw_input'}
