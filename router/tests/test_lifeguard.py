"""Pruebas del guardian y del plugin lifeguard con mocks de la API HF (sin red, sin lanzar nada real)."""
from __future__ import annotations

import base64
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace as NS

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("guardian_under_test", ROOT / "agents-yaiwes" / "common" / "guardian.py")
g = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = g
spec.loader.exec_module(g)

NL = chr(10)
NOW = 1_800_000_000.0
ENV = {"HF_CONTROL_JOBS_TOKEN": "hf_test", "GH_AGENT_TOKEN": "gh_test", "GROQ_API_KEY_2": "k2", "RIU_AGENT_API_KEYS": "{}", "GUARDIAN_DRY_RUN": "0"}


def job(jid, kind, age_s=3600, life_s=7 * 86400, stage="RUNNING"):
    mark = g.MARKS[kind]
    return NS(id=jid, status=NS(stage=stage), command=["bash", "-lc", "python x/" + mark], environment={"RIU_JOB_LIFETIME_S": str(life_s)},
              created_at=datetime.fromtimestamp(NOW - age_s, tz=timezone.utc))


class FakeApi:
    def __init__(self, jobs, new_stage="RUNNING", reject=()):
        self.jobs, self.runs, self.cancels, self.new_stage, self.reject = list(jobs), [], [], new_stage, set(reject)

    def list_jobs(self): return list(self.jobs)

    def run_job(self, **kw):
        if kw["timeout"] in self.reject:
            raise RuntimeError("timeout no permitido")
        self.runs.append(kw)
        j = job("new%d" % len(self.runs), "router" if "router_job" in kw["command"][-1] else "guardian", age_s=0, stage=self.new_stage)
        self.jobs.append(j)
        return j

    def inspect_job(self, job_id): return next(j for j in self.jobs if j.id == job_id)

    def cancel_job(self, job_id): self.cancels.append(job_id)


class FakeHttp:
    def __init__(self, healthy=True, live="https://old--8000.hf.jobs", put_ok=True, paused=False):
        self.healthy, self.live, self.put_ok, self.paused, self.puts, self.calls = healthy, live, put_ok, paused, [], []

    def __call__(self, method, url, headers=None, data=None, timeout=20):
        self.calls.append((method, url))
        if url.endswith("/health"):
            return (200 if self.healthy else 503), b""
        if "api.github.com" in url and method == "GET":
            txt = f"PAUSED={'true' if self.paused else 'false'}" + NL + f"LIVE_URL={self.live}" + NL
            return 200, json.dumps({"sha": "abc", "content": base64.b64encode(txt.encode()).decode()}).encode()
        if "api.github.com" in url and method == "PUT":
            self.puts.append(json.loads(data))
            return (200 if self.put_ok else 500), b"{}"
        return 404, b""


def cfg(**kw):
    c = g.Config.from_env(ENV)
    for k, v in kw.items():
        setattr(c, k, v)
    return c


def st(tmp_path): return g.State(str(tmp_path / "s.json"))


def run(kind, c, api, http, state, **kw):
    return g.relaunch(kind, c, api, http, state, "t", now=lambda: NOW, sleep=lambda s: None, **kw)


def test_parse_duration():
    assert g.parse_duration("7d") == 604800 and g.parse_duration("48h") == 172800 and g.parse_duration("90m") == 5400 and g.parse_duration("x", 5) == 5


def test_decide_healthy_and_each_trigger(tmp_path):
    c = cfg()
    base = {"kind": "router", "alive": ["a"], "remaining_s": 86400, "fails": 0}
    assert g.decide(base, c)["action"] == "none"
    assert g.decide({**base, "remaining_s": 5 * 3600}, c)["action"] == "relaunch"      # < 6 h
    assert g.decide({**base, "remaining_s": 7 * 3600}, c)["action"] == "none"
    assert g.decide({**base, "fails": 3}, c)["action"] == "relaunch"                    # 3 fallos
    assert g.decide({**base, "fails": 2}, c)["action"] == "none"
    assert g.decide({**base, "alive": []}, c)["action"] == "relaunch"                   # ausente
    assert g.decide({"kind": "guardian", "alive": ["g"], "remaining_s": 10, "fails": 9}, c)["action"] == "relaunch"


def test_remaining_uses_marker_override_and_fallback():
    c = cfg(expiry_overrides={"live": NOW + 1000})
    assert g.remaining_s(job("j", "router", age_s=3600, life_s=7200), c, "router", NOW) == 3600
    assert g.remaining_s(job("live", "router"), c, "router", NOW) == 1000
    old = job("z", "router", age_s=3600); old.environment = {}
    assert g.remaining_s(old, c, "router", NOW) == 24 * 3600 - 3600                      # vida supuesta


