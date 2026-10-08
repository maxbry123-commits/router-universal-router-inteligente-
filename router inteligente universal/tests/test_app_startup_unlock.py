"""El hook de arranque abre el banco con RIU_VAULT_PASSPHRASE del entorno (antes fallaba con AttributeError)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

pytest.importorskip("fastapi")
pytest.importorskip("cryptography")

PASS = "test-master-passphrase"


def test_startup_hook_unlocks_bank(tmp_path, monkeypatch, caplog):
    monkeypatch.setenv("RIU_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("RIU_VAULT_PATH", str(tmp_path / "v.db"))
    monkeypatch.delenv("HF_BUCKET_ID", raising=False)
    from integration.chat_mvp import app as app_mod
    b = app_mod.vault_bridge
    b.lock()
    b.mod().Vault(b.path()).initialize(PASS)
    monkeypatch.setenv("RIU_VAULT_PASSPHRASE", PASS)
    app_mod._unlock_provider_bank()
    assert b.status()["unlocked"] is True
    assert "failed" not in caplog.text and PASS not in caplog.text
    b.lock()
