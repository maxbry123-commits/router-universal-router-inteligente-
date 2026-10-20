"""Deterministic baseline tests for canonical red/conectores.py REUSE."""
from __future__ import annotations

import asyncio
import importlib.util
import sys
from pathlib import Path


def _load_module():
    path = Path(__file__).parents[1] / "red" / "conectores.py"
    spec = importlib.util.spec_from_file_location("riu_conectores", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_missing_secret_is_not_hardcoded() -> None:
    m = _load_module()
    connector = m.ConectorHTTP(
        "test-http",
        "https://example.invalid",
        headers_env={"Authorization": "RIU_TEST_MISSING_SECRET"},
    )
    assert connector._headers() == {}


def test_vps_rejects_unapproved_command_without_network() -> None:
    m = _load_module()
    connector = m.ConectorVPS("test-vps", "http://127.0.0.1")
    result = asyncio.run(connector.enviar({"_cmd": "rm"}))
    assert result["status"] == "FAIL"
    assert result["error"].startswith("cmd_no_permitido:")


def test_webhook_fails_closed_without_env() -> None:
    m = _load_module()
    connector = m.ConectorWebhook("test-webhook", "RIU_TEST_MISSING_WEBHOOK")
    result = asyncio.run(connector.enviar({"payload": "x"}))
    assert result == {
        "status": "FAIL",
        "error": "env_faltante:RIU_TEST_MISSING_WEBHOOK",
    }
