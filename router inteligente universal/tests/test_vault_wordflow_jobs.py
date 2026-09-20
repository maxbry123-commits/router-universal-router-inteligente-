from __future__ import annotations

import base64
import gzip
import json
import sys
import threading
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

pytest.importorskip("fastapi")
pytest.importorskip("huggingface_hub")

from fastapi.testclient import TestClient  # noqa: E402

from integration.chat_mvp import app as chat_app  # noqa: E402
from integration.chat_mvp import core, jobs, wordflow_agents  # noqa: E402
from integration.chat_mvp import github_tools as gh  # noqa: E402
from integration.chat_mvp import providers as prov  # noqa: E402
from integration.chat_mvp import router as rt  # noqa: E402
from integration.chat_mvp import vault_bridge as vb  # noqa: E402
from integration.chat_mvp.store import Store  # noqa: E402

PASS = "una-contrasena-de-prueba-larga"
FAST_KDF = {"n": 2**10, "r": 8, "p": 1}
SECRETS = {"nvidia/uno": "nvapi-TEST-SECRET-UNO", "nvidia/dos": "nvapi-TEST-SECRET-DOS", "huggingface/primary": "hf_TEST_SECRET",
           "github/planeta123": "ghp_TEST_SECRET_PLANETA"}
NAMES = ("NVIDIA_API_KEY", "NVIDIA_API_KEY_1", "NVIDIA_API_KEY_2", "NVIDIA_API_KEY_3", "NVIDIA_API_KEY_4", "NVIDIA_API_KEY_5", "HF_TOKEN", "HF_TOKEN_1", "RIU_GITHUB_ACCOUNTS")


@pytest.fixture
def bank(tmp_path, monkeypatch):
    for n in NAMES:
        monkeypatch.delenv(n, raising=False)
    path = tmp_path / "vault.db"
    monkeypatch.setenv("RIU_VAULT_PATH", str(path))
    b = vb.VaultBridge()
    mod = b.mod()
    mod.Vault(path, kdf=FAST_KDF).initialize(PASS)
    opened = mod.Vault(path).unlock(PASS)
    for ref, value in SECRETS.items():
        opened.put(ref, value, scope="github" if ref.startswith("github/") else "inference")
    monkeypatch.setattr(vb, "bridge", b)
    from integration.chat_mvp import vault_hook

    vault_hook.set_provider_keys(b.provider_keys)
    yield b
    b.lock()
    vault_hook.set_provider_keys(lambda p: [])


