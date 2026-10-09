"""Runtime nativo XRAY-V2.

El DSL/DAG ya no se envia al modelo como prompt. Este modulo ejecuta en Python
los estados y compuertas del workflow de cada nodo. La tarea del usuario se
conserva verbatim en memoria del runtime y el modelo recibe solo tarea/rol/
dependencias desde FichaOS.
"""
from __future__ import annotations

import hashlib
from threading import local
from time import time

_CTX = local()
MAX_FIXES = 2

TERMINALES = {'CLOSED', 'BLOCKED'}
TRANSICIONES = {
    'PENDING': {'RESEARCHING', 'EXECUTING', 'VALIDATING', 'BLOCKED'},
    'RESEARCHING': {'RESEARCH_PASS', 'BLOCKED'},
    'RESEARCH_PASS': {'CLOSED', 'BLOCKED'},
    'EXECUTING': {'EXECUTION_PASS', 'BLOCKED'},
    'EXECUTION_PASS': {'CLOSED', 'GAP', 'BLOCKED'},
    'VALIDATING': {'STABLE', 'GAP', 'BLOCKED'},
    'GAP': {'FIXING', 'BLOCKED'},
    'FIXING': {'RETESTING', 'BLOCKED'},
    'RETESTING': {'VALIDATING', 'BLOCKED'},
    'STABLE': {'CLOSED', 'GAP', 'BLOCKED'},
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


def _hash_texto(texto: str) -> str:
    return hashlib.sha256(texto.encode('utf-8')).hexdigest()


def _hash_scope(read_paths, write_paths) -> str:
    base = '\n'.join(['R:' + str(x) for x in read_paths] + ['W:' + str(x) for x in write_paths])
    return hashlib.sha256(base.encode('utf-8')).hexdigest()


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
    reads = tuple(nodo.get('read_paths') or ())
    writes = tuple(rutas or ())
    ctx = {
        'nodo': str(nodo.get('id') or ''),
        'task_id': str(task_id),
        'paso': int(paso),
        'rol': str(nodo.get('rol') or ''),
        'raw_input': raw_input,
        'read_paths': reads,
        'write_paths': writes,
        'objective_lock': _hash_texto(raw_input),
        'scope_lock': _hash_scope(reads, writes),
        'requiere_evidencia': bool(nodo.get('requiere_evidencia')),
        'fase': _fase(str(nodo.get('rol') or '')),
        'estado': 'PENDING',
        'historial': [{'estado': 'PENDING', 'ts': time()}],
        'llamadas': 0,
        'fixes': 0,
        'gap': None,
    }
    _CTX.nodo = ctx
    return ctx


def validar_locks(nodo: dict, raw_input: str, rutas: list[str]) -> None:
    """Goal-lock + scope-lock deterministas antes de ejecutar el nodo."""
    ctx = getattr(_CTX, 'nodo', None)
    if not ctx:
        raise RuntimeXrayError('XRAY_SIN_BIND')
    reads = tuple(nodo.get('read_paths') or ())
    writes = tuple(rutas or ())
    if _hash_texto(raw_input) != ctx['objective_lock']:
        if ctx['estado'] not in TERMINALES:
            _mover('BLOCKED')
        raise RuntimeXrayError('OBJECTIVE_LOCK_VIOLADO')
    if _hash_scope(reads, writes) != ctx['scope_lock']:
        if ctx['estado'] not in TERMINALES:
            _mover('BLOCKED')
        raise RuntimeXrayError('SCOPE_LOCK_VIOLADO')


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
    """Cierra la fase del modelo; la evidencia real sigue siendo compuerta aparte."""
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
        if not ctx['requiere_evidencia']:
            _mover('CLOSED')
    elif estado == 'VALIDATING':
        _mover('STABLE')
        if not ctx['requiere_evidencia']:
            _mover('CLOSED')


def registrar_evidencia(ok: bool, motivo: str = '') -> bool:
    """PASS real cierra; evidencia ausente/incompleta deja GAP fail-closed."""
    ctx = getattr(_CTX, 'nodo', None)
    if not ctx or not ctx.get('requiere_evidencia'):
        return bool(ok)
    if ok:
        if ctx['estado'] in ('EXECUTION_PASS', 'STABLE'):
            _mover('CLOSED')
        elif ctx['estado'] != 'CLOSED':
            raise RuntimeXrayError('EVIDENCIA_EN_ESTADO_INVALIDO:' + ctx['estado'])
        ctx['gap'] = None
        return True
    ctx['gap'] = str(motivo or 'EVIDENCIA_NO_PASS')
    if ctx['estado'] in ('EXECUTION_PASS', 'VALIDATING', 'STABLE'):
        _mover('GAP')
    elif ctx['estado'] not in ('GAP', 'BLOCKED'):
        _mover('BLOCKED')
    return False


def iniciar_fix() -> int:
    """GAP -> FIXING, maximo dos ciclos. No llama a la LLM por si solo."""
    ctx = getattr(_CTX, 'nodo', None)
    if not ctx or ctx['estado'] != 'GAP':
        raise RuntimeXrayError('FIX_SIN_GAP')
    if ctx['fixes'] >= MAX_FIXES:
        _mover('BLOCKED')
        raise RuntimeXrayError('MAX_FIXES_XRAY')
    ctx['fixes'] += 1
    _mover('FIXING')
    return ctx['fixes']


def iniciar_retest() -> None:
    """FIXING -> RETESTING -> VALIDATING, sin prompt DSL."""
    ctx = getattr(_CTX, 'nodo', None)
    if not ctx or ctx['estado'] != 'FIXING':
        raise RuntimeXrayError('RETEST_SIN_FIX')
    _mover('RETESTING')
    _mover('VALIDATING')


def snapshot() -> dict:
    ctx = getattr(_CTX, 'nodo', None)
    if not ctx:
        return {}
    return {k: v for k, v in ctx.items() if k != 'raw_input'}
