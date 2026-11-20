#!/usr/bin/env python3
"""build_public.py (raiz del repo) — Shim: delega en vercel/build_public.py
(fuente unica). Existe para que el build de Vercel funcione con Root Directory
= raiz del repo y Build Command = "python3 build_public.py"."""
import importlib.util, os, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
REAL = os.path.join(AQUI, "vercel", "build_public.py")
if not os.path.isfile(REAL):
    raise RuntimeError("no se encuentra %s" % REAL)
_spec = importlib.util.spec_from_file_location("_riu_build", REAL)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["_riu_build"] = _mod
_spec.loader.exec_module(_mod)
_mod.main()
