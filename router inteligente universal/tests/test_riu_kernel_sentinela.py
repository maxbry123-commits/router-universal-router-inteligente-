"""Sentinela del supervisor (riu_kernel): candado, 3 strikes, sucesor listo antes de cambiar. Todo simulado, sin red."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import riu_kernel as k  # noqa: E402


@pytest.fixture()
def world(monkeypatch):
    bucket, calls = {}, []
    state = {"healthy": {}, "bank": {}, "chat": {}, "next_id": 1}
    monkeypatch.setattr(k, "read", lambda rel: dict(bucket.get(rel, {})))
    monkeypatch.setattr(k, "write", lambda rel, d: bucket.__setitem__(rel, dict(d)))
    monkeypatch.setattr(k.time, "sleep", lambda s: None)
    monkeypatch.setattr(k, "healthy", lambda url: state["healthy"].get(url, False))
    monkeypatch.setattr(k, "bank_ok", lambda url: state["bank"].get(url, False))
    monkeypatch.setattr(k, "reopen_bank", lambda url: calls.append(("reopen", url)) or state["bank"].get(url + "#reopen", False))
    monkeypatch.setattr(k, "chat_ok", lambda url: state["chat"].get(url, False))
    monkeypatch.setattr(k, "hydrate", lambda: None)
    monkeypatch.setattr(k, "http", lambda *a, **kw: (200, {}))
    monkeypatch.setattr(k, "publish", lambda reg: calls.append(("publish", reg["job_id"])) or state.get("gh_ok", True))

    def launch():
        jid = "new%d" % state["next_id"]; state["next_id"] += 1
        calls.append(("launch", jid))
        return {"job_id": jid, "url": "https://%s--8000.hf.jobs" % jid, "flavor": "cpu-basic", "started": k.time.time(), "timeout_s": 172800}
    monkeypatch.setattr(k, "launch", launch)

    class Api:
        def __init__(self, token=None): pass
        def cancel_job(self, job_id, namespace=None): calls.append(("cancel", job_id)); state.setdefault("dead", set()).add(job_id)
        def run_job(self, **kw):
            jid = "sent%d" % state["next_id"]; state["next_id"] += 1
            calls.append(("run_sentinel", jid, kw["flavor"], kw["env"]["RIU_KERNEL_ROLE"], sorted(kw["secrets"])))
            return type("J", (), {"id": jid})()
        def inspect_job(self, job_id, namespace=None):
            stage = "CANCELED" if job_id in state.get("dead", set()) else "RUNNING"
            return type("J", (), {"status": type("S", (), {"stage": stage})()})()
    monkeypatch.setattr(k, "HfApi", Api)
    monkeypatch.setenv("HF_TOKEN", "x")
    monkeypatch.setenv("RIU_SENTINEL_DISABLED", "1")
    return bucket, state, calls


def _reg(bucket, jid="old", started_ago=3600, timeout=172800):
    bucket["control/router-current.json"] = {"job_id": jid, "url": "https://%s--8000.hf.jobs" % jid, "flavor": "cpu-basic",
                                             "started": k.time.time() - started_ago, "timeout_s": timeout}


def test_healthy_router_is_left_alone(world):
    bucket, state, calls = world
    _reg(bucket); state["healthy"]["https://old--8000.hf.jobs"] = True; state["bank"]["https://old--8000.hf.jobs"] = True
    k.tick()
    assert calls == []


def test_locked_bank_is_reopened_without_relaunch(world):
    bucket, state, calls = world
    _reg(bucket); state["healthy"]["https://old--8000.hf.jobs"] = True
    k.tick()
    assert calls == [("reopen", "https://old--8000.hf.jobs")]


def test_three_strikes_before_relaunch(world):
    bucket, state, calls = world
    _reg(bucket)
    state["healthy"]["https://new1--8000.hf.jobs"] = True
    state["bank"]["https://new1--8000.hf.jobs"] = True
    state["chat"]["https://new1--8000.hf.jobs"] = True
    k.tick(); k.tick()
    assert calls == [] and bucket["control/strikes.json"]["n"] == 2
    k.tick()
    assert calls == [("launch", "new1"), ("publish", "new1"), ("cancel", "old")]


def test_successor_without_chat_stays_pending_then_is_cancelled_old_preserved(world, monkeypatch):
    bucket, state, calls = world
    _reg(bucket, started_ago=172800 - 600)  # quedan 10 min: toca renovar
    state["healthy"]["https://old--8000.hf.jobs"] = True; state["bank"]["https://old--8000.hf.jobs"] = True
    state["healthy"]["https://new1--8000.hf.jobs"] = True; state["bank"]["https://new1--8000.hf.jobs"] = True
    t = [k.time.time()]
    monkeypatch.setattr(k.time, "time", lambda: t.__setitem__(0, t[0] + 20) or t[0])
    k.tick()  # primera corrida: sucesor pendiente, nada cambia
    assert calls == [("launch", "new1")]
    k.tick()  # segunda corrida: lo adopta (no lanza otro) y, pasados 30 min sin chat, lo cancela
    with pytest.raises(RuntimeError, match="SUCCESSOR_NOT_READY"):
        for _ in range(5):
            k.tick()
    assert [c for c in calls if c[0] == "launch"] == [("launch", "new1")]
    assert ("cancel", "new1") in calls and ("cancel", "old") not in calls and not any(c[0] == "publish" for c in calls)


def test_locked_bank_three_times_relaunches_safely(world):
    bucket, state, calls = world
    _reg(bucket); state["healthy"]["https://old--8000.hf.jobs"] = True
    for u in ("https://new1--8000.hf.jobs",):
        state["healthy"][u] = state["bank"][u] = state["chat"][u] = True
    k.tick(); k.tick(); k.tick()
    assert [c for c in calls if c[0] != "reopen"] == [("launch", "new1"), ("publish", "new1"), ("cancel", "old")]


def test_github_publish_failure_keeps_old_running(world):
    bucket, state, calls = world
    _reg(bucket)
    state["gh_ok"] = False
    u = "https://new1--8000.hf.jobs"; state["healthy"][u] = state["bank"][u] = state["chat"][u] = True
    k.tick(); k.tick(); k.tick()
    assert ("cancel", "old") not in calls and bucket["control/recovery-16gb.json"]["job_id"] == "new1"
    state["gh_ok"] = True
    k.tick()  # adopta el pendiente: no lanza otro
    assert [c for c in calls if c[0] == "launch"] == [("launch", "new1")] and calls[-1] == ("cancel", "old")


def test_other_supervisor_holds_lock(world):
    bucket, state, calls = world
    _reg(bucket)
    bucket["control/kernel-lock.json"] = {"owner": "otro:1", "until": k.time.time() + 600}
    k.tick(); k.tick(); k.tick()
    assert calls == [] and "control/strikes.json" not in bucket


def test_renewal_at_04_cot(world, monkeypatch):
    bucket, state, calls = world
    _reg(bucket, started_ago=20 * 3600)
    for u in ("https://old--8000.hf.jobs", "https://new1--8000.hf.jobs"):
        state["healthy"][u] = state["bank"][u] = True
    state["chat"]["https://new1--8000.hf.jobs"] = True
    real = k.time.gmtime
    monkeypatch.setattr(k.time, "gmtime", lambda *a: real(0).__class__((2026, 10, 8, 9, 5, 0, 3, 281, 0)))
    k.tick()
    assert calls == [("launch", "new1"), ("publish", "new1"), ("cancel", "old")]


def _sentinel_on(monkeypatch):
    monkeypatch.delenv("RIU_SENTINEL_DISABLED")
    monkeypatch.setenv("RIU_VAULT_PASSPHRASE", "x")
    monkeypatch.setattr(k, "_SENT_CHECK", [0.0])


def test_sentinel_job_launched_when_missing_and_not_duplicated(world, monkeypatch):
    bucket, state, calls = world
    _sentinel_on(monkeypatch)
    k.ensure_sentinel()
    assert calls == [("run_sentinel", "sent1", "cpu-basic", "sentinel", ["HF_TOKEN", "RIU_VAULT_PASSPHRASE"])]
    k._SENT_CHECK[0] = 0.0
    k.ensure_sentinel()  # sigue RUNNING y con vida: no lanza otro
    assert len(calls) == 1


def test_sentinel_renewed_before_expiry_and_old_cancelled(world, monkeypatch):
    bucket, state, calls = world
    _sentinel_on(monkeypatch)
    bucket["control/sentinel.json"] = {"job_id": "sentOld", "started": k.time.time() - 172800 + 600, "timeout_s": 172800}
    k.ensure_sentinel()
    assert calls == [("run_sentinel", "sent1", "cpu-basic", "sentinel", ["HF_TOKEN", "RIU_VAULT_PASSPHRASE"]), ("cancel", "sentOld")]


def test_sentinel_does_not_spawn_sentinels(world, monkeypatch):
    bucket, state, calls = world
    _sentinel_on(monkeypatch)
    monkeypatch.setattr(k, "SENTINEL_ROLE", True)
    k.ensure_sentinel()
    assert calls == []


def test_sentinel_command_snippet_compiles():
    c = k.sentinel_command()[2]
    compile(c.split("<<'PY'\n")[1].split("\nPY")[0], "sentinel", "exec")


def test_manual_relaunch_request_uses_safe_switch_once(world):
    bucket, state, calls = world
    _reg(bucket)
    for u in ("https://old--8000.hf.jobs", "https://new1--8000.hf.jobs"):
        state["healthy"][u] = state["bank"][u] = True
    state["chat"]["https://new1--8000.hf.jobs"] = True
    bucket["control/router-desired.json"] = {"relaunch_now": True, "ts": k.time.time() - 7200}  # anterior al arranque: se ignora
    k.tick()
    assert calls == []
    bucket["control/router-desired.json"] = {"relaunch_now": True, "ts": k.time.time()}
    k.tick()
    assert calls == [("launch", "new1"), ("publish", "new1"), ("cancel", "old")]
