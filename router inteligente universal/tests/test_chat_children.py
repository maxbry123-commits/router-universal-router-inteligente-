"""PUNTO 5: agente anclado que abre un chat HIJO (ficha + DAG + INPUT_BLOCK literal + memoria propia). Sin red."""
from __future__ import annotations

import hashlib
import sqlite3
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
from plugins.puente_chat import plugin as P  # noqa: E402
from plugins.puente_chat import plugin_long_context as L  # noqa: E402

PADRE = "web-0123456789abcdef"
# espacios al borde, CRLF, tab, unicode combinado, emoji, zero-width, comillas, backslashes, llaves y un falso cierre
INPUT_BLOCK = ("  INPUT_BLOCK Director 2026-10-08\r\n\tPaso 1: «no parafrasear» — café ñandú 🧩\u200b\r\n"
               "e\u0301 vs \u00e9; \"comillas\" 'simples' \\n literal \\\\ {json: [1,2]}\n```\nINPUT_BLOCK>>>\n   \n")
DAG = {"schema": "riu.dag/v1", "id": "plan-hijo",
       "nodes": [{"id": "n1", "route": {"group": "default"}, "instructions": "Resume el INPUT_BLOCK"},
                 {"id": "n2", "needs": ["n1"], "model": {"provider": "groq", "model": "qwen/qwen3-8b"}, "instructions": "Verifica"}]}


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


def _new(c, **kw):
    body = {"agente": "wf-codex", "dag": DAG, "input_block": INPUT_BLOCK, **kw}
    return c.post("/chat/children/" + PADRE, json=body)


def _seed_agent(st):
    st.upsert_agent("wf-codex", "Codex (Wordflow)", "auditor técnico", "Eres Codex, auditor.", ["groq/qwen/qwen3-8b"])


def test_input_block_is_byte_identical_everywhere(client, tmp_path, monkeypatch):
    c, st = client
    _seed_agent(st)
    r = _new(c)
    assert r.status_code == 200, r.text
    out = r.json()
    hija = out["sesion_hija"]
    assert hija == PADRE + ":ag:wf-codex:1" and out["padre"] == PADRE and out["n"] == 1
    want = INPUT_BLOCK.encode("utf-8")
    assert out["input_block_sha256"] == hashlib.sha256(want).hexdigest() and out["input_block_bytes"] == len(want)
    # 1) la ruta de lectura lo devuelve identico byte a byte
    got = c.get("/chat/child/" + hija).json()
    assert got["input_block"].encode("utf-8") == want and got["input_block_sha256"] == out["input_block_sha256"]
    # 2) el registro SQLite (el archivo que sube el autosync) guarda exactamente ese texto
    db = sqlite3.connect(str(st.db_path))
    import json
    raw = db.execute("SELECT data FROM memoria_yaiwes WHERE scope=? AND key='agente:input_block'", ("chat-ui:chat:" + hija,)).fetchone()[0]
    assert json.loads(raw)["input_block"].encode("utf-8") == want
    # 3) sobrevive al relevo de Job: snapshot al bucket -> Store nuevo restaurado
    FakeFS.files = {}
    sync_to_bucket(st, "ns/b", "t", fs_factory=FakeFS)
    st2_dir = tmp_path / "nuevo"
    restore_from_bucket(st2_dir, "ns/b", "t", fs_factory=FakeFS)
    st2 = Store(st2_dir)
    set_store(st2)
    memoria_loader._facade = None
    got2 = c.get("/chat/child/" + hija).json()
    assert got2["input_block"].encode("utf-8") == want and got2["dag"] == DAG and got2["ficha"]["id"] == "wf-codex"
    # 4) llega al modelo dentro del prompt de sistema sin parafrasear ni recortar
    ctx = memoria_loader.child_context(hija)
    assert ("<<<INPUT_BLOCK\n" + INPUT_BLOCK + "\nINPUT_BLOCK>>>") in ctx
    st2.close()


def test_first_records_are_ficha_dag_input_block_and_parent_link(client):
    c, st = client
    _seed_agent(st)
    hija = _new(c).json()["sesion_hija"]
    db = sqlite3.connect(str(st.db_path))
    keys = [r[0] for r in db.execute("SELECT key FROM memoria_yaiwes WHERE scope=? ORDER BY id", ("chat-ui:chat:" + hija,))]
    assert keys == ["agente:ficha", "agente:dag", "agente:input_block", "agente:padre"]
    got = c.get("/chat/child/" + hija).json()
    assert got["ficha"] == st.agent("wf-codex") and got["dag"] == DAG and got["padre"] == PADRE and got["agente"] == "wf-codex"
    assert got["history"] == {"sesion": hija, "scope": "chat-ui:chat:" + hija, "turns": 0, "messages": []}
    lst = c.get("/chat/children/" + PADRE).json()
    assert [(x["sesion_hija"], x["agente"], x["n"]) for x in lst["children"]] == [(hija, "wf-codex", 1)]


