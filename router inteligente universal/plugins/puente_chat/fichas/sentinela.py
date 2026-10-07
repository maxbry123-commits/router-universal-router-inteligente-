#!/usr/bin/env python3
"""sentinela.py — guardian determinista que envuelve a la LLM (mini-agente MVP).

Sistema LOOP/coda: no para ni escala hasta terminar la tarea o agotar las vueltas.
Si la llamada se cae, reinicia desde el ultimo checkpoint y continua el trabajo.

Salida unica: lista de verificacion (checklist) con esquema riu.ficha.sentinela.v1.
"""
from __future__ import annotations

ESQUEMA = 'riu.ficha.sentinela.v1'
MAX_VUELTAS = 3  # pasadas completas sobre el plan antes de rendirse


def _valido(d):
    """sheriff/validador: respuesta util = dict sin error, con choices y contenido."""
    if not isinstance(d, dict) or 'error' in d or not d.get('choices'):
        return False
    msg = (d['choices'][0] or {}).get('message') or {}
    fin = d['choices'][0].get('finish_reason')
    return bool((msg.get('content') or '').strip() and not msg.get('tool_calls')
                and fin in ('stop', 'end_turn'))


def _checklist(items, completada, resultado):
    """unico formato de salida del sentinela: lista de verificacion de la tarea."""
    return {
        'esquema': ESQUEMA,
        'completada': bool(completada),
        'items': items,
        'resultado': resultado,
    }


def ejecutar(plan, mensajes, guardar_ck=None, cargar_ck=None, max_vueltas=MAX_VUELTAS):
    """Bucle principal: recorre el plan de pasos hasta validar la respuesta.

    plan: lista de (nombre, paso) donde paso(mensajes) -> (respuesta, usadas).
    Antes de cada paso guarda checkpoint; al terminar una vuelta se reinicia
    desde el ultimo checkpoint y continua. Nunca se detiene a mitad.
    """
    items = []
    usadas = []
    d = {'error': 'SIN_PLAN'}
    max_vueltas = max(1, min(MAX_VUELTAS, int(max_vueltas)))
    for vuelta in range(1, max_vueltas + 1):
        for nombre, paso in plan:
            if guardar_ck:
                try:
                    guardar_ck(mensajes)
                except Exception:  # noqa: BLE001
                    pass
            try:
                d, us = paso(mensajes)
            except Exception as e:  # noqa: BLE001
                d, us = {'error': 'EXCEPCION', 'detalle': str(e)[:200]}, []
            usadas.extend(us or [])
            if _valido(d):
                items.append({'item': nombre, 'vuelta': vuelta, 'estado': 'COMPLETADO'})
                return _checklist(items, True, (d, usadas))
            items.append({'item': nombre, 'vuelta': vuelta, 'estado': 'REANUDADO',
                          'motor': 'failover' if nombre.startswith('reserva:') else 'watchdog',
                          'detalle': str(d.get('error', 'RESPUESTA_NO_FINAL'))[:80]})
        # fin de vuelta sin exito: reinicia desde el ultimo checkpoint
        ck = None
        if cargar_ck:
            try:
                ck = cargar_ck()
            except Exception:  # noqa: BLE001
                ck = None
        origen = 'no_disponible'
        if isinstance(ck, dict):
            origen = ck.get('origen') or origen
            ck = ck.get('mensajes')
        if vuelta < max_vueltas:
            base = ck if ck else mensajes
            mensajes[:] = [dict(m) for m in base]
            mensajes.append({'role': 'user', 'content': 'Continua desde el ultimo checkpoint y termina la tarea sin repetir herramientas.'})
            items.append({'item': 'checkpoint', 'vuelta': vuelta, 'estado': 'REANUDADO',
                          'motor': 'estado_' + origen if ck else 'sin_checkpoint',
                          'checkpoint': bool(ck)})
    d = {'error': 'RECOVERY_EXHAUSTED', 'ultimo_error': str(d.get('error', 'RESPUESTA_NO_FINAL'))[:80]}
    return _checklist(items, False, (d, usadas))
