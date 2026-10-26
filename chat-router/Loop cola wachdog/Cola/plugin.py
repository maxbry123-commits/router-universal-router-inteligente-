"""Enchufe PluginHost de la Cola CIT-50 (nct_addons.cola50).
NO duplica el Router ni crea colas nuevas: expone el QueueStore existente por
POST /plugins/cola50/call/<accion>. Los modelos entran por callback externo
(model_call -> plugins.puente_chat.plugin._chat, el mismo cableado del chat);
Ricardo ejecuta ops por motor_cli en un workspace confinado.
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
_DB = _STATE / 'cola50.db'
_WS = _STATE / 'workspaces'
_MOTOR = _DIR.parent / 'Loop' / 'referencia_ricardo' / 'motor_cli.py'
_POLICY = _DIR.parent / 'Loop' / 'referencia_ricardo' / 'allowed_ops.json'


def _mod(nombre: str, ruta: Path):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


_core = _mod('cola50_core', _DIR / 'nct_addons' / 'cola50' / 'core.py')
_motor_mod = None
_STORE = None
_WORKER = {'thread': None, 'worker': None, 'loop': None}


def _store():
    global _STORE
    if _STORE is None:
        _STORE = _core.QueueStore(_DB)
    return _STORE


def _motor():
    global _motor_mod
    if _motor_mod is None:
        _motor_mod = _mod('ricardo_motor_cli', _MOTOR)
    return _motor_mod


def _chat_modelo(modelo: str, prompt: str, sesion: str) -> dict:
    from plugins.puente_chat import plugin as _pc
    return _pc._chat({'model': modelo, 'messages': [{'role': 'user', 'content': prompt}], 'sesion': sesion})


async def _model_call(q: dict, t: dict) -> dict:
    modelo = str(t.get('model') or q.get('model') or 'ficha-qwen38flash')
    prompt = str(t.get('prompt') or t.get('title') or '')
    r = await asyncio.to_thread(_chat_modelo, modelo, prompt, str(q.get('chat_id') or 'cit50'))
    if isinstance(r, dict) and r.get('error'):
        raise _core.QueueError('model_call: ' + str(r['error']))
    txt = ''
    if isinstance(r, dict):
        txt = str(r.get('reply') or r.get('texto')
                  or ((r.get('choices') or [{}])[0].get('message') or {}).get('content') or '')
    return {'texto': txt, 'finish_reason': (r or {}).get('finish_reason') if isinstance(r, dict) else None}


async def _ricardo_call(q: dict, t: dict) -> dict:
    mm = _motor()
    import json as _json
    policy = _json.loads(_POLICY.read_text(encoding='utf-8'))
    ws = _WS / str(q.get('queue_id') or 'cola')
    ws.mkdir(parents=True, exist_ok=True)
    ops = t.get('ops') or t.get('payload', {}).get('ops') or []
    if not isinstance(ops, list) or not ops:
        raise _core.QueueError('ricardo sin ops')
    doc = {'meta': {'name': str(t['id'])[:48]}, 'ops': ops}
    rep = await asyncio.to_thread(mm.Motor(ws, policy).run, doc)
    rep['verified'] = bool(rep.get('ok'))
    return rep


def _worker_run(modelo: str, sesion: str) -> None:
    loop = asyncio.new_event_loop()
    _WORKER['loop'] = loop

    async def mc(q, t):
        if modelo:
            t = dict(t, model=modelo)
        return await _model_call(q, t)

    w = _core.QueueWorker(_store(), mc, _ricardo_call, interval=1)
    _WORKER['worker'] = w
    try:
        loop.run_until_complete(w.run())
    finally:
        loop.close()


def handle(action: str, payload: "dict | None" = None) -> dict:
    p = payload or {}
    s = _store()
    try:
        if action in ('status', 'health'):
            return {'ok': True, 'service': 'cit50', 'db': _DB.name,
                    'worker': bool(_WORKER['thread'] and _WORKER['thread'].is_alive())}
        if action == 'crear':
            return s.create(p)
        if action == 'listar':
            return {'queues': s.list(p.get('chat_id'))}
        if action == 'estado':
            return s.get(str(p.get('qid') or p.get('queue_id') or ''))
        if action == 'eventos':
            return {'events': s.events(str(p.get('qid') or ''), int(p.get('after') or 0))}
        if action == 'tarea':
            sub = str(p.get('sub') or '')
            qid = str(p.get('qid') or '')
            if sub == 'agregar':
                return s.add_task(qid, p.get('task') or {}, int(p.get('revision') or 0))
            if sub == 'editar':
                return s.edit_task(qid, str(p.get('task_id') or ''), p.get('updates') or {}, int(p.get('revision') or 0))
            if sub == 'quitar':
                return s.remove_task(qid, str(p.get('task_id') or ''), int(p.get('revision') or 0))
            return {'error': 'tarea.sub desconocido (agregar|editar|quitar)'}
        if action == 'orden':
            return s.reorder(str(p.get('qid') or ''), p.get('order') or [], int(p.get('revision') or 0))
        if action == 'draft':
            return s.replace_draft(str(p.get('qid') or ''), p.get('body') or {}, int(p.get('revision') or 0))
        if action == 'aprobar':
            return s.approve(str(p.get('qid') or ''), str(p.get('task_id') or ''))
        if action == 'accion':
            sub = str(p.get('sub') or '')
            qid = str(p.get('qid') or '')
            if sub == 'start':
                return s.start(qid, seconds=int(p.get('seconds') or 3600))
            if sub in ('pause', 'resume', 'cancel'):
                return s.control(qid, sub)
            return {'error': 'accion.sub desconocido (start|pause|resume|cancel)'}
        if action == 'worker':
            sub = str(p.get('sub') or 'estado')
            if sub == 'estado':
                return {'ok': True, 'activo': bool(_WORKER['thread'] and _WORKER['thread'].is_alive())}
            if sub == 'start':
                if _WORKER['thread'] and _WORKER['thread'].is_alive():
                    return {'ok': True, 'activo': True, 'ya_activo': True}
                hilo = threading.Thread(target=_worker_run,
                                        args=(str(p.get('modelo') or ''), str(p.get('sesion') or 'cit50')),
                                        daemon=True, name='cit50-worker')
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
    except _core.QueueError as e:
        return {'error': str(e), 'status': e.status}


ACCIONES = ['status', 'health', 'crear', 'listar', 'estado', 'eventos', 'tarea',
            'orden', 'draft', 'aprobar', 'accion', 'worker']