def test_unlock_puts_bank_keys_first_in_the_pool_and_lock_removes_them(bank, monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY_1", "env-key")
    assert prov.env_keys("nvidia") == ["env-key"]
    assert bank.unlock(PASS) == 4
    keys = prov.env_keys("nvidia")
    assert keys[:2] == ["nvapi-TEST-SECRET-UNO", "nvapi-TEST-SECRET-DOS"] and keys[-1] == "env-key"
    assert prov.resolve_key("hf") == "hf_TEST_SECRET"
    assert core.key_pool("nvidia", keys[0]) == keys
    bank.lock()
    assert prov.env_keys("nvidia") == ["env-key"] and prov.resolve_key("hf") is None


def test_github_tokens_reach_the_account_selector_only_while_unlocked(bank):
    assert "planeta123" not in gh.accounts_from_env()
    bank.unlock(PASS)
    assert gh.accounts_from_env()["planeta123"] and gh.token_for("planeta123") == "ghp_TEST_SECRET_PLANETA"
    bank.lock()
    assert "planeta123" not in gh.accounts_from_env() and gh.token_for("planeta123") is None


def test_wrong_passphrase_lockout_and_status_never_returns_values(bank):
    for _ in range(vb.MAX_FAILS):
        with pytest.raises(vb.BankError, match="INVALID_PASSPHRASE"):
            bank.unlock("contrasena-incorrecta-123")
    with pytest.raises(vb.BankError, match="TOO_MANY_ATTEMPTS"):
        bank.unlock(PASS)
    bank._fails.clear()
    bank.unlock(PASS)
    status = json.dumps(bank.status())
    assert "nvidia/uno" in status and not any(v in status for v in SECRETS.values())


def test_unlock_expires_by_ttl(bank, monkeypatch):
    monkeypatch.setenv("RIU_VAULT_TTL", "0.05")
    bank.unlock(PASS)
    assert prov.env_keys("nvidia")
    time.sleep(0.1)
    assert bank.status()["unlocked"] is False and prov.env_keys("nvidia") == []


def test_import_only_when_missing_and_only_sqlite(tmp_path, monkeypatch):
    monkeypatch.setenv("RIU_VAULT_PATH", str(tmp_path / "new.db"))
    b = vb.VaultBridge()
    with pytest.raises(vb.BankError, match="VAULT_IMPORT_INVALID"):
        b.import_b64gz(base64.b64encode(gzip.compress(b"not sqlite")).decode())
    good = base64.b64encode(gzip.compress(b"SQLite format 3\x00" + b"x" * 64)).decode()
    assert b.import_b64gz(good) > 0
    with pytest.raises(vb.BankError, match="VAULT_EXISTS"):
        b.import_b64gz(good)


@pytest.fixture
def client(tmp_path, monkeypatch, bank):
    monkeypatch.setenv("RIU_AGENT_API_KEYS", '{"k1": "agent-a"}')
    rt.set_store(Store(tmp_path / "data"))
    yield TestClient(chat_app.app)
    rt.set_store(None)


H = {"X-API-Key": "k1"}


def test_vault_api_requires_key_unlocks_puts_and_locks(client):
    assert client.get("/vault/status").status_code == 401
    assert "Banco secreto" in client.get("/vault").text
    assert client.post("/vault/unlock", json={"passphrase": "mala-contrasena-1234"}, headers=H).status_code == 401
    ok = client.post("/vault/unlock", json={"passphrase": PASS}, headers=H)
    assert ok.status_code == 200 and ok.json()["credentials"] == 4
    assert not any(v in ok.text for v in SECRETS.values())
    put = client.post("/vault/credentials", json={"ref": "cerebras/uno", "secret": "csk-TEST", "scope": "inference"}, headers=H)
    assert put.status_code == 200 and "csk-TEST" not in put.text
    assert client.get("/vault/status", headers=H).json()["credentials"][-1]["credential_ref"] in {"nvidia/uno", "nvidia/dos", "huggingface/primary", "github/planeta123", "cerebras/uno"}
    assert client.post("/vault/lock", headers=H).json() == {"unlocked": False}
    assert client.post("/vault/credentials", json={"ref": "cerebras/dos", "secret": "x"}, headers=H).status_code == 423


def test_wordflow_fleet_is_mirrored_as_14_agents(tmp_path):
    store = Store(tmp_path)
    assert wordflow_agents.seed(store) == 14 and wordflow_agents.seed(store) == 14  # idempotent
    ids = {a["id"] for a in store.agents()}
    assert {"wf-opencode", "wf-openhands", "wf-openclaw", "wf-aider", "wf-goose", "wf-kimi-k-code"} <= ids
    agent = store.agent("wf-openhands")
    assert "review/repair" in agent["system_prompt"] and "GAP:" in agent["system_prompt"] and agent["models"]
    assert len([i for i in ids if i.startswith("wf-")]) == 14


def _executor(delay=0.0, tracker=None):
    def ex(*, provider, model, messages, max_tokens):
        if tracker is not None:
            with tracker["lock"]:
                tracker["now"] += 1
                tracker["max"] = max(tracker["max"], tracker["now"])
        time.sleep(delay)
        if tracker is not None:
            with tracker["lock"]:
                tracker["now"] -= 1
        node = messages[1]["content"]
        text = "GAP: no puedo" if "falla" in node else ("hecho zafiro" if "zafiro" in node else "texto libre")
        return {"message": {"content": text}, "usage": {}, "cached": False}

    return ex


def test_parallel_jobs_commit_only_verified_results_to_the_chosen_account(tmp_path, monkeypatch):
    store = Store(tmp_path)
    wordflow_agents.seed(store)
    monkeypatch.setenv("RIU_GITHUB_ACCOUNTS", json.dumps({"cuenta-a": "TOK_A", "cuenta-b": "TOK_B"}))
    monkeypatch.setenv("TOK_A", "tok-a")
    monkeypatch.setenv("TOK_B", "tok-b")
    commits = []

    def put_file(token, repo, path, text, message, branch=None):
        commits.append((token, repo, path, text))
        return {"path": path, "commit": "K" * 40}

    tracker = {"lock": threading.Lock(), "now": 0, "max": 0}
    todo = [
        {"id": "j1", "agent_id": "wf-opencode", "provider": "hf", "model": "m", "instructions": "escribe zafiro", "expect": {"contains": ["zafiro"]},
         "github": {"account": "cuenta-a", "repo": "o/r", "path": "out/j1.md"}},
        {"id": "j2", "agent_id": "wf-aider", "provider": "hf", "model": "m", "instructions": "escribe zafiro", "expect": {"contains": ["zafiro"]},
         "github": {"account": "cuenta-b", "repo": "o/r2", "path": "out/j2.md"}},
        {"id": "j3", "agent_id": "wf-codex", "provider": "hf", "model": "m", "instructions": "esto falla", "expect": {"contains": ["zafiro"]},
         "github": {"account": "cuenta-a", "repo": "o/r", "path": "out/j3.md"}},
        {"id": "j4", "agent_id": "wf-goose", "provider": "hf", "model": "m", "instructions": "sin expect",
         "github": {"account": "cuenta-a", "repo": "o/r", "path": "out/j4.md"}},
        {"id": "j5", "agent_id": "wf-goose", "provider": "hf", "model": "m", "instructions": "sin expect", "github": {"account": "cuenta-a", "repo": "o/r", "path": "out/j5.md", "allow_unverified": True}},
        {"id": "j6", "agent_id": "wf-cline", "provider": "hf", "model": "m", "instructions": "escribe zafiro", "expect": {"contains": ["zafiro"]},
         "github": {"account": "no-existe", "repo": "o/r", "path": "out/j6.md"}},
    ]
    results = {r["id"]: r for r in jobs.run_jobs(store, "owner", todo, max_parallel=6, executor=_executor(0.05, tracker), put_file=put_file)}
    assert tracker["max"] > 1  # really parallel
    assert results["j1"]["commit"]["commit"] == "K" * 40 and results["j2"]["commit"] and results["j5"]["commit"]
    assert results["j3"]["status"] == "FAIL" and results["j3"]["error"] == "NOT_COMMITTED_STATUS_FAIL"
    assert results["j4"]["status"] == "UNVERIFIED" and results["j4"]["commit"] is None and results["j4"]["error"] == "NOT_COMMITTED_STATUS_UNVERIFIED"
    assert results["j6"]["error"] == "GITHUB_ACCOUNT_NOT_CONFIGURED"
    assert {(c[0], c[1]) for c in commits} == {("tok-a", "o/r"), ("tok-b", "o/r2")} and len(commits) == 3
    assert all(r["ledger_valid"] for r in results.values())


def test_jobs_endpoint_runs_through_the_router_core(client, monkeypatch):
    rt.get_store()
    wordflow_agents.seed(rt.get_store())
    monkeypatch.setenv("CEREBRAS_API_KEY_1", "c-key")
    monkeypatch.setattr(core, "call_via_router", lambda provider, key, model, messages, max_tokens, temperature=None: {
        "message": {"role": "assistant", "content": "hecho zafiro"}, "finish_reason": "stop", "usage": {"prompt_tokens": 3, "completion_tokens": 2}})
    body = {"jobs": [{"id": "a1", "agent_id": "wf-opencode", "provider": "cerebras", "model": "llama", "instructions": "zafiro", "expect": {"contains": ["zafiro"]}},
                     {"id": "a2", "agent_id": "wf-aider", "provider": "cerebras", "model": "llama", "instructions": "zafiro", "expect": {"contains": ["nunca"]}}]}
    assert client.post("/chat/jobs/run", json=body).status_code == 401
    r = client.post("/chat/jobs/run", json=body, headers=H)
    assert r.status_code == 200, r.text
    out = r.json()
    assert out["total"] == 2 and out["passed"] == 1 and {x["id"]: x["status"] for x in out["results"]} == {"a1": "PASS", "a2": "FAIL"}
