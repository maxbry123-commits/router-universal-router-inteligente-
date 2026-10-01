"""Regresiones de la política de método y el plan canónico."""

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "chat router/11-EVIDENCIA"
sys.path.insert(0, str(EVIDENCE))

spec = importlib.util.spec_from_file_location("auditoria_metodo", EVIDENCE / "auditoria_metodo.py")
auditoria = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auditoria)
import puerta

guard_spec = importlib.util.spec_from_file_location(
    "checkpoint_guard_method_test", ROOT / "chat router/03-ESTADO/checkpoint_guard.py"
)
guard = importlib.util.module_from_spec(guard_spec)
guard_spec.loader.exec_module(guard)

visual_spec = importlib.util.spec_from_file_location(
    "catalogo_visual_test", ROOT / "chat router/01-PLAN/catalogo_visual.py"
)
visual = importlib.util.module_from_spec(visual_spec)
visual_spec.loader.exec_module(visual)

inventory_spec = importlib.util.spec_from_file_location(
    "inventory_memory_test", ROOT / "chat router/03-ESTADO/inventory_memory.py"
)
inventory = importlib.util.module_from_spec(inventory_spec)
inventory_spec.loader.exec_module(inventory)


def test_memory_readback_does_not_promote_source_to_runtime():
    result = inventory.inspect_sources()
    assert len(result["components"]) == 13
    components = {item["name"]: item for item in result["components"]}
    assert components["sqlite"]["source"] == "PRESENT"
    assert components["sqlite"]["adapter"] == "PRESENT"
    assert all(item["runtime"] == "NOT_VERIFIED_THIS_RUN" for item in result["components"])


def test_visual_catalog_readback_and_original_hashes():
    catalog = visual.build_catalog()
    assert catalog["count"] == 65
    assert [item["id"] for item in catalog["items"]] == [f"UI-REF-{i:03}" for i in range(1, 66)]
    assert json.loads(visual.OUTPUT.read_text(encoding="utf-8")) == catalog
    assert all(item["status"] == "PENDING_VISUAL_VERIFICATION" for item in catalog["items"])
    assert all(item["backend"] == "NOT_CONNECTED" for item in catalog["items"])


def test_plan_requires_known_acyclic_dependencies_and_preserves_source(tmp_path, monkeypatch):
    original = tmp_path / "original.md"
    original.write_text("100 pasos originales", encoding="utf-8")
    plan_path = tmp_path / "PLAN.json"
    steps = [{"id": f"STEP-{index:03}", "needs": []} for index in range(1, 101)]
    plan = {
        "status": "VALIDATED", "source_path": "original.md",
        "source_sha256": hashlib.sha256(original.read_bytes()).hexdigest(),
        "steps": steps,
    }
    monkeypatch.setattr(guard, "ROOT", tmp_path)
    monkeypatch.setattr(guard, "PLAN_PATH", plan_path)
    steps[0]["needs"] = ["STEP-999"]
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    with pytest.raises(ValueError, match="PLAN_DEPENDENCY_UNKNOWN"):
        guard.load_plan()
    steps[0]["needs"] = ["STEP-002"]
    steps[1]["needs"] = ["STEP-001"]
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    with pytest.raises(ValueError, match="PLAN_DEPENDENCY_CYCLE"):
        guard.load_plan()
    steps[0]["needs"] = []
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    assert guard.load_plan()[1] == [step["id"] for step in steps]
    assert original.read_text(encoding="utf-8") == "100 pasos originales"


def test_checkpoint_repairs_projection_from_append_only_log(tmp_path, monkeypatch):
    event = guard.ui_bridge._state_event({
        "type": "TASK_CLAIMED", "project": "chat-yaiwes", "task": "UI-T-01", "actor": "devin",
    }, 1)
    (tmp_path / "BITACORA.jsonl").write_text(json.dumps(event) + "\n", encoding="utf-8")
    (tmp_path / "STATE.json").write_text('{"revision": 0}', encoding="utf-8")
    (tmp_path / "CRAZY_WALL.json").write_text("corrupted", encoding="utf-8")
    checkpoint = tmp_path / "CHECKPOINT.json"
    checkpoint.write_text('{"bitacora_revision": 0}', encoding="utf-8")
    monkeypatch.setattr(guard, "STATE_DIR", tmp_path)
    monkeypatch.setattr(guard, "CHECKPOINT_PATH", checkpoint)
    assert guard.verify_projection() == 1
    assert json.loads((tmp_path / "STATE.json").read_text(encoding="utf-8"))["revision"] == 1
    assert guard.verify_projection() == 1


