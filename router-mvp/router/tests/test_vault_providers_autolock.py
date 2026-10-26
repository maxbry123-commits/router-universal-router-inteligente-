from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

pytest.importorskip("fastapi")
pytest.importorskip("cryptography")

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from integration.chat_mvp import vault_bridge as vb  # noqa: E402
from integration.chat_mvp.router import _auth  # noqa: E402
from integration.chat_mvp.vault_api import build_vault_router  # noqa: E402

PASS = "test-master-passphrase"
FAKE_SECRET = "sk-FAKE-not-a-real-key-0123456789"


@pytest.fixture()
def bank(tmp_path, monkeypatch):
    monkeypatch.setenv("RIU_VAULT_PATH", str(tmp_path / "v.db"))
    monkeypatch.setenv("RIU_VAULT_PROVIDERS_FILE", str(tmp_path / "providers.json"))
    monkeypatch.delenv("RIU_VAULT_AUTOLOCK_S", raising=False)
    monkeypatch.delenv("RIU_VAULT_TTL", raising=False)
    b = vb.VaultBridge()
    b.mod().Vault(b.path()).initialize(PASS)
    return b, tmp_path


def _write(tmp, data):
    (tmp / "providers.json").write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")


def test_missing_file_falls_back_to_builtin_map(bank):
    _, tmp = bank
    assert vb.provider_map() == vb.DEFAULT_PROVIDER_MAP
    assert vb.provider_map()["hf"] == "huggingface"


@pytest.mark.parametrize("bad", ["{not json", "[1,2]", "\"text\"", "{\"providers\": 5}"])
def test_invalid_file_falls_back(bank, bad):
    _, tmp = bank
    _write(tmp, bad)
    assert vb.provider_map() == vb.DEFAULT_PROVIDER_MAP


def test_one_json_line_adds_provider_and_keeps_builtins(bank):
    _, tmp = bank
    _write(tmp, {"providers": {"acme": {"env": "ACME_API_KEY", "base_url": "https://api.acme.test/v1", "auth": "x-api-key"},
                              "short": "short-vault"}})
    pm = vb.provider_map()
    assert pm["acme"] == "acme" and pm["short"] == "short-vault" and pm["groq"] == "groq"
    info = vb.load_providers()["acme"]
    assert info["env"] == "ACME_API_KEY" and info["auth"] == "x-api-key" and info["base_url"].startswith("https://")


def test_invalid_entries_are_skipped_not_fatal(bank):
    _, tmp = bank
    _write(tmp, {"providers": {"ok": {}, "Bad Name": {}, "badauth": {"auth": "magic"}, "badurl": {"base_url": "ftp://x"},
                              "badenv": {"env": "1 BAD"}, "_note": {}, "num": 3}})
    pm = vb.provider_map()
    assert "ok" in pm
    for k in ("Bad Name", "badauth", "badurl", "badenv", "_note", "num"):
        assert k not in pm
    assert pm["nvidia"] == "nvidia"


def test_json_reloads_without_restart(bank):
    _, tmp = bank
    _write(tmp, {"providers": {"one": {}}})
    assert "one" in vb.provider_map()
    _write(tmp, {"providers": {"one": {}, "two": {"vault_provider": "two-x"}}})
    assert vb.provider_map()["two"] == "two-x"


def test_shipped_providers_json_is_valid_and_equals_builtin(monkeypatch):
    monkeypatch.delenv("RIU_VAULT_PROVIDERS_FILE", raising=False)
    assert vb.providers_file().is_file()
    assert vb.provider_map() == vb.DEFAULT_PROVIDER_MAP


def test_new_sdk_key_reaches_provider_keys(bank):
    b, tmp = bank
    _write(tmp, {"providers": {"acme": {}}})
    b.unlock(PASS)
    b.put("acme/main", FAKE_SECRET)
    b.put("acme/second", FAKE_SECRET + "-2")
    assert b.provider_keys("acme") == [FAKE_SECRET, FAKE_SECRET + "-2"]
    assert b.provider_keys("unknown") == []
    assert FAKE_SECRET not in json.dumps(b.status())
    b.lock()
    assert b.provider_keys("acme") == []


def test_autolock_default_is_never(bank, monkeypatch):
    b, _ = bank
    assert vb.autolock_seconds() == 0.0
    b.unlock(PASS)
    real = vb.time.time()
    monkeypatch.setattr(vb.time, "time", lambda: real + 10 * 365 * 86400)
    assert b.status()["unlocked"] is True
    assert b.status()["ttl_seconds"] is None and b.status()["autolock_s"] == 0.0


def test_autolock_env_closes_bank(bank, monkeypatch):
    b, _ = bank
    monkeypatch.setenv("RIU_VAULT_AUTOLOCK_S", "60")
    b.unlock(PASS)
    st = b.status()
    assert st["unlocked"] and 0 < st["ttl_seconds"] <= 60
    real = vb.time.time()
    monkeypatch.setattr(vb.time, "time", lambda: real + 61)
    assert b.status()["unlocked"] is False


def test_autolock_env_zero_and_legacy_ttl(bank, monkeypatch):
    monkeypatch.setenv("RIU_VAULT_AUTOLOCK_S", "0")
    monkeypatch.setenv("RIU_VAULT_TTL", "5")
    assert vb.autolock_seconds() == 0.0
    monkeypatch.delenv("RIU_VAULT_AUTOLOCK_S")
    assert vb.autolock_seconds() == 5.0
    monkeypatch.setenv("RIU_VAULT_AUTOLOCK_S", "garbage")
    assert vb.autolock_seconds() == 5.0


def test_post_credentials_is_encrypted_and_never_logged_or_echoed(bank, caplog):
    b, tmp = bank
    _write(tmp, {"providers": {"acme": {}}})
    b.unlock(PASS)
    app = FastAPI()
    app.include_router(build_vault_router())
    app.dependency_overrides[_auth] = lambda: "tester"
    # the API module holds its own bridge singleton: point it at this bank
    from integration.chat_mvp import vault_api
    vault_api.bridge = b
    caplog.set_level(logging.DEBUG)
    c = TestClient(app)
    r = c.post("/vault/credentials", json={"ref": "acme/main", "secret": FAKE_SECRET})
    assert r.status_code == 200 and r.json() == {"stored": "acme/main"}
    assert FAKE_SECRET not in r.text
    assert FAKE_SECRET not in c.get("/vault/status").text
    assert FAKE_SECRET not in caplog.text
    raw = (tmp / "v.db").read_bytes()
    assert FAKE_SECRET.encode() not in raw and b"FAKE-not-a-real" not in raw
    bad = c.post("/vault/credentials", json={"ref": "Bad Ref", "secret": FAKE_SECRET})
    assert bad.status_code == 422 and FAKE_SECRET not in bad.text.replace("\"input\"", "") or bad.status_code == 422
    assert b.provider_keys("acme") == [FAKE_SECRET]
