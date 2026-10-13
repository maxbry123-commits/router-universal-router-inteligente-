"""ficha_mvp (Director 2026-10-13): camino MVP separado de las fichas 1-4.

FICHA MVP: INPUT + HISTORIAL DE LA MISMA SESION + TOOLS -> 1 MODELO ELEGIDO -> TOOL CALL si hace falta -> RESPUESTA.
Sin DAG, sin Council, sin N1..N8, sin revisores/juez, sin X-Ray automatico, sin FAST separado, sin aprobacion
intermedia y sin timeout por nodo de 150 s. El modelo sale del MISMO selector/registro que alimenta Team qwen
(Ficha 1: plugins/fichas_qwen/fichas/ficha1-modelos.json + mapa ficha-* -> qw-*) y la llamada va por el MISMO
Harness ya autorizado del Router (puente_chat._chat): mismo registry de modelos qw-*, mismas herramientas
GitHub/Hugging Face, misma autenticacion y mismas claves del banco. No se modifica fichas_qwen ni se toca N4.

Contrato HTTP (el mismo de siempre del plugin host): POST /plugins/ficha_mvp/call/<accion>.
Acciones: status, modelos, chat, chat_async, resultado, cancelar.
Payload de chat: sesion, modelo (id ficha-*, nombre del selector o id qw-*), message | messages,
contexto_previo (historial real de la sesion: user + assistant), max_tokens, perfil, timeout_ms.
"""
from __future__ import annotations

import concurrent.futures as _cf
import json
import re
import secrets
import threading
import time
from pathlib import Path
from typing import Any

DIR = Path(__file__).resolve().parent

# El mismo mapa ficha-* -> qw-* que usa fichas_qwen para Team qwen (Ficha 1). Imagen y voz no tienen
# ejecutor todavia: se declaran en el selector pero devuelven MODELO_<TIPO>_SIN_EJECUTOR, como en Ficha 1.
_QW = {'ficha-qwen38max': 'qw-qwen-3-8-max', 'ficha-qwen38flash': 'qw-qwen-3-8-flash', 'ficha-qwen37max': 'qw-qwen-3-7-max',
       'ficha-qwen37plus': 'qw-qwen-3-7-plus', 'ficha-qwen36flash': 'qw-qwen-3-6-flash', 'ficha-dsv4pro': 'qw-deepseek-v4-pro',
       'ficha-dsv4pro0813': 'qw-deepseek-v4-pro-0813', 'ficha-dsv4flash': 'qw-deepseek-v4-flash', 'ficha-glm52': 'qw-glm-5-2',
       'ficha-qwen37flash': 'qw-qwen-3-7-flash'}

_POOL = _cf.ThreadPoolExecutor(max_workers=2, thread_name_prefix='ficha_mvp')  # 1 modelo activo por llamada; cola corta
_LOCK = threading.Lock()
_PROCESOS: dict[str, tuple[Any, float]] = {}
_PROG: dict[str, dict[str, Any]] = {}
_CANCEL: set[str] = set()
_SEL_CACHE: list[dict[str, Any]] = []


def _selector() -> list[dict[str, Any]]:
    # selector de la Ficha 1 tal cual (plugins/fichas_qwen/fichas/ficha1-modelos.json): todos los modelos del registro
    if not _SEL_CACHE:
        p = DIR.parent / 'fichas_qwen' / 'fichas' / 'ficha1-modelos.json'
        d = json.loads(p.read_text(encoding='utf-8'))
        _SEL_CACHE.extend(d.get('selector') or [])
    return _SEL_CACHE


