from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integration.chat_mvp import jev  # noqa: E402


def fake_result(text: str) -> dict[str, Any]:
    return {"message": {"role": "assistant", "content": text}, "finish_reason": "stop", "usage": None}


def test_choice_parses_and_validates(monkeypatch):
    monkeypatch.setattr(jev.core, "call_via_router", lambda *a, **k: fake_result(
        '{"choice": "billing", "probabilities": {"billing": 0.8, "technical": 0.15, "other": 0.05}, "confidence": 0.8}'))
    out = jev.choice({"body": "cobro duplicado"}, "¿Qué departamento?", {"billing": "pagos", "technical": "errores", "other": "resto"})
    assert out["choice"] == "billing" and abs(sum(out["probabilities"].values()) - 1.0) < 1e-6 and out["confidence"] == 0.8


def test_choice_rejects_option_outside_criteria(monkeypatch):
    monkeypatch.setattr(jev.core, "call_via_router", lambda *a, **k: fake_result('{"choice": "shipping", "probabilities": {}, "confidence": 0.5}'))
    with pytest.raises(jev.JevError, match="JEV_INVALID_CHOICE"):
        jev.choice({}, "x", {"billing": "a", "technical": "b"})


def test_choice_rejects_probability_keys_outside_criteria(monkeypatch):
    monkeypatch.setattr(jev.core, "call_via_router", lambda *a, **k: fake_result(
        '{"choice": "billing", "probabilities": {"billing": 0.9, "shipping": 0.1}, "confidence": 0.9}'))
    with pytest.raises(jev.JevError, match="JEV_INVALID_CHOICE"):
        jev.choice({}, "x", {"billing": "a", "technical": "b"})


def test_score_in_range(monkeypatch):
    monkeypatch.setattr(jev.core, "call_via_router", lambda *a, **k: fake_result('{"score": 1.4, "probabilities": {"0": 0.1, "1": 0.5, "2": 0.4}, "confidence": 0.6}'))
    out = jev.score({}, "urgencia", ["baja", "media", "alta"])
    assert out["score"] == 1.4 and out["legend"] == ["baja", "media", "alta"] and set(out["probabilities"]) == {"0", "1", "2"}


def test_score_out_of_range_raises(monkeypatch):
    monkeypatch.setattr(jev.core, "call_via_router", lambda *a, **k: fake_result('{"score": 5.0, "probabilities": {}, "confidence": 0.9}'))
    with pytest.raises(jev.JevError, match="JEV_INVALID_SCORE"):
        jev.score({}, "x", ["a", "b", "c"])


def test_noul_returns_probability(monkeypatch):
    monkeypatch.setattr(jev.core, "call_via_router", lambda *a, **k: fake_result('{"noul": 0.92}'))
    assert jev.noul({}, "¿es urgente?")["noul"] == 0.92


def test_noul_out_of_range_raises(monkeypatch):
    monkeypatch.setattr(jev.core, "call_via_router", lambda *a, **k: fake_result('{"noul": 1.4}'))
    with pytest.raises(jev.JevError, match="JEV_INVALID_NOUL"):
        jev.noul({}, "x")


def test_missing_json_raises(monkeypatch):
    monkeypatch.setattr(jev.core, "call_via_router", lambda *a, **k: fake_result("no puedo responder eso"))
    with pytest.raises(jev.JevError, match="JEV_INVALID_RESPONSE"):
        jev.noul({}, "x")


def test_choice_needs_criteria():
    with pytest.raises(ValueError):
        jev.choice({}, "x", {})


def test_jev_route_endpoint(tmp_path, monkeypatch):
    pytest.importorskip("fastapi")
    pytest.importorskip("huggingface_hub")
    from fastapi.testclient import TestClient

    from integration.chat_mvp import app as chat_app
    from integration.chat_mvp import jev as jev_mod
    from integration.chat_mvp import router as rt
    from integration.chat_mvp.store import Store

    monkeypatch.setenv("RIU_AGENT_API_KEYS", '{"k1": "agent-a"}')
    monkeypatch.setattr(jev_mod.core, "call_via_router", lambda *a, **k: fake_result('{"noul": 0.77}'))
    rt.set_store(Store(tmp_path))
    client = TestClient(chat_app.app)
    H = {"X-API-Key": "k1"}
    try:
        assert client.post("/chat/jev", json={"kind": "noul", "state": {}, "instructions": "x"}).status_code == 401
        ok = client.post("/chat/jev", json={"kind": "noul", "state": {"a": 1}, "instructions": "x"}, headers=H)
        assert ok.status_code == 200 and ok.json()["answer"]["noul"] == 0.77
        bad = client.post("/chat/jev", json={"kind": "choice", "state": {}, "instructions": "x"}, headers=H)
        assert bad.status_code == 400
    finally:
        rt.set_store(None)
