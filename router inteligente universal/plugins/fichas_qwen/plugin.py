"""Puerta fina para fichas_qwen.

Mantiene el nucleo original en plugin_core.py y corrige una sola regla:
para las fichas 1, 2 y 3, los carriles FAST interactivos solo pueden activarse
cuando el usuario encendio explicitamente el boton de respuesta rapida.
Ficha 4 conserva su fast-lane automatico para workflows internos.
"""
from __future__ import annotations

import importlib.util as _importlib_util
from pathlib import Path as _Path

_core_path = _Path(__file__).with_name("plugin_core.py")
_spec = _importlib_util.spec_from_file_location("fichas_qwen_plugin_core", _core_path)
if _spec is None or _spec.loader is None:
    raise RuntimeError("FICHAS_QWEN_CORE_NO_CARGA")
_core = _importlib_util.module_from_spec(_spec)
_spec.loader.exec_module(_core)

_fast_chat_ok_original = _core._fast_chat_ok
_fast_consult_ok_original = _core._fast_consult_ok


def _fast_chat_ok(ficha, mensaje, opts, nodos):
    """Ficha 1: OFF significa OFF. Ficha 4 mantiene su ruta automatica."""
    fid = str((ficha or {}).get("ficha") or "")
    if fid.startswith("ficha1") and not bool((opts or {}).get("fast_reply")):
        return False
    return _fast_chat_ok_original(ficha, mensaje, opts, nodos)


def _fast_consult_ok(ficha, mensaje, opts, nodos):
    """Fichas 2/3: no activar FAST_CONSULT con el boton rapido apagado."""
    fid = str((ficha or {}).get("ficha") or "")
    if (fid.startswith("ficha2") or fid.startswith("ficha3")) and not bool((opts or {}).get("fast_reply")):
        return False
    return _fast_consult_ok_original(ficha, mensaje, opts, nodos)


# Las funciones del nucleo resuelven sus globals en el modulo core: parchear alli es
# lo que garantiza que _correr() use estas compuertas sin duplicar todo el plugin.
_core._fast_chat_ok = _fast_chat_ok
_core._fast_consult_ok = _fast_consult_ok

# Reexportar la API y el estado que el Router ya espera del plugin.
for _name in dir(_core):
    if _name.startswith("__") or _name in globals():
        continue
    globals()[_name] = getattr(_core, _name)

handle = _core.handle
