"""Puerta fina para fichas_qwen.

Mantiene el nucleo original en plugin_core.py y corrige reglas de entrada sin duplicar el motor:
- Fichas 1, 2, 3 y 4: FAST del chat solo si el Director encendio explicitamente el boton.
- Historial e instrucciones fijas se separan del input literal antes de clasificar ok, /aprobar,
  mutacion, FAST o tarea nueva. Se vuelven a inyectar unicamente en los prompts de los modelos.
- La accion interna `llm` de Ficha 4 conserva su fast automatico para workflows.
"""
from __future__ import annotations

import importlib.util as _importlib_util
import threading as _threading
from pathlib import Path as _Path

_core_path = _Path(__file__).with_name("plugin_core.py")
_spec = _importlib_util.spec_from_file_location("fichas_qwen_plugin_core", _core_path)
if _spec is None or _spec.loader is None:
    raise RuntimeError("FICHAS_QWEN_CORE_NO_CARGA")
_core = _importlib_util.module_from_spec(_spec)
_spec.loader.exec_module(_core)

_fast_chat_ok_original = _core._fast_chat_ok
_fast_consult_ok_original = _core._fast_consult_ok
_chat_original = _core._chat
_correr_original = _core._correr
_llamar_harness_1_original = _core._llamar_harness_1
_ctx_local = _threading.local()


def _fast_chat_ok(ficha, mensaje, opts, nodos):
    """Ficha 1 y Ficha 4 en chat: OFF significa OFF."""
    fid = str((ficha or {}).get("ficha") or "")
    if (fid.startswith("ficha1") or fid.startswith("ficha4")) and not bool((opts or {}).get("fast_reply")):
        return False
    return _fast_chat_ok_original(ficha, mensaje, opts, nodos)


def _fast_consult_ok(ficha, mensaje, opts, nodos):
    """Fichas 2/3 en chat: no activar FAST_CONSULT con el boton rapido apagado."""
    fid = str((ficha or {}).get("ficha") or "")
    if (fid.startswith("ficha2") or fid.startswith("ficha3")) and not bool((opts or {}).get("fast_reply")):
        return False
    return _fast_consult_ok_original(ficha, mensaje, opts, nodos)


def _separar_entrada(texto):
    """Devuelve (input_literal, contexto_para_modelos) sin dejar que contexto cambie la clasificacion."""
    s = str(texto or "")
    extras = []

    # GAP memoria: api.js / chat-contexto-fichas pueden anteponer este bloque.
    if s.startswith("[CONTEXTO PREVIO DE ESTA MISMA SESIÓN") and "[FIN CONTEXTO PREVIO]" in s:
        cab, s = s.split("[FIN CONTEXTO PREVIO]", 1)
        extras.append(cab.strip() + "\n[FIN CONTEXTO PREVIO]")
        s = s.lstrip("\r\n ")

    # GAP instrucciones fijas: A.envolver() las coloca alrededor del input. Para el kernel son
    # instrucciones del modelo, no parte del comando literal que decide /aprobar, ok o mutacion.
    if s.startswith("[INSTRUCCIONES FIJAS.") and "[FIN INSTRUCCIONES FIJAS]" in s:
        cab, resto = s.split("[FIN INSTRUCCIONES FIJAS]", 1)
        extras.insert(0, cab.strip() + "\n[FIN INSTRUCCIONES FIJAS]")
        s = resto.lstrip("\r\n ")
        marca = "[ANTES DE RESPONDER: comprueba que tu salida cumple las INSTRUCCIONES FIJAS de arriba.]"
        if s.rstrip().endswith(marca):
            s = s.rstrip()[:-len(marca)].rstrip()

    return s.strip(), "\n\n".join(x for x in extras if x).strip()


def _chat_con_contexto(p):
    q = dict(p or {})
    literal, extra = _separar_entrada(q.get("message") or "")
    extra_payload = str(q.get("contexto_previo") or "").strip()
    if extra_payload:
        extra = (extra + "\n\n" + extra_payload).strip() if extra else extra_payload
    if q.get("message") is not None:
        q["message"] = literal
    anterior = getattr(_ctx_local, "extra", "")
    _ctx_local.extra = extra
    try:
        return _chat_original(q)
    finally:
        _ctx_local.extra = anterior


def _correr_con_contexto(ficha, mensaje, modelo, pid="", opts=None):
    o = {} if opts is None else opts
    extra = str(getattr(_ctx_local, "extra", "") or "").strip()
    if extra:
        o["contexto_prompt"] = extra
    return _correr_original(ficha, mensaje, modelo, pid, o)


def _llamar_harness_1_con_contexto(modelo, prompt, ficha, n, opts):
    extra = str((opts or {}).get("contexto_prompt") or "").strip()
    if extra and extra not in str(prompt):
        prompt = extra + "\n\n[INPUT / PROMPT ACTUAL]\n" + str(prompt)
    return _llamar_harness_1_original(modelo, prompt, ficha, n, opts)


# Las funciones del nucleo resuelven sus globals dentro del modulo core. Parchearlas alli garantiza
# que chat_async, FAST_QA, FAST_CONSULT, DAG, anexos y verificadores usen las mismas compuertas.
_core._fast_chat_ok = _fast_chat_ok
_core._fast_consult_ok = _fast_consult_ok
_core._chat = _chat_con_contexto
_core._correr = _correr_con_contexto
_core._llamar_harness_1 = _llamar_harness_1_con_contexto

# Reexportar la API y el estado que el Router ya espera del plugin.
for _name in dir(_core):
    if _name.startswith("__") or _name in globals():
        continue
    globals()[_name] = getattr(_core, _name)


def handle(action, payload):
    # Normaliza antes de que core.handle cree el Future de chat_async. El Future termina llamando
    # a _core._chat, que ya esta parcheado arriba y conserva el input literal para el kernel.
    return _core.handle(action, payload)
