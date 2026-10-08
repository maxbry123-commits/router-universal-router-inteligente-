"""Banco: borrar / activar-desactivar credenciales y persistir el banco cifrado en el bucket HF. Sin red."""
from __future__ import annotations

import base64
import gzip
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

pytest.importorskip("fastapi")
pytest.importorskip("cryptography")

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from integration.chat_mvp import vault_api, vault_bridge as vb  # noqa: E402
from integration.chat_mvp.router import _auth  # noqa: E402

PASS = "test-master-passphrase"
FAKE = "sk-FAKE-not-a-real-key-0123456789"


class FakeFS:
    files: dict[str, bytes] = {}

    def __init__(self, token=None, skip_instance_cache=False):
        assert token

    def cat_file(self, p):
        if p not in self.files:
            raise FileNotFoundError(p)
        return self.files[p]

    def pipe_file(self, p, data):
        self.files[p] = bytes(data)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("RIU_VAULT_PATH", str(tmp_path / "v.db"))
    monkeypatch.setenv("RIU_VAULT_PROVIDERS_FILE", str(tmp_path / "providers.json"))
    monkeypatch.delenv("RIU_VAULT_AUTOLOCK_S", raising=False)
    monkeypatch.delenv("RIU_VAULT_TTL", raising=False)
    monkeypatch.setenv("RIU_VAULT_SOURCE", "buckets/x/y/banco/vault.db.gz.b64")
    monkeypatch.setenv("HF_TOKEN", "hf_fake")
    FakeFS.files = {"buckets/x/y/banco/vault.db.gz.b64": b"old"}
    monkeypatch.setitem(sys.modules, "huggingface_hub", types.SimpleNamespace(HfFileSystem=FakeFS))
    b = vb.VaultBridge()
    b.mod().Vault(b.path()).initialize(PASS)
    b.unlock(PASS)
    monkeypatch.setattr(vault_api, "bridge", b)
    app = FastAPI()
    app.include_router(vault_api.build_vault_router())
    app.dependency_overrides[_auth] = lambda: "tester"
    return TestClient(app), b


def _remote_vault(tmp_path):
    raw = gzip.decompress(base64.b64decode(FakeFS.files["buckets/x/y/banco/vault.db.gz.b64"]))
    assert raw.startswith(b"SQLite format 3")
    p = tmp_path / "remote.db"
    p.write_bytes(raw)
    return p


def test_put_persists_encrypted_bank_with_backup(client, tmp_path):
    c, b = client
    r = c.post("/vault/credentials", json={"ref": "groq/k1", "secret": FAKE})
    assert r.status_code == 200 and r.json() == {"stored": "groq/k1", "persisted": "PERSISTED"}
    assert FAKE not in r.text
    assert any(k.startswith("buckets/x/y/banco/vault.db.gz.b64.bak-") and v == b"old" for k, v in FakeFS.files.items())
    remote = b.mod().Vault(_remote_vault(tmp_path)).unlock(PASS)
    assert remote.get_secret("groq/k1") == FAKE
    assert FAKE.encode() not in FakeFS.files["buckets/x/y/banco/vault.db.gz.b64"]


def test_disable_enable_and_pool(client, tmp_path):
    c, b = client
    c.post("/vault/credentials", json={"ref": "groq/k1", "secret": FAKE})
    assert b.provider_keys("groq") == [FAKE]
    r = c.post("/vault/credentials/groq/k1/enabled", json={"enabled": False})
    assert r.status_code == 200 and r.json() == {"ref": "groq/k1", "enabled": False, "persisted": "PERSISTED"}
    assert b.provider_keys("groq") == []
    remote = b.mod().Vault(_remote_vault(tmp_path)).unlock(PASS)
    assert remote.get_record("groq/k1")["enabled"] in (False, 0)
    assert c.post("/vault/credentials/groq/k1/enabled", json={"enabled": True}).json()["enabled"] is True
    assert b.provider_keys("groq") == [FAKE]


def test_delete_and_not_found(client, tmp_path):
    c, b = client
    c.post("/vault/credentials", json={"ref": "groq/k1", "secret": FAKE})
    r = c.delete("/vault/credentials/groq/k1")
    assert r.status_code == 200 and r.json() == {"deleted": "groq/k1", "persisted": "PERSISTED"}
    assert [x["credential_ref"] for x in b.status()["credentials"]] == []
    assert c.delete("/vault/credentials/groq/k1").status_code == 404
    assert c.post("/vault/credentials/groq/nope/enabled", json={"enabled": True}).status_code == 404
    assert c.delete("/vault/credentials/GROQ/k1").status_code == 422


def test_locked_bank_refuses(client):
    c, b = client
    b.lock()
    assert c.delete("/vault/credentials/groq/k1").status_code == 423
    assert c.post("/vault/credentials/groq/k1/enabled", json={"enabled": False}).status_code == 423


def test_persist_skipped_without_source(client, monkeypatch):
    c, b = client
    monkeypatch.delenv("RIU_VAULT_SOURCE")
    assert c.post("/vault/credentials", json={"ref": "groq/k2", "secret": FAKE}).json() == {"stored": "groq/k2"}
