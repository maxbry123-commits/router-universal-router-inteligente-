"""Pruebas reales sin red ni descargas: python test_runtime_lifecycle.py
Ruta: busca runtime_adapters.py y storage_lifecycle.py por ruta relativa al repo o al directorio actual."""
import importlib.util, json, os, sqlite3, sys, tempfile, threading, time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

HERE = Path(__file__).resolve()
REPO = HERE.parents[3] if len(HERE.parents) > 3 else HERE.parent


def _find(name):
    for p in (REPO.rglob(name) if REPO.exists() else []):
        return p
    return Path(name)


def _load(name):
    spec = importlib.util.spec_from_file_location(name[:-3], _find(name))
    m = importlib.util.module_from_spec(spec); sys.modules[spec.name] = m; spec.loader.exec_module(m); return m


ra, sl = _load("runtime_adapters.py"), _load("storage_lifecycle.py")


class FakeFS:
    def __init__(self, files): self.f = files
    def __call__(self, token=None): return self
    def cat_file(self, p):
        if p not in self.f: raise FileNotFoundError(p)
        return self.f[p]
    def ls(self, p, detail=False): return [k for k in self.f if k.startswith(p + "/")]


def _db_bytes():
    d = tempfile.mkdtemp(); p = Path(d) / "x.sqlite3"
    c = sqlite3.connect(p); c.execute("create table t(a)"); c.execute("insert into t values('hola')"); c.commit(); c.close()
    return p.read_bytes()


def test_restore_arranque_vacio():
    d = Path(tempfile.mkdtemp()); b = "buckets/B/riu-chat"
    fs = FakeFS({f"{b}/riu_chat.sqlite3": _db_bytes(), f"{b}/docs/d1": b"doc"})
    r = sl.restore_if_empty(d, "B", "tok", fs)
    assert r["status"] == "RESTORED" and r["docs"] == 1, r
    assert sqlite3.connect(d / "riu_chat.sqlite3").execute("select a from t").fetchone()[0] == "hola"
    assert (d / "docs" / "d1").read_bytes() == b"doc"


def test_no_pisa_base_local():
    d = Path(tempfile.mkdtemp()); (d / "riu_chat.sqlite3").write_bytes(b"local")
    assert sl.restore_if_empty(d, "B", "tok", FakeFS({}))["status"] == "SKIPPED_LOCAL_EXISTS"
    assert (d / "riu_chat.sqlite3").read_bytes() == b"local"


def test_snapshot_corrupto_se_rechaza():
    d = Path(tempfile.mkdtemp()); b = "buckets/B/riu-chat"
    r = sl.restore_if_empty(d, "B", "tok", FakeFS({f"{b}/riu_chat.sqlite3": b"basura" * 50}))
    assert r["status"] == "REMOTE_SNAPSHOT_CORRUPT" and not (d / "riu_chat.sqlite3").exists()


def test_sin_config_o_sin_remoto():
    d = Path(tempfile.mkdtemp())
    assert sl.restore_if_empty(d, None, None)["status"] == "SKIPPED_NOT_CONFIGURED"
    assert sl.restore_if_empty(d, "B", "t", FakeFS({}))["status"].startswith("NO_REMOTE_SNAPSHOT")


def test_autosync_periodico():
    calls = []
    r = sl.start_autosync(lambda: "store", lambda s, b, t: calls.append((s, b)), "B", "t", 0.05)
    time.sleep(0.4); r["stop"].set()
    assert len(calls) >= 2 and calls[0] == ("store", "B") and sl.STATUS["last_sync"]


def test_embedding_gap_especifico():
    os.environ.pop("RIU_EMBED_MODEL_DIR", None); ra.EmbeddingAdapter.reset()
    h = ra.EmbeddingAdapter().health()
    assert h["status"] == "GAP_EMBEDDING_MODEL_NOT_AVAILABLE" and h["semantic"] is False


def test_graphiti_nunca_connected_sin_dependencias():
    os.environ.pop("RIU_GRAPHITI_ENABLE", None)
    g = ra.GraphitiAdapter(); assert g.health()["status"] == "GAP_DISABLED" and not g._endpoint()
    os.environ["RIU_GRAPHITI_ENABLE"] = "1"
    try:
        s = g.health()["status"]
        assert s.startswith("GAP_") and s != "GAP_DISABLED", s
    finally:
        os.environ.pop("RIU_GRAPHITI_ENABLE")


def test_graphify_busca_en_graph_json():
    root = Path(tempfile.mkdtemp()); (root / "graphify-out").mkdir()
    (root / "graphify-out" / "graph.json").write_text(json.dumps({"nodes": [{"id": "a", "label": "gov_prepare"}, {"id": "b", "label": "otra"}]}))
    os.environ["RIU_GRAPHIFY_ROOT"] = str(root)
    try:
        g = ra.GraphifyCodeAdapter()
        assert g.health()["status"] == "CONNECTED"
        assert [r["node"] for r in g.search("s", "gov_prepare")] == ["a"]
        assert g.save("s", "k", {})["status"] == "SKIPPED"
    finally:
        os.environ.pop("RIU_GRAPHIFY_ROOT")
    assert ra.GraphifyCodeAdapter().health()["status"] == "GAP_DISABLED"


def test_memanto_contra_servicio_falso_y_caido():
    seen = []
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0)); body = json.loads(self.rfile.read(n) or b"{}")
            seen.append((self.path, self.headers.get("X-Session-Token")))
            out = {"session_token": "T1"} if self.path.endswith("/activate") else ({"memories": [{"content": "s1 dato"}]} if self.path.endswith("/recall") else {})
            raw = json.dumps(out).encode(); self.send_response(200); self.send_header("Content-Length", str(len(raw))); self.end_headers(); self.wfile.write(raw)
    srv = HTTPServer(("127.0.0.1", 0), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
    os.environ["RIU_MEMANTO_URL"] = f"http://127.0.0.1:{srv.server_port}"
    try:
        m = ra.MemantoAdapter(); assert m.health()["status"] == "CONNECTED"
        assert m.save("s1", "k", {"a": 1})["status"] == "SAVED"
        assert m.search("s1", "dato")[0]["text"] == "s1 dato"
        assert m.search("otro-scope", "dato") == []
        assert any(tok == "T1" for p, tok in seen if p.endswith("/remember"))
    finally:
        srv.shutdown(); os.environ["RIU_MEMANTO_URL"] = "http://127.0.0.1:1"
    try:
        assert ra.MemantoAdapter().health()["status"].startswith("GAP_SERVICE_UNREACHABLE")
    finally:
        os.environ.pop("RIU_MEMANTO_URL")


if __name__ == "__main__":
    n = 0
    for k, v in sorted(globals().items()):
        if k.startswith("test_"):
            v(); n += 1; print("PASS", k)
    print(n, "tests OK")
