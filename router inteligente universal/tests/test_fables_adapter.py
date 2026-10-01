from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

pytest.importorskip("fastapi")
pytest.importorskip("huggingface_hub")

from fastapi import FastAPI
from fastapi.testclient import TestClient

from integration.chat_mvp import router

HEADERS = {"X-API-Key": "fables-test-key"}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("RIU_AGENT_API_KEYS", '{"fables-test-key":"test-owner"}')
    router._fables_catalog = None
    app = FastAPI()
    app.include_router(router.build_router())
    yield TestClient(app)
    router._fables_catalog = None


def test_fables_registration_validation_and_readback(client):
    assert client.get("/chat/fichas").status_code == 401
    seeded = client.get("/chat/fichas", headers=HEADERS)
    assert seeded.status_code == 200
    rows = seeded.json()["fichas"]
    assert {"yaiwes.panel.chat", "yaiwes.agent.rowboat", "yaiwes.agent.judge"} <= {row["id"] for row in rows}
    assert all(row["status"] == "INACTIVE" and not row["health"] for row in rows)

    ficha = {"artifact_id": "yaiwes.panel.custom", "version": "1.0.0", "estado": "testing",
             "contrato": {"rol": "service"},
             "ejecucion": {"kind": "tool", "transport": "importlib", "runtime_type": "compute"},
             "seguridad": {"sandbox": "process", "limites": {"timeout_ms": 1000}}}
    created = client.post("/chat/fichas", headers=HEADERS, json={"ficha": ficha})
    assert created.status_code == 200, created.text
    assert created.json()["ficha"]["status"] == "INACTIVE"
    assert client.get("/chat/fichas/yaiwes.panel.custom", headers=HEADERS).json() == created.json()
    assert client.post("/chat/fichas", headers=HEADERS, json={"ficha": ficha}).status_code == 409

    invalid = {**ficha, "artifact_id": "yaiwes.panel.invalid", "estado": "active"}
    assert client.post("/chat/fichas", headers=HEADERS, json={"ficha": invalid}).status_code == 422
    malformed = {**ficha, "artifact_id": "yaiwes.panel.malformed", "contrato": []}
    assert client.post("/chat/fichas", headers=HEADERS, json={"ficha": malformed}).status_code == 422
    assert client.get("/chat/fichas/yaiwes.panel.invalid", headers=HEADERS).status_code == 404
