"""PUNTO 4: archivos por chat (sesion) en la memoria SQLite, sincronizados al bucket. Sin red."""
from __future__ import annotations

import base64
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

A, B = "web-1111111111111111", "web-2222222222222222"


def b64(t: bytes) -> str:
    return base64.b64encode(t).decode()


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
    yield TestClient(app), st, app
    set_store(None)
    memoria_loader._facade = None
    st.close()


def test_upload_list_download_delete_scoped_to_chat(client):
    c, st, _ = client
    r = c.post("/chat/files/" + A, json={"nombre": "notas v2.txt", "tipo": "text/plain", "datos_b64": b64(b"hola A")})
    assert r.status_code == 200 and r.json()["ok"] and r.json()["bytes"] == 6
    fid = r.json()["file_id"]
    c.post("/chat/files/" + B, json={"nombre": "otro.txt", "datos_b64": b64(b"de B")})
    files = c.get("/chat/files/" + A).json()["files"]
    assert [(f["file_id"], f["nombre"], f["tipo"], f["bytes"]) for f in files] == [(fid, "notas v2.txt", "text/plain", 6)]
    d = c.get("/chat/files/%s/%d" % (A, fid))
    assert d.status_code == 200 and d.content == b"hola A"
    assert d.headers["content-disposition"].startswith("attachment;") and d.headers["x-content-type-options"] == "nosniff"
    bid = c.get("/chat/files/" + B).json()["files"][0]["file_id"]
    assert c.get("/chat/files/%s/%d" % (A, bid)).status_code == 404  # el archivo de B no se ve desde A
    assert c.delete("/chat/files/%s/%d" % (A, bid)).status_code == 404
    r = c.delete("/chat/files/%s/%d" % (A, fid))
    assert r.status_code == 200 and r.json() == {"deleted": fid, "nombre": "notas v2.txt", "versions": 1}
    assert c.get("/chat/files/" + A).json()["files"] == []
    assert len(c.get("/chat/files/" + B).json()["files"]) == 1
    assert st._all("SELECT COUNT(*) n FROM graph_nodes WHERE id LIKE ?", ("%notas v2.txt",))[0]["n"] == 0


def test_reupload_replaces_and_delete_removes_all_versions(client):
    c, _, _ = client
    c.post("/chat/files/" + A, json={"nombre": "a.txt", "datos_b64": b64(b"v1")})
    r2 = c.post("/chat/files/" + A, json={"nombre": "a.txt", "datos_b64": b64(b"v2")}).json()
    files = c.get("/chat/files/" + A).json()["files"]
    assert len(files) == 1 and files[0]["file_id"] == r2["file_id"]
    assert c.get("/chat/files/%s/%d" % (A, r2["file_id"])).content == b"v2"
    assert c.delete("/chat/files/%s/%d" % (A, r2["file_id"])).json()["versions"] == 2
    assert c.get("/chat/files/" + A).json()["files"] == []


@pytest.mark.parametrize("name", ["../etc/passwd", "a/b.txt", "a\\\\b", "..", "x..y", "", "a\\x00b", "n" * 121])
def test_bad_names_rejected(client, name):
    c, _, _ = client
    r = c.post("/chat/files/" + A, json={"nombre": name, "datos_b64": b64(b"x")})
    assert r.status_code == 422


def test_size_base64_sesion_and_auth(client, monkeypatch):
    c, _, app = client
    monkeypatch.setattr(memoria_loader, "FILE_MAX_B64", 8)
    assert c.post("/chat/files/" + A, json={"nombre": "big.bin", "datos_b64": b64(b"0123456789")}).status_code == 413
    assert c.post("/chat/files/" + A, json={"nombre": "x.bin", "datos_b64": "!!no!!"}).json()["detail"] == "BASE64_INVALIDO"
    assert c.get("/chat/files/bad%20sesion").status_code == 422
    assert c.get("/chat/files/" + A + "/abc").status_code == 422
    app.dependency_overrides.clear()
    assert c.get("/chat/files/" + A).status_code == 401


def test_html_never_served_inline(client):
    c, _, _ = client
    fid = c.post("/chat/files/" + A, json={"nombre": "x.html", "tipo": "text/html", "datos_b64": b64(b"<script>1</script>")}).json()["file_id"]
    r = c.get("/chat/files/%s/%d" % (A, fid))
    assert "attachment" in r.headers["content-disposition"]
    bad = c.post("/chat/files/" + A, json={"nombre": "y.bin", "tipo": "text/html; x=<", "datos_b64": b64(b"1")}).json()["file_id"]
    assert c.get("/chat/files/%s/%d" % (A, bad)).headers["content-type"].startswith("application/octet-stream")


def test_bridge_subir_same_record_and_exact_anchor(client):
    c, _, _ = client
    out = L.handle("subir", {"sesion": A, "nombre": "a.txt", "tipo": "text/plain", "datos_b64": b64(b"CONTENIDO-A")})
    assert out["ok"] and out["file_id"]
    L.handle("subir", {"sesion": A, "nombre": "a.txt.bak", "datos_b64": b64(b"CONTENIDO-BAK")})
    assert L.handle("subir", {"sesion": A, "nombre": "../x", "datos_b64": b64(b"1")}) == {"error": "NOMBRE_INVALIDO"}
    assert sorted(L.handle("archivos", {"sesion": A})["archivos"]) == ["a.txt", "a.txt.bak"]
    assert {f["nombre"] for f in c.get("/chat/files/" + A).json()["files"]} == {"a.txt", "a.txt.bak"}
    assert P._archivo_memoria(A, "a.txt") == "CONTENIDO-A"  # antes: LIKE devolvia el mas nuevo que contuviera 'archivo:a.txt'


def test_files_survive_job_switch(client, tmp_path):
    c, st, app = client
    fid = c.post("/chat/files/" + A, json={"nombre": "plan.md", "datos_b64": b64(b"# plan")}).json()["file_id"]
    FakeFS.files = {}
    sync_to_bucket(st, "ns/b", "tok", fs_factory=FakeFS)
    assert restore_from_bucket(tmp_path / "job2", "ns/b", "tok", fs_factory=FakeFS)["status"] == "RESTORED"
    set_store(None); memoria_loader._facade = None
    st2 = Store(tmp_path / "job2"); set_store(st2)
    try:
        assert c.get("/chat/files/%s/%d" % (A, fid)).content == b"# plan"
    finally:
        set_store(None); st2.close()
