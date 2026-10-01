from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integration.chat_mvp import agent_gates, dag

JOB = {"job_id": "work-1", "objective": "Inspect file", "scope": ["chat router/README.md"],
       "acceptance": ["read-back"]}
NODE = {"id": "A", "type": "agent", "agente": "codex", "rol": "FINAL_REVIEW_AND_CORRECT",
        "model": {"provider": "local", "model": "reviewer"}, "instructions": "Inspect",
        "input": JOB, "output_schema": "yaiwes.result/v1", "allowed_paths": JOB["scope"],
        "puertas": ["sheriff", "judge"], "checklist": {"scope": True, "permissions": True},
        "step": 1, "total_steps": 1}
PLAN = {"schema": dag.SCHEMA, "id": "agent-demo", "input_block": "Inspect only", "nodes": [NODE]}
TRUTH = {"CORE": {"state": "READY"}, "CONTRATOS": {"state": "READY"},
         "DECISIONES": {}, "GRAFO": {"state": "READY"}}
REPLY = json.dumps({"job_id": "work-1", "agent": "codex", "status": "PASS",
                    "changed_files": [], "tests": [], "evidence": []})


def _executor(**kwargs):
    return {"message": {"content": REPLY}, "usage": {"prompt_tokens": 5, "completion_tokens": 3}}


def _proof():
    return {"A": {"status": "PASS", "tests": ["verified externally"], "changed_files": [],
                  "input_sha256": agent_gates._hash(JOB), "output_sha256": agent_gates._hash(REPLY)}}


def _run(plan=PLAN, **kwargs):
    events = []
    result = dag.run_dag(plan, _executor, active_truth=TRUTH,
                         state_emit=lambda body: events.append(body) or {"ok": True}, **kwargs)
    return result, events


def test_agent_graph_matches_registry_and_codex_follows_fixer():
    expected = agent_gates.graph()
    saved = json.loads((agent_gates.ROOT / "chat router/03-ESTADO/AGENT_GRAPH.json").read_text())
    assert saved == expected
    assert ["meta_fixer", "codex"] in saved["edges"] and ["codex", "sentinel"] in saved["edges"]


def test_agent_pass_requires_trusted_evidence_and_both_reviews():
    reviews = {"A": {"hermes": {"approve": True}, "openclaw": {"approve": True}}}
    result, events = _run(reviews=reviews, evidence=_proof())
    assert result["status"] == "PASS" and result["ledger_valid"]
    assert result["nodes"]["A"]["checkpoint"]["input_sha256"] == _proof()["A"]["input_sha256"]
    assert events[0]["type"] == "CHECKPOINT_RECORDED"
    gap, blocked = _run(evidence=_proof())
    assert gap["status"] == "GAP" and gap["nodes"]["A"]["state"] == "needs_intervention"
    assert blocked[0]["type"] == "TASK_BLOCKED"


@pytest.mark.parametrize("change,error", [
    ({"agente": "unknown"}, "AGENT_INVALID_ROLE"),
    ({"rol": "director"}, "AGENT_INVALID_ROLE"),
    ({"allowed_paths": ["/etc/passwd"]}, "AGENT_JOB_SCOPE_INVALID"),
    ({"checklist": {"scope": "yes"}}, "AGENT_CHECKLIST_INVALID"),
    ({"puertas": ["judge"]}, "AGENT_GATES_REQUIRED"),
])
def test_invalid_agents_are_rejected(change, error):
    plan = copy.deepcopy(PLAN)
    plan["nodes"][0].update(change)
    assert any(error in issue for issue in dag.validate(plan))
    with pytest.raises(dag.DagError):
        dag.run_dag(plan, _executor)


def test_preflight_blocks_without_truth_or_with_conflict_or_failed_checklist():
    cases = [(None, "ACTIVE_TRUTH_MISSING"), (
        {**TRUTH, "GRAFO": {"state": "BLOCKED"}}, "ACTIVE_TRUTH_CONFLICT:state")]
    calls = []
    for truth, reason in cases:
        calls.clear()
        result = dag.run_dag(PLAN, lambda **k: calls.append(k), active_truth=truth,
                             state_emit=lambda body: {"ok": True})
        assert result["nodes"]["A"]["checks_failed"] == [reason] and not calls
    plan = copy.deepcopy(PLAN)
    plan["nodes"][0]["checklist"]["scope"] = False
    assert _run(plan)[0]["nodes"]["A"]["checks_failed"] == ["P1_CHECKLIST_FAILED"]


def test_p2_archive_and_p1_scope_drift_halt_downstream():
    plan = copy.deepcopy(PLAN)
    plan["nodes"][0]["token_budget"] = 10
    result, _ = _run(plan, reviews={"A": {"hermes": {"approve": True}, "openclaw": {"approve": True}}},
                     evidence=_proof())
    assert result["nodes"]["A"]["checks_failed"] == ["P2_ARCHIVE_REQUIRED"]
    archived = []
    result, _ = _run(plan, reviews={"A": {"hermes": {"approve": True}, "openclaw": {"approve": True}}},
                     evidence=_proof(), archive=lambda cp: archived.append(cp) or True)
    assert result["status"] == "PASS" and archived and result["nodes"]["A"]["checkpoint"]["archived"]
    wrong = REPLY.replace('"changed_files": []', '"changed_files": ["other"]')
    downstream = copy.deepcopy(PLAN)
    downstream["nodes"].append({"id": "B", "model": {"provider": "local", "model": "m"},
                                "instructions": "next", "needs": ["A"]})
    events = []
    out = dag.run_dag(downstream, lambda **k: {"message": {"content": wrong}, "usage": {}},
                      active_truth=TRUTH, state_emit=lambda body: events.append(body) or {"ok": True})
    assert out["nodes"]["A"]["checks_failed"] == ["P1_SCOPE_DRIFT"]
    assert out["nodes"]["B"]["status"] == "BLOCKED"


def test_state_hub_failure_blocks_agent_pass():
    result = dag.run_dag(PLAN, _executor, active_truth=TRUTH, reviews={
        "A": {"hermes": {"approve": True}, "openclaw": {"approve": True}}},
        evidence=_proof(), state_emit=lambda body: {"ok": False})
    assert result["status"] == "GAP" and result["nodes"]["A"]["checks_failed"] == ["STATE_HUB_EMIT_FAILED"]
