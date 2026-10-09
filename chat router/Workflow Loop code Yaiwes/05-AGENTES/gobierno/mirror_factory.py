"""MirrorFactory — schema yaiwes.mirror/v1 (T11-F).

Adaptador fino: reusa ClaimManager/LeaseError de task_runtime (NUEVO-08),
el aislamiento de MirrorManager (worktree + allowed_paths) y el manifiesto de
espejo_equipo. Registra cada hijo con parent_id, mirror_id, node_id, claim_id,
scopes y heartbeat. El hijo recibe ADAPTERS a Sheriff/Judge centrales —
nunca duplica autoridad de autorización o cierre.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_TASK_RUNTIME = (Path(__file__).resolve().parents[3]
                 / "chat router/Workflow Loop code Yaiwes/_copias-anteriores/wordflow loop code Yaiwes/runtime/src/core/task_runtime.py")
_spec = importlib.util.spec_from_file_location("yaiwes_task_runtime", _TASK_RUNTIME)
_tr = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _tr
_spec.loader.exec_module(_tr)

ClaimManager = _tr.ClaimManager
LeaseError = _tr.LeaseError

SCHEMA = "yaiwes.mirror/v1"
_FINAL_AUTHORITIES = {"sheriff": "central", "judge": "central"}


class MirrorFactory:
    """Crea mirrors por proyecto/tarea; el orquestador central conserva scheduling."""

    def __init__(self, claims: ClaimManager | None = None):
        self.claims = claims or ClaimManager()
        self.mirrors: dict[str, dict] = {}

    def create(self, mirror_id: str, node_id: str, parent_id: str, worker_id: str,
               scopes: list[str], base_sha: str, parent_scopes: list[str] | None = None,
               now: float | None = None) -> dict:
        """Scopes aislados: solapados entre hijos rechazados por ClaimManager.
        El hijo no puede elevar permisos: sus scopes deben estar dentro del padre."""
        if parent_scopes is not None:
            parents = [p.rstrip("/") for p in parent_scopes]
            for s in scopes:
                ns = s.rstrip("/")
                if not any(ns == p or ns.startswith(p + "/") for p in parents):
                    raise LeaseError(f"SCOPE_ELEVATION:{s}")
        claim = self.claims.acquire({
            "claim_id": f"claim-{mirror_id}-{worker_id}", "node_id": node_id,
            "worker_id": worker_id, "base_sha": base_sha, "write_scope": list(scopes),
            "lease_expires_at": "", "heartbeat_at": "", "status": "CLAIMED"}, now)
        rec = {
            "schema": SCHEMA, "parent_id": parent_id, "mirror_id": mirror_id,
            "node_id": node_id, "claim_id": claim["claim_id"],
            "scopes": list(scopes), "heartbeat": claim["heartbeat_at"],
            "base_sha": base_sha, "adapters": dict(_FINAL_AUTHORITIES),
            "children": {"hermes_child": f"{mirror_id}-hermes",
                         "openclaw_child": f"{mirror_id}-openclaw"},
        }
        self.mirrors[mirror_id] = rec
        return rec

    def heartbeat(self, mirror_id: str, now: float | None = None) -> dict:
        rec = self.mirrors.get(mirror_id)
        if rec is None:
            raise LeaseError(f"MIRROR_UNKNOWN:{mirror_id}")
        claim = self.claims.heartbeat(rec["claim_id"], now)
        rec["heartbeat"] = claim["heartbeat_at"]
        return rec

    def side_effect(self, mirror_id: str, scope: str, now: float | None = None) -> None:
        rec = self.mirrors.get(mirror_id)
        if rec is None:
            raise LeaseError(f"MIRROR_UNKNOWN:{mirror_id}")
        self.claims.side_effect_allowed(rec["claim_id"], scope, now)

    def manifest(self) -> dict:
        return {"schema": SCHEMA, "mirrors": list(self.mirrors.values())}
