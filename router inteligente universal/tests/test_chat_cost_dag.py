from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integration.chat_mvp import core, dag_cli  # noqa: E402
from integration.chat_mvp import dag as D  # noqa: E402
from integration.chat_mvp import providers as prov  # noqa: E402
from integration.chat_mvp import usage as U  # noqa: E402
from integration.chat_mvp.store import Store  # noqa: E402

M = {"provider": "hf", "model": "m1"}
M2 = {"provider": "hf", "model": "m2"}
BASE = {"schema": "riu.dag/v1", "id": "t", "input_block": "HAZ X literal", "nodes": [
    {"id": "A", "stage": "worker", "model": M, "instructions": "di zafiro", "expect": {"contains": ["zafiro"]}},
    {"id": "B", "model": M, "instructions": "json", "needs": ["A"], "expect": {"json_keys": ["ok"]}, "retries": 1},
    {"id": "C", "model": M, "instructions": "sin expect", "needs": ["A"]},
]}


def test_usage_normalization_and_direct_providers():
    assert U.normalize_usage({"prompt_tokens": 100, "completion_tokens": 5, "prompt_cache_hit_tokens": 80}) == {"input": 100, "output": 5, "cached": 80}
    assert U.normalize_usage({"prompt_tokens": 10, "prompt_tokens_details": {"cached_tokens": 4}})["cached"] == 4
    assert U.normalize_usage({"prompt_tokens": 10, "cached_tokens": 6})["cached"] == 6
    assert U.normalize_usage(None) == {"input": 0, "output": 0, "cached": 0}
    assert {"deepseek", "moonshot", "minimax"} <= set(prov.PROVIDERS)


def test_response_cache_refresh_temperature_and_cost_accounting(tmp_path, monkeypatch):
    s = Store(tmp_path)
    calls = []

    def fake(provider, key, model, messages, max_tokens, temperature=None):
        calls.append(1)
        return {"message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop",
                "usage": {"prompt_tokens": 1000, "completion_tokens": 10, "prompt_cache_hit_tokens": 900}}

    monkeypatch.setattr(core, "call_via_router", fake)
    monkeypatch.setenv("RIU_PRICES_JSON", '{"deepseek/m": {"in": 1.0, "cached_in": 0.1, "out": 2.0}}')
    msgs = [{"role": "user", "content": "hola"}]
    a = core.run_completion(s, "o", "deepseek", "k", "m", msgs, 100)
    b = core.run_completion(s, "o", "deepseek", "k", "m", msgs, 100)
    c = core.run_completion(s, "o", "deepseek", "k", "m", msgs, 100, refresh=True)
    d = core.run_completion(s, "o", "deepseek", "k", "m", msgs, 100, temperature=0.9)
    e = core.run_completion(s, "o", "deepseek", "k", "m", msgs, 100, use_cache=False)
    assert [x["cached"] for x in (a, b, c, d, e)] == [False, True, False, False, False] and len(calls) == 4
    summary = U.UsageLog(s).summary()
    t = summary["totals"]
    assert t["calls"] == 4 and t["response_cache_hits"] == 1 and t["cached_input"] == 3600 and t["input"] == 4000
    assert abs(t["provider_cache_hit_ratio"] - 0.9) < 1e-6
    m = summary["models"][0]
    assert abs(m["est_cost_usd"] - 4 * (100 * 1.0 + 900 * 0.1 + 10 * 2.0) / 1e6) < 1e-9
    assert abs(m["est_saved_usd"] - (100 * 1.0 + 900 * 0.1 + 10 * 2.0) / 1e6) < 1e-9


def test_history_budget_drops_in_one_large_step_and_cache_key_is_stable():
    h = [{"role": "user" if i % 2 == 0 else "assistant", "content": "x" * 3000} for i in range(12)]
    trimmed = core.trim_history(h, budget=24000)
    assert sum(len(m["content"]) for m in trimmed) <= 14400 and trimmed[0]["role"] == "user"
    assert core.trim_history(h[:4]) == h[:4]
    msgs = [{"role": "user", "content": "hola"}]
    assert core.cache_key("a", "m", msgs, 1, None) == core.cache_key("a", "m", msgs, 1, None) != core.cache_key("a", "m", msgs, 1, 0.5)


def _executor(script):
    seen = []

    def ex(*, provider, model, messages, max_tokens):
        seen.append((model, messages))
        return {"message": {"content": script(model, messages)}, "usage": {"prompt_tokens": 10, "completion_tokens": 2, "prompt_cache_hit_tokens": 8}, "cached": False}

    return ex, seen


