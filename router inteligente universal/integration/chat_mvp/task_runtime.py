"""ADAPTER — task_runtime canonical vive en el loop wordflow.

N-2 dedup: la implementación única está en
`chat router/wordflow loop code Yaiwes/runtime/src/core/task_runtime.py`
(leases con expiración, heartbeat, StuckDetector, FAILURE_POLICY,
Checkpoint, WorkerBootstrap, WorkspaceRegistry, RunLedger). Este módulo
solo re-exporta el canónico para no mantener dos implementaciones.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_CANONICAL = (Path(__file__).resolve().parents[3]
              / "chat router/wordflow loop code Yaiwes"
              / "runtime/src/core/task_runtime.py")
_spec = importlib.util.spec_from_file_location("yaiwes_task_runtime_canonical", _CANONICAL)
_mod = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _mod
_spec.loader.exec_module(_mod)

for _name in dir(_mod):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_mod, _name)
