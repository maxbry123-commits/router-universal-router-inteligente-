"""Team 5 MVP (ficha_qwen == '5', Director 2026-10-13): camino directo dentro de fichas_qwen.

FICHA 5: INPUT ACTUAL + HISTORIAL DE ESA SESION + TOOLS -> 1 MODELO ELEGIDO -> TOOLS SI LAS NECESITA -> RESPUESTA.
Sin DAG, sin N1..N8, sin Council, sin juez, sin revisores, sin X-Ray automatico, sin FAST, sin aprobacion intermedia
y sin timeout de nodo de 150 s (techo unico de solicitud: 300 s, con progreso mientras siga viva).

Nada aqui es paralelo a la familia: el selector/modelos salen de la Ficha 1 (ficha1-modelos.json, tal cual),
el mapa ficha-* -> qw-* es el _QW ya declarado en plugin.py, la llamada va por el MISMO Harness autorizado
puente_chat._chat (mismo banco/sello, mismas tools GitHub/Hugging Face de herramientas.py, misma memoria
memoria_yaiwes con llave chat:<sesion>) y la concurrencia/cancelacion/progreso son las de fichas_qwen
(_POOL, _PROCESOS, _CANCEL, _prog/_meta/_texto_prog). No hay _QW, pool, procesos ni memoria propios.
"""
from __future__ import annotations

import re
import time
from typing import Any

# max_tokens operativos de Team 5 por modelo elegido (no son los maximos fisicos): cabe programacion extensa
# sin inflar latencia. El payload puede subirlos si una tarea lo pide.
_MAX_DEF = {'ficha-qwen38max': 4096, 'ficha-qwen38flash': 4096, 'ficha-qwen37max': 4096, 'ficha-qwen37plus': 4096,
            'ficha-qwen36flash': 2048, 'ficha-dsv4pro': 4096, 'ficha-dsv4pro0813': 4096, 'ficha-dsv4flash': 4096,
            'ficha-glm52': 4096, 'ficha-qwen37flash': 2048}  # salida normal MVP; 8192 solo si el usuario pide algo largo, 16384 explicito
_RAZON = {'ficha-qwen38max': 'medium', 'ficha-qwen38flash': 'low', 'ficha-qwen37max': 'medium', 'ficha-qwen37plus': 'medium',
          'ficha-qwen36flash': 'low', 'ficha-dsv4pro': 'high', 'ficha-dsv4pro0813': 'high', 'ficha-dsv4flash': 'high',
          'ficha-glm52': 'high', 'ficha-qwen37flash': 'low'}  # Team 5: reasoning_effort por modelo (Token Plan oficial)
_QUIERE_TOOLS = re.compile(r'(tools?|herramienta|github|hugging ?face|huggingface|acceso)', re.I)  # intencion explicita de tools, sin LLM
_SOLO_LEER = re.compile(r'(comprobar|comprueba|verifica|verificar|revisa|probar|prueba|checa|confirma).{0,40}(acceso|tools?|herramienta)', re.I)  # 'comprueba acceso a GitHub/HF usando las tools' -> prueba solo-lectura
_ORDEN_MUTAR = re.compile(r'(crea|crear|modifica|actualiza|borra|mueve|sube|commit|escribe|cambia)', re.I)  # orden real de escritura -> solo_lectura nunca se activa
_TOOL_NOMBRE = ('github', 'GitHub'), ('hf_', 'Hugging Face'), ('hugging', 'Hugging Face')
_TIMEOUT_S = 300  # techo unico de solicitud para toda la ficha; no hay timeout por nodo


def _fq():
    # el propio modulo de la familia (ya cargado por el plugin host): reutiliza FICHAS, _elegido, _QW, _pc, _prog/_meta
    import plugins.fichas_qwen.plugin as fq
    return fq


