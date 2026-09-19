from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

pytest.importorskip("fastapi")
pytest.importorskip("huggingface_hub")

from fastapi.testclient import TestClient  # noqa: E402

from integration.huggingface import fastapi_gateway as gw  # noqa: E402

BODY = {"model": "moonshotai/Kimi-K3", "messages": [{"role": "user", "content": "hola"}]}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("RIU_AGENT_API_KEYS", '{"test-key": "agent-chat"}')
    monkeypatch.setattr(gw, "cached_discovery", lambda: [])  # never touch the network in tests
    monkeypatch.delenv(gw.LIVE_ENV, raising=False)
    return TestClient(gw.app)


def _kimi(payload):
    return next(m for m in payload["models"] if m["model_id"] == "moonshotai/Kimi-K3")


def test_chat_page_and_selector_follow_live_flag(client, monkeypatch):
    page = client.get("/chat")
    assert page.status_code == 200
    assert "/chat/models" in page.text and "/v1/chat/completions" in page.text
    off = client.get("/chat/models").json()
    ids = {m["model_id"] for m in off["models"]}
    assert {"moonshotai/Kimi-K3", "deepseek-ai/DeepSeek-V4-Pro", "deepseek-ai/DeepSeek-V4-Flash"} <= ids
    assert off["live_provider_inference"] is False and _kimi(off)["selectable"] is False
    monkeypatch.setenv(gw.LIVE_ENV, "1")
    on = client.get("/chat/models").json()
    assert on["live_provider_inference"] is True and _kimi(on)["selectable"] is True
    assert _kimi(on)["certified"] is False


def test_chat_requires_api_key(client):
    assert client.post("/v1/chat/completions", json=BODY).status_code == 401
    assert client.post("/v1/chat/completions", json=BODY, headers={"X-API-Key": "wrong"}).status_code == 401


def test_flag_off_rejects_uncertified_model_with_400_through_real_hot_path(client):
    r = client.post("/v1/chat/completions", json=BODY, headers={"X-API-Key": "test-key"})
    assert r.status_code == 400
    assert "MODEL_NOT_IN_CERTIFIED_REGISTRY" in r.json()["detail"]


def test_gateway_passes_executor_and_reports_certified_flag(client, monkeypatch):
    seen = {}

    async def fake_route(**kw):
        seen.update(kw)
        return {"model": kw["model_id"], "message": {"role": "assistant", "content": "hola"},
                "finish_reason": "stop", "certified": False}

    monkeypatch.setattr(gw, "route_chat_completion", fake_route)
    r = client.post("/v1/chat/completions", json=BODY, headers={"Authorization": "Bearer test-key"})
    assert r.status_code == 200
    body = r.json()
    assert body["certified"] is False and body["agent_id"] == "agent-chat"
    assert body["choices"][0]["message"]["content"] == "hola"
    assert callable(seen["executor"])
