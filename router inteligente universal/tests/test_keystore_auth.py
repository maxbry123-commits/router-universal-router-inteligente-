from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integration.huggingface import keystore_auth as ks  # noqa: E402

sys.path.insert(0, str(ROOT / "security"))
from api_key_manager import APIKeyManager  # noqa: E402


def _keystore(tmp_path, n=3, **kw):
    mgr = APIKeyManager()
    keys = {}
    for i in range(1, n + 1):
        agent = f"MAXBRY-{i:03d}"
        plain, _ = mgr.create(agent, **kw)
        keys[agent] = plain
    path = tmp_path / "ks.json"
    path.write_text(json.dumps(mgr.hash_state()), encoding="utf-8")
    return path, keys


def test_valid_key_returns_agent_id_with_a_single_pbkdf2(tmp_path, monkeypatch):
    path, keys = _keystore(tmp_path)
    calls = []
    real = APIKeyManager._digest
    monkeypatch.setattr(APIKeyManager, "_digest", staticmethod(lambda k, s: (calls.append(1), real(k, s))[1]))
    assert ks.verify_keystore_key(keys["MAXBRY-002"], path=path) == "MAXBRY-002"
    assert len(calls) == 1


def test_wrong_unknown_and_malformed_keys_fail_closed(tmp_path):
    path, keys = _keystore(tmp_path)
    assert ks.verify_keystore_key(keys["MAXBRY-001"] + "x", path=path) is None
    assert ks.verify_keystore_key("riu_MAXBRY-999_abc", path=path) is None
    assert ks.verify_keystore_key("not-a-riu-key", path=path) is None
    assert ks.verify_keystore_key("", path=path) is None and ks.verify_keystore_key(None, path=path) is None
    assert ks.verify_keystore_key(keys["MAXBRY-001"], path=tmp_path / "missing.json") is None


def test_revoked_and_wrong_scope_are_rejected(tmp_path):
    path, keys = _keystore(tmp_path)
    data = json.loads(path.read_text())
    data[0]["status"] = "revoked"
    path.write_text(json.dumps(data))
    assert ks.verify_keystore_key(keys["MAXBRY-001"], path=path) is None
    assert ks.verify_keystore_key(keys["MAXBRY-002"], path=path) == "MAXBRY-002"
    assert ks.verify_keystore_key(keys["MAXBRY-002"], scope="admin", path=path) is None


def test_wrapped_json_format_is_accepted(tmp_path):
    path, keys = _keystore(tmp_path, n=1)
    path.write_text(json.dumps({"schema": "x", "keys": json.loads(path.read_text())}))
    assert ks.verify_keystore_key(keys["MAXBRY-001"], path=path) == "MAXBRY-001"


def test_committed_keystore_has_100_active_hash_only_slots():
    recs = ks.load_records(ks.DEFAULT_KEYSTORE)
    assert len(recs) == 100
    assert {r["agent_id"] for r in recs} == {f"MAXBRY-{i:03d}" for i in range(1, 101)}
    assert all(r.get("status", "active") == "active" for r in recs)
    blob = ks.DEFAULT_KEYSTORE.read_text(encoding="utf-8")
    assert '"riu_' not in blob  # no plaintext key material


def test_gateway_authenticates_keystore_keys(tmp_path, monkeypatch):
    pytest.importorskip("fastapi")
    pytest.importorskip("huggingface_hub")
    from fastapi.testclient import TestClient

    from integration.huggingface import fastapi_gateway as gw

    path, keys = _keystore(tmp_path, n=2)
    monkeypatch.setenv(ks.KEYSTORE_ENV, str(path))
    monkeypatch.delenv("RIU_AGENT_API_KEYS", raising=False)
    monkeypatch.setenv(gw.LIVE_ENV, "1")
    monkeypatch.setattr(gw, "cached_discovery", lambda: [])

    async def fake_route(**kw):
        return {"model": kw["model_id"], "message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop", "certified": False}

    monkeypatch.setattr(gw, "route_chat_completion", fake_route)
    client = TestClient(gw.app)
    body = {"model": "moonshotai/Kimi-K3", "messages": [{"role": "user", "content": "hi"}]}
    ok = client.post("/v1/chat/completions", json=body, headers={"X-API-Key": keys["MAXBRY-002"]})
    assert ok.status_code == 200 and ok.json()["agent_id"] == "MAXBRY-002"
    assert client.post("/v1/chat/completions", json=body, headers={"X-API-Key": keys["MAXBRY-002"] + "x"}).status_code == 401
