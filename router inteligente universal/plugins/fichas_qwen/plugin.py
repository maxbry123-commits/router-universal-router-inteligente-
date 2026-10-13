"""Puerta fina para fichas_qwen.

Mantiene el nucleo original en plugin_core.py y corrige reglas de entrada sin duplicar el motor:
- Fichas 1, 2, 3 y 4: FAST del chat solo si el Director encendio explicitamente el boton.
- Historial e instrucciones fijas se separan del input literal antes de clasificar ok, /aprobar,
  mutacion, FAST o tarea nueva. Se vuelven a inyectar unicamente en los prompts de los modelos.
- Ficha 3: N6 y N7 son revisores independientes de solo lectura y corren en paralelo;
  N8 conserva el juicio final y espera a ambos.
- Cola global: maximo 4 procesos/llamadas activas; el resto espera en cola.
- Detener: cancela si aun esta en cola o corta cooperativamente al terminar la llamada en curso.
- La accion interna `llm` de Ficha 4 conserva su fast automatico para workflows.
"""
from __future__ import annotations

import concurrent.futures as _cf
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
_CANCELADOS = set()
_CANCEL_LOCK = _threading.Lock()

# Contrato del Director: hasta 4 solicitudes activas; overflow queda en la cola del executor.
try:
    _pool_viejo = _core._POOL
    _core._POOL = _cf.ThreadPoolExecutor(max_workers=4, thread_name_prefix="fichas-qwen")
    _pool_viejo.shutdown(wait=False, cancel_futures=True)
except Exception:
    pass
_core._SEM = _threading.BoundedSemaphore(4)


def _cancelado(pid):
    if not pid:
        return False
    with _CANCEL_LOCK:
        return str(pid) in _CANCELADOS


def _marcar_cancelado(pid):
    if pid:
        with _CANCEL_LOCK:
            _CANCELADOS.add(str(pid))


def _limpiar_cancelado(pid):
    if pid:
        with _CANCEL_LOCK:
            _CANCELADOS.discard(str(pid))


def _optimizar_ficha3():
    """Quita una fase serial sin quitar verificadores: N6 || N7 -> N8."""
    f = _core.FICHAS.get("ficha3-frontend")
    if not isinstance(f, dict):
        return
    ns = {str(n.get("id")): n for n in (f.get("nodos") or []) if isinstance(n, dict)}
    n6, n7, n8 = ns.get("N6"), ns.get("N7"), ns.get("N8")
    if not (n6 and n7 and n8):
        return
    n7["depende_de"] = ["N4", "N5"]
    n7["rol"] = str(n7.get("rol") or "").replace(
        "de nuevo el resultado de N6 segun N5",
        "independientemente el resultado de N4 segun N5, en paralelo con N6",
    )
    n8["depende_de"] = ["N6", "N7", "N5"]
    n8["rol"] = str(n8.get("rol") or "").replace(
        "de nuevo el resultado de N7 segun N5 y entrega la SALIDA final",
        "los resultados independientes de N6 y N7 segun N5 y entrega la SALIDA final",
    )
    f["flujo"] = "N0 -> [N1|N2|N3|N3B] paralelo -> N3D decide -> N4 ejecuta -> N5 -> [N6|N7] revisan en paralelo -> N8 juez final -> SALIDA"


_optimizar_ficha3()


def _fast_chat_ok(ficha, mensaje, opts, nodos):
    fid = str((ficha or {}).get("ficha") or "")
    if (fid.startswith("ficha1") or fid.startswith("ficha4")) and not bool((opts or {}).get("fast_reply")):
        return False
    return _fast_chat_ok_original(ficha, mensaje, opts, nodos)


def _fast_consult_ok(ficha, mensaje, opts, nodos):
    fid = str((ficha or {}).get("ficha") or "")
    if (fid.startswith("ficha2") or fid.startswith("ficha3")) and not bool((opts or {}).get("fast_reply")):
        return False
    return _fast_consult_ok_original(ficha, mensaje, opts, nodos)