def test_dag_happy_path_retry_feedback_unverified_and_ledger():
    def script(model, msgs):
        u = msgs[1]["content"]
        if "TU INTENTO ANTERIOR" in u:
            return '{"ok": 1}'
        if "[worker]" in u:
            return "Zafiro!"
        return "texto" if "sin expect" in u else "no json"

    ex, seen = _executor(script)
    r = D.run_dag(BASE, ex)
    assert r["nodes"]["A"]["status"] == "PASS" and r["nodes"]["B"]["status"] == "PASS" and len(r["nodes"]["B"]["attempts"]) == 2
    assert r["nodes"]["C"]["status"] == "DONE_UNVERIFIED" and r["status"] == "UNVERIFIED"
    assert r["ledger_valid"] is True and len(r["ledger"]) == 4 and r["totals"]["cached_input"] == 32
    assert "HAZ X literal" in seen[0][1][1]["content"] and "Zafiro!" in seen[1][1][1]["content"]
    bad = copy.deepcopy(r["ledger"])
    bad[1]["verdict"] = "PASS"
    assert not D.verify_ledger(bad)


def test_dag_escalation_blocking_gap_and_executor_errors():
    dag2 = copy.deepcopy(BASE)
    dag2["nodes"][0]["escalate_to"] = M2
    dag2["nodes"] = dag2["nodes"][:2]

    def ex(*, provider, model, messages, max_tokens):
        return {"message": {"content": "zafiro" if model == "m2" else "nada"}, "usage": {}, "cached": True}

    r = D.run_dag(dag2, ex)
    assert r["nodes"]["A"]["status"] == "PASS" and r["nodes"]["A"]["attempts"][-1]["model"] == "hf/m2" and r["totals"]["cached_responses"] >= 2
    gap = D.run_dag(dag2, lambda **k: {"message": {"content": "GAP: no puedo"}, "usage": {}})
    assert gap["nodes"]["A"]["status"] == "FAIL" and gap["nodes"]["B"]["status"] == "BLOCKED" and gap["status"] == "FAIL"

    def boom(**k):
        raise RuntimeError("PROVIDER_ERROR:402:x")

    err = D.run_dag(dag2, boom)
    assert err["nodes"]["A"]["status"] == "FAIL" and "EXECUTOR_ERROR" in err["nodes"]["A"]["checks_failed"][0]


def test_dag_validation_and_expect_checks():
    assert D.validate({"schema": "x"})
    cyc = {**BASE, "nodes": [{"id": "A", "model": M, "instructions": "x", "needs": ["B"]}, {"id": "B", "model": M, "instructions": "x", "needs": ["A"]}]}
    assert any("ciclo" in e for e in D.validate(cyc))
    assert any("desconocido" in e for e in D.validate(BASE, known_providers={"nvidia"}))
    assert D.check_expect('```json\n{"a": 1}\n```', {"json_keys": ["a"]}) == []
    assert D.check_expect("abc", {"regex": "^x"})
    with pytest.raises(D.DagError):
        D.run_dag({"schema": "riu.dag/v1", "input_block": "", "nodes": []}, lambda **k: {})


def test_dag_cli_runs_through_core_with_env_keys_and_never_leaks_them(tmp_path, monkeypatch):
    plan = {"schema": "riu.dag/v1", "id": "cli-t", "input_block": "literal", "nodes": [
        {"id": "A", "model": {"provider": "cerebras", "model": "llama"}, "agent": "seals-team-yaiwes-001", "instructions": "di ok", "expect": {"contains": ["ok"]}},
        {"id": "B", "model": {"provider": "nvidia", "model": "x"}, "instructions": "y", "needs": ["A"], "expect": {"contains": ["z"]}}]}
    (tmp_path / "p.json").write_text(json.dumps(plan))
    seen = []

    def fake(provider, key, model, messages, max_tokens, temperature=None):
        seen.append((provider, key, messages[0]["content"]))
        return {"message": {"role": "assistant", "content": "ok listo"}, "finish_reason": "stop", "usage": {"prompt_tokens": 5, "completion_tokens": 2}}

    monkeypatch.setattr(core, "call_via_router", fake)
    monkeypatch.setenv("CEREBRAS_API_KEY_1", "ckey-not-a-secret")
    for name in ("NVIDIA_API_KEY", "NVIDIA_API_KEY_1"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("RIU_DATA_DIR", str(tmp_path / "data"))
    rc = dag_cli.main([str(tmp_path / "p.json"), "--out", str(tmp_path / "out" / "r.json")])
    r = json.loads((tmp_path / "out" / "r.json").read_text())
    assert rc == 1 and r["status"] == "FAIL" and r["nodes"]["A"]["status"] == "PASS" and r["nodes"]["B"]["status"] == "FAIL"
    assert "PROVIDER_KEY_MISSING:nvidia" in r["nodes"]["B"]["checks_failed"][0]
    assert seen[0][1] == "ckey-not-a-secret" and "Seals Team" in seen[0][2]
    assert r["ledger_valid"] and r["usage_summary"]["calls"] == 1 and "ckey-not-a-secret" not in json.dumps(r)
