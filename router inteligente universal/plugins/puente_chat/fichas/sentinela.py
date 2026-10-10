#!/usr/bin/env python3
"""sentinela.py — guardian determinista que envuelve a la LLM (mini-agente MVP).

Sistema LOOP/coda: no para ni escala hasta terminar la tarea o agotar las vueltas.
Una vuelta = un intento de completar o corregir LA MISMA tarea (no se repite todo el DAG).
Si la llamada se cae, reinicia desde el ultimo checkpoint y continua el trabajo.
Un error definitivo (clave inexistente, 401/403/404, modelo o herramienta inexistente, herramienta bloqueada)
no gasta vueltas: GAP inmediato. Agotadas las vueltas: GAP_FINAL; un GAP nunca se convierte en PASS.

Salida unica: lista de verificacion (checklist) con esquema riu.ficha.sentinela.v1.
"""
from __future__ import annotations

ESQUEMA = 'riu.ficha.sentinela.v1'
MAX_VUELTAS = 5  # intentos sobre la misma tarea antes de rendirse (GAP_FINAL)
_DEFINITIVOS = ('GAP MODELO_SIN_TOOLS', 'GAP HISTORIAL_DEEPSEEK_INCOMPLETO', 'GAP TOOL_ARGUMENTS_INCOMPLETOS',
                'SIN_CLAVES', 'MODELO_DESCONOCIDO', 'MODELO_NO_ESTA_EN_EL_SELLO', 'HERRAMIENTA_BLOQUEADA',
                'HTTP 401', 'HTTP 403', 'HTTP 404')


def _valido(d):
    """sheriff/validador: respuesta util = dict sin error, con choices y contenido."""
    if not isinstance(d, dict) or 'error' in d or not d.get('choices'):
        return False
    msg = (d['choices'][0] or {}).get('message') or {}
    return bool((msg.get('content') or '').strip() or msg.get('tool_calls'))


def _definitivo(d):
    """error que no se arregla reintentando: no gasta vueltas."""
    if not isinstance(d, dict):
        return False
    txt = str(d.get('error') or '') + ' ' + str(d.get('detalle') or '')[:200]
    return any(x in txt for x in _DEFINITIVOS)


def _checklist(items, completada, resultado):
    """unico formato de salida del sentinela: lista de verificacion de la tarea."""
    return {
        'esquema': ESQUEMA,
        'completada': bool(completada),
        'estado': 'PASS' if completada else 'GAP_FINAL',
        'items': items,
        'resultado': resultado,
    }


def ejecutar(plan, mensajes, guardar_ck=None, cargar_ck=None, max_vueltas=MAX_VUELTAS):
    """Bucle principal: recorre el plan de pasos hasta validar la respuesta.

    plan: lista de (nombre, paso) donde paso(mensajes) -> (respuesta, usadas).
    Cada paso que falla guarda checkpoint; al terminar una vuelta se reinicia
    desde el ultimo checkpoint y continua con el error anterior a la vista.
    """
    items = []
    usadas = []
    errores = []
    d = {'error': 'SIN_PLAN'}
    for vuelta in range(1, int(max_vueltas) + 1):
        for nombre, paso in plan:
            try:
                d, us = paso(mensajes)
            except Exception as e:  # noqa: BLE001
                d, us = {'error': 'EXCEPCION', 'detalle': str(e)[:200]}, []
            usadas.extend(us or [])
            if _valido(d):
                items.append({'item': nombre, 'vuelta': vuelta, 'estado': 'COMPLETADO', 'siguiente': 'NEXT_NODE'})
                return _checklist(items, True, (d, usadas))
            err = str(d.get('error'))[:80] if isinstance(d, dict) else 'RESPUESTA_INVALIDA'
            errores.append(err)
            if _definitivo(d):
                items.append({'item': nombre, 'vuelta': vuelta, 'estado': 'GAP_FINAL', 'detalle': err, 'siguiente': 'GAP'})
                return _checklist(items, False, (d, usadas))
            items.append({'item': nombre, 'vuelta': vuelta, 'estado': 'REANUDADO', 'detalle': err, 'siguiente': 'RETRY'})
            if guardar_ck:
                try:
                    guardar_ck(mensajes)
                except Exception:  # noqa: BLE001
                    pass
        # fin de vuelta sin exito: reinicia desde el ultimo checkpoint
        ck = None
        if cargar_ck:
            try:
                ck = cargar_ck()
            except Exception:  # noqa: BLE001
                ck = None
        cont = {'role': 'user', 'content': 'Continua el trabajo donde quedo y terminalo. Corrige unicamente el fallo indicado y no repitas operaciones ya completadas. Fallos anteriores: ' + '; '.join(errores[-3:])}
        if ck:
            mensajes[:] = list(ck) + [cont]
        else:
            mensajes.append(cont)
    items.append({'item': 'tarea', 'vuelta': int(max_vueltas), 'estado': 'GAP_FINAL', 'siguiente': 'GAP'})
    return _checklist(items, False, (d, usadas))
