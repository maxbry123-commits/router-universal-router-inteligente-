"""El adaptador de grafo de memoria_yaiwes respeta el scope pedido (antes /memoria/search devolvia 'graph' de otros chats)."""
from __future__ import annotations

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
from integration.chat_mvp.router import _auth, set_store  # noqa: E402
from integration.chat_mvp.store import Store  # noqa: E402

A = "chat-ui:chat:web-aaaaaaaaaaaaaaaa"
B = "chat-ui:chat:web-bbbbbbbbbbbbbbbb"
HIJA = A + ":ag:wf-codex:1"  # mismo prefijo de id 'memory:<A>:' que el padre
RARO = "chat-ui:chat:web_a%"  # comodines de LIKE en el scope


@pytest.fixture()
def client(tmp_path):
    st = Store(tmp_path / "d")
    set_store(st)
    memoria_loader._facade = None
    app = FastAPI()
    app.include_router(memoria_loader.build_memory_router())
    app.dependency_overrides[_auth] = lambda: "tester"
    yield TestClient(app), st
    set_store(None)
    memoria_loader._facade = None
    st.close()


def test_graph_search_and_load_only_return_the_requested_scope(client):
    c, st = client
    mem = memoria_loader._memory()
    for scope in (A, B, HIJA, RARO):
        mem.save(scope, "turno-1", {"pregunta": "secreto de " + scope})
        mem.save(scope, "archivo:notas.txt", {"nombre": "notas.txt"})
    st.record_turn(conv_id="turno-conv", owner="o", provider="p", model="turno-model", agent_id=None, doc_ids=[])  # nodos ajenos con 'turno' en la etiqueta
    for scope in (A, B, HIJA, RARO):
        r = c.get("/memoria/search", params={"scope": scope, "query": "turno", "k": 50}).json()["results"]
        assert [n["id"] for n in r["graph"]] == ["memory:%s:turno-1" % scope]
        assert all(x["scope"] == scope for x in r["sqlite"])
        g = mem.graph.load(scope, "archivo:notas.txt")
        assert [n["id"] for n in g] == ["memory:%s:archivo:notas.txt" % scope]
    assert c.get("/memoria/search", params={"scope": "chat-ui:chat:web-%", "query": "", "k": 50}).json()["results"]["graph"] == []
    assert len(c.get("/memoria/search", params={"scope": A, "query": "", "k": 1}).json()["results"]["graph"]) == 1


def test_shared_sqlite_connection_is_thread_safe(client):
    """chat_async y los nodos del orquestador escriben a la vez por la MISMA conexion: sin candado daba
    sqlite3.InterfaceError 'bad parameter or other API misuse'."""
    import threading

    c, _ = client
    mem = memoria_loader._memory()
    errors: list[str] = []

    def worker(i: int) -> None:
        try:
            for j in range(150):
                scope = "chat-ui:chat:web-%016d" % i
                mem.sqlite.save(scope, "turno-%d" % j, {"pregunta": "p%d" % j, "respuesta": "r"})
                mem.sqlite.search(scope, "turno-", 5)
                mem.sqlite.load(scope, "turno-%d" % j)
                memoria_loader.list_children("web-%016d" % i)
        except Exception as exc:  # noqa: BLE001
            errors.append("%s: %s" % (type(exc).__name__, exc))

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(120)
    assert errors == []
    assert mem.sqlite.health()["records"] == 8 * 150
