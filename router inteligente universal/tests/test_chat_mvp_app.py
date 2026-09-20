from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

pytest.importorskip("fastapi")
pytest.importorskip("huggingface_hub")

from fastapi.testclient import TestClient  # noqa: E402

from integration.chat_mvp import app as chat_app  # noqa: E402
from integration.chat_mvp import github_tools as gh  # noqa: E402
from integration.chat_mvp import providers as prov  # noqa: E402
from integration.chat_mvp import router as rt  # noqa: E402
from integration.chat_mvp.store import Store  # noqa: E402

H = {"X-API-Key": "k1"}
KIMI = "moonshotai/Kimi-K3"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("RIU_AGENT_API_KEYS", '{"k1": "agent-a", "k2": "agent-b"}')
    monkeypatch.setenv("RIU_CHAT_ALLOW_PROVIDER_LIVE", "1")
    monkeypatch.setenv("HF_TOKEN_1", "hf-test-not-a-secret")
    for name in ("HF_TOKEN", "NVIDIA_API_KEY", "NVIDIA_API_KEY_1", "CEREBRAS_API_KEY", "CEREBRAS_API_KEY_1", "RIU_GITHUB_ACCOUNTS"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(rt, "cached_discovery", lambda: [])
    rt.set_store(Store(tmp_path))
    calls: list[dict] = []

    def fake_chat(provider, key, model, messages, max_tokens, *, temperature=None, post=None):
        calls.append({"provider": provider, "key": key, "model": model, "messages": messages})
        return {"model": model, "message": {"role": "assistant", "content": "eco:" + messages[-1]["content"]},
                "finish_reason": "stop", "usage": {"total_tokens": 3}}

    monkeypatch.setattr(prov, "chat", fake_chat)
    monkeypatch.setattr(prov, "list_models", lambda provider, key, **kw: ["llama3.1-8b", "deepseek-v4-flash-x"])
    c = TestClient(chat_app.app)
    c.calls = calls
    yield c
    rt.set_store(None)


def send(client, **over):
    body = {"message": "hola", "provider": "hf", "model": KIMI, **over}
    return client.post("/chat/send", json=body, headers=H)


def test_page_providers_and_auth(client):
    page = client.get("/chat")
    assert page.status_code == 200 and "Chat RIU" in page.text and "/chat/send" in page.text
    body = client.get("/chat/providers").json()
    assert {p["id"] for p in body["providers"]} == {"hf", "cerebras", "nvidia", "groq", "local"}
    assert next(p for p in body["providers"] if p["id"] == "hf")["configured"] is True
    assert client.post("/chat/send", json={"message": "x", "model": KIMI}).status_code == 401
    assert client.get("/chat/agents").status_code == 401


def test_send_hf_live_model_keeps_history_and_isolates_owners(client):
    r = send(client)
    assert r.status_code == 200, r.text
    first = r.json()
    assert first["reply"] == "eco:hola" and first["certified"] is False and first["conversation_id"]
    assert client.calls[-1]["key"] == "hf-test-not-a-secret" and client.calls[-1]["model"] == KIMI
    r2 = send(client, message="segundo", conversation_id=first["conversation_id"])
    assert r2.status_code == 200
    roles = [m["role"] for m in client.calls[-1]["messages"]]
    assert roles == ["user", "assistant", "user"]
    assert len(client.get("/chat/conversations", headers=H).json()["conversations"]) == 1
    assert client.get(f"/chat/conversations/{first['conversation_id']}", headers=H).status_code == 200
    other = client.get(f"/chat/conversations/{first['conversation_id']}", headers={"X-API-Key": "k2"})
    assert other.status_code == 404


def test_hf_gate_rejects_unselectable_models_and_flag_off(client, monkeypatch):
    assert send(client, model="Qwen/Qwen3.8-27B").json()["detail"] == "MODEL_NOT_SELECTABLE"
    monkeypatch.setenv("RIU_CHAT_ALLOW_PROVIDER_LIVE", "0")
    r = send(client)
    assert r.status_code == 400 and r.json()["detail"] == "MODEL_NOT_SELECTABLE"


def test_other_providers_use_catalog_and_byok(client):
    r = client.post("/chat/send", json={"message": "hola", "provider": "cerebras", "model": "llama3.1-8b"},
                    headers={**H, "X-Provider-Key": "byok-key"})
    assert r.status_code == 200 and client.calls[-1]["key"] == "byok-key" and client.calls[-1]["provider"] == "cerebras"
    bad = client.post("/chat/send", json={"message": "hola", "provider": "cerebras", "model": "no-existe"},
                      headers={**H, "X-Provider-Key": "byok-key"})
    assert bad.status_code == 400 and bad.json()["detail"] == "MODEL_NOT_IN_PROVIDER_CATALOG"
    missing = client.post("/chat/send", json={"message": "hola", "provider": "nvidia", "model": "x"}, headers=H)
    assert missing.status_code == 400 and missing.json()["detail"] == "PROVIDER_KEY_MISSING:nvidia"
    listing = client.get("/chat/providers/nvidia/models", headers={**H, "X-Provider-Key": "k"}).json()
    assert [m["model_id"] for m in listing["models"]][0] == "deepseek-v4-flash-x" and listing["models"][0]["suggested"] is True


def test_agent_mode_and_agent_crud(client):
    r = client.post("/chat/send", json={"message": "haz X", "provider": "hf", "model": KIMI, "mode": "agent",
                                        "agent_id": "seals-team-yaiwes-001"}, headers=H)
    assert r.status_code == 200 and r.json()["agent_id"] == "seals-team-yaiwes-001"
    first = client.calls[-1]["messages"][0]
    assert first["role"] == "system" and "Seals Team" in first["content"]
    nf = client.post("/chat/send", json={"message": "x", "provider": "hf", "model": KIMI, "mode": "agent", "agent_id": "nope"}, headers=H)
    assert nf.status_code == 400 and nf.json()["detail"] == "AGENT_NOT_FOUND"
    up = client.post("/chat/agents", json={"id": "seals-team-yaiwes-002", "name": "Seals 002", "role": "code", "system_prompt": "PROMPT-002"}, headers=H)
    assert up.status_code == 200
    assert client.post("/chat/send", json={"message": "x", "provider": "hf", "model": KIMI, "mode": "agent", "agent_id": "seals-team-yaiwes-002"}, headers=H).status_code == 200
    assert client.calls[-1]["messages"][0]["content"] == "PROMPT-002"
    assert client.delete("/chat/agents/seals-team-yaiwes-002", headers=H).status_code == 200
    assert client.delete("/chat/agents/seals-team-yaiwes-002", headers=H).status_code == 404
    assert client.post("/chat/agents", json={"id": "BAD ID", "name": "x"}, headers=H).status_code == 422


def test_documents_upload_attach_and_delete(client):
    data = base64.b64encode(b"la palabra secreta es zafiro").decode()
    up = client.post("/chat/documents", json={"name": "notas.txt", "mime": "text/plain", "data_b64": data}, headers=H)
    assert up.status_code == 200
    did = up.json()["document"]["id"]
    assert client.get("/chat/documents", headers=H).json()["documents"][0]["id"] == did
    assert "zafiro" in client.get(f"/chat/documents/{did}", headers=H).json()["preview"]
    r = send(client, doc_ids=[did])
    assert r.status_code == 200 and r.json()["docs_used"] == [did]
    assert any("zafiro" in m["content"] and m["role"] == "system" for m in client.calls[-1]["messages"])
    binary = client.post("/chat/documents", json={"name": "a.bin", "data_b64": base64.b64encode(b"\x00\x01").decode()}, headers=H).json()["document"]["id"]
    assert send(client, doc_ids=[binary]).status_code == 404
    assert client.post("/chat/documents", json={"name": "x", "data_b64": "###"}, headers=H).json()["detail"] == "DOCUMENT_BASE64_INVALID"
    assert client.delete(f"/chat/documents/{did}", headers=H).status_code == 200
    assert client.delete(f"/chat/documents/{did}", headers=H).status_code == 404


def test_cache_hit_skips_the_provider(client):
    a = send(client, cache=True).json()
    n = len(client.calls)
    b = send(client, cache=True).json()
    assert a["cached"] is False and b["cached"] is True and len(client.calls) == n
    assert client.get("/chat/storage", headers=H).json()["cache"]["hits"] == 1


def test_github_accounts_switch_read_attach_and_commit(client, monkeypatch):
    monkeypatch.setenv("RIU_GITHUB_ACCOUNTS", json.dumps({"cuenta-1": "T1", "cuenta-2": "T2"}))
    monkeypatch.setenv("T1", "tok-one")
    monkeypatch.setenv("T2", "tok-two")
    seen: list[tuple[str, str]] = []

    def fake_http(method, url, token, body):
        seen.append((method, token))
        if url.endswith("/user"):
            return 200, {"login": "user-of-" + token}
        if "/contents/" in url and method == "GET":
            return 200, {"type": "file", "path": "a.md", "sha": "S", "size": 4, "content": base64.b64encode(b"data").decode()}
        if method == "PUT":
            return 201, {"content": {"path": "a.md", "sha": "C"}, "commit": {"sha": "K" * 40}}
        return 200, [{"full_name": "o/r", "private": True, "default_branch": "main"}]

    monkeypatch.setattr(gh, "_http", fake_http)
    accounts = client.get("/chat/github/accounts", headers=H).json()["accounts"]
    assert [a["account"] for a in accounts] == ["cuenta-1", "cuenta-2"] and all(a["configured"] for a in accounts)
    assert client.get("/chat/github/whoami?account=cuenta-2", headers=H).json()["login"] == "user-of-tok-two"
    assert client.get("/chat/github/whoami?account=cuenta-1", headers=H).json()["login"] == "user-of-tok-one"
    assert client.get("/chat/github/repos?account=cuenta-1", headers=H).json()["repos"][0]["full_name"] == "o/r"
    f = client.get("/chat/github/file?account=cuenta-1&repo=o/r&path=a.md&attach=true", headers=H).json()
    assert f["text"] == "data" and f["document"]["name"] == "r_a.md"
    commit = client.post("/chat/github/commit", json={"account": "byok", "repo": "o/r", "path": "a.md", "content": "nuevo"},
                         headers={**H, "X-GitHub-Token": "tok-byok"})
    assert commit.status_code == 200 and commit.json()["commit"] == "K" * 40 and ("PUT", "tok-byok") in seen
    assert client.get("/chat/github/whoami?account=desconocida", headers=H).json()["detail"] == "GITHUB_ACCOUNT_NOT_CONFIGURED"
    assert "tok-one" not in json.dumps(accounts)


def test_storage_graph_and_bucket_sync(client):
    send(client, message="uno")
    stats = client.get("/chat/storage", headers=H).json()
    assert stats["sql"]["messages"] == 2 and stats["graph"]["edges"] >= 2 and stats["hf_bucket"]["configured"] is False
    graph = client.get("/chat/graph", headers=H).json()
    assert {"conversation", "model", "owner"} <= {n["kind"] for n in graph["nodes"]}
    assert client.post("/chat/storage/sync", headers=H).json()["detail"] == "HF_BUCKET_ID_NOT_SET"

    written: dict[str, bytes] = {}

    class FakeFS:
        def __init__(self, token=None):
            assert token == "w"

        def pipe_file(self, path, data):
            written[path] = data

    client.post("/chat/documents", json={"name": "n.txt", "mime": "text/plain", "data_b64": base64.b64encode(b"x").decode()}, headers=H)
    out = rt.sync_to_bucket(rt.get_store(), "u/b", "w", fs_factory=FakeFS)
    assert out == {"bucket": "u/b", "files": 2}
    assert written["buckets/u/b/riu-chat/riu_chat.sqlite3"].startswith(b"SQLite format 3")
