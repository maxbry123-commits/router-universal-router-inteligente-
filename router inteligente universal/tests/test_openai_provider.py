"""Proveedor openai: 14 claves por entorno, max_completion_tokens, sin temperature en gpt nuevos, grupo sdk y ficha banco."""
import json
from pathlib import Path

from integration.chat_mvp import providers as P
from integration.plugin_host import host as H

ROOT = Path(__file__).resolve().parents[1]
MSG = [{"role": "user", "content": "hi"}]


def test_env_keys_openai_14(monkeypatch):
    for n in ["OPENAI_API_KEY", *[f"OPENAI_API_KEY_{i}" for i in range(1, 15)]]:
        monkeypatch.delenv(n, raising=False)
    for i in range(1, 15):
        monkeypatch.setenv(f"OPENAI_API_KEY_{i}", f"k{i}")
    monkeypatch.setattr(P.vault_hook, "provider_keys", lambda p: [])
    assert P.env_keys("openai") == [f"k{i}" for i in range(1, 15)]
    assert P.PROVIDERS["openai"]["base"] == "https://api.openai.com/v1"


def _fake(captured):
    def post(url, key, body):
        captured.update(url=url, key=key, body=body)
        return {"choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}], "usage": {}}
    return post


def test_openai_payload_new_models():
    c = {}
    P.chat("openai", "k", "gpt-6-luna", MSG, 16, temperature=0.7, post=_fake(c))
    assert c["url"] == "https://api.openai.com/v1/chat/completions"
    assert c["body"]["max_completion_tokens"] == 16
    assert "max_tokens" not in c["body"] and "temperature" not in c["body"]


def test_other_providers_unchanged():
    c = {}
    P.chat("groq", "k", "m", MSG, 16, temperature=0.7, post=_fake(c))
    assert c["body"]["max_tokens"] == 16 and c["body"]["temperature"] == 0.7


def test_openai_old_model_keeps_temperature():
    c = {}
    P.chat("openai", "k", "gpt-4.1", MSG, 16, temperature=0.2, post=_fake(c))
    assert c["body"]["temperature"] == 0.2


def test_sdk_group_chain():
    chain = json.loads((ROOT / "integration/chat_mvp/policies.json").read_text())["groups"]["sdk"]["chain"]
    assert 1 <= len(chain) <= 10
    assert all(o["provider"] == "openai" and o["timeout"] == 90 and o["model"].startswith("gpt") for o in chain)


def test_banco_ficha_valida():
    ficha = json.loads((ROOT / "plugins/banco/ficha.json").read_text())
    assert H.check_v1(ficha, "banco") == []
    assert ficha["ejecucion"]["runtime_type"] == "compute" and ficha["seguridad"]["sandbox"] == "egress-allowlist"
