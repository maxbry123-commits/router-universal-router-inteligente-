"""api/chat.py — Shim de la funcion trigger para Root Directory = raiz del repo.

La implementacion vive en vercel/api/chat.py (una sola fuente, sin duplicar
codigo). Este shim la carga por ruta para que el proyecto Vercel funcione
igual con Root Directory = raiz del repo o Root Directory = vercel/.

Trigger: llama al proxy del Grupo 1 (3 espejos). Si el Space esta dormido o
reiniciandose (404/503), espera y reintenta: la llamada lo despierta.
"""
import importlib.util
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
REAL = os.path.join(RAIZ, "vercel", "api", "chat.py")

if not os.path.isfile(REAL):
    raise RuntimeError("no se encuentra la funcion real: %s" % REAL)

_spec = importlib.util.spec_from_file_location("_riu_trigger", REAL)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["_riu_trigger"] = _mod
_spec.loader.exec_module(_mod)

handler = _mod.handler
