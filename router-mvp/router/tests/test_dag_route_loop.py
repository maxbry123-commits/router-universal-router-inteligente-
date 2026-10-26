from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integration.chat_mvp import dag as D  # noqa: E402

M = {"provider": "hf", "model": "m1"}


def plan(*nodes):
    return {"schema": "riu.dag/v1", "id": "t", "input_block": "IN", "nodes": list(nodes)}


def seq_executor(replies, calls):
    it = iter(replies)

    def ex(**kw):
        calls.append(kw)
        return {"message": {"content": next(it)}, "usage": {}}

    return ex


def test_route_node_uses_the_chain_callable_and_records_group():
    calls: list[dict] = []

    def ex(**kw):
        calls.append(kw)
        return {"message": {"content": "zafiro"}, "usage": {}, "route": {"provider": "groq", "model": "llama"}}

    r = D.run_dag(plan({"id": "A", "route": {"group": "code"}, "instructions": "x", "expect": {"contains": ["zafiro"]}}), ex)
    assert r["status"] == "PASS" and len(calls) == 1
    assert calls[0]["group"] == "code" and "provider" not in calls[0] and "model" not in calls[0]
    e = r["ledger"][0]
    assert (e["provider"], e["model"], e["group"]) == ("groq", "llama", "code") and r["ledger_valid"]


def test_validation_route_vs_provider():
    ok = plan({"id": "A", "route": {"group": "g2"}, "instructions": "x"})
    assert D.validate(ok) == []
    assert D.validate(plan({"id": "A", "instructions": "x"}))
    assert any("no ambos" in e for e in D.validate(plan({"id": "A", "model": M, "route": {"group": "code"}, "instructions": "x"})))
    assert D.validate(plan({"id": "A", "route": {"group": "nope"}, "instructions": "x"}))
    assert D.validate(plan({"id": "A", "route": "code", "instructions": "x"}))
    with pytest.raises(D.DagError):
        D.run_dag(plan({"id": "A", "instructions": "x"}), lambda **k: {})


def test_validation_loop_rules():
    def v(loop, **extra):
        return D.validate(plan({"id": "A", "model": M, "instructions": "x", "loop": loop, **extra}))

    assert v({"until": {"contains": ["ok"]}, "max_iterations": 3}) == []
    assert v({"until": {"contains": ["ok"]}, "max_iterations": 20}) == []
    for bad in ({"until": {"contains": ["ok"]}, "max_iterations": 0}, {"until": {"contains": ["ok"]}, "max_iterations": 21},
                {"until": {"contains": ["ok"]}, "max_iterations": True}, {"until": {}, "max_iterations": 3}, {"max_iterations": 3}, "x"):
        assert v(bad)
    assert v({"until": {"contains": ["ok"]}, "max_iterations": 3}, retries=1)


def loop_node(n, **kw):
    return {"id": "A", "model": M, "instructions": "x", "loop": {"until": {"contains": ["listo"]}, "max_iterations": n}, **kw}


def test_loop_passes_on_iteration_3_with_feedback_and_ledger():
    calls: list[dict] = []
    r = D.run_dag(plan(loop_node(5), {"id": "B", "model": M, "instructions": "y", "needs": ["A"]}), seq_executor(["a", "b", "listo", "z"], calls))
    a = r["nodes"]["A"]
    assert a["status"] == "PASS" and a["stop_reason"] == "PASSED" and a["iterations"] == 3
    assert r["nodes"]["B"]["status"] == "DONE_UNVERIFIED"
    la = [e for e in r["ledger"] if e["node"] == "A"]
    assert [e["iteration"] for e in la] == [1, 2, 3] and [e["verdict"] for e in la] == ["FAIL", "FAIL", "PASS"]
    assert "FALLÓ" in calls[1]["messages"][1]["content"] and "FALLÓ" not in calls[0]["messages"][1]["content"]
    assert len(r["ledger"]) == 4 and r["ledger_valid"] is True


def test_loop_hits_max_iterations():
    calls: list[dict] = []
    r = D.run_dag(plan(loop_node(4), {"id": "B", "model": M, "instructions": "y", "needs": ["A"]}), seq_executor(["a", "b", "c", "d"], calls))
    a = r["nodes"]["A"]
    assert (a["status"], a["stop_reason"], a["iterations"]) == ("FAIL", "MAX_ITERATIONS", 4) and len(calls) == 4
    assert r["nodes"]["B"]["status"] == "BLOCKED" and r["status"] == "FAIL" and r["ledger_valid"]


def test_loop_stops_at_repeated_x3():
    calls: list[dict] = []
    r = D.run_dag(plan(loop_node(10)), seq_executor(["a", "b", "same", "same", "same", "never"], calls))
    a = r["nodes"]["A"]
    assert (a["status"], a["stop_reason"], a["iterations"]) == ("FAIL", "REPEATED_x3", 5) and len(calls) == 5
    # repeated executor errors count as the same error
    def boom(**kw):
        raise RuntimeError("down")
    r2 = D.run_dag(plan(loop_node(10)), boom)
    assert r2["nodes"]["A"]["stop_reason"] == "REPEATED_x3" and r2["nodes"]["A"]["iterations"] == 3 and r2["ledger_valid"]


def test_loop_with_route_and_chain_tamper_detected():
    calls: list[dict] = []
    node = {"id": "A", "route": {"group": "minor"}, "instructions": "x", "loop": {"until": {"contains": ["listo"]}, "max_iterations": 3}}
    r = D.run_dag(plan(node), seq_executor(["no", "listo"], calls))
    assert r["nodes"]["A"]["stop_reason"] == "PASSED" and all(c["group"] == "minor" for c in calls)
    r["ledger"][0]["checks_failed"] = []
    assert D.verify_ledger(r["ledger"]) is False


def test_old_dag_unchanged_shape_and_ledger_keys():
    calls: list[dict] = []
    node = {"id": "A", "model": M, "instructions": "x", "expect": {"contains": ["ok"]}, "retries": 1}
    r = D.run_dag(plan(node), seq_executor(["no", "ok"], calls))
    assert r["status"] == "PASS" and [c["provider"] for c in calls] == ["hf", "hf"]
    assert "stop_reason" not in r["nodes"]["A"]
    assert set(r["ledger"][0]) == {"node", "attempt", "provider", "model", "prompt_sha256", "reply_sha256", "cached", "verdict",
                                   "checks_failed", "prev", "hash"}
    assert r["ledger_valid"]
