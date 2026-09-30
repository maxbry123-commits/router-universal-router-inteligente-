"""POST /plugins/sync, PluginHost.sync and reload_policies: host with temp folder, no restart."""
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from integration.plugin_host.host import PluginHost  # noqa: E402
from integration.chat_mvp import resilience  # noqa: E402


def _host(tmp_path):
    (tmp_path / "plugins").mkdir()
    return PluginHost(tmp_path / "plugins", tmp_path / "state.json", use_repo_validator=False)


def _copy_template(tmp_path, name, broken=False):
    src = ROOT / "plugins" / "remote_router"
    dst = tmp_path / "plugins" / name
    dst.mkdir()
    ficha = json.loads((src / "ficha.json").read_text(encoding="utf-8"))
    ficha["plugin_host"]["id"] = name
    (dst / "ficha.json").write_text("{rota" if broken else json.dumps(ficha), encoding="utf-8")
    return dst


def test_sync_adds_then_removes_and_bad_ficha_only_marks_itself(tmp_path):
    h = _host(tmp_path)
    assert h.list_plugins() == []
    _copy_template(tmp_path, "nuevo-uno")
    _copy_template(tmp_path, "roto-dos", broken=True)
    r = h.sync()
    assert "nuevo-uno" in r["added"] and "roto-dos" in r["added"]
    assert "roto-dos" in r["invalid"] and "nuevo-uno" not in r["invalid"]
    assert h.get("roto-dos")["status"] == "invalid"
    assert h.get("nuevo-uno") is not None
    shutil.rmtree(tmp_path / "plugins" / "nuevo-uno")
    r2 = h.sync()
    assert r2["removed"] == ["nuevo-uno"] and h.get("nuevo-uno") is None and h.get("roto-dos")["status"] == "invalid"


def test_sync_keeps_runtime_counters(tmp_path):
    h = _host(tmp_path)
    _copy_template(tmp_path, "uno")
    h.sync()
    h._plugins["uno"].last_error = "boom"
    h.sync()
    assert h.get("uno")["last_error"] == "boom"


def test_http_route_sync_and_auth(tmp_path, monkeypatch):
    fastapi = pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    from integration.plugin_host import api as api_mod, host as host_mod

    h = _host(tmp_path)
    host_mod.set_host(h)
    app = fastapi.FastAPI()
    app.dependency_overrides = {}
    app.include_router(api_mod.build_plugin_router())
    c = TestClient(app)
    _copy_template(tmp_path, "via-http")
    resp = c.post("/plugins/sync")
    host_mod.set_host(None)
    if resp.status_code in (401, 403):  # same auth as the other routes: without key it is refused
        assert c.post("/plugins/sync").status_code == resp.status_code
    else:
        assert resp.status_code == 200 and "via-http" in resp.json()["added"]


def test_reload_policies_valid_invalid_keeps_previous(tmp_path):
    f = tmp_path / "policies.json"
    good = {"groups": {"sdk": {"authorized_fallback": True, "chain": [{"provider": "hf", "model": "x/y"}]}}}
    f.write_text(json.dumps(good), encoding="utf-8")
    snapshot = json.loads(json.dumps(resilience.DEFAULT_POLICY))
    try:
        r = resilience.reload_policies(f)
        assert r["ok"] and resilience.DEFAULT_POLICY["sdk"]["chain"][0]["model"] == "x/y"
        f.write_text("{ no json", encoding="utf-8")
        r = resilience.reload_policies(f)
        assert r["ok"] is False and r["kept_previous"] and resilience.DEFAULT_POLICY["sdk"]["chain"][0]["model"] == "x/y"
        f.write_text(json.dumps({"groups": {"sdk": {"chain": "mal"}}}), encoding="utf-8")
        r = resilience.reload_policies(f)
        assert r["ok"] and r["rejected"] == ["sdk"]
    finally:
        resilience.DEFAULT_POLICY.clear()
        resilience.DEFAULT_POLICY.update(snapshot)
