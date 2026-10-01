"""Organization views preserve the State Hub and chat store on GET."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

pytest.importorskip("fastapi")
pytest.importorskip("huggingface_hub")

from fastapi.testclient import TestClient

from integration.chat_mvp import app as chat_app
from integration.chat_mvp import router as rt
from integration.chat_mvp.store import Store


def test_org_views_are_authenticated_real_and_read_only(tmp_path, monkeypatch):
    monkeypatch.setenv("RIU_AGENT_API_KEYS", '{"key": "owner"}')
    store = Store(tmp_path)
    rt.set_store(store)
    client = TestClient(chat_app.app)
    state = ROOT.parent / "chat router/03-ESTADO"
    before = {path: path.read_bytes() for path in state.iterdir() if path.is_file()}
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
        assert store._db.total_changes == writes
        assert before == {path: path.read_bytes() for path in before}
    finally:
        rt.set_store(None)