def _mensajes(p: dict[str, Any], mensaje: str) -> list[dict[str, Any]]:
    # system instrucciones fijas -> historial REAL de esta sesion (user + assistant, roles conservados) -> input actual.
    # contexto_previo trae TODA la conversacion de esa sesion (el frontend ya no corta a 20); aqui no se recorta:
    # la unica capa de limite es la del Harness/provider, como en el resto de la familia.
    prev = p.get('contexto_previo')
    if isinstance(prev, str) and prev.strip():
        prev_msgs = [{'role': 'user', 'content': prev.strip()}]
    elif isinstance(prev, list):
        prev_msgs = [{'role': str(m.get('role')), 'content': str(m.get('content') or '')}
                     for m in prev if isinstance(m, dict) and m.get('role') in ('user', 'assistant')
                     and str(m.get('content') or '').strip()]
    else:
        prev_msgs = []
    msgs = [{'role': str(m.get('role')), 'content': str(m.get('content') or '')}
            for m in (p.get('messages') or []) if isinstance(m, dict) and str(m.get('content') or '').strip()]
    conv = msgs if len(msgs) > 1 else prev_msgs + msgs  # si el llamador manda la conversacion completa, se respeta
    if mensaje and (not conv or conv[-1].get('role') != 'user' or conv[-1].get('content') != mensaje):
        conv.append({'role': 'user', 'content': mensaje})  # el input actual es siempre el ultimo user
    instr = str(p.get('instrucciones_fijas') or '').strip()
    if instr:  # separadas del input, no envueltas dentro del texto
        conv = [{'role': 'system', 'content': 'INSTRUCCIONES FIJAS DEL USUARIO (cumple todas): ' + instr}] + conv
    return conv


