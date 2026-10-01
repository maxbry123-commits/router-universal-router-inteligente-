"""T-11-C/D runtime tests: claim/lease, STUCK, failure policy, crash/resume, bootstrap."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integration.chat_mvp import task_runtime as tr


def _claim(cid="c1", scope=None, expires=1000.0):
    return {
        "claim_id": cid, "node_id": "n1", "worker_id": "w1", "base_sha": "abc",
        "write_scope": scope or ["chat router/03-ESTADO"],
        "lease_expires_at": expires, "heartbeat_at": 0.0, "status": "CLAIMED",
    }


def test_second_writer_overlapping_scope_rejected():
    cm = tr.ClaimManager()
    cm.acquire(_claim("c1"), now=100.0)
    with pytest.raises(tr.LeaseError, match="SCOPE_OVERLAP"):
        cm.acquire(_claim("c2", scope=["chat router/03-ESTADO/sub"]), now=100.0)
    # scope disjunto sí se acepta
    cm.acquire(_claim("c3", scope=["otro/dir"]), now=100.0)


def test_expired_lease_denies_side_effect():
    cm = tr.ClaimManager(lease_seconds=10)
    cm.acquire(_claim("c1", expires=110.0), now=100.0)
    cm.side_effect_allowed("c1", "chat router/03-ESTADO/x", now=105.0)
    with pytest.raises(tr.LeaseError, match="SIDE_EFFECT_DENIED_LEASE_EXPIRED"):
        cm.side_effect_allowed("c1", "chat router/03-ESTADO/x", now=115.0)
    cm2 = tr.ClaimManager()
    cm2.acquire(_claim("c9"), now=100.0)
    with pytest.raises(tr.LeaseError, match="SIDE_EFFECT_DENIED_SCOPE"):
        cm2.side_effect_allowed("c9", "fuera/de/scope", now=100.0)


def test_heartbeat_renews_within_limits():
    cm = tr.ClaimManager(lease_seconds=10)
    cm.acquire(_claim("c1", expires=110.0), now=100.0)
    renewed = cm.heartbeat("c1", now=105.0)
    assert renewed["lease_expires_at"] == 115.0
    assert renewed["heartbeat_at"] == 105.0
    with pytest.raises(tr.LeaseError, match="LEASE_EXPIRED"):
        cm.heartbeat("c1", now=999.0)


def test_stuck_detector_fingerprint():
    sd = tr.StuckDetector(max_repeats=3)
    args = {"cmd": "ls"}
    assert sd.record("shell", args, {"n": 0}, new_evidence=True) is None
    assert sd.record("shell", args, {"n": 0}, new_evidence=False) is None
    assert sd.record("shell", args, {"n": 0}, new_evidence=False) is None
    assert sd.record("shell", args, {"n": 0}, new_evidence=False) == "STUCK"


def test_failure_policy_typed():
    assert tr.FAILURE_POLICY[tr.FailureKind.AUTH]["requires_human"] is True
    assert tr.FAILURE_POLICY[tr.FailureKind.STUCK]["next_state"] == "STRATEGY_CHANGE"
    assert tr.classify(tr.LeaseError("x")) == tr.FailureKind.DEPENDENCY
    assert tr.classify(TimeoutError("x")) == tr.FailureKind.RETRYABLE
    assert tr.classify(PermissionError("x")) == tr.FailureKind.AUTH


def test_crash_resume_verifies_hash_and_skips_done_effects():
    cp = tr.Checkpoint(run_id="r1", node_id="n1", input_hash="ih",
                       state_hash="sh", base_sha="base1")
    data = tr.asdict(cp)
    ok = tr.verify_checkpoint(data, expected_state_hash="sh", base_sha="base1")
    assert ok.run_id == "r1"
    with pytest.raises(tr.ContractError, match="STATE_HASH_MISMATCH"):
        tr.verify_checkpoint(data, expected_state_hash="otro", base_sha="base1")
    with pytest.raises(tr.ContractError, match="BASE_SHA_MISMATCH"):
        tr.verify_checkpoint(data, expected_state_hash="sh", base_sha="otro")
    assert tr.reconcile_side_effect(ok, "write:file1") is False
    assert tr.reconcile_side_effect(ok, "write:file1") is True  # no duplicar


def test_worker_bootstrap_fail_closed():
    cm = tr.ClaimManager()
    contract = {"task_id": "t1", "node_id": "n1", "worker_id": "w1",
                "capability": "code", "write_scope": ["a"], "base_sha": "b1"}
    out = tr.worker_bootstrap(contract, "w1", "n1", ["code"], "b1", True, cm, now=1.0)
    assert out["status"] == "READY"
    with pytest.raises(tr.BootstrapError, match="verify_worker"):
        tr.worker_bootstrap(contract, "otro", "n1", ["code"], "b1", True, cm)
    with pytest.raises(tr.BootstrapError, match="verify_base_sha"):
        tr.worker_bootstrap(contract, "w1", "n1", ["code"], "distinto", True, cm)
    with pytest.raises(tr.BootstrapError, match="verify_environment"):
        tr.worker_bootstrap(contract, "w1", "n1", ["code"], "b1", False, cm)
    with pytest.raises(tr.BootstrapError, match="validate_schema"):
        tr.worker_bootstrap({"task_id": "t1"}, "w1", "n1", ["code"], "b1", True, cm)


def _ws(child="ws1", workspace="ws/dir1", claim="c1"):
    return {"parent_id": "p", "child_id": child, "node_id": "n1", "claim_id": claim,
            "workspace": workspace, "base_sha": "b1", "write_scope": ["ws"],
            "command_id": "cmd1"}


def test_workspace_isolation_and_promote(tmp_path):
    cm = tr.ClaimManager(lease_seconds=100)
    cm.acquire({
        "claim_id": "c1", "node_id": "n1", "worker_id": "w1", "base_sha": "b1",
        "write_scope": ["ws"], "lease_expires_at": 200.0, "heartbeat_at": 0.0,
        "status": "CLAIMED"}, now=100.0)
    reg = tr.WorkspaceRegistry()
    reg.register(_ws(), cm, now=100.0)
    with pytest.raises(tr.LeaseError, match="WORKSPACE_SHARED"):
        reg.register(_ws(child="ws2", workspace="ws/dir1"), cm, now=100.0)
    reg.register(_ws(child="ws2", workspace="ws/dir2"), cm, now=100.0)
    with pytest.raises(tr.LeaseError, match="PROMOTE_DENIED"):
        reg.promote("ws1", test_passed=False, target_sha="b1")
    reg2 = tr.WorkspaceRegistry()
    reg2.register(_ws(child="ws3", workspace="ws/dir3"), cm, now=100.0)
    with pytest.raises(tr.LeaseError, match="BASE_SHA_CONFLICT"):
        reg2.promote("ws3", test_passed=True, target_sha="otro")
    assert reg2.promote("ws3", test_passed=True, target_sha="b1")["status"] == "PROMOTED"


def test_llm_output_typed_fail_closed():
    good = {"decision": "aprobar", "confidence": 0.9, "evidence_refs": ["e1"],
            "recommended_action": "x", "unknowns": []}
    assert tr.validate_llm_output(good) is good
    with pytest.raises(tr.ContractError):
        tr.validate_llm_output({"decision": "x"})
    with pytest.raises(tr.ContractError):
        tr.validate_llm_output({**good, "extra": 1})
    with pytest.raises(tr.ContractError):
        tr.validate_llm_output("not a dict")


def test_research_result_schema():
    ok = {"query": "q", "sources": [], "source_type": [], "claims": [],
          "cross_check": [], "new_evidence": False, "conclusion": "none"}
    assert tr.validate_research_result(ok) is ok
    with pytest.raises(tr.ContractError):
        tr.validate_research_result({**ok, "new_evidence": "yes"})


def test_task_folder_idempotent(tmp_path):
    r1 = tr.ensure_task_folder(str(tmp_path), "task-1")
    r2 = tr.ensure_task_folder(str(tmp_path), "task-1")
    assert r1["path"] == r2["path"]
    assert sorted(r1["created"]) == sorted(tr._TASK_FILES)
    assert r2["created"] == []


def test_run_ledger_finalize_requires_judge_and_evidence():
    rl = tr.RunLedger()
    rl.dispatch("r1")
    rl.transition("r1", "RUNNING")
    with pytest.raises(tr.ContractError, match="NEEDS_EVIDENCE"):
        rl.transition("r1", "VERIFIED")
    rl.attach_evidence("r1", {"id": "e1"})
    rl.transition("r1", "VERIFIED")
    with pytest.raises(tr.ContractError, match="JUDGE"):
        rl.finalize("r1", {})
    out = rl.finalize("r1", {"judge": "j1", "decision": "PASS"})
    assert out["state"] == "FINALIZED"
    with pytest.raises(tr.ContractError, match="TRANSITION_INVALID"):
        rl.transition("r1", "DISPATCHED")
