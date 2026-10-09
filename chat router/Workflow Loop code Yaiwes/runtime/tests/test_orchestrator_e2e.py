"""O4-19: E2E — misma mission_id, FAIL->replan->PASS, crash sin duplicar."""
import pytest

from wordflow_loop.contracts import Evidence, LayerResult, NodeContract, Status
from wordflow_loop.orchestrator_adapters import (
    AdapterError, ComponentAdapter, EvidenceLedger, create_global_goal,
    oracle_verdict, sheriff_precheck)
from wordflow_loop.orchestrator_contracts import (
    EvidenceRecord, MissionAuthority, MissionContract, OracleStatus,
    ResultEnvelope, TaskContract)


def _run_task(adapter, ledger, task, mission, result_status, evidence=()):
    """Ciclo completo: sheriff -> adapter -> resultado -> oracle -> ledger."""
    node = NodeContract.build(node_id=task.node_id, layer="L", literal="x",
                              mutation=True, authorization=("sheriff",),
                              allowed_paths=("/w",), allowed_actions=("write",))
    errs = sheriff_precheck(node, "write")
    assert errs == []
    out = adapter.invoke(task, mission)
    result = LayerResult(task.node_id, "L", result_status,
                         output=out,
                         evidence=[Evidence(kind=r.kind, ref=r.ref, sha256=r.sha256_hash)
                                   for r in evidence])
    verdict = oracle_verdict(node, result)
    envelope = ResultEnvelope(task.task_id, mission.mission_id, task.node_id,
                              result.status, output=result.output,
                              evidence=evidence).sealed()
    if verdict.status == OracleStatus.PASS:
        ledger.record(task, envelope)
    return verdict, envelope


def test_e2e_same_mission_fail_replan_pass():
    calls = {"n": 0}

    def flaky(payload):
        calls["n"] += 1
        return {"wrote": calls["n"] >= 2}

    adapter = ComponentAdapter("rowboat", invoke_fn=flaky)
    ledger = EvidenceLedger()
    mission = create_global_goal("m-e2e", "close backend", caller="hermes")
    task = TaskContract("t1", mission.mission_id, "n-write", "writer", {})

    # intento 1: el adapter no produce evidencia -> oracle FAIL -> replan
    v1, _ = _run_task(adapter, ledger, task, mission, Status.PASS, ())
    assert v1.status == OracleStatus.FAIL  # PASS sin evidencia -> judge falla

    # Hermes replanifica (solo él crea); mismo mission_id
    mission2 = create_global_goal(mission.mission_id, mission.global_goal, caller="hermes")
    ev = (EvidenceRecord("/out.txt", "artifact", "ab" * 32),)
    v2, env = _run_task(adapter, ledger, task, mission2, Status.PASS, ev)
    assert v2.status == OracleStatus.PASS
    assert env.mission_id == mission.mission_id
    assert ledger.verify()
    assert calls["n"] == 2


def test_crash_resume_no_duplicate_side_effect():
    """Crash tras escribir: re-intento no duplica el side effect."""
    effects: list[str] = []

    def writer(payload):
        key = payload["write_key"]
        if key not in effects:      # idempotencia de side effect
            effects.append(key)
        return {"written": key}

    adapter = ComponentAdapter("dagu_dbos", invoke_fn=writer)
    ledger = EvidenceLedger()
    mission = create_global_goal("m-crash", "g", caller="hermes")
    task = TaskContract("t1", "m-crash", "n1", "writer", {"write_key": "k1"})

    ev = (EvidenceRecord("/w/k1", "file", "cd" * 32),)
    _run_task(adapter, ledger, task, mission, Status.PASS, ev)
    _run_task(adapter, ledger, task, mission, Status.PASS, ev)  # retry post-crash
    assert effects == ["k1"]  # side effect ejecutado UNA vez


def test_oracle_fail_blocks_and_keeps_evidence():
    node = NodeContract.build(node_id="n9", layer="L", literal="x")
    result = LayerResult("n9", "L", Status.BLOCKED,
                         gaps=["dep_missing"],
                         evidence=[Evidence(kind="t", ref="/r")])
    v = oracle_verdict(node, result)
    assert v.status == OracleStatus.BLOCKED
    assert v.evidence
