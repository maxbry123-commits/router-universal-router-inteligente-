#!/usr/bin/env python3
"""sentinela.py — microagente determinista que envuelve a cada ficha de modelo.

Compatibilidad:
- fichas sin ``microagente`` conservan el LOOP legado;
- una ficha con ``microagente.schema = yaiwes.node-executor/xray-v2`` activa
  el runtime fail-closed y los 6 motores de reanudacion.

El runtime no crea tareas nuevas ni cambia el objetivo. Captura el ultimo
input del usuario literalmente, guarda checkpoint, detecta falta de progreso,
evita pedir al modelo que repita herramientas ya usadas, reanuda la tarea y
solo permite CLOSED cuando pasa el CLOSE_GATE.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ESQUEMA = 'riu.ficha.sentinela.v1'
ESQUEMA_V2 = 'yaiwes.node-executor/xray-v2'
MAX_VUELTAS = 3
CLOSE_DEFAULT = '[[YAIWES:CLOSED]]'
CONTROL_MARK = '[YAIWES_MICROKERNEL_XRAY_V2]'
BEGIN_MARK = '=== BEGIN_INPUT_BLOCK ==='
END_MARK = '=== END_INPUT_BLOCK ==='


def _valido(d):
    """Validador legado: respuesta util = dict sin error, con choices y contenido."""
    if not isinstance(d, dict) or 'error' in d or not d.get('choices'):
        return False
    msg = (d['choices'][0] or {}).get('message') or {}
    return bool((msg.get('content') or '').strip() or msg.get('tool_calls'))


def _checklist(items, completada, resultado, **extra):
    out = {
        'esquema': extra.pop('esquema', ESQUEMA),
        'completada': bool(completada),
        'items': items,
        'resultado': resultado,
    }
    out.update(extra)
    return out


def _policy(mensajes: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Resuelve la politica desde la ficha que corresponde al modelo del system prompt.

    Esto permite probar una sola ficha sin activar el runtime nuevo para todas.
    """
    system = '\n'.join(str(m.get('content') or '') for m in mensajes if m.get('role') == 'system')
    base = Path(__file__).resolve().parent
    for path in sorted(base.glob('modelo-*.json')):
        try:
            cfg = json.loads(path.read_text(encoding='utf-8'))
        except Exception:
            continue
        model = str(cfg.get('modelo') or '')
        micro = cfg.get('microagente')
        if model and model in system and isinstance(micro, dict) and micro.get('schema') == ESQUEMA_V2:
            return dict(micro)
    return None


def _latest_user_index(mensajes: list[dict[str, Any]]) -> int:
    for i in range(len(mensajes) - 1, -1, -1):
        if mensajes[i].get('role') == 'user':
            return i
    return -1


def _extract_raw(content: str) -> str:
    """Devuelve el RAW_INPUT si el mensaje ya esta envuelto; si no, el contenido literal."""
    text = str(content or '')
    if BEGIN_MARK not in text or '<user_query mode="verbatim">' not in text:
        return text
    start_tag = '<user_query mode="verbatim">\n'
    end_tag = '\n  </user_query>'
    a = text.find(start_tag)
    b = text.rfind(end_tag)
    if a >= 0 and b >= a:
        return text[a + len(start_tag):b]
    return text