def test_spec_shape_matches_current_launcher():
    c = cfg()
    s = g.build_spec("router", c)
    assert s["image"] == "python:3.12" and s["flavor"] == "cpu-basic" and s["expose"] == [8000] and s["timeout"] == "7d"
    assert s["command"][:2] == ["bash", "-lc"] and "router_job_persistent.py" in s["command"][2] and "git clone --depth 1" in s["command"][2]
    assert s["env"]["RIU_G2_GROQ_MODEL"] == "qwen/qwen3.8-27b"
    assert s["secrets"]["GROQ_API_KEY_2"] == "k2" and s["secrets"]["GITHUB_TOKEN"] == "gh_test"
    assert "expose" not in g.build_spec("guardian", c) and g.build_spec("guardian", c)["timeout"] == "5d"
    d = g.describe_spec(s)
    assert "k2" not in json.dumps(d) and "gh_test" not in json.dumps(d) and "GROQ_API_KEY_2" in d["secrets"]


def test_dry_run_launches_nothing(tmp_path):
    api, http = FakeApi([job("old", "router")]), FakeHttp()
    r = run("router", cfg(), api, http, st(tmp_path), dry_run=True)
    assert r["ok"] and r["dry_run"] and api.runs == [] and api.cancels == [] and http.puts == []


def test_relaunch_order_health_then_liveurl_then_cancel(tmp_path):
    api, http = FakeApi([job("old", "router", age_s=3600)]), FakeHttp()
    r = run("router", cfg(), api, http, st(tmp_path), dry_run=False)
    assert r["ok"] and r["new_job_id"] == "new1" and r["cancelled"] == ["old"]
    assert len(api.runs) == 1 and api.cancels == ["old"]
    assert http.puts and base64.b64decode(http.puts[0]["content"]).decode() == "PAUSED=false" + NL + "LIVE_URL=https://new1--8000.hf.jobs" + NL
    assert http.puts[0]["sha"] == "abc" and "[skip ci]" in http.puts[0]["message"]
    kinds = [u.endswith("/health") for _, u in http.calls]
    assert kinds.index(True) < [m for m, _ in http.calls].index("PUT")                # health antes de escribir


def test_new_unhealthy_keeps_old_and_cancels_new(tmp_path):
    api, http = FakeApi([job("old", "router")]), FakeHttp(healthy=False)
    c = cfg(health_wait_s=30, poll_s=10)
    t = [NOW]
    r = g.relaunch("router", c, api, http, st(tmp_path), "t", False, now=lambda: t[0], sleep=lambda s: t.__setitem__(0, t[0] + s))
    assert not r["ok"] and api.cancels == ["new1"] and "old" not in api.cancels and http.puts == []


def test_liveurl_write_failure_keeps_old(tmp_path):
    api, http = FakeApi([job("old", "router")]), FakeHttp(put_ok=False)
    r = run("router", cfg(), api, http, st(tmp_path), dry_run=False)
    assert not r["ok"] and api.cancels == []                                             # viejo intacto


def test_life_ladder_7d_48h_24h():
    api = FakeApi([], reject=("7d", "48h"))
    j, used = g.launch_with_ladder("router", cfg(), api)
    assert used["timeout"] == "24h"


def test_pause_between_relaunches_and_hourly_cap(tmp_path):
    c, state = cfg(), st(tmp_path)
    api, http = FakeApi([job("old", "router", age_s=100000)]), FakeHttp()
    assert run("router", c, api, http, state, dry_run=False)["ok"]
    r2 = run("router", c, api, http, state, dry_run=False)
    assert not r2["ok"] and "pausa minima" in r2["blocked"] and len(api.runs) == 1
    state.launches = [NOW - 3000, NOW - 2000, NOW - 1000]
    ok, why = g.launch_allowed(state, cfg(min_pause_s=1), NOW)
    assert not ok and "tope" in why


def test_single_simultaneous_launch_lock(tmp_path):
    state = st(tmp_path)
    state.lock.acquire()
    r = run("router", cfg(), FakeApi([]), FakeHttp(), state, dry_run=False)
    assert not r["ok"] and "cerrojo" in r["blocked"]


def test_young_job_blocks_second_guardian_process(tmp_path):
    api = FakeApi([job("fresh", "router", age_s=60)])
    r = run("router", cfg(), api, FakeHttp(), st(tmp_path), dry_run=False)
    assert not r["ok"] and "fresh" in r["blocked"] and api.runs == []


