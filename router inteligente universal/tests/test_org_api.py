"""Organization views preserve the State Hub and chat store on GET."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

pytest.importorskip("fastapi")
pytest.importorskip("huggingface_hub")

from fastapi import HTTPException
from fastapi.testclient import TestClient
from integration.chat_mvp import app as chat_app
from integration.chat_mvp import router as rt
from integration.chat_mvp import ui_bridge
from integration.chat_mvp.store import Store


def test_state_event_replay_recovers_missing_snapshot_and_rejects_corruption(tmp_path, monkeypatch):
    records = {}
    legacy = {
        "seq": 1, "type": "TASK_CLAIMED", "at": "2026-09-30T00:00:00Z",
        "project": "chat-yaiwes", "task": "T-11", "actor": "devin",
    }
    current = ui_bridge._state_event({
        "type": "CHECKPOINT_RECORDED", "project": "chat-yaiwes",
        "task": "T-11", "actor": "devin", "summary": "verificado",
    }, 2)
    log = json.dumps(legacy) + "\n" + json.dumps(current) + "\n"
    records[ui_bridge.BITACORA] = log
    records[ui_bridge.HANDOFF] = "# Handoff\n"
    monkeypatch.setattr(ui_bridge, "_read", lambda path: (records.get(path, ""), None))
    monkeypatch.setattr(ui_bridge, "_write", lambda path, text, _msg: records.__setitem__(path, text))

    expected = ui_bridge._rebuild_state()
    snapshot = records[ui_bridge.STATE]
    del records[ui_bridge.STATE]
    assert ui_bridge._rebuild_state() == expected
    assert records[ui_bridge.STATE] == snapshot

    altered = {**current, "summary": "sin verificar"}
    with pytest.raises(HTTPException, match="STATE_BITACORA_INVALID_HASH"):
        ui_bridge._state_events(json.dumps(legacy) + "\n" + json.dumps(altered))
    with pytest.raises(HTTPException, match="STATE_BITACORA_INVALID_SCHEMA"):
        ui_bridge._state_events(json.dumps(current) + "\n" + json.dumps({**legacy, "seq": 3}))
    with pytest.raises(HTTPException, match="STATE_BITACORA_INVALID_HASH"):
        ui_bridge._state_events(json.dumps(current) + "\n" + json.dumps({**current, "seq": 3}))
    monkeypatch.setattr(
        ui_bridge, "_write",
        lambda path, text, _msg: None if path == ui_bridge.BITACORA else records.__setitem__(path, text),
    )
    with pytest.raises(HTTPException, match="STATE_EVENT_READBACK_FAILED"):
        ui_bridge._emit_state_event({
            "type": "TASK_COMPLETED", "project": "chat-yaiwes",
            "task": "T-11", "actor": "devin",
        })
    assert records[ui_bridge.STATE] == snapshot


def test_org_views_audit_reads_without_changing_functional_state(tmp_path, monkeypatch):
    monkeypatch.setenv("RIU_AGENT_API_KEYS", '{"key": "owner"}')
    store = Store(tmp_path)
    rt.set_store(store)
    client = TestClient(chat_app.app)
    state = ROOT.parent / "chat router/03-ESTADO"
    before = {path: path.read_bytes() for path in state.iterdir() if path.is_file()}
    audit_log = tmp_path / "audit.jsonl"
    audit_log.write_bytes((state / "BITACORA.jsonl").read_bytes())
    original_events = ui_bridge._state_events(audit_log.read_text(encoding="utf-8"))
    original_projection = ui_bridge._state_projection(original_events)

    def read_audit(path):
        assert path == ui_bridge.BITACORA
        return audit_log.read_text(encoding="utf-8"), "test-sha"

    def write_audit(path, text, _message):
        assert path == ui_bridge.BITACORA
        audit_log.write_text(text, encoding="utf-8")

    monkeypatch.setattr(ui_bridge, "_read", read_audit)
    monkeypatch.setattr(ui_bridge, "_write", write_audit)
    writes = store._db.total_changes
    try:
        for path, key in (
            ("graph", "graph"), ("queue", "tasks"), ("bitacora", "events"),
            ("connectors", "connectors"), ("templates", "templates"),
            ("engineering", "toggles"), ("files", "files"),
        ):
            response = client.get(f"/chat/org/{path}", headers={"X-API-Key": "key"})
            assert response.status_code == 200, (path, response.text)
            assert response.json()["status"] == "ok"
            assert key in response.json()["data"]
        run = client.get("/chat/org/dag/ORDER-000-smoke", headers={"X-API-Key": "key"})
        assert run.status_code == 200
        assert run.json()["data"]["run"]["ledger"]
        assert client.get("/chat/org/graph").status_code == 401
        assert client.get("/chat/org/dag/unknown", headers={"X-API-Key": "key"}).json() == {
            "status": "error", "detail": "DAG_NOT_FOUND",
        }
        assert client.get("/chat/org/bitacora?limit=201", headers={"X-API-Key": "key"}).json() == {
            "status": "error", "detail": "LIMIT_INVALID",
        }
        assert client.get("/chat/org/bitacora?limit=invalid", headers={"X-API-Key": "key"}).json() == {
            "status": "error", "detail": "LIMIT_INVALID",
        }
        assert store._db.total_changes == writes
        assert before == {path: path.read_bytes() for path in before}
        events = ui_bridge._state_events(audit_log.read_text(encoding="utf-8"))
        reads = events[len(original_events):]
        assert len(reads) == 11
        assert [event["seq"] for event in reads] == list(range(original_events[-1]["seq"] + 1, events[-1]["seq"] + 1))
        assert all(event["type"] == "RESOURCE_READ" and event["task"] == "UI-T-05" for event in reads)
        assert [event["summary"] for event in reads[-2:]] == [
            "GET /chat/org/bitacora HTTP 400", "GET /chat/org/bitacora HTTP 400",
        ]
        assert ui_bridge._state_projection(events) == original_projection
    finally:
        rt.set_store(None)


def test_org_views_fail_closed_if_audit_cannot_be_recorded(monkeypatch):
    monkeypatch.setenv("RIU_AGENT_API_KEYS", '{"key": "owner"}')
    monkeypatch.setattr(ui_bridge, "_read", lambda _path: ("", None))

    def fail_audit(_path, _text, _message):
        raise OSError("write failed")

    monkeypatch.setattr(ui_bridge, "_write", fail_audit)
    client = TestClient(chat_app.app)
    response = client.get("/chat/org/queue", headers={"X-API-Key": "key"})
    assert response.status_code == 503
    assert response.json() == {
        "status": "error", "detail": "STATE_AUDIT_UNAVAILABLE",
    }


def test_org_shell_serves_modular_panels_and_locked_palette():
    client = TestClient(chat_app.app)
    shell = client.get("/chat/organization")
    assert shell.status_code == 200 and "shell.js" in shell.text
    for name in ("chat", "archivos", "seguimiento", "canvas", "org"):
        for extension in ("html", "js"):
            result = client.get(f"/chat/ui/panel-{name}.{extension}")
            assert result.status_code == 200
            assert len(result.text.splitlines()) <= 500
    css = client.get("/chat/ui/shell.css")
    assert css.status_code == 200
    assert all(color in css.text for color in ("#1B1B1B", "#202020", "#2A2A2A", "#3C3C3C", "#484848", "#0848F7"))
    assert "localStorage" not in client.get("/chat/ui/api.js").text


def test_browser_auth_uses_native_challenge_without_key_in_ui(monkeypatch):
    monkeypatch.setenv("RIU_ROUTER_API_KEY", "local-test-key")
    monkeypatch.setenv("RIU_AGENT_API_KEYS", '{"local-test-key": "owner"}')
    client = TestClient(chat_app.app)
    unauthorized = client.get("/chat/ui/shell.html")
    assert unauthorized.status_code == 401
    assert unauthorized.headers["www-authenticate"] == 'Basic realm="Router"'
    authorized = client.get("/chat/ui/shell.html", auth=("router", "local-test-key"))
    assert authorized.status_code == 200
    assert "router-key" not in authorized.text
    api_js = client.get("/chat/ui/api.js", auth=("router", "local-test-key"))
    assert api_js.status_code == 200
    assert "X-API-Key" not in api_js.text
    assert client.get("/chat/providers", auth=("router", "wrong-key")).status_code == 401
    assert client.get("/chat/providers", auth=("router", "local-test-key")).status_code == 200


def test_media_only_serves_authenticated_safe_formats(tmp_path, monkeypatch):
    monkeypatch.setenv("RIU_AGENT_API_KEYS", '{"key": "owner"}')
    store = Store(tmp_path)
    rt.set_store(store)
    client = TestClient(chat_app.app)
    try:
        image = store.put_document("photo.png", "image/png", b"image-bytes")
        html = store.put_document("page.html", "text/html", b"<script>bad()</script>")
        assert client.get(f"/chat/media/{image['id']}").status_code == 401
        result = client.get(f"/chat/media/{image['id']}", headers={"X-API-Key": "key"})
        assert result.status_code == 200 and result.content == b"image-bytes"
        assert result.headers["x-content-type-options"] == "nosniff"
        assert client.get(f"/chat/media/{html['id']}", headers={"X-API-Key": "key"}).status_code == 404
    finally:
        rt.set_store(None)
