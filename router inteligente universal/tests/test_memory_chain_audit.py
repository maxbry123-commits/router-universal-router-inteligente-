"""PUNTO 3: auditoría de la cadena puente_chat -> memory_runtime -> memoria_loader -> memoria_yaiwes -> Store SQLite -> bucket."""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

pytest.importorskip("fastapi")

from integration.chat_mvp import memoria_loader  # noqa: E402
from integration.chat_mvp.router import set_store, sync_to_bucket  # noqa: E402
from integration.chat_mvp.storage_runtime import restore_from_bucket  # noqa: E402
from integration.chat_mvp.store import Store  # noqa: E402
from plugins.puente_chat import plugin as P  # noqa: E402
from plugins.puente_chat import plugin_long_context as L  # noqa: E402

S = "web-aaaaaaaaaaaaaaaa"


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
    st = Store(tmp_path / "d")
    set_store(st)
    memoria_loader._facade = None
    yield st
    set_store(None)
    memoria_loader._facade = None
    st.close()


def test_turn_written_by_bridge_lands_in_store_sqlite_file(store):
    assert L._guardar(S, "groq-qwen-3-8", "pregunta-1", "respuesta-1")
    db = sqlite3.connect(str(store.db_path))  # mismo archivo que Store (y que sube storage_runtime)
    rows = db.execute("SELECT scope,key,data FROM memoria_yaiwes").fetchall()
    assert rows and rows[0][0] == "chat-ui:chat:" + S and rows[0][1].startswith("turno-") and "respuesta-1" in rows[0][2]


@pytest.mark.parametrize("ctx", ["long", "base"])
def test_context_recall_is_not_crowded_out_by_checkpoints(store, ctx):
    L._guardar(S, "m", "pregunta-vieja", "respuesta-vieja")
    for i in range(80):  # el bucle de herramientas guarda 4-10 checkpoints por turno
        P._ck_guardar(S, [{"role": "user", "content": "ck %d" % i}])
    text = (L._contexto if ctx == "long" else P._contexto)(S, "nueva")
    assert "pregunta-vieja" in text and "respuesta-vieja" in text


def test_checkpoint_roundtrip_still_works(store):
    P._ck_guardar(S, [{"role": "user", "content": "estado"}])
    P._CHECKPOINTS.clear()  # simula otro proceso: debe leerse de SQLite
    assert P._ck_cargar(S) == [{"role": "user", "content": "estado"}]


def test_sessions_are_isolated(store):
    L._guardar(S, "m", "solo-A", "rA")
    L._guardar("web-bbbbbbbbbbbbbbbb", "m", "solo-B", "rB")
    assert "solo-B" not in L._contexto(S, "x") and "solo-A" not in L._contexto("web-bbbbbbbbbbbbbbbb", "x")


def test_bucket_roundtrip_keeps_memory_for_next_job(store, tmp_path):
    L._guardar(S, "m", "antes-del-relevo", "ok")
    FakeFS.files = {}
    out = sync_to_bucket(store, "ns/b", "tok", fs_factory=FakeFS)
    assert out["files"] >= 1 and "buckets/ns/b/riu-chat/riu_chat.sqlite3" in FakeFS.files
    res = restore_from_bucket(tmp_path / "job2", "ns/b", "tok", fs_factory=FakeFS)
    assert res["status"] == "RESTORED"
    again = restore_from_bucket(tmp_path / "job2", "ns/b", "tok", fs_factory=FakeFS)
    assert again["status"] == "LOCAL_PRESENT"  # nunca pisa un SQLite local con datos
    set_store(None); memoria_loader._facade = None
    st2 = Store(tmp_path / "job2"); set_store(st2)
    try:
        assert "antes-del-relevo" in L._contexto(S, "x")
    finally:
        set_store(None); st2.close()
