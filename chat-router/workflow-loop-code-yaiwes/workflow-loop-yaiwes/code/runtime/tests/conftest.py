"""Wiring del repo: permite `pytest runtime/tests` sin PYTHONPATH manual.
El loop usa tres layouts de import historicos (runtime.src.*, src.*, core.*);
se resuelven por namespace packages añadiendo estas rutas a sys.path.
"""
import sys
from pathlib import Path

_LOOP_ROOT = Path(__file__).resolve().parents[2]
for _p in (_LOOP_ROOT, _LOOP_ROOT / "runtime", _LOOP_ROOT / "runtime" / "src", _LOOP_ROOT / "wordflow_loop"):
    s = str(_p)
    if s not in sys.path:
        sys.path.insert(0, s)