def _separar_entrada(texto):
    s = str(texto or "")
    extras = []
    if s.startswith("[CONTEXTO PREVIO DE ESTA MISMA SESIÓN") and "[FIN CONTEXTO PREVIO]" in s:
        cab, s = s.split("[FIN CONTEXTO PREVIO]", 1)
        extras.append(cab.strip() + "\n[FIN CONTEXTO PREVIO]")
        s = s.lstrip("\r\n ")
    if s.startswith("[INSTRUCCIONES FIJAS.") and "[FIN INSTRUCCIONES FIJAS]" in s:
        cab, resto = s.split("[FIN INSTRUCCIONES FIJAS]", 1)
        extras.insert(0, cab.strip() + "\n[FIN INSTRUCCIONES FIJAS]")
        s = resto.lstrip("\r\n ")
        marca = "[ANTES DE RESPONDER: comprueba que tu salida cumple las INSTRUCCIONES FIJAS de arriba.]"
        if s.rstrip().endswith(marca):
            s = s.rstrip()[:-len(marca)].rstrip()
    return s.strip(), "\n\n".join(x for x in extras if x).strip()


def _ultimo_user(messages):
    for m in reversed(messages or []):
        if isinstance(m, dict) and m.get("role") == "user":
            return str(m.get("content") or "")
    return ""


def _chat_con_contexto(p):
    q = dict(p or {})
    bruto = str(q.get("message") or "") or _ultimo_user(q.get("messages") or [])
    literal, extra = _separar_entrada(bruto)
    extra_payload = str(q.get("contexto_previo") or "").strip()
    if extra_payload:
        extra = (extra + "\n\n" + extra_payload).strip() if extra else extra_payload
    q["message"] = literal
    anterior = getattr(_ctx_local, "extra", "")
    _ctx_local.extra = extra
    try:
        return _chat_original(q)
    finally:
        _ctx_local.extra = anterior


def _correr_con_contexto(ficha, mensaje, modelo, pid="", opts=None):
    if _cancelado(pid):
        raise RuntimeError("PROCESO_DETENIDO")
    o = {} if opts is None else opts
    extra = str(getattr(_ctx_local, "extra", "") or "").strip()
    if extra:
        o["contexto_prompt"] = extra
    return _correr_original(ficha, mensaje, modelo, pid, o)


def _llamar_harness_1_con_contexto(modelo, prompt, ficha, n, opts):
    pid = str((opts or {}).get("pid") or "")
    if _cancelado(pid):
        raise RuntimeError("PROCESO_DETENIDO")
    extra = str((opts or {}).get("contexto_prompt") or "").strip()
    if extra and extra not in str(prompt):
        prompt = extra + "\n\n[INPUT / PROMPT ACTUAL]\n" + str(prompt)
    r = _llamar_harness_1_original(modelo, prompt, ficha, n, opts)
    if _cancelado(pid):
        raise RuntimeError("PROCESO_DETENIDO")
    return r


_core._fast_chat_ok = _fast_chat_ok
_core._fast_consult_ok = _fast_consult_ok
_core._chat = _chat_con_contexto
_core._correr = _correr_con_contexto
_core._llamar_harness_1 = _llamar_harness_1_con_contexto

for _name in dir(_core):
    if _name.startswith("__") or _name in globals():
        continue
    globals()[_name] = getattr(_core, _name)


def handle(action, payload):
    p = payload or {}
    if action == "detener":
        pid = str(p.get("proceso_id") or "")
        if not pid:
            return {"error": "PROCESO_ID_FALTA"}
        _marcar_cancelado(pid)
        item = getattr(_core, "_PROCESOS", {}).get(pid)
        if not item:
            return {"error": "PROCESO_NO_EXISTE"}
        fut = item[0]
        en_cola = bool(fut.cancel())
        if en_cola:
            try:
                with _core._LOCK:
                    _core._PROCESOS.pop(pid, None)
            except Exception:
                pass
            _limpiar_cancelado(pid)
        return {"ok": True, "proceso_id": pid, "cancelado_en_cola": en_cola, "detencion_cooperativa": not en_cola}
    r = _core.handle(action, p)
    if action == "resultado":
        pid = str(p.get("proceso_id") or "")
        if isinstance(r, dict) and (r.get("error") or r.get("estado") != "procesando"):
            _limpiar_cancelado(pid)
    return r
