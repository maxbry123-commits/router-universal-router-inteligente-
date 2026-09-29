"""Plugin Host tests. The core (registry, call() harness, allowlist, switch file) runs WITHOUT fastapi; the HTTP/gate tests skip without it."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integration.plugin_host import host as H  # noqa: E402


def ficha(pid: str = "demo", entry: str = "plugins.demo_fake:handle", enabled: bool = True, **over) -> dict:
    f = {
        "plugin_host": {"schema": "plugin_host/v1", "id": pid, "enabled_default": enabled, "health_action": "ping"},
        "artifact_id": "riu.plugins." + pid.replace("-", "_"), "version": "1.0.0", "estado": "testing", "categoria": "pipeline", "etapa": "P",
        "contrato": {"rol": "service"},
        "ejecucion": {"kind": "code", "transport": "importlib", "runtime_type": "compute", "entry_point": entry, "idempotente": True,
                      "allowed_actions": ["ping", "boom", "slow", "coro"]},
        "seguridad": {"sandbox": "none", "permisos": [], "limites": {"timeout_ms": 300}},
        "firma": {"gpg_key_id": "PENDIENTE"},
    }
    f.update(over)
    return f


def make_host(tmp_path: Path, fichas: dict, state: Path | None = None, **kw) -> H.PluginHost:
    """fichas: folder name -> ficha dict, or raw text (written as is), or None (folder without ficha.json)."""
    plugins = tmp_path / "plugins"
    plugins.mkdir(parents=True, exist_ok=True)
    for name, body in fichas.items():
        (plugins / name).mkdir(exist_ok=True)
        if body is not None:
            (plugins / name / "ficha.json").write_text(body if isinstance(body, str) else json.dumps(body), encoding="utf-8")
    return H.PluginHost(plugins, state or tmp_path / "state.json", **kw)


def install_fake(monkeypatch) -> types.ModuleType:
    """A fake plugin module registered as plugins.demo_fake (nothing is written to disk)."""
    mod = types.ModuleType("plugins.demo_fake")
    mod.release = threading.Event()
    mod.calls = []

    def handle(action, payload=None):
        mod.calls.append(action)
        if action == "ping":
            return {"pong": True, "payload": payload}
        if action == "boom":
            raise RuntimeError("kaboom")
        if action == "slow":
            mod.release.wait(10)
            return "late"
        if action == "coro":
            async def _c():
                return 1
            return _c()
        raise ValueError(action)

    mod.handle = handle
    monkeypatch.setitem(sys.modules, "plugins.demo_fake", mod)
    return mod


def test_shipped_fichas_chat_on_thinking_modes_off(tmp_path):
    h = H.PluginHost(ROOT / "plugins", tmp_path / "state.json")
    by_id = {p["id"]: p for p in h.list_plugins()}
    assert set(by_id) >= {"chat", "thinking-modes"}
    chat, tm = by_id["chat"], by_id["thinking-modes"]
    assert chat["status"] == "ready" and chat["enabled"] is True and chat["entrypoint"] == "plugins.chat.plugin:handle", chat
    assert chat["version"] == "0.1.0" and chat["category"] == "pipeline" and chat["last_error"] is None
    assert tm["status"] == "off" and tm["enabled"] is False and "ROJO" in tm["nota_roja"] and tm["entrypoint"] is None, tm
    assert h.call("thinking-modes", "anything")["status"] == "off"
    assert h.validator is not None and h.load_error is None
    on = h.set_enabled("thinking-modes", True)  # a placeholder has no code: switching it on must not pretend it works
    assert on["status"] == "degraded" and "placeholder" in on["last_error"]
    out = h.call("thinking-modes", "x")
    assert out["status"] == "degraded" and "placeholder" in out["reason"]


def test_shipped_chat_ficha_passes_the_repo_validator_but_could_not_be_active():
    validar = H.repo_validator()
    assert validar is not None
    chat = json.loads((ROOT / "plugins" / "chat" / "ficha.json").read_text(encoding="utf-8"))
    assert H.check_v1(chat, "chat") == [] and validar(chat).valido
    active = dict(chat, estado="active")  # what the README-ROJO says: without contract_hash and a real GPG key it cannot be active
    verdict = validar(active)
    assert not verdict.valido and set(verdict.errores) == {"I04_active_requiere_hash", "V13_active_requiere_gpg"}, verdict.errores


def test_invalid_fichas_mark_only_that_plugin_and_never_raise(tmp_path):
    install = {
        "bad-json": "{esto no es json",
        "no-ficha": None,
        "wrong-id": ficha("otro-id"),
        "bad-entry": ficha("bad-entry", entry="os:system"),
        "not-object": "[1, 2, 3]",
        "fables-fail": ficha("fables-fail", estado="active"),  # active without contract_hash / GPG key: the repo validator rejects it
        "good": ficha("good"),
    }
    h = make_host(tmp_path, install)
    by_id = {p["id"]: p for p in h.list_plugins()}
    for bad in ("bad-json", "no-ficha", "wrong-id", "bad-entry", "not-object", "fables-fail"):
        assert by_id[bad]["status"] == "invalid" and by_id[bad]["last_error"] and by_id[bad]["errors"], bad
        out = h.call(bad, "ping")
        assert out["status"] == "degraded" and "ficha invalida" in out["reason"], (bad, out)
    assert "H09_entrypoint" in by_id["bad-entry"]["last_error"] and "I04_active_requiere_hash" in by_id["fables-fail"]["last_error"]
    assert by_id["good"]["status"] == "ready"
    assert h.gate_open("bad-json") is True  # an invalid ficha never closes a gate
    small = make_host(tmp_path / "small", {"fables-fail": ficha("fables-fail", estado="active")}, use_repo_validator=False)
    assert small.validator is None and small.validator_name.startswith("plugin_host/v1 solo")
    assert small.get("fables-fail")["status"] == "ready"  # the small check alone does not know the 36 invariants


def test_missing_plugins_folder_is_not_fatal(tmp_path):
    h = H.PluginHost(tmp_path / "no-such-dir", tmp_path / "state.json")
    assert h.list_plugins() == [] and h.load_error
    assert h.call("chat", "status")["status"] == "degraded"


def test_disabled_plugin_is_off_and_does_not_run(tmp_path, monkeypatch):
    mod = install_fake(monkeypatch)
    h = make_host(tmp_path, {"demo": ficha("demo", enabled=False)})
    assert h.get("demo")["status"] == "off"
    out = h.call("demo", "ping")
    assert out["status"] == "off" and "apagado" in out["reason"] and mod.calls == []


def test_call_ok_returns_result_and_records_time(tmp_path, monkeypatch):
    install_fake(monkeypatch)
    h = make_host(tmp_path, {"demo": ficha()})
    out = h.call("demo", "ping", {"a": 1})
    assert out["status"] == "ok" and out["result"] == {"pong": True, "payload": {"a": 1}} and out["ms"] >= 0
    rec = h.get("demo")
    assert rec["status"] == "ready" and rec["last_call_ms"] == out["ms"] and rec["last_error"] is None
    assert h.health("demo")["status"] == "ok"


def test_timeout_returns_degraded_then_recovers(tmp_path, monkeypatch):
    mod = install_fake(monkeypatch)
    h = make_host(tmp_path, {"demo": ficha()})
    t0 = time.time()
    out = h.call("demo", "slow", timeout_s=0.1)
    assert time.time() - t0 < 2 and out["status"] == "degraded" and out["reason"].startswith("timeout"), out
    assert h.get("demo")["status"] == "degraded" and h.get("demo")["last_error"].startswith("timeout")
    mod.release.set()
    assert h.call("demo", "ping")["status"] == "ok" and h.get("demo")["status"] == "ready"


def test_exception_returns_degraded_and_the_next_call_still_works(tmp_path, monkeypatch):
    install_fake(monkeypatch)
    h = make_host(tmp_path, {"demo": ficha()})
    out = h.call("demo", "boom")
    assert out["status"] == "degraded" and out["reason"] == "RuntimeError: kaboom"
    assert h.get("demo")["status"] == "degraded" and h.get("demo")["last_error"] == "RuntimeError: kaboom"
    assert h.call("demo", "ping")["status"] == "ok"


def test_call_refuses_bad_requests_without_raising(tmp_path, monkeypatch):
    mod = install_fake(monkeypatch)
    h = make_host(tmp_path, {"demo": ficha()})
    assert h.call("nope", "ping") == {"status": "degraded", "plugin": "nope", "action": "ping", "reason": "plugin desconocido"}
    assert "accion no permitida" in h.call("demo", "rm-rf")["reason"]
    assert "payload" in h.call("demo", "ping", payload=[1])["reason"]
    assert "async" in h.call("demo", "coro")["reason"]
    assert mod.calls == ["coro"]  # only the async one reached the plugin; the refused ones never ran
    h._plugins = None  # even a broken host must answer instead of raising
    out = h.call("demo", "ping")
    assert out["status"] == "degraded" and "fallo interno" in out["reason"]


def test_entrypoint_outside_allowlist_is_refused(tmp_path, monkeypatch):
    for bad in ("os:system", "subprocess:run", "builtins:exec", "integration:handle", "integrationx.foo:bar", "pluginsx.foo:bar",
                "plugins.x:_private", "plugins..x:y", "plugins.x", "plugins.x:a.b", "", None, 5, "plugins.x:y; import os"):
        assert H.entrypoint_error(bad), bad
    for outside in ("os:system", "subprocess:run", "builtins:exec", "integration:handle", "integrationx.foo:bar", "pluginsx.foo:bar", "os.path:join"):
        assert "fuera de la lista permitida" in H.entrypoint_error(outside), outside  # named for what it is, not just "malformed"
    for good in ("plugins.chat.plugin:handle", "integration.plugin_host.host:get_host"):
        assert H.entrypoint_error(good) is None, good
    with pytest.raises(ValueError):
        H.resolve_entrypoint("os:system")
    install_fake(monkeypatch)
    h = make_host(tmp_path, {"demo": ficha()})
    h._plugins["demo"].entrypoint = "os:system"  # as if the ficha had been changed after loading: the check is repeated before the import
    out = h.call("demo", "ping")
    assert out["status"] == "degraded" and "fuera de la lista permitida" in out["reason"]


def test_inflight_cap_bounds_hung_calls(tmp_path, monkeypatch):
    mod = install_fake(monkeypatch)
    h = make_host(tmp_path, {"demo": ficha()})
    for _ in range(H.MAX_INFLIGHT):
        assert h.call("demo", "slow", timeout_s=0.02)["reason"].startswith("timeout")
    out = h.call("demo", "ping")
    assert out["status"] == "degraded" and "llamadas en curso" in out["reason"]
    mod.release.set()
    deadline = time.time() + 5
    while time.time() < deadline and h._inflight.get("demo"):
        time.sleep(0.02)
    assert h.call("demo", "ping")["status"] == "ok"


def test_toggle_persists_across_hosts_and_defaults_come_from_the_ficha(tmp_path, monkeypatch):
    install_fake(monkeypatch)
    state = tmp_path / "state.json"
    fichas = {"demo": ficha(), "other": ficha("other", enabled=False)}
    h1 = make_host(tmp_path, fichas, state)
    assert h1.get("demo")["enabled"] is True and h1.get("other")["enabled"] is False  # enabled_default
    assert h1.state_info() == {"persisted": None, "error": None}
    assert h1.set_enabled("demo", False)["status"] == "off" and h1.state_info()["persisted"] is True
    assert json.loads(state.read_text(encoding="utf-8")) == {"schema": "plugin_host_state/v1", "enabled": {"demo": False}}
    assert h1.set_enabled("nope", True) is None
    h2 = make_host(tmp_path, fichas, state)  # a new host (as after a restart with the same file) sees the switch
    assert h2.get("demo")["enabled"] is False and h2.get("other")["enabled"] is False and h2.gate_open("demo") is False
    assert h2.set_enabled("other", True)["status"] == "ready" and h2.set_enabled("demo", True)["status"] == "ready"
    assert json.loads(state.read_text(encoding="utf-8"))["enabled"] == {"demo": True, "other": True}
    assert make_host(tmp_path, fichas, state).get("other")["enabled"] is True


def test_unwritable_state_path_keeps_the_switch_in_memory(tmp_path, monkeypatch):
    install_fake(monkeypatch)
    blocker = tmp_path / "blocker"
    blocker.write_text("i am a file, not a folder", encoding="utf-8")
    h = make_host(tmp_path, {"demo": ficha()}, blocker / "sub" / "state.json")
    rec = h.set_enabled("demo", False)  # must not raise
    assert rec["enabled"] is False and rec["status"] == "off"
    assert h.state_info()["persisted"] is False and "memoria" in h.state_info()["error"]
    assert h.call("demo", "ping")["status"] == "off" and h.gate_open("demo") is False
    assert h.set_enabled("demo", True)["status"] == "ready" and h.state_info()["persisted"] is False


def test_corrupt_state_file_is_ignored_and_the_env_path_is_used(tmp_path, monkeypatch):
    install_fake(monkeypatch)
    state = tmp_path / "state.json"
    state.write_text("{nada", encoding="utf-8")
    h = make_host(tmp_path, {"demo": ficha()}, state)
    assert h.get("demo")["enabled"] is True and "ilegible" in h.state_info()["error"]
    monkeypatch.setenv("RIU_PLUGINS_STATE", str(tmp_path / "from-env.json"))
    assert H.default_state_path() == tmp_path / "from-env.json"
    monkeypatch.delenv("RIU_PLUGINS_STATE")
    monkeypatch.setenv("RIU_DATA_DIR", str(tmp_path / "data"))
    assert H.default_state_path() == tmp_path / "data" / "plugins_state.json"


def test_gate_is_closed_only_for_a_valid_plugin_that_is_off(tmp_path, monkeypatch):
    install_fake(monkeypatch)
    h = make_host(tmp_path, {"demo": ficha(), "off": ficha("off", enabled=False), "bad": ficha("bad", entry="os:system")})
    assert h.gate_open("demo") is True and h.gate_open("off") is False
    assert h.gate_open("bad") is True and h.gate_open("unknown") is True
    h.set_enabled("demo", False)
    assert h.gate_open("demo") is False


def test_chat_status_call_never_raises_without_the_router_dependencies(tmp_path):
    h = H.PluginHost(ROOT / "plugins", tmp_path / "state.json")
    out = h.call("chat", "status", timeout_s=20)
    assert out["status"] in ("ok", "degraded") and (out["status"] == "ok" or out["reason"])  # fastapi missing -> degraded, present -> ok
    assert h.get("chat")["status"] in ("ready", "degraded")


# ---- HTTP / gate (need fastapi) ---------------------------------------------------------------------------------------
KEY = {"X-API-Key": "k1"}


def _shipped_host(tmp_path):
    host = H.PluginHost(ROOT / "plugins", tmp_path / "state.json")
    H.set_host(host)
    return host


def test_plugins_endpoints_and_chat_gate_with_a_stub_chat_router(tmp_path, monkeypatch):
    pytest.importorskip("fastapi")
    pytest.importorskip("huggingface_hub")
    from fastapi import APIRouter, FastAPI
    from fastapi.testclient import TestClient

    from integration.plugin_host import api as plugin_api

    monkeypatch.setenv("RIU_AGENT_API_KEYS", '{"k1": "agent-a"}')
    _shipped_host(tmp_path)
    try:
        chat = APIRouter()

        @chat.get("/chat/ping")
        def ping():
            return {"ok": True}

        app = FastAPI()
        app.include_router(plugin_api.build_plugin_router())
        app.include_router(chat, dependencies=plugin_api.chat_gate_dependencies())
        c = TestClient(app)
        assert c.get("/plugins").status_code == 401 and c.post("/plugins/chat/disable").status_code == 401  # same auth as the rest of the Router
        listing = c.get("/plugins", headers=KEY).json()
        by_id = {p["id"]: p for p in listing["plugins"]}
        assert by_id["chat"]["enabled"] is True and by_id["thinking-modes"]["status"] == "off" and "thinking-modes" in by_id
        assert by_id["chat"]["health"]["status"] in ("ok", "degraded") and by_id["thinking-modes"]["health"] is None
        assert c.get("/chat/ping").json() == {"ok": True}  # default: on, nothing changes
        off = c.post("/plugins/chat/disable", headers=KEY)
        assert off.status_code == 200 and off.json()["plugin"]["status"] == "off" and off.json()["state"]["persisted"] is True
        blocked = c.get("/chat/ping")
        assert blocked.status_code == 503 and blocked.json()["detail"] == "plugin chat apagado"
        assert c.get("/plugins", headers=KEY).status_code == 200  # the plugin API itself is not behind the chat gate
        assert c.post("/plugins/chat/enable", headers=KEY).json()["plugin"]["status"] in ("ready", "degraded")
        assert c.get("/chat/ping").status_code == 200
        assert c.post("/plugins/nope/enable", headers=KEY).status_code == 404
    finally:
        H.set_host(None)


def test_gate_fails_open_if_the_host_breaks(tmp_path, monkeypatch):
    pytest.importorskip("fastapi")
    pytest.importorskip("huggingface_hub")
    import asyncio

    from fastapi import HTTPException

    from integration.plugin_host import api as plugin_api

    host = _shipped_host(tmp_path)
    try:
        host.set_enabled("chat", False)
        with pytest.raises(HTTPException) as info:
            asyncio.run(plugin_api.chat_gate())
        assert info.value.status_code == 503 and info.value.detail == "plugin chat apagado"
        host._plugins = None  # broken host: the gate lets the request through instead of failing
        assert asyncio.run(plugin_api.chat_gate()) is None
    finally:
        H.set_host(None)


def test_real_router_chat_routes_answer_503_when_chat_is_off(tmp_path, monkeypatch):
    pytest.importorskip("fastapi")
    pytest.importorskip("huggingface_hub")
    from fastapi.testclient import TestClient

    from integration.chat_mvp import app as chat_app

    monkeypatch.setenv("RIU_AGENT_API_KEYS", '{"k1": "agent-a"}')
    _shipped_host(tmp_path)
    try:
        c = TestClient(chat_app.app)
        assert c.get("/plugins", headers=KEY).status_code == 200
        assert c.get("/chat").status_code == 200 and c.get("/chat/router/status", headers=KEY).status_code == 200  # default: on
        assert c.post("/plugins/chat/disable", headers=KEY).status_code == 200
        for path in ("/chat", "/chat/providers", "/chat/router/status", "/chat/agents"):
            r = c.get(path, headers=KEY)
            assert r.status_code == 503 and r.json()["detail"] == "plugin chat apagado", path
        assert c.post("/chat/route", json={"message": "hola"}, headers=KEY).status_code == 503
        assert c.post("/chat/jobs/run", json={}, headers=KEY).status_code == 503
        assert c.get("/health").status_code == 200  # the rest of the Router keeps answering
        assert c.post("/plugins/chat/enable", headers=KEY).status_code == 200
        assert c.get("/chat").status_code == 200
    finally:
        H.set_host(None)


def test_router_still_starts_if_the_plugin_host_cannot_be_imported():
    pytest.importorskip("fastapi")
    pytest.importorskip("huggingface_hub")
    code = ("import sys\n"
            "sys.modules['integration.plugin_host.api'] = None  # makes `from ..plugin_host.api import ...` raise ImportError\n"
            f"sys.path.insert(0, {str(ROOT)!r})\n"
            "from integration.chat_mvp import app as a\n"
            "from fastapi.testclient import TestClient\n"
            "c = TestClient(a.app)  # by requests, not by route list: newer FastAPI hides included routes behind one wrapper\n"
            "codes = (c.get('/plugins').status_code, c.get('/chat').status_code, c.get('/health').status_code)\n"
            "assert codes[0] == 404 and codes[1] == 200 and codes[2] == 200, codes\n"
            "print('APP-OK')\n")
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=180, env=dict(os.environ))
    assert r.returncode == 0 and "APP-OK" in r.stdout, (r.stdout + r.stderr)[-1500:]