def test_s2_documentary_claim_cannot_pass_code_without_tests(tmp_path):
    source = tmp_path / "README.md"
    source.write_text("fuente", encoding="utf-8")
    pack = {
        "known_facts": [{"fact": "archivo disponible"}], "conflicts": [],
        "unknown": [], "sources": [str(source)],
        "parsed": {"task_type": "MODIFY_CODE", "forbidden": []},
    }
    result = puerta.despues("modifica código", {"claims": [{"tipo": "archivo", "ruta": str(source)}]}, pack=pack)
    assert result["veredicto"] == "INCOMPLETE"
    assert not result["detalle_goals"]["G09"]["ok"]
    assert not result["detalle_goals"]["G10"]["ok"]


def test_method_policy_rejects_missing_evidence_and_cannot_self_certify(tmp_path):
    artifact = tmp_path / "receipt.txt"
    artifact.write_text("prueba independiente", encoding="utf-8")
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    policy = json.loads(auditoria.POLICY.read_text(encoding="utf-8"))
    auditoria.validate_policy(policy)
    required = {kind for goal in policy["goals"] for kind in goal["requires"]}
    required.update(policy["risk"]["code"])

    def receipt(actor):
        return {"status": "PASS", "actor": actor, "path": "receipt.txt", "sha256": digest}

    packet = {"areas": ["code"], "executor": "ejecutor", "checks": [
        {"kind": kind, **receipt("verificador")} for kind in sorted(required)
    ], "reviews": {
        actor: {**receipt(actor), "labels": ["AUDIT-CODE"]}
        for actor in ("sentinel", "openclaw")
    }}
    result = auditoria.audit(packet, root=tmp_path)
    assert result["verdict"] == "PASS" and len(result["goals"]) == 12
    assert len(result["council"]) == 12
    assert result["verification_levels"] == {
        "local": "PASS", "suite": "NOT_VERIFIED", "ci": "NOT_VERIFIED",
        "browser": "NOT_VERIFIED", "external_services": "NOT_VERIFIED",
    }
    packet["checks"] = [check for check in packet["checks"] if check["kind"] != "tests"]
    result = auditoria.audit(packet, root=tmp_path)
    assert result["verdict"] == "INCOMPLETE" and "tests" in result["missing"]
    packet["checks"].append({"kind": "tests", **receipt("ejecutor")})
    assert auditoria.audit(packet, root=tmp_path)["verdict"] == "INCOMPLETE"
    packet["checks"][-1] = {"kind": "tests", **receipt("verificador")}
    packet["conflicts"] = ["fuente A contradice B"]
    assert auditoria.audit(packet, root=tmp_path)["verdict"] == "CONTRADICTION"
    packet["conflicts"] = []
    packet["checks"][-1]["status"] = "FAIL"
    assert auditoria.audit(packet, root=tmp_path)["verdict"] == "FAIL"
    packet["checks"][-1]["status"] = "PASS"
    artifact.write_text("corrompido", encoding="utf-8")
    assert auditoria.audit(packet, root=tmp_path)["verdict"] == "INCOMPLETE"


def test_critical_label_requires_external_reviews(tmp_path):
    artifact = tmp_path / "evidence.txt"
    artifact.write_text("receipt", encoding="utf-8")
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    policy = json.loads(auditoria.POLICY.read_text(encoding="utf-8"))
    kinds = {kind for goal in policy["goals"] for kind in goal["requires"]}
    kinds.update(policy["risk"]["ui"])
    receipt = {"status": "PASS", "path": "evidence.txt", "sha256": digest, "actor": "verificador"}
    packet = {
        "areas": ["ui"], "executor": "ejecutor", "checks": [{"kind": kind, **receipt} for kind in kinds],
        "reviews": {},
    }
    result = auditoria.audit(packet, root=tmp_path)
    assert result["verdict"] == "INCOMPLETE"
    assert result["labels"][0]["id"] == "AUDIT-UI"
    assert set(result["pending_reviews"]) == {"hermes", "openclaw", "sentinel"}
    packet["reviews"] = {
        actor: {**receipt, "actor": actor, "labels": ["AUDIT-UI"]}
        for actor in ("hermes", "openclaw", "sentinel")
    }
    assert auditoria.audit(packet, root=tmp_path)["verdict"] == "PASS"
    packet["reviews"]["sentinel"]["actor"] = "verificador"
    result = auditoria.audit(packet, root=tmp_path)
    assert result["verdict"] == "INCOMPLETE"
    assert result["pending_reviews"] == ["sentinel"]
