#!/usr/bin/env python3
"""chat-router/build_public.py — Shim: si el Root Directory del proyecto Vercel
es chat-router/, delega en vercel/build_public.py (fuente unica)."""
import importlib.util, os, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
REAL = os.path.join(RAIZ, "vercel", "build_public.py")
if not os.path.isfile(REAL):
    raise RuntimeError("no se encuentra %s" % REAL)
_spec = importlib.util.spec_from_file_location("_riu_build", REAL)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["_riu_build"] = _mod
_spec.loader.exec_module(_mod)
_mod.main()
