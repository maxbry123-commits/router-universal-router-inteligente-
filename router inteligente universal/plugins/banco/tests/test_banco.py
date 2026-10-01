import os
from plugins.banco import plugin, build_bank


def test_roundtrip(tmp_path, monkeypatch):
    f = tmp_path / "b.vault"
    env = {"NVIDIA_API_KEY_1": "nv-fake-1", "GROQ_API_KEY_1": "gq-fake-1", "GROQ_API_KEY_2": "gq-fake-2", "OPENAI_1_1": "oa-fake-a", "OPENAI_R10": "oa-fake-b"}
    assert build_bank.build(f, "master-de-prueba-123", env) == 5
    monkeypatch.setattr(plugin, "BANK", f)
    monkeypatch.setenv("RIU_BANK_MASTER", "master-de-prueba-123")
    assert plugin.handle("providers")["providers"] == {"nvidia": 1, "groq": 2, "openai": 2}
    assert plugin.handle("get_keys", {"provider": "groq"})["error"] == "INTERNAL_ONLY"
    assert len(plugin.handle("get_keys", {"provider": "groq"}, internal=True)["keys"]) == 2
    assert [r for r, _ in plugin.get_keys("openai")] == ["openai/1.1", "openai/r10"]
    monkeypatch.setenv("RIU_BANK_MASTER", "otra-clave-incorrecta")
    assert plugin.handle("providers")["ok"] is False
    monkeypatch.delenv("RIU_BANK_MASTER")
    assert plugin.handle("status")["locked"] is True
