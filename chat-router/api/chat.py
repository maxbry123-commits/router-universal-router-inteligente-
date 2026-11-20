"""chat-router/api/chat.py — Shim: si el Root Directory del proyecto Vercel es
chat-router/, delega en vercel/api/chat.py (fuente unica del trigger)."""
import importlib.util, os, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
REAL = os.path.join(RAIZ, "vercel", "api", "chat.py")
if not os.path.isfile(REAL):
    raise RuntimeError("no se encuentra %s" % REAL)
_spec = importlib.util.spec_from_file_location("_riu_trigger", REAL)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["_riu_trigger"] = _mod
_spec.loader.exec_module(_mod)
handler = _mod.handler