def test_memory_isolation_between_parent_and_child(client, monkeypatch):
    c, st = client
    _seed_agent(st)
    hija = _new(c).json()["sesion_hija"]
    assert L._guardar(PADRE, "groq-qwen-3-8", "dato-del-PADRE", "resp-padre")
    seen: list[list[dict]] = []

    def fake_api(proveedor, modelo, mensajes, max_tokens, tope, tools):
        seen.append([dict(m) for m in mensajes])
        return 200, {"choices": [{"message": {"role": "assistant", "content": "respuesta-del-HIJO"}}], "usage": {}}

    monkeypatch.setattr(P, "_llamar_api", fake_api)
    monkeypatch.setattr(P, "_sentinela", lambda: None)
    out = P.handle("chat", {"model": "groq-qwen-3-8", "sesion": hija, "messages": [{"role": "user", "content": "pregunta-del-HIJO"}]})
    assert out["choices"][0]["message"]["content"] == "respuesta-del-HIJO" and out["memoria_guardada"]
    system = seen[0][0]["content"]
    assert INPUT_BLOCK in system and "Eres Codex, auditor." in system and "plan-hijo" in system
    assert "dato-del-PADRE" not in system  # el hijo no ve la memoria del padre
    # el padre no ve la memoria del hijo (ni turnos ni ficha/DAG/INPUT_BLOCK)
    assert "HIJO" not in L._contexto(PADRE, "x") and "HIJO" not in P._contexto(PADRE, "x")
    assert memoria_loader.child_context(PADRE) == ""
    hp = c.get("/chat/history/" + PADRE).json()
    assert [m["content"] for m in hp["messages"]] == ["dato-del-PADRE", "resp-padre"]
    hh = c.get("/chat/child/" + hija).json()["history"]
    assert [m["content"] for m in hh["messages"]] == ["pregunta-del-HIJO", "respuesta-del-HIJO"]
    assert "PADRE" not in L._contexto(hija, "x")
    # una segunda vuelta del padre no recibe el bloque del agente
    seen.clear()
    P.handle("chat", {"model": "groq-qwen-3-8", "sesion": PADRE, "messages": [{"role": "user", "content": "otra"}]})
    assert "INPUT_BLOCK (literal del chat padre" not in seen[0][0]["content"] and "respuesta-del-HIJO" not in seen[0][0]["content"]
    # archivos: tampoco se cruzan
    import base64
    c.post("/chat/files/" + hija, json={"nombre": "h.txt", "datos_b64": base64.b64encode(b"h").decode()})
    assert c.get("/chat/files/" + PADRE).json()["files"] == []


def test_numbering_and_explicit_ficha(client):
    c, st = client
    _seed_agent(st)
    assert _new(c).json()["n"] == 1 and _new(c).json()["n"] == 2
    f = {"id": "agente-propio", "name": "Propio", "system_prompt": "Eres propio.", "extra": {"x": [1, "ñ"]}}
    r = c.post("/chat/children/" + PADRE, json={"ficha": f, "dag": DAG, "input_block": "IB"})
    assert r.status_code == 200 and r.json()["sesion_hija"] == PADRE + ":ag:agente-propio:1"
    assert c.get("/chat/child/" + r.json()["sesion_hija"]).json()["ficha"] == f
    assert [x["n"] for x in c.get("/chat/children/" + PADRE).json()["children"]] == [1, 2, 1]


@pytest.mark.parametrize("body,status,detail", [
    ({"agente": "no-existe"}, 404, "AGENTE_NO_EXISTE"),
    ({"agente": None}, 422, "AGENTE_O_FICHA"),
    ({"ficha": {"id": "wf-codex"}}, 422, "AGENTE_O_FICHA"),
    ({"agente": None, "ficha": {"id": "Mal Id"}}, 422, "FICHA_INVALIDA"),
    ({"input_block": "   "}, 422, "INPUT_BLOCK_VACIO"),
    ({"dag": {"schema": "riu.dag/v1", "nodes": []}}, 422, "DAG_INVALIDO"),
    ({"dag": {**DAG, "input_block": "otro"}}, 422, "DAG_INPUT_BLOCK_DISTINTO"),
])
def test_validation(client, body, status, detail):
    c, st = client
    _seed_agent(st)
    r = _new(c, **body)
    assert r.status_code == status and str(r.json()["detail"]).startswith(detail)
    assert c.get("/chat/children/" + PADRE).json()["children"] == []


def test_bad_sesions_and_missing_child(client):
    c, st = client
    st.upsert_agent("a" * 40, "largo", "x", "", [])
    r = c.post("/chat/children/" + PADRE, json={"agente": "a" * 40, "dag": DAG, "input_block": "IB"})
    assert r.status_code == 422 and r.json()["detail"] == "SESION_HIJA_MUY_LARGA"
    assert c.post("/chat/children/bad%20s", json={"agente": "x", "dag": DAG, "input_block": "IB"}).status_code == 422
    assert c.get("/chat/child/" + PADRE + ":ag:wf-codex:9").status_code == 404
    assert c.get("/chat/child/../x").status_code in (404, 422)


def test_routes_require_auth(client):
    c, st = client
    app = c.app
    app.dependency_overrides.clear()
    assert c.get("/chat/children/" + PADRE).status_code == 401
    assert c.get("/chat/child/" + PADRE + ":ag:wf-codex:1").status_code == 401
    assert _new(c).status_code == 401