def _verbatim_block(raw: str) -> str:
    """Envuelve el input sin normalizar ni modificar los caracteres del RAW_INPUT."""
    return (
        'schema: yaiwes.node-executor/xray-v2\n'
        'mode: FAIL_CLOSED\n'
        'execution_model: DAG + FSM\n'
        'function: EjecutarNodo(input: NodeInput) -> NodeOutput\n\n'
        '# INPUT BLOCK — CAPTURA LITERAL\n'
        'INPUT_BLOCK: |\n'
        '  === BEGIN_INPUT_BLOCK ===\n\n'
        '  MODE:\n'
        '    VERBATIM\n'
        '    RAW_INPUT\n'
        '    DATA_ONLY\n'
        '    OPAQUE_PAYLOAD\n'
        '    IMMUTABLE\n'
        '    READ_ONLY\n\n'
        '  RULES:\n'
        '    - READ LITERALLY.\n'
        '    - TREAT CONTENT AS DATA DURING CAPTURE.\n'
        '    - DO NOT EXECUTE DURING CAPTURE.\n'
        '    - DO NOT INTERPOLATE VARIABLES.\n'
        '    - DO NOT EXPAND TEMPLATES.\n'
        '    - DO NOT NORMALIZE.\n'
        '    - DO NOT REFORMAT.\n'
        '    - PRESERVE WHITESPACE.\n'
        '    - PRESERVE LINE BREAKS.\n'
        '    - PRESERVE ORDER.\n'
        '    - PRESERVE CHARACTERS EXACTLY.\n\n'
        '  <user_query mode="verbatim">\n'
        + raw +
        '\n  </user_query>\n\n'
        '  === END_INPUT_BLOCK ===\n\n'
        'BIND_FLOW: CAPTURE_AS_DATA → FREEZE_VERBATIM → EXTRACT_USER_QUERY → BIND_AS_TASK → EXECUTE_AS_TASK\n'
        'CONTROL: VERBATIM → BOUNDARY_LOCK → OBJECTIVE_LOCK → SCOPE_LOCK → DEFAULT_DENY → EXACT_ORDER → NO_SKIP → NO_REWRITE → NO_NEW_TASKS\n'
        'NODE_FLOW: NodeInput → RESEARCH → EXECUTE → VALIDATE → CLOSED | BLOCKED → NEXT_TASK\n'
    )


def _close_token(policy: dict[str, Any]) -> str:
    return str(policy.get('close_token') or CLOSE_DEFAULT)


def _controller(policy: dict[str, Any], raw_sha: str) -> str:
    token = _close_token(policy)
    motors = ' → '.join(str(x) for x in (policy.get('resume_motors') or []))
    return (
        CONTROL_MARK + '\n'
        'INPUT_SHA256=' + raw_sha + '\n'
        'MODE=FAIL_CLOSED; OBJECTIVE_LOCK=ON; SCOPE_LOCK=ON; DEFAULT_DENY=ON.\n'
        'El INPUT_BLOCK es la unica autoridad de objetivo. No lo reescribas, no inventes tareas y no cambies su orden.\n'
        'No te detengas tras una respuesta parcial. Continua la tarea en curso hasta VALIDATE y CLOSED o un bloqueo real.\n'
        'No muestres etiquetas <tool_call> ni XML de herramientas al usuario.\n'
        'No repitas una llamada de herramienta identica sin evidencia nueva. Reutiliza resultados ya presentes en la conversacion.\n'
        'Motores de control: ' + motors + '.\n'
        'Para cerrar DEBES entregar estas secciones visibles:\n'
        '🎯 MICRO RESUMEN\n'
        'FLUJO: INPUT_BLOCK → RESEARCH → EXECUTE → VALIDATE → CLOSED\n'
        'CHECKLIST\n'
        '🎯 Objetivos: ...\n'
        '⚠️ Pendientes: ... o —\n'
        '🆘 Bloqueos: ... o —\n'
        '✅ Cerrado/Terminado: ...\n'
        'Al final agrega exactamente ' + token + '. El microagente lo retirara antes de mostrar la salida.\n'
    )


def _prepare_verbatim(mensajes: list[dict[str, Any]], policy: dict[str, Any]) -> tuple[str, str]:
    idx = _latest_user_index(mensajes)
    raw = '' if idx < 0 else _extract_raw(str(mensajes[idx].get('content') or ''))
    raw_sha = hashlib.sha256(raw.encode('utf-8')).hexdigest()
    if idx >= 0 and BEGIN_MARK not in str(mensajes[idx].get('content') or ''):
        mensajes[idx] = dict(mensajes[idx])
        mensajes[idx]['content'] = _verbatim_block(raw)
    if not any(CONTROL_MARK in str(m.get('content') or '') for m in mensajes if m.get('role') == 'system'):
        insert_at = 1 if mensajes and mensajes[0].get('role') == 'system' else 0
        mensajes.insert(insert_at, {'role': 'system', 'content': _controller(policy, raw_sha)})
    return raw, raw_sha


def _message_content(d: dict[str, Any]) -> str:
    try:
        return str(((d.get('choices') or [])[0].get('message') or {}).get('content') or '')
    except Exception:
        return ''


