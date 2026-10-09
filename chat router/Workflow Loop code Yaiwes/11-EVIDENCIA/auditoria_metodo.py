"""Auditoría reproducible de contratos y recibos; no llama a modelos."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "chat router/Workflow Loop code Yaiwes/01-PLAN/DM-METODO-DAG.json"
AREAS = {"ui", "runtime", "memory", "plan", "code"}
ACTORS = {"sentinel", "hermes", "openclaw"}
INDEPENDENT = {"tests", "security", "integration", "readback", "service_health", "operation", "restart", "browser", "responsive", "second_pass"}
DELIVERY_LEVELS = {
    "local": "tests", "suite": "full_suite", "ci": "ci",
    "browser": "browser", "external_services": "service_health",
}


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _receipt_valid(
    receipt: dict, root: Path, executor: str, independent: bool,
    expected_actor: str | None = None,
) -> bool:
    if not isinstance(receipt, dict) or receipt.get("status") != "PASS":
        return False
    actor = receipt.get("actor")
    if not isinstance(actor, str) or not actor or (independent and actor == executor) or (
        expected_actor is not None and actor != expected_actor
    ):
        return False
    name = receipt.get("path")
    digest = receipt.get("sha256")
    if not isinstance(name, str) or not isinstance(digest, str):
        return False
    path = (root / name).resolve()
    return path.is_relative_to(root.resolve()) and path.is_file() and _digest(path) == digest


def validate_policy(policy: dict) -> None:
    if policy.get("schema") != "yaiwes.method-audit/v1":
        raise ValueError("INVALID_POLICY_SCHEMA")
    for key, prefix in (("goals", "DM-G"), ("council", "DM-C")):
        ids = [entry["id"] for entry in policy[key]]
        if ids != [f"{prefix}{number:02}" for number in range(1, 13)]:
            raise ValueError(f"INVALID_{key.upper()}_IDS")
    changes = {item["id"]: item for item in policy["changes"]}
    if len(changes) != 8 or set(changes) != {f"P{i:02}" for i in range(1, 9)}:
        raise ValueError("INVALID_CHANGE_IDS")
    visiting: set[str] = set()
    visited: set[str] = set()

    def walk(node: str) -> None:
        if node not in changes or node in visiting:
            raise ValueError("INVALID_DAG_DEPENDENCY_OR_CYCLE")
        if node in visited:
            return
        visiting.add(node)
        for dependency in changes[node]["needs"]:
            walk(dependency)
        visiting.remove(node)
        visited.add(node)

    for identifier in changes:
        walk(identifier)


def audit(packet: dict, root: Path = ROOT, policy_path: Path = POLICY) -> dict:
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    validate_policy(policy)
    areas = packet.get("areas", [])
    if not isinstance(areas, list) or not areas or set(areas) - AREAS:
        raise ValueError("UNKNOWN_AUDIT_AREA")
    executor = packet.get("executor")
    if not isinstance(executor, str) or not executor:
        raise ValueError("MISSING_EXECUTOR")
    checks = packet.get("checks", [])
    if not isinstance(checks, list):
        raise TypeError("INVALID_CHECKS")
    if any(not isinstance(item, dict) or not isinstance(item.get("kind"), str) for item in checks):
        raise TypeError("INVALID_CHECK")
    kinds = {item["kind"] for item in checks}
    if len(kinds) != len(checks):
        raise ValueError("DUPLICATE_CHECK")
    by_kind = {item["kind"]: item for item in checks}
    required = {kind for goal in policy["goals"] for kind in goal["requires"]}
    for area in areas:
        required.update(policy["risk"][area])

    checked = {
        kind: _receipt_valid(by_kind[kind], root, executor, kind in INDEPENDENT)
        for kind in sorted(required & kinds)
    }
    delivery = {
        level: "PASS" if kind in by_kind and _receipt_valid(by_kind[kind], root, executor, True)
        else "FAIL" if kind in by_kind and by_kind[kind].get("status") == "FAIL"
        else "NOT_VERIFIED"
        for level, kind in DELIVERY_LEVELS.items()
    }
    missing = sorted(kind for kind in required if not checked.get(kind, False))
    labels = [
        {
            "id": f"AUDIT-{area.upper()}",
            "severity": "CRITICAL" if area in {"ui", "runtime", "memory", "plan"} else "HIGH",
            "required": sorted(set(policy["risk"][area]) | {"tests", "readback"}),
            "reviewers": sorted({actor for kind in (area, "security", "integration") for actor in policy["review_owners"].get(kind, [])}),
            "status": "NEED_EVIDENCE" if missing else "READY_FOR_REVIEW",
        }
        for area in sorted(set(areas))
    ]
    reviews = packet.get("reviews", {})
    if not isinstance(reviews, dict) or set(reviews) - ACTORS:
        raise ValueError("INVALID_REVIEWERS")
    pending_reviews = sorted({
        actor for label in labels for actor in label["reviewers"]
        if not _receipt_valid(reviews.get(actor, {}), root, executor, True, actor)
        or label["id"] not in reviews[actor].get("labels", [])
    })
    goals = [
        {
            "id": goal["id"],
            "status": "PASS" if all(checked.get(kind, False) for kind in goal["requires"]) else "INCOMPLETE",
            "missing": sorted(kind for kind in goal["requires"] if not checked.get(kind, False)),
        }
        for goal in policy["goals"]
    ]
    conflicts = packet.get("conflicts", [])
    failures = sorted(kind for kind, item in by_kind.items() if item.get("status") == "FAIL")
    if conflicts:
        verdict = "CONTRADICTION"
    elif failures:
        verdict = "FAIL"
    elif any(item.get("status") == "BLOCKED" for item in checks):
        verdict = "BLOCKED"
    elif missing or pending_reviews:
        verdict = "INCOMPLETE"
    else:
        verdict = "PASS"
    canonical = json.dumps(packet, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {
        "schema": "yaiwes.method-audit-result/v1",
        "packet_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "verdict": verdict,
        "goals": goals,
        "labels": labels,
        "missing": missing,
        "pending_reviews": pending_reviews,
        "conflicts": conflicts,
        "failures": failures,
        "verification_levels": delivery,
        "council": [{"id": item["id"], "role": item["role"], "status": "PENDING_ADVICE"} for item in policy["council"]],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path, help="JSON de claims y recibos verificados")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    result = audit(json.loads(args.packet.read_text(encoding="utf-8")), args.root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["verdict"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