def _pc():
    # el Harness original (puente_chat): se reutiliza el modulo que el Router ya cargo (mismo mecanismo que fichas_qwen)
    import importlib.util
    import sys
    for m in list(sys.modules.values()):
        try:
            f = str(getattr(m, '__file__', '') or '').replace(chr(92), '/')
            if f.endswith('puente_chat/plugin.py') and hasattr(m, '_chat'):
                return m
        except Exception:  # noqa: BLE001
            continue
    spec = importlib.util.spec_from_file_location('puente_chat_desde_mvp', DIR.parent / 'puente_chat' / 'plugin.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _norm(s: Any) -> str:
    return re.sub(r'[^a-z0-9]', '', str(s or '').lower())


def _resolver(pedido: str, pc) -> tuple[str | None, str, str]:
    # modelo elegido -> (id qw-* del registry del Harness, id ficha-*, tipo). Nunca cambia de modelo en silencio.
    if pedido in pc.FICHAS:
        return pedido, pedido, 'texto'  # ya vino como id qw-* valido
    for s in _selector():
        if pedido and (pedido == s.get('id') or _norm(pedido) in (_norm(s.get('id')), _norm(s.get('nombre')))):
            return _QW.get(s['id']), s['id'], str(s.get('tipo') or 'texto')
    return None, pedido, ''


def _mensajes(p: dict[str, Any]) -> list[dict[str, Any]]:
    # historial REAL de esta sesion (usuario + asistente) + input literal; si el llamador ya manda la conversacion
    # completa en messages, se respeta tal cual
    msgs = [dict(m) for m in (p.get('messages') or []) if isinstance(m, dict) and str(m.get('content') or '').strip()]
    prev = p.get('contexto_previo')
    if isinstance(prev, str) and prev.strip():
        prev_msgs = [{'role': 'user', 'content': prev.strip()}]
    elif isinstance(prev, list):
        prev_msgs = [dict(m) for m in prev if isinstance(m, dict) and m.get('role') in ('user', 'assistant') and str(m.get('content') or '').strip()]
    else:
        prev_msgs = []
    if len(msgs) > 1:
        conv = msgs
    else:
        conv = prev_msgs + msgs
    return conv


def _compactar(conv: list[dict[str, Any]], perfil: str, pc) -> list[dict[str, Any]]:
    # auto_compact ~0.85 del techo de contexto del perfil del Harness: se sueltan los turnos mas viejos
    techo = int((getattr(pc, '_PERFILES', {}).get(perfil) or getattr(pc, '_PERFILES', {}).get('normal') or (22000,))[0] * 0.85)
    def tam(ms):
        return sum(len(str(m.get('content') or '')) for m in ms)
    while len(conv) > 2 and tam(conv) > techo:
        conv.pop(0)  # suelta el turno mas viejo; nunca el input actual (ultimo)
    return conv


def _chat(p: dict[str, Any]) -> dict[str, Any]:
    t0 = time.time()
    pid = str(p.get('_pid') or '')
    pc = _pc()
    sel = _selector()
    pedido = str(p.get('modelo') or p.get('model') or '')
    qw, fid, tipo = _resolver(pedido, pc)
    if tipo and tipo != 'texto':
        return {'model': fid, 'error': 'GAP MODELO_' + tipo.upper() + '_SIN_EJECUTOR',
                'detalle': fid + ' es un modelo de ' + tipo + ': la ficha MVP todavia no tiene como ejecutarlo'}
    if not qw or qw not in pc.FICHAS:
        return {'model': fid, 'error': 'GAP MODELO_NO_ESTA_EN_EL_REGISTRO',
                'detalle': 'modelo no reconocido por el selector de la Ficha 1: ' + str(pedido)[:80],
                'validos': [s.get('id') for s in sel]}
    conv = _compactar(_mensajes(p), str(p.get('perfil') or 'normal'), pc)
    if not conv:
        return {'model': fid, 'error': 'GAP SIN_MENSAJE', 'detalle': 'no llego ni input ni historial'}
    ses = str(p.get('sesion') or 'mvp')[:60]
    perfil = str(p.get('perfil') or 'normal')
    try:
        presupuesto = max(30, min(300, int(float(p.get('timeout_ms') or 300000) / 1000)))
    except (TypeError, ValueError):
        presupuesto = 300
    max_tok = int(p.get('max_tokens') or 2048)
    if pid:
        _PROG[pid] = {'modelo': fid, 't0': t0}
    r = pc._chat({'model': qw, 'messages': conv, 'max_tokens': max_tok, 'sesion': ses,
                  'presupuesto_s': presupuesto, 'solo_lectura': False, 'requiere_tools': False,
                  'tarea_id': str(p.get('tarea_id') or ''), 'perfil': perfil,
                  'task_id': str(p.get('task_id') or ''), 'anclados': list(p.get('anclados') or [])})
    if not isinstance(r, dict):
        return {'model': fid, 'error': 'GAP RESPUESTA_INVALIDA_DEL_HARNESS'}
    if r.get('error'):
        e = str(r['error'])
        return {'model': fid, 'error': e if e.startswith('GAP') else 'GAP ' + e,
                'detalle': str(r.get('detalle') or r.get('mensaje') or '')[:300],
                'herramientas': [x for x in (r.get('herramientas') or []) if isinstance(x, dict)],
                'ms': int((time.time() - t0) * 1000)}
    texto = str(((r.get('choices') or [{}])[0].get('message') or {}).get('content') or '').strip()
    if not texto:
        return {'model': fid, 'error': 'GAP RESPUESTA_VACIA', 'herramientas': [x for x in (r.get('herramientas') or []) if isinstance(x, dict)]}
    return {'model': fid, 'modelo': fid, 'reply': texto,
            'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': texto}}],
            'usage': r.get('usage'),
            'herramientas': [x for x in (r.get('herramientas') or []) if isinstance(x, dict)],
            'evidencia_tools': r.get('evidencia_tools') or [],
            'traza': [{'nodo': 'MVP', 'modelo': fid, 'rol': 'input + historial + tools -> 1 modelo -> respuesta', 'ok': True}],
            'estado_tarea': 'COMPLETADO', 'execution_path': 'MVP',
            'memoria_guardada': r.get('memoria_guardada'),
            'ms': int((time.time() - t0) * 1000)}


