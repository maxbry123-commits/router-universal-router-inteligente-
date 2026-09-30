"""Bloque 3: plugins deepseek_harness, fables_enchufe, parallel, connectivity cargados por el host real (sin fastapi)."""
from __future__ import annotations

import http.server
import json
import sys
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integration.plugin_host import host as H  # noqa: E402

IDS = ("deepseek_harness", "fables_enchufe", "parallel", "connectivity")


@pytest.fixture()
def host(tmp_path, monkeypatch):
    for k in ("RIU_DEEPSEEK_HARNESS_URL", "RIU_MCP_URL", "RIU_MCP_CONFIG", "RIU_SELF_URL", "RIU_HTTP_ALLOWLIST"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.chdir(tmp_path)
    h = H.PluginHost(ROOT / "plugins", tmp_path / "state.json")
    H.set_host(h)
    yield h
    H.set_host(None)


def _on(h):
    for i in IDS:
        assert h.set_enabled(i, True) is not None


def test_load_at_start_valid_and_off_by_default(host):
    recs = {r["id"]: r for r in host.list()} if hasattr(host, "list") else {}
    for i in IDS:
        p = host._plugins[i]
        assert p.errors == [], (i, p.errors)
        assert p.enabled is False and p.status == "off"
    assert recs == {} or all(recs[i]["status"] == "off" for i in IDS)


def test_off_plugin_call_is_off_not_raise(host):
    assert host.call("parallel", "status")["status"] == "off"


def test_deepseek_degraded_without_url(host):
    _on(host)
    r = host.call("deepseek_harness", "invoke", {"x": 1})
    assert r["status"] == "ok" and r["result"]["status"] == "degraded" and "RIU_DEEPSEEK_HARNESS_URL" in r["result"]["reason"]
    assert host.call("deepseek_harness", "status")["result"]["status"] == "degraded"


def test_deepseek_removed_plugin_is_degraded(tmp_path):
    h = H.PluginHost(tmp_path / "vacio", tmp_path / "s.json")
    r = h.call("deepseek_harness", "invoke", {})
    assert r["status"] == "degraded" and r["reason"]


class _Echo(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        out = json.dumps({"echo": json.loads(body)}).encode()
        self.send_response(200); self.send_header("Content-Length", str(len(out))); self.end_headers(); self.wfile.write(out)

    def do_GET(self):
        self.send_response(200 if self.path == "/health" else 404); self.send_header("Content-Length", "0"); self.end_headers()

    def log_message(self, *a):
        pass


@pytest.fixture()
def server():
    s = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Echo)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{s.server_address[1]}"
    s.shutdown()


def test_deepseek_invoke_over_http(host, server, monkeypatch):
    _on(host)
    monkeypatch.setenv("RIU_DEEPSEEK_HARNESS_URL", server)
    r = host.call("deepseek_harness", "invoke", {"q": "hola"})
    assert r["status"] == "ok" and r["result"]["status"] == "ok" and r["result"]["response"] == {"echo": {"q": "hola"}}


def test_fables_enchufe(host):
    _on(host)
    assert host.call("fables_enchufe", "status")["result"]["validator_v2_cargado"] is True
    good = json.loads((ROOT / "plugins" / "parallel" / "ficha.json").read_text(encoding="utf-8"))
    r = host.call("fables_enchufe", "validate", {"ficha": good})["result"]
    assert r["status"] == "ok" and r["valido"] is True, r
    bad = host.call("fables_enchufe", "validate", {"ficha": {}})["result"]
    assert bad["status"] == "ok" and bad["valido"] is False and bad["errores"]
    assert host.call("fables_enchufe", "validate", {"ficha": 3})["result"]["status"] == "degraded"


def test_parallel_runs_and_isolates_failures(host):
    _on(host)
    calls = [{"plugin": "parallel", "action": "status"}, {"plugin": "nope", "action": "x"}, {"plugin": "fables_enchufe", "action": "status"}, {"plugin": "deepseek_harness", "action": "status"}, "basura"]
    r = host.call("parallel", "run", {"calls": calls})["result"]
    assert r["total"] == 5 and r["status"] == "degraded"
    res = r["results"]
    assert res[0]["status"] == "degraded" and "a si mismo" in res[0]["reason"]
    assert res[1]["reason"] == "plugin desconocido"
    assert res[2]["status"] == "ok" and res[4]["status"] == "degraded"


def test_parallel_limit_8_and_timeout(host, monkeypatch):
    import threading as T, time
    _on(host)
    live, peak, lock = [0], [0], T.Lock()

    def fake_call(pid, action, payload=None, timeout_s=None):
        with lock:
            live[0] += 1; peak[0] = max(peak[0], live[0])
        time.sleep(0.05)
        with lock:
            live[0] -= 1
        return {"status": "ok", "timeout_s": timeout_s}

    monkeypatch.setattr(host, "call", fake_call)
    from plugins.parallel import plugin as P
    r = P.handle("run", {"calls": [{"plugin": "x", "action": "y"}] * 20, "timeout_s": 2})
    assert r["total"] == 20 and r["ok"] == 20 and peak[0] <= 8 and r["results"][0]["timeout_s"] == 2
    assert P.handle("run", {"calls": [{"plugin": "x", "action": "y"}] * 33})["status"] == "degraded"
    assert P.handle("run", {})["status"] == "degraded"


def test_parallel_real_timeout(host):
    _on(host)
    r = host.call("parallel", "run", {"calls": [{"plugin": "connectivity", "action": "check"}], "timeout_s": 0.01})["result"]
    assert r["results"][0]["status"] == "degraded"


def test_connectivity_reports_per_transport(host, server, monkeypatch):
    _on(host)
    monkeypatch.setenv("RIU_SELF_URL", server)
    monkeypatch.setenv("RIU_HTTP_ALLOWLIST", "")
    r = host.call("connectivity", "check")["result"]
    t = r["transports"]
    assert t["fastapi"]["status"] == "ok" and t["http"]["status"] == "off" and t["mcp"]["status"] == "off"
    assert "no hay cliente MCP" in t["mcp"]["reason"] and r["status"] == "ok"
    monkeypatch.setenv("RIU_SELF_URL", "http://127.0.0.1:9")
    assert host.call("connectivity", "check")["result"]["transports"]["fastapi"]["status"] == "off"
    monkeypatch.setenv("RIU_MCP_URL", server + "/health")
    assert host.call("connectivity", "check")["result"]["transports"]["mcp"]["status"] == "ok"


def test_connectivity_allowlist(monkeypatch):
    from plugins.connectivity import plugin as C
    monkeypatch.delenv("RIU_HTTP_ALLOWLIST", raising=False)
    assert C.allowed("https://huggingface.co/x") and not C.allowed("https://evil.example/")
    monkeypatch.setenv("RIU_HTTP_ALLOWLIST", "127.0.0.1")
    r = C.handle("check", {})
    assert r["transports"]["http"]["hosts"]["127.0.0.1"] is not None


def test_bad_plugin_does_not_break_startup(tmp_path):
    d = tmp_path / "plugins"
    for i in ("roto", "malo"):
        (d / i).mkdir(parents=True)
    (d / "roto" / "ficha.json").write_text("{no json")
    (d / "malo" / "ficha.json").write_text(json.dumps({"plugin_host": {"schema": "plugin_host/v1", "id": "malo"}}))
    import shutil
    shutil.copytree(ROOT / "plugins" / "parallel", d / "parallel")
    h = H.PluginHost(d, tmp_path / "s.json")
    assert h._plugins["roto"].status == "invalid" and h._plugins["malo"].status == "invalid"
    assert h._plugins["parallel"].errors == []
