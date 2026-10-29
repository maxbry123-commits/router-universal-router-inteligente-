"""Enchufe PluginHost del Watchdog48 (nct_addons.watchdog48).
Observa y registra; no ejecuta tareas. queue_observer lee SOLO estado de la
Cola CIT-50 (mismo archivo SQLite, lectura via QueueStore.get).
POST /plugins/watchdog48/call/<accion>.
"""
from __future__ import annotations

import asyncio
import importlib.util
import threading
from pathlib import Path
from typing import Any

_DIR = Path(__file__).resolve().parent
_STATE = _DIR / 'state'
_STATE.mkdir(exist_ok=True)
_DB = _STATE / 'watchdog48.db'
_COLA_DIR = _DIR.parent / 'Cola'
_COLA_DB = _COLA_DIR / 'state' / 'cola50.db'


def _mod(nombre: str, ruta: Path):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


_core = _mod('watchdog48_core', _DIR / 'nct_addons' / 'watchdog48' / 'core.py')
_cola_core = _mod('cola50_core_obs', _COLA_DIR / 'nct_addons' / 'cola50' / 'core.py')
_STORE = None
_COLA = None
_WORKER = {'thread': None, 'worker': None}


def _store():
    global _STORE
    if _STORE is None:
        _STORE = _core.WatchStore(_DB)
    return _STORE


def _cola():
    global _COLA
    if _COLA is None:
        _COLA = _cola_core.QueueStore(_COLA_DB)
    return _COLA


def _observer(tid: str):
    """Lectura del estado de la cola para el watchdog; nunca ejecuta ni modifica."""
    try:
        return _cola().get(tid)
    except Exception:  # noqa: BLE001
        return None


def _worker_run(intervalo: int) -> None:
    loop = asyncio.new_event_loop()
    w = _core.WatchWorker(_store(), queue_observer=_observer, interval=intervalo)
    _WORKER['worker'] = w
    loop.run_until_complete(w.run())


def handle(action: str, payload: "dict | None" = None) -> dict:
    p = payload or {}
    s = _store()
    try:
        if action in ('status', 'health'):
            return {'ok': True, 'service': 'watchdog48', 'db': _DB.name,
                    'worker': bool(_WORKER['thread'] and _WORKER['thread'].is_alive())}
        if action == 'crear':
            return s.create(p)
        if action == 'listar':
            return {'watches': s.list()}
        if action == 'estado':
            return s.get(str(p.get('wid') or p.get('watch_id') or ''))
        if action == 'eventos':
            return {'events': s.events(str(p.get('wid') or ''), int(p.get('after') or 0))}
        if action == 'heartbeat':
            return s.heartbeat(str(p.get('wid') or ''), str(p.get('progress_id') or ''))
        if action == 'accion':
            sub = str(p.get('sub') or '')
            if sub not in ('pause', 'resume', 'cancel'):
                return {'error': 'accion.sub desconocido (pause|resume|cancel)'}
            return s.control(str(p.get('wid') or ''), sub)
        if action == 'tick':
            return {'result': s.tick(queue_observer=_observer)}
        if action == 'worker':
            sub = str(p.get('sub') or 'estado')
            if sub == 'estado':
                return {'ok': True, 'activo': bool(_WORKER['thread'] and _WORKER['thread'].is_alive())}
            if sub == 'start':
                if _WORKER['thread'] and _WORKER['thread'].is_alive():
                    return {'ok': True, 'activo': True, 'ya_activo': True}
                hilo = threading.Thread(target=_worker_run, args=(int(p.get('interval') or 5),),
                                        daemon=True, name='watchdog48-worker')
                hilo.start()
                _WORKER['thread'] = hilo
                return {'ok': True, 'activo': True}
            if sub == 'stop':
                w = _WORKER.get('worker')
                if w is not None:
                    w.stop()
                return {'ok': True, 'activo': False}
            return {'error': 'worker.sub desconocido (start|stop|estado)'}
        return {'error': 'ACCION_DESCONOCIDA', 'allowed': ACCIONES}
    except _core.WatchError as e:
        return {'error': str(e), 'status': e.status}


ACCIONES = ['status', 'health', 'crear', 'listar', 'estado', 'eventos', 'heartbeat',
            'accion', 'tick', 'worker']