def _progreso(pid: str) -> str:
    d = _PROG.get(pid) or {}
    if not d:
        return ''
    return 'MVP -> ' + str(d.get('modelo') or 'modelo') + ' trabajando · ' + str(int(time.time() - float(d.get('t0') or time.time()))) + ' s'


def handle(action: str, payload: dict[str, Any] | None) -> dict[str, Any]:
    p = payload or {}
    if action == 'status':
        sel = _selector()
        try:
            pc = _pc()
            reg = [s.get('id') for s in sel if _QW.get(s.get('id')) in pc.FICHAS]
        except Exception as x:  # noqa: BLE001
            reg = []
            return {'ok': False, 'error': 'HARNESS_NO_DISPONIBLE', 'detalle': repr(x)[:160], 'selector': [s.get('id') for s in sel]}
        return {'ok': True, 'ficha': 'MVP', 'selector': [s.get('id') for s in sel], 'ejecutables': reg,
                'flujo': 'INPUT + HISTORIAL + TOOLS -> 1 MODELO -> RESPUESTA (sin DAG, sin council, sin timeout de nodo)'}
    if action == 'modelos':
        return {'modelos': [{'id': s.get('id'), 'nombre': s.get('nombre'), 'rol': s.get('rol'), 'tipo': s.get('tipo')} for s in _selector()]}
    if action == 'chat':
        return _chat(p)
    if action == 'chat_async':
        clave = secrets.token_urlsafe(24)
        with _LOCK:
            for k, (fut, t) in list(_PROCESOS.items()):
                if time.time() - t > 900 and fut.done():
                    del _PROCESOS[k]
                    _PROG.pop(k, None); _CANCEL.discard(k)
            _PROCESOS[clave] = (_POOL.submit(_chat, dict(p, _pid=clave)), time.time())
            _PROG[clave] = {'modelo': str(p.get('modelo') or ''), 't0': time.time()}
        return {'estado': 'procesando', 'proceso_id': clave}
    if action == 'resultado':
        item = _PROCESOS.get(str(p.get('proceso_id') or ''))
        if not item:
            return {'error': 'PROCESO_NO_EXISTE'}
        if not item[0].done():
            return {'estado': 'procesando', 'proceso_id': p.get('proceso_id'), 'progreso': _progreso(str(p.get('proceso_id') or ''))}
        try:
            r = item[0].result()
            if isinstance(r, dict) and 'reply' in r:
                r.setdefault('estado', 'completado')
            return r
        except Exception as x:  # noqa: BLE001
            return {'error': 'CHAT_FAILED', 'detalle': type(x).__name__}
    if action == 'cancelar':  # Detener: en cola se cancela antes de ejecutar
        k = str(p.get('proceso_id') or '')
        _CANCEL.add(k)
        it = _PROCESOS.get(k)
        return {'estado': 'cancelado', 'proceso_id': k, 'en_cola': bool(it and it[0].cancel())}
    return {'error': 'ACCION_DESCONOCIDA'}
