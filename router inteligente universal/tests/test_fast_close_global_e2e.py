"""FAST-CLOSE global E2E using the live public GitHub API as destination."""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for sub in ("security", "gateway"):
    p = str(ROOT / sub)
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi.testclient import TestClient  # noqa: E402
from api_key_manager import APIKeyManager  # noqa: E402
from fastapi_app import create_app  # noqa: E402


def test_api_key_manager_hash_only_rotate_revoke_and_100_slots() -> None:
    manager = APIKeyManager()
    assert manager.MAX_SLOTS == 100
    plain, meta = manager.create("agent-e2e", allowed_models=("github/public",))
    assert plain.startswith("riu_agent-e2e_")
    assert manager.verify(plain, model_id="github/public") is not None
    serialized = json.dumps(manager.hash_state())
    assert plain not in serialized
    assert "key_hash" in serialized
    rotated, _ = manager.rotate(meta["key_id"])
    assert rotated != plain
    assert manager.verify(plain, model_id="github/public") is None
    assert manager.verify(rotated, model_id="github/public") is not None
    assert manager.revoke(meta["key_id"]) is True
    assert manager.verify(rotated, model_id="github/public") is None

    # Materialize the full authorized capacity without logging or persisting
    # plaintext secrets. The revoked first slot still occupies one of 100 slots.
    issued_plaintexts = []
    for index in range(1, manager.MAX_SLOTS):
        slot_plain, _ = manager.create(
            f"agent-slot-{index:03d}", allowed_models=("github/public",)
        )
        issued_plaintexts.append(slot_plain)
    assert len(manager.hash_state()) == manager.MAX_SLOTS
    hashed_state = json.dumps(manager.hash_state())
    assert all(secret not in hashed_state for secret in issued_plaintexts)
    try:
        manager.create("agent-slot-overflow", allowed_models=("github/public",))
    except RuntimeError as exc:
        assert str(exc) == "max_slots_100"
    else:
        raise AssertionError("slot_101_must_fail_closed")


def test_real_agent_key_fastapi_enchufe_red_github_verifier_response() -> None:
    manager = APIKeyManager()
    plain, meta = manager.create(
        "agent-live-github", scopes=("route",), allowed_models=("github/public",)
    )
    app = create_app(manager)
    client = TestClient(app)
    bad = client.post("/v1/chat/completions", json={"model": "github/public"})
    assert bad.status_code == 401
    response = client.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {plain}"},
        json={"model": "github/public", "messages": [{"role": "user", "content": "read repository README"}], "path": "README.md"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["verified"] is True
    assert body["provider"] == "github"
    assert body["via"] == "dest.github.public"
    assert body["route"] == "FastAPI->APIKeyGuard->EnchufeGate->RedUniversal->GitHubAdapter->Verifier"
    assert isinstance(body["response"], dict)
    assert body["response"].get("type") == "file"
    assert plain not in response.text
    assert manager.revoke(meta["key_id"])
    revoked = client.get("/v1/models", headers={"Authorization": f"Bearer {plain}"})
    assert revoked.status_code == 403
