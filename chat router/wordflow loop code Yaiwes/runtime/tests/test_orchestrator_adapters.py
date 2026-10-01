"""O4-04..O4-18: guards del orquestador con adapters fail-closed."""
import os
import pytest

from wordflow_loop.contracts import Evidence, LayerResult, NodeContract, Status
from wordflow_loop.orchestrator_adapters import (
    AdapterError, ComponentAdapter, EvidenceLedger, assert_no_global_goal_mutation,
    create_global_goal, input_shark, oracle_verdict, sheriff_precheck)
from wordflow_loop.orchestrator_contracts import (
    EvidenceRecord, MissionAuthority, MissionContract, OracleStatus,
    ResultEnvelope, TaskContract)


def _node(**kw):
    base = NodeContract.build(node_id="n1", layer="L", literal="x")
    return NodeContract(**{**base.__dict__, **kw})


def test_only_hermes_creates_global_goal():
    m = create_global_goal("m1", "goal", caller="hermes")
    assert isinstance(m, MissionContract)
    with pytest.raises(PermissionError):
        create_global_goal("m2", "x", caller="rowboat")


def test_adapter_cannot_mutate_global_goal():
    m = MissionContract.build("m1", "goal-a", MissionAuthority.HERMES)
    with pytest.raises(AdapterError):
        assert_no_global_goal_mutation("rowboat", m, "otro-goal")


def test_sheriff_precheck_mutation_needs_authorization():
    n = _node(mutation=True, authorization=("sheriff",), allowed_paths=("/w",),
              allowed_actions=("write",))
    assert sheriff_precheck(n, "write") == []
    n2 = _node(mutation=True, authorization=(), allowed_paths=("/w",))
    errs = sheriff_precheck(n2, "write")
    assert any("sheriff" in e for e in errs)


def test_adapter_fail_closed_sin_runtime():
    a = ComponentAdapter("rowboat")
    m = MissionContract.build("m1", "g", MissionAuthority.HERMES)
    t = TaskContract("t1", "m1", "n1", "writer", {})
    os.environ.pop("YAIWES_ROWBOAT_COMMAND", None)
    with pytest.raises(AdapterError, match="RUNTIME_UNAVAILABLE"):
        a.invoke(t, m)


def test_adapter_invoke_fn_blocked_goal_mutation():
    a = ComponentAdapter("rowboat", invoke_fn=lambda p: {"ok": True})
    m = MissionContract.build("m1", "g", MissionAuthority.HERMES)
    t = TaskContract("t1", "m1", "n1", "writer", {"global_goal": "HACK"})
    with pytest.raises(AdapterError):
        a.invoke(t, m)


def test_evidence_ledger_tamper_and_missing_detected():
    led = EvidenceLedger()
    env = ResultEnvelope("t1", "m1", "n1", Status.PASS,
                         evidence=(EvidenceRecord("/e", "test", "aa" * 32),)).sealed()
    led.record(TaskContract("t1", "m1", "n1", "writer", {}), env)
    assert led.verify()
    led.rows[0]["event"]["status"] = "FAIL"  # tamper
    assert not led.verify()


def test_evidence_ledger_rechaza_pass_sin_evidencia():
    led = EvidenceLedger()
    env = ResultEnvelope("t2", "m1", "n1", Status.PASS)
    with pytest.raises(AdapterError, match="PASS_WITHOUT_EVIDENCE"):
        led.record(TaskContract("t2", "m1", "n1", "writer", {}), env)


def test_oracle_verdict_pass_fail_incomplete():
    n = _node()
    ok = LayerResult("n1", "L", Status.PASS,
                     evidence=[Evidence(kind="t", ref="/e", sha256="aa" * 32)])
    assert oracle_verdict(n, ok).status == OracleStatus.PASS
    bad = LayerResult("n1", "L", Status.PASS)
    assert oracle_verdict(n, bad).status == OracleStatus.FAIL
    inc = LayerResult("n1", "L", Status.INCONCLUSIVE, gaps=["g1"])
    assert oracle_verdict(n, inc).status == OracleStatus.INCOMPLETE


def test_input_shark_missing_fields():
    r = input_shark({"mission_id": "m1"})
    assert not r["complete"] and "global_goal" in r["missing_fields"]
    r2 = input_shark({"mission_id": "m1", "global_goal": "g", "allowed_roles": ["writer"]})
    assert r2["complete"] and r2["normalized_goal_sha"]
