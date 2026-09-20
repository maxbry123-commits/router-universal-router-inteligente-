from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integration.chat_mvp import github_tools as gh  # noqa: E402
from integration.chat_mvp import providers as prov  # noqa: E402
from integration.chat_mvp.store import Store  # noqa: E402


def test_store_four_systems(tmp_path):
    s = Store(tmp_path)
    assert [a["id"] for a in s.agents()] == ["orquestador-g0", "seals-team-yaiwes-001"]
    cid = s.new_conversation("hola", "seals-team-yaiwes-001", "MAXBRY-001")
    s.add_message(cid, "user", "hi")
    s.add_message(cid, "assistant", "yo", "hf", "m")
    assert [m["role"] for m in s.messages(cid)] == ["user", "assistant"]

    doc = s.put_document("../x/notas.md", "text/markdown", b"palabra secreta: zafiro", cid)
    assert doc["name"] == "notas.md" and doc["is_text"] == 1
    assert "zafiro" in s.document_text(doc["id"])
    assert s.put_document("otra.txt", "text/plain", b"palabra secreta: zafiro")["id"] == doc["id"]  # dedupe by sha256
    binary = s.put_document("a.bin", "application/octet-stream", b"\x00\x01")
    assert s.document_text(binary["id"]) is None
    with pytest.raises(ValueError, match="DOCUMENT_EMPTY"):
        s.put_document("x", "text/plain", b"")

    s.cache_put("k", {"a": 1}, ttl=60)
    assert s.cache_get("k") == {"a": 1}
    s.cache_put("e", 1, ttl=-1)
    assert s.cache_get("e") is None

    s.record_turn(conv_id=cid, owner="MAXBRY-001", provider="hf", model="m", agent_id="seals-team-yaiwes-001", doc_ids=[doc["id"]], repo="o/r")
    g = s.graph_view()
    assert len(g["edges"]) == 5
    assert {n["kind"] for n in g["nodes"]} >= {"owner", "conversation", "model", "agent", "document", "repo"}

    st = s.stats()
    assert st["cache"]["hits"] == 1 and st["documents"]["count"] == 2 and st["graph"]["edges"] == 5
    assert s.snapshot(tmp_path / "snap.sqlite3").stat().st_size > 0
    assert s.delete_document(binary["id"]) and not s.delete_document(binary["id"])


def test_providers_catalog_cache_chat_and_local(monkeypatch):
    prov._models_cache.clear()
    assert prov.list_models("cerebras", "k1", fetch=lambda url, k: {"data": [{"id": "b"}, {"id": "a"}, {"x": 1}]}) == ["a", "b"]

    def boom(url, k):
        raise AssertionError("cache miss")

    assert prov.list_models("cerebras", "k1", fetch=boom) == ["a", "b"]
    out = prov.chat("nvidia", "k", "m", [{"role": "user", "content": "x"}], 5,
                    post=lambda u, k, b: {"choices": [{"message": {"content": None}, "finish_reason": "length"}], "usage": {"total_tokens": 3}})
    assert out["message"]["content"] == "" and out["finish_reason"] == "length"
    monkeypatch.delenv("RIU_LOCAL_BASE_URL", raising=False)
    with pytest.raises(prov.ProviderError, match="NO_BASE_URL"):
        prov.chat("local", None, "m", [], 5)
    monkeypatch.setenv("RIU_LOCAL_BASE_URL", "http://x:8080/v1/")
    assert prov.base_url("local") == "http://x:8080/v1" and prov.configured("local")
    assert prov.resolve_key("groq", "byok") == "byok"


def test_github_accounts_switch_and_tools():
    env = {"RIU_GITHUB_ACCOUNTS": json.dumps({"cuenta-1": "T1", "cuenta-2": "T2"}), "T1": "tok1", "T2": "tok2"}
    assert gh.accounts_from_env(env) == {"cuenta-1": "T1", "cuenta-2": "T2"}
    assert gh.token_for("cuenta-2", env=env) == "tok2" and gh.token_for("x", env=env) is None
    assert gh.token_for("x", "byok", env) == "byok"

    seen = []

    def http(method, url, token, body):
        seen.append((method, token))
        if url.endswith("/user"):
            return 200, {"login": "maxbry"}
        if "/contents/" in url and method == "GET":
            if "nuevo.md" in url:
                return 404, {"message": "Not Found"}
            return 200, {"type": "file", "path": "a/b.md", "sha": "S1", "size": 5, "content": base64.b64encode(b"hola\n").decode()}
        if method == "PUT":
            return 201, {"content": {"path": "nuevo.md", "sha": "C1"}, "commit": {"sha": "K1"}}
        return 200, [{"full_name": "o/r", "private": False}]

    assert gh.whoami("t", http) == "maxbry" and gh.list_repos("t", http)[0]["full_name"] == "o/r"
    assert gh.get_file("t", "o/r", "a/b.md", None, http)["text"] == "hola\n"
    assert gh.put_file("t", "o/r", "nuevo.md", "x", "m", None, http)["commit"] == "K1"
    with pytest.raises(gh.GitHubError) as exc:
        gh.get_file("t", "o/r", "a", None, lambda *a: (200, [{}]))
    assert exc.value.status == "NOT_A_FILE"
