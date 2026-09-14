from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

PLUGIN_ID = "yaiwes.dataset.router"
PLUGIN_VERSION = "3.0.0"
TRIBUNAL_CASE_ID = "YAIWES-DATASET-PLUGIN-999"

HERE = Path(__file__).resolve()
DATASET_ROOT = HERE.parents[1]
REPO_ROOT = DATASET_ROOT.parent
REGISTRY_PATH = DATASET_ROOT / "registry.json"
SHARD_INDEX_PATH = DATASET_ROOT / "indexes" / "shard_index.json"
MANIFEST_PATH = HERE.with_name("ficha_yaiwes_dataset_v2.json")
CONTROL_ROUTER_PATH = REPO_ROOT / "Yaiwes Cognitive Control Plane" / "router.py"


@dataclass(frozen=True)
class ShadowReport:
    passed: bool
    checks: Dict[str, bool]
    details: Dict[str, Any]


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _contract_hash(contract: Mapping[str, Any]) -> str:
    payload = json.dumps(contract, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def load_manifest(path: Path = MANIFEST_PATH) -> Dict[str, Any]:
    return _load_json(path)


def validate_manifest_shape(manifest: Mapping[str, Any]) -> List[str]:
    """Small fail-closed preflight compatible with FichaContractV2 invariants used here."""
    errors: List[str] = []
    required = ("artifact_id", "version", "estado", "contract_hash", "contrato",
                "ejecucion", "seguridad", "firma")
    for key in required:
        if key not in manifest:
            errors.append(f"missing:{key}")

    if manifest.get("artifact_id") != PLUGIN_ID:
        errors.append("artifact_id")
    if manifest.get("version") != PLUGIN_VERSION:
        errors.append("version")
    if manifest.get("estado") not in {"draft", "testing", "active", "deprecated", "revoked"}:
        errors.append("estado")

    contract = manifest.get("contrato") or {}
    if contract.get("rol") != "transform":
        errors.append("contrato.rol")
    if not contract.get("consume") or not contract.get("expone"):
        errors.append("contrato.transform_requires_io")
    expected_hash = _contract_hash(contract)
    if manifest.get("contract_hash") != expected_hash:
        errors.append("contract_hash")

    execution = manifest.get("ejecucion") or {}
    if execution.get("kind") != "code" or execution.get("runtime_type") != "compute":
        errors.append("ejecucion")
    if execution.get("llm_ratio", 0.0) > 0.10:
        errors.append("ejecucion.llm_ratio")
    if not execution.get("idempotente", False):
        errors.append("ejecucion.idempotente")

    security = manifest.get("seguridad") or {}
    limits = security.get("limites") or {}
    timeout_ms = limits.get("timeout_ms")
    deadline_ms = limits.get("deadline_ms", timeout_ms)
    if not isinstance(timeout_ms, int) or timeout_ms <= 0:
        errors.append("seguridad.timeout_ms")
    if isinstance(timeout_ms, int) and isinstance(deadline_ms, int) and deadline_ms < timeout_ms:
        errors.append("seguridad.deadline_ms")

    if manifest.get("estado") == "active":
        gpg = (manifest.get("firma") or {}).get("gpg_key_id", "")
        if not gpg or gpg == "PENDIENTE":
            errors.append("active_requires_signature")
    return errors


class DatasetYaiwesPlugin:
    """Read-only adapter exposing the compact YAIWES dataset as a plugin surface."""

    def __init__(self, dataset_root: Path = DATASET_ROOT) -> None:
        self.dataset_root = Path(dataset_root)
        self.registry = _load_json(self.dataset_root / "registry.json")
        self.index = _load_json(self.dataset_root / "indexes" / "shard_index.json")

    def health(self) -> Dict[str, Any]:
        methods = self.index.get("methods", {})
        indexed_records = int(self.index.get("records", 0))
        return {
            "ok": len(methods) == 107 and indexed_records == 1139,
            "methods": len(methods),
            "indexed_records": indexed_records,
            "registry_methods": int(self.registry.get("logical_methods", 0)),
            "mode": "read_only",
        }

    def _read_method(self, method_id: str) -> List[Dict[str, Any]]:
        spec = self.index.get("methods", {}).get(method_id)
        if not spec:
            raise KeyError(f"unknown method_id: {method_id}")
        path = self.dataset_root / spec["path"]
        start = int(spec["start_line"]) - 1
        count = int(spec["count"])
        with path.open("r", encoding="utf-8") as fh:
            lines = list(itertools.islice(fh, start, start + count))
        rows = [json.loads(line) for line in lines if line.strip()]
        if len(rows) != count:
            raise ValueError(f"{method_id}: expected {count} records, got {len(rows)}")
        if any(row.get("method_id") != method_id for row in rows):
            raise ValueError(f"{method_id}: index range contains foreign method records")
        return rows

    def retrieve(
        self,
        method_id: str,
        limits: Optional[Mapping[str, int]] = None,
    ) -> List[Dict[str, Any]]:
        rows = self._read_method(method_id)
        if not limits:
            return rows
        out: List[Dict[str, Any]] = []
        used: Dict[str, int] = {}
        aliases = {
            "debugging": "debugging",
            "causal": "causal",
            "causal_pattern": "causal",
            "error": "error",
            "similar_error": "error",
            "counterexample": "counterexample",
        }
        for row in rows:
            raw = str(row.get("category", ""))
            category = aliases.get(raw, raw)
            maximum = int(limits.get(category, 0))
            if maximum <= 0:
                continue
            if used.get(category, 0) >= maximum:
                continue
            out.append(row)
            used[category] = used.get(category, 0) + 1
        return out

    def route_and_retrieve(
        self,
        query: str,
        parallel_width: int = 1,
        limits: Optional[Mapping[str, int]] = None,
    ) -> List[Dict[str, Any]]:
        """Delegate classification to the existing Control Plane router, read-only."""
        if not CONTROL_ROUTER_PATH.exists():
            raise FileNotFoundError(f"control router missing: {CONTROL_ROUTER_PATH}")
        spec = importlib.util.spec_from_file_location("_yaiwes_control_router", CONTROL_ROUTER_PATH)
        if spec is None or spec.loader is None:
            raise ImportError("unable to load YAIWES Control Plane router")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        bundles = module.route_and_retrieve(
            query,
            parallel_width=parallel_width,
            per_route_limits=dict(limits or {"debugging": 2, "causal": 2, "error": 1, "counterexample": 1}),
        )
        return bundles


def shadow_validate() -> ShadowReport:
    manifest = load_manifest()
    errors = validate_manifest_shape(manifest)
    plugin = DatasetYaiwesPlugin()
    health = plugin.health()
    y26 = plugin.retrieve("Y26")
    routed = plugin.route_and_retrieve(
        "recover resume workflow safely",
        parallel_width=1,
        limits={"debugging": 2, "causal": 2, "error": 1, "counterexample": 1},
    )
    checks = {
        "manifest_valid": not errors,
        "health_107_1139": bool(health["ok"]),
        "tier_a_range_y26_20": len(y26) == 20,
        "router_returns_route": bool(routed),
        "read_only_manifest": (manifest.get("seguridad") or {}).get("permisos", []) == [],
        "testing_not_active": manifest.get("estado") == "testing",
    }
    return ShadowReport(
        passed=all(checks.values()),
        checks=checks,
        details={
            "manifest_errors": errors,
            "health": health,
            "routed_method_ids": [getattr(b.get("route"), "method_id", None) if isinstance(b, dict) else None for b in routed],
        },
    )


def activation_preflight(gpg_key_id: str = "", tribunal_approved: bool = False) -> Dict[str, Any]:
    """Fail closed. This never activates the plugin; it only returns an activation-ready manifest."""
    manifest = load_manifest()
    shadow = shadow_validate()
    blockers: List[str] = []
    if not shadow.passed:
        blockers.append("shadow_failed")
    if not tribunal_approved:
        blockers.append("tribunal_approval_required")
    if not gpg_key_id or gpg_key_id == "PENDIENTE":
        blockers.append("signed_ficha_required")
    if blockers:
        return {"ready": False, "blockers": blockers, "manifest": manifest}
    active = json.loads(json.dumps(manifest))
    active["estado"] = "active"
    active["firma"]["gpg_key_id"] = gpg_key_id
    errors = validate_manifest_shape(active)
    if errors:
        return {"ready": False, "blockers": errors, "manifest": active}
    return {"ready": True, "blockers": [], "manifest": active}


def route_and_retrieve(
    query: str,
    parallel_width: int = 1,
    limits: Optional[Mapping[str, int]] = None,
) -> List[Dict[str, Any]]:
    return DatasetYaiwesPlugin().route_and_retrieve(query, parallel_width, limits)