def test_tick_three_fails_then_relaunch(tmp_path):
    c, state = cfg(min_pause_s=1), st(tmp_path)
    api, http = FakeApi([job("old", "router", age_s=7200), job("g", "guardian", age_s=7200)]), FakeHttp(healthy=False)
    calls = []
    for _ in range(2):
        out = g.tick(("router",), c, api, http, state, now=lambda: NOW, sleep=lambda s: None)
        calls.append(out[0]["decision"]["action"])
    assert calls == ["none", "none"] and api.runs == []
    api.jobs[0] = job("old", "router", age_s=7200)
    http.healthy = True                                                                   # el nuevo sera sano; el viejo ya fallo 2 veces
    state.fails["router"] = 2
    http2 = FakeHttp(healthy=False)
    def h(method, url, headers=None, data=None, timeout=20):
        if url.endswith("/health") and "new1" in url: return 200, b""
        return http2(method, url, headers, data, timeout)
    out = g.tick(("router",), c, api, h, state, now=lambda: NOW, sleep=lambda s: None)
    assert out[0]["decision"]["action"] == "relaunch" and out[0]["result"]["ok"] and api.cancels == ["old"]


def test_tick_expiring_guardian_self_renews(tmp_path):
    c = cfg(min_pause_s=1)
    api = FakeApi([job("g", "guardian", age_s=5 * 86400 - 3600, life_s=5 * 86400)])
    out = g.tick(("guardian",), c, api, FakeHttp(), st(tmp_path), now=lambda: NOW, sleep=lambda s: None)
    assert out[0]["decision"]["action"] == "relaunch" and out[0]["result"]["ok"] and api.cancels == ["g"]


def test_flag_paused_preserved(tmp_path):
    http = FakeHttp(paused=True)
    assert g.write_live_url(cfg(), http, "j", "https://j--8000.hf.jobs", sleep=lambda s: None)
    assert base64.b64decode(http.puts[0]["content"]).decode().startswith("PAUSED=true")


def test_guardian_command_is_self_contained():
    cmd = g.build_spec("guardian", cfg())["command"][2]
    assert "raw.githubusercontent.com" in cmd and "guardian.py" in cmd and "git clone" not in cmd


# ------------------------------------------------------------------ plugin
def _plugin(monkeypatch):
    for k, v in ENV.items():
        monkeypatch.setenv(k, v)
    spec2 = importlib.util.spec_from_file_location("lifeguard_plugin", ROOT / "plugins" / "lifeguard" / "plugin.py")
    m = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(m)
    return m


def test_plugin_ficha_valid():
    f = json.loads((ROOT / "plugins" / "lifeguard" / "ficha.json").read_text())
    assert f["plugin_host"]["schema"] == "plugin_host/v1" and f["plugin_host"]["enabled_default"] is False
    assert f["ejecucion"]["allowed_actions"] == ["status", "plan", "relaunch"]


def test_plugin_status_plan_relaunch_dry_default(monkeypatch, tmp_path):
    monkeypatch.setenv("GUARDIAN_STATE", str(tmp_path / "p.json"))
    m = _plugin(monkeypatch)
    api, http = FakeApi([job("old", "router"), job("g", "guardian", age_s=5 * 86400 - 600, life_s=5 * 86400)]), FakeHttp()
    # el reloj real no es NOW: los jobs fake se fechan respecto a NOW, asi que usamos vida relativa a time.time()
    import time
    real = time.time()
    for j in api.jobs:
        j.created_at = datetime.fromtimestamp(real - (3600 if j.id == "old" else 5 * 86400 - 600), tz=timezone.utc)
    p = {"_api": api, "_http": http}
    s = m.handle("status", p)
    assert s["ok"] and s["router"]["health_ok"] and s["guardian"]["alive"] == ["g"]
    pl = m.handle("plan", {**p, "kind": "guardian"})
    assert pl["decision"]["action"] == "relaunch" and "k2" not in json.dumps(pl)
    r = m.handle("relaunch", {**p, "kind": "guardian"})                                    # sin dry_run -> dry por defecto
    assert r["ok"] and r["dry_run"] and api.runs == []
    skip = m.handle("relaunch", {**p, "kind": "router", "dry_run": False})                 # router sano: no actua
    assert skip["skipped"] and api.runs == []
    real_r = m.handle("relaunch", {**p, "kind": "guardian", "dry_run": False})
    assert real_r["ok"] and len(api.runs) == 1 and api.cancels == ["g"]


def test_plugin_unknown_action_and_no_token(monkeypatch):
    m = _plugin(monkeypatch)
    assert not m.handle("borrar", {})["ok"]
    monkeypatch.delenv("HF_CONTROL_JOBS_TOKEN")
    assert "falta HF_CONTROL_JOBS_TOKEN" in m.handle("status", {})["error"]
