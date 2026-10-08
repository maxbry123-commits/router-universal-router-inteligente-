"""PUNTO 2: historial persistente por chat (sesion) en SQLite, legible por GET /chat/history/{sesion}. Sin red."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

pytest.importorskip("fastapi")

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from integration.chat_mvp import memoria_loader  # noqa: E402
from integration.chat_mvp.router import _auth, set_store, sync_to_bucket  # noqa: E402
from integration.chat_mvp.storage_runtime import restore_from_bucket  # noqa: E402
from integration.chat_mvp.store import Store  # noqa: E402

A, B = "web-0123456789abcdef", "web-fedcba9876543210"


def _plugin():
    path = ROOT / "plugins" / "puente_chat" / "plugin.py"
    spec = importlib.util.spec_from_file_location("puente_chat_plugin_hist", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


class FakeFS:
    files: dict[str, bytes] = {}

    def __init__(self, token=None):
        pass

    def pipe_file(self, p, data):
        self.files[p] = bytes(data)

    def cat_file(self, p):
        if p not in self.files:
            raise FileNotFoundError(p)
        return self.files[p]

    def ls(self, p, detail=False):
        return [k for k in self.files if k.startswith(p.rstrip("/") + "/")]

    def find(self, p, **kw):
        return self.ls(p)

    def exists(self, p):
        return p in self.files


@pytest.fixture()
def store(tmp_path):
    st = Store(tmp_path / "job1")
    set_store(st)
    memoria_loader._facade = None
    yield st
    set_store(None)
    memoria_loader._facade = None
    st.close()


def _client(auth=True):
    app = FastAPI()
    app.include_router(memoria_loader.build_memory_router())
    if auth:
        app.dependency_overrides[_auth] = lambda: "tester"
    return TestClient(app)


def _write_turns(plugin):
    assert plugin.DUENO == memoria_loader.CHAT_OWNER
    assert plugin._guardar(A, "groq-qwen-3-8", "hola A1", "resp A1")
    assert plugin._guardar(B, "nv-nemotron-super", "hola B1", "resp B1")
    assert plugin._guardar(A, "groq-qwen-3-8", "hola A2", "resp A2")
    plugin._ck_guardar(A, [{"role": "user", "content": "checkpoint interno"}])  # no debe salir en el historial


def test_history_returns_only_that_chat_in_order(store):
    _write_turns(_plugin())
    c = _client()
    r = c.get("/chat/history/" + A)
    assert r.status_code == 200
    body = r.json()
    assert body["sesion"] == A and body["turns"] == 2 and body["scope"] == "chat-ui:chat:" + A
    assert [(m["role"], m["content"]) for m in body["messages"]] == [
        ("user", "hola A1"), ("assistant", "resp A1"), ("user", "hola A2"), ("assistant", "resp A2")]
    assert body["messages"][1]["model"] == "groq-qwen-3-8" and body["messages"][1]["ts"]
    rb = c.get("/chat/history/" + B).json()
    assert [m["content"] for m in rb["messages"]] == ["hola B1", "resp B1"]
    assert c.get("/chat/history/web-0000000000000000").json()["messages"] == []
    assert c.get("/chat/history/" + A + "?limit=1").json()["turns"] == 1


def test_history_validates_and_requires_key(store):
    assert _client().get("/chat/history/bad%20sesion").status_code == 422
    assert _client(auth=False).get("/chat/history/" + A).status_code == 401


def test_history_survives_job_switch_via_bucket_sync(store, tmp_path):
    _write_turns(_plugin())
    FakeFS.files = {}
    sync_to_bucket(store, "ns/bucket", "tok", fs_factory=FakeFS)  # autosync / sync antes de cancelar el Job viejo
    set_store(None)
    memoria_loader._facade = None
    res = restore_from_bucket(tmp_path / "job2", "ns/bucket", "tok", fs_factory=FakeFS)  # arranque del Job nuevo
    assert res["status"] not in ("SKIPPED_NOT_CONFIGURED",)
    st2 = Store(tmp_path / "job2")
    set_store(st2)
    try:
        body = _client().get("/chat/history/" + A).json()
        assert [m["content"] for m in body["messages"]] == ["hola A1", "resp A1", "hola A2", "resp A2"]
    finally:
        set_store(None)
        st2.close()