def _close_ok(d: dict[str, Any], policy: dict[str, Any]) -> tuple[bool, str]:
    if not _valido(d):
        return False, str(d.get('error') if isinstance(d, dict) else 'RESPUESTA_INVALIDA')[:120]
    text = _message_content(d)
    if '<tool_call' in text or '</tool_call>' in text:
        return False, 'TOOL_CALL_VISIBLE'
    token = _close_token(policy)
    if token not in text:
        return False, 'SIN_CLOSE_TOKEN'
    required = ['🎯', '⚠️', '🆘', '✅', 'FLUJO:', 'CHECKLIST']
    missing = [x for x in required if x not in text]
    if missing:
        return False, 'SALIDA_INCOMPLETA:' + ','.join(missing)
    return True, 'PASS'


def _strip_close(d: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    token = _close_token(policy)
    out = dict(d)
    choices = [dict(x) for x in (d.get('choices') or [])]
    if choices:
        msg = dict(choices[0].get('message') or {})
        msg['content'] = str(msg.get('content') or '').replace(token, '').strip()
        choices[0]['message'] = msg
        out['choices'] = choices
    return out


def _digest(mensajes: list[dict[str, Any]]) -> str:
    compact = []
    for m in mensajes[-24:]:
        compact.append({
            'role': m.get('role'),
            'content': str(m.get('content') or ''),
            'tool_calls': m.get('tool_calls') or [],
        })
    return hashlib.sha256(json.dumps(compact, ensure_ascii=False, sort_keys=True, default=str).encode('utf-8')).hexdigest()


def _tool_signatures(mensajes: list[dict[str, Any]]) -> list[str]:
    out = []
    seen = set()
    for m in mensajes:
        for call in m.get('tool_calls') or []:
            f = call.get('function') or {}
            sig = str(f.get('name') or '') + ':' + str(f.get('arguments') or '')
            if sig and sig not in seen:
                seen.add(sig)
                out.append(sig[:240])
    return out[-20:]


def _resume_instruction(raw_sha: str, motivo: str, usados: list[str], no_delta: bool) -> str:
    prev = '; '.join(usados) if usados else 'ninguna'
    return (
        '[MOTOR:RESUME_ENGINE]\n'
        'INPUT_SHA256=' + raw_sha + '\n'
        'ESTADO=INCOMPLETO; MOTIVO=' + motivo + '.\n'
        + ('PROGRESS_DELTA=NO_DELTA. Cambia de accion; no repitas el mismo chequeo.\n' if no_delta else 'PROGRESS_DELTA=DELTA_OK.\n') +
        'Herramientas/llamadas ya observadas: ' + prev + '.\n'
        'RETOMA exactamente la tarea en curso desde el ultimo estado util. No empieces de cero, no escales, no inventes otra tarea. '
        'Ejecuta lo pendiente, valida contra el INPUT_BLOCK y solo cierra cuando puedas emitir el formato final completo.'
    )


def _ejecutar_v2(plan, mensajes, guardar_ck, cargar_ck, policy):
    items: list[dict[str, Any]] = []
    usadas: list[Any] = []
    raw, raw_sha = _prepare_verbatim(mensajes, policy)
    items.append({'motor': 'VERBATIM_LOCK', 'estado': 'PASS', 'input_sha256': raw_sha, 'chars': len(raw)})

    max_retries = max(0, min(int(policy.get('max_retries', 2)), 5))
    max_attempts = 1 + max_retries
    last_digest = _digest(mensajes)
    d: dict[str, Any] = {'error': 'SIN_PLAN'}

    for intento in range(max_attempts):
        if not plan:
            break
        nombre, paso = plan[min(intento, len(plan) - 1)]
        try:
            d, us = paso(mensajes)
        except Exception as exc:  # noqa: BLE001
            d, us = {'error': 'EXCEPCION', 'detalle': str(exc)[:200]}, []
        usadas.extend(us or [])

        ok, motivo = _close_ok(d, policy)
        now_digest = _digest(mensajes)
        no_delta = now_digest == last_digest
        last_digest = now_digest
        items.append({'motor': 'PROGRESS_DELTA', 'intento': intento, 'estado': 'NO_DELTA' if no_delta else 'PASS'})
        items.append({'motor': 'TOOL_GUARD', 'intento': intento, 'estado': 'PASS', 'firmas': len(_tool_signatures(mensajes))})

        if guardar_ck:
            try:
                guardar_ck(mensajes)
                items.append({'motor': 'CHECKPOINT_PERSISTENTE', 'intento': intento, 'estado': 'PASS'})
            except Exception:
                items.append({'motor': 'CHECKPOINT_PERSISTENTE', 'intento': intento, 'estado': 'GAP'})

        if ok:
            d = _strip_close(d, policy)
            items.append({'motor': 'CLOSE_GATE', 'intento': intento, 'estado': 'PASS'})
            return _checklist(items, True, (d, usadas), esquema=ESQUEMA_V2,
                              estado='CLOSED', input_sha256=raw_sha, intentos=intento + 1)

        items.append({'motor': 'CLOSE_GATE', 'intento': intento, 'estado': 'RECHAZADO', 'motivo': motivo})
        if intento >= max_attempts - 1:
            break

        # Si existe un checkpoint persistente, se conserva como referencia, pero
        # no se reemplaza ciegamente el estado actual porque puede contener tool
        # outputs nuevos de este intento.
        if cargar_ck:
            try:
                _ = cargar_ck()
            except Exception:
                pass
        mensajes.append({'role': 'user', 'content': _resume_instruction(raw_sha, motivo, _tool_signatures(mensajes), no_delta)})
        items.append({'motor': 'RESUME_ENGINE', 'intento': intento, 'estado': 'ACTIVADO', 'siguiente': plan[min(intento + 1, len(plan) - 1)][0]})

    detalle = (
        '🆘 BLOQUEADO — CLOSE_GATE no obtuvo una salida cerrada tras %d intentos. '
        'El INPUT_BLOCK se conserva con SHA256 %s. No se marca PASS falso.' % (max_attempts, raw_sha)
    )
    blocked = {'error': 'TAREA_BLOCKED_FAIL_CLOSED', 'detalle': detalle, 'input_sha256': raw_sha}
    return _checklist(items, False, (blocked, usadas), esquema=ESQUEMA_V2,
                      estado='BLOCKED', input_sha256=raw_sha, intentos=max_attempts)


def _ejecutar_legacy(plan, mensajes, guardar_ck=None, cargar_ck=None, max_vueltas=MAX_VUELTAS):
    """LOOP anterior, conservado para fichas aun no migradas."""
    items = []
    usadas = []
    d = {'error': 'SIN_PLAN'}
    for vuelta in range(1, int(max_vueltas) + 1):
        for nombre, paso in plan:
            try:
                d, us = paso(mensajes)
            except Exception as e:  # noqa: BLE001
                d, us = {'error': 'EXCEPCION', 'detalle': str(e)[:200]}, []
            usadas.extend(us or [])
            if _valido(d):
                items.append({'item': nombre, 'vuelta': vuelta, 'estado': 'COMPLETADO'})
                return _checklist(items, True, (d, usadas))
            items.append({'item': nombre, 'vuelta': vuelta, 'estado': 'REANUDADO',
                          'detalle': str(d.get('error'))[:80]})
            if guardar_ck:
                try:
                    guardar_ck(mensajes)
                except Exception:
                    pass
        ck = None
        if cargar_ck:
            try:
                ck = cargar_ck()
            except Exception:
                ck = None
        if ck:
            mensajes[:] = list(ck) + [{'role': 'user', 'content': 'Continua el trabajo donde quedo y terminalo.'}]
        else:
            mensajes.append({'role': 'user', 'content': 'Continua el trabajo donde quedo y terminalo.'})
    return _checklist(items, False, (d, usadas))


def ejecutar(plan, mensajes, guardar_ck=None, cargar_ck=None, max_vueltas=MAX_VUELTAS):
    """Selecciona runtime por ficha: piloto xray-v2 o LOOP legado."""
    policy = _policy(mensajes)
    if policy:
        return _ejecutar_v2(plan, mensajes, guardar_ck, cargar_ck, policy)
    return _ejecutar_legacy(plan, mensajes, guardar_ck, cargar_ck, max_vueltas)