def chat(p: dict[str, Any], ficha: dict[str, Any], mensaje: str, ses: str, t0: float) -> dict[str, Any]:
    fq = _fq()
    sel = fq.FICHAS.get('ficha1-modelos') or {}  # selector de la Ficha 1 tal cual; si Ficha 1 cambia, Team 5 cambia
    elegido = fq._elegido(sel, str(p.get('modelo') or ''))
    if not elegido:
        return {'model': 'Team 5 MVP', 'error': 'GAP MODELO_NO_ESTA_EN_EL_SELECTOR',
                'validos': [s.get('id') for s in (sel.get('selector') or [])]}
    tipo = next((str(s.get('tipo') or 'texto') for s in (sel.get('selector') or []) if s.get('id') == elegido), 'texto')
    if tipo != 'texto':  # imagen/voz quedan visibles en el catalogo pero aun no tienen ejecutor de texto
        return {'model': elegido, 'error': 'GAP MODELO_' + tipo.upper() + '_SIN_EJECUTOR',
                'detalle': elegido + ' es un modelo de ' + tipo + ' y Team 5 todavia no tiene como ejecutarlo'}
    qw = fq._QW.get(elegido)
    pc = fq._pc()
    if not qw or qw not in pc.FICHAS:
        return {'model': elegido, 'error': 'GAP MODELO_SIN_REGISTRO_EN_EL_HARNESS', 'detalle': str(qw or elegido)}
    if pc.FICHAS[qw][1] == 'qwencloud':  # Token Plan oficial: misma base + clave sk-sp, sin compensar con timeouts
        try:
            _k, _u = pc._qwen_conf()
            if 'token-plan' not in _u or not str(_k).startswith('sk-sp'):
                return {'model': elegido, 'error': 'GAP TOKEN_PLAN_NO_CONFIGURADO',
                        'detalle': 'base_url_ok=' + str('token-plan' in _u) + ' key_type_ok=' + str(str(_k).startswith('sk-sp'))}
        except Exception as x:  # noqa: BLE001
            return {'model': elegido, 'error': 'GAP TOKEN_PLAN_NO_CONFIGURADO', 'detalle': str(x)[:150]}
    conv = _mensajes(p, mensaje)
    tiene_historial = any(x.get('role') in ('user', 'assistant') for x in conv[:-1])  # hay turnos previos reales o solo el input actual
    if not conv:
        return {'model': elegido, 'error': 'GAP SIN_MENSAJE'}
    try:
        mt = int(p.get('max_tokens') or 0) or _MAX_DEF.get(elegido, 16384)
    except (TypeError, ValueError):
        mt = _MAX_DEF.get(elegido, 16384)
    pid = str(p.get('_pid') or '')
    nombre = (sel.get('selector') or [{}])
    nombre = str(next((x.get('label') for x in nombre if x.get('id') == elegido), elegido))  # nombre de Ficha 1 (Qwen 3.8 Max)
    tiempos: list = []
    def _tl(nom: str) -> str:  # tool -> nombre visible del progreso
        n = str(nom or '').lower()
        for k_, v_ in _TOOL_NOMBRE:
            if k_ in n:
                return v_
        return str(nom or 'tool')
    def _pf(ev: str) -> None:  # progreso real en el mismo visor + tiempos (sin prompts ni claves)
        tiempos.append({'ev': ev, 'ms': int((time.time() - t0) * 1000)})
        if not pid:
            return
        if ev == 'modelo':
            fq._prog(pid, 'MVP · llamando ' + nombre, 'trabajando')
        elif ev == 'respuesta':
            fq._prog(pid, 'MVP · generando respuesta', 'trabajando')
        elif ev.startswith('tool_ok:'):
            fq._prog(pid, 'MVP · ' + _tl(ev[8:]), 'ok')
        elif ev.startswith('tool:'):
            fq._prog(pid, 'MVP · ' + _tl(ev[5:]), 'trabajando')
    _buf: list = []
    def _sf(chunk: str) -> None:  # chunk del stream -> el visor muestra la respuesta creciendo
        _buf.append(chunk)
        if pid:
            fq._prog(pid, 'MVP · generando respuesta', '…' + ''.join(_buf)[-80:])
    requiere = bool(_QUIERE_TOOLS.search(mensaje or ''))  # 'revisa acceso a GitHub/HF', 'prueba las tools'... -> tools obligatorias
    solo_lectura = bool(_SOLO_LEER.search(mensaje or '')) and not _ORDEN_MUTAR.search(mensaje or '')  # verificar acceso = jamas escribir; una orden de crear/modificar... no se protege
    if pid:  # mismo visor de progreso de la familia
        fq._prog(pid, 'MVP', 'trabajando')
        fq._meta(pid, 'MVP', elegido, 'responde con el modelo elegido')
    r = pc._chat({'model': qw, 'messages': conv, 'max_tokens': mt, 'sesion': ses,
                  'presupuesto_s': _TIMEOUT_S, 'solo_lectura': solo_lectura, 'requiere_tools': requiere,
                  'rondas_tools_max': 3,  # MVP: modelo->tool->modelo->tool->modelo->respuesta, sin 6 vueltas automaticas
                  'progreso_fn': _pf, 'stream_fn': _sf,
                  'extra_llm': {'reasoning_effort': _RAZON[elegido]} if elegido in _RAZON else None,
                  'tarea_id': str(p.get('tarea_id') or ''), 'task_id': str(p.get('task_id') or ''),
                  'anclados': list(p.get('anclados') or []), 'perfil': str(p.get('perfil') or ''),
                  'contexto_explicito': tiene_historial,  # historial del navegador -> no reinsertar _contexto(); historial vacio -> el mismo Harness lee memoria_yaiwes
                  'techo_duro': True,  # techo literal 0-300 s: sin la ventana extra de 45 s del bucle comun
                  'cancelar_si': (lambda _k=pid: _k in fq._CANCEL) if pid else None})  # Detener: se mira antes de cada modelo/tool; un HTTP en vuelo se deja terminar  # el historial completo ya va en messages: sin perfil artificial y sin reinsertar _contexto() en el system
    if pid:
        fq._prog(pid, 'MVP', 'gap' if (isinstance(r, dict) and r.get('error')) else 'ok')
    if not isinstance(r, dict):
        return {'model': elegido, 'error': 'GAP RESPUESTA_INVALIDA_DEL_HARNESS'}
    if r.get('error'):
        e = str(r['error'])
        return {'model': elegido, 'error': e if e.startswith('GAP') else 'GAP ' + e,
                'detalle': str(r.get('detalle') or r.get('mensaje') or '')[:300],
                'herramientas': [x for x in (r.get('herramientas') or []) if isinstance(x, dict)],
                'ms': int((time.time() - t0) * 1000)}
    texto = str(((r.get('choices') or [{}])[0].get('message') or {}).get('content') or '').strip()
    if not texto:
        return {'model': elegido, 'error': 'GAP RESPUESTA_VACIA',
                'herramientas': [x for x in (r.get('herramientas') or []) if isinstance(x, dict)]}
    return {'model': elegido, 'reply': texto,
            'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': texto}}],
            'usage': r.get('usage'),
            'herramientas': [x for x in (r.get('herramientas') or []) if isinstance(x, dict)],
            'evidencia_tools': r.get('evidencia_tools') or [],
            'traza': [{'nodo': 'MVP', 'modelo': elegido, 'rol': 'input + historial + tools -> 1 modelo -> respuesta', 'ok': True,
                        'modelo_pedido': str(p.get('modelo') or ''), 'modelo_ficha1': elegido,
                        'provider_model': str(pc.FICHAS[qw][2]), 'tiempos': tiempos}],
            'estado_tarea': 'COMPLETADO', 'execution_path': 'MVP',
            'memoria_guardada': r.get('memoria_guardada'),
            'ms': int((time.time() - t0) * 1000)}
