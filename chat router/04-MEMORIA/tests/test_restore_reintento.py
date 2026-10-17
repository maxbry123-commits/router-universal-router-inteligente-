"""Red caida al arrancar -> escrituras locales -> vuelve la red: reintento con backoff, FUSION sin perder ni duplicar,
respaldo aparte en backups/pendiente-* mientras esta bloqueado, y la base principal del bucket nunca se pisa antes.
Sin red real: python -m pytest test_restore_reintento.py"""
import importlib.util, os, sqlite3, sys, tempfile, threading, time
from pathlib import Path

HERE = Path(__file__).resolve()
REPO = HERE.parents[3]


def _load(name, rel):
    p = REPO / rel
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m; spec.loader.exec_module(m); return m


sl = _load("sl_reintento", "router inteligente universal/integration/chat_mvp/storage_lifecycle.py")
st = _load("st_reintento", "router inteligente universal/integration/chat_mvp/store.py")
B = "buckets/B/riu-chat"


def _remota():
    d = tempfile.mkdtemp(); s = st.Store(d)
    cid = s.new_conversation("vieja", None, "antonio")
    for i in range(5):
        s._exec("INSERT INTO messages(conv_id,role,content,provider,model,created_at) VALUES(?,?,?,?,?,?)", (cid, "user", f"remoto {i}", "p", "m", 1000 + i))
    s._exec("CREATE TABLE IF NOT EXISTS memoria_yaiwes (id INTEGER PRIMARY KEY AUTOINCREMENT, scope TEXT NOT NULL, key TEXT NOT NULL, data TEXT NOT NULL, created_at REAL NOT NULL)")
    for i in range(3):
        s._exec("INSERT INTO memoria_yaiwes(scope,key,data,created_at) VALUES(?,?,?,?)", ("s", f"k{i}", "{}", 2000 + i))
    s._exec("UPDATE agents SET system_prompt='personalizado' WHERE id='orquestador-g0'")
    s.graph_node("memory:s:k0", "memory", "k0", data="v-bucket")
    snap = s.snapshot(Path(d) / "snap.sqlite3").read_bytes(); s.close(); return snap, cid


class FS:
    def __init__(self, files): self.f, self.red, self.writes, self.lock = files, False, [], threading.Lock()
    def __call__(self, token=None): return self
    def _chk(self):
        if not self.red: raise ConnectionError("red caida")
    def cat_file(self, p):
        self._chk()
        if p not in self.f: raise FileNotFoundError(p)
        return self.f[p]
    def ls(self, p, detail=False):
        self._chk(); ks = [k for k in self.f if k.startswith(p + "/")]
        if not ks: raise FileNotFoundError(p)
        return ks
    def pipe_file(self, p, data):
        with self.lock:
            self.writes.append((p, self.red))
            if "/backups/pendiente-" not in p: self._chk()  # el respaldo aparte se prueba aunque la lectura falle
            self.f[p] = data


def _cuenta(blob, sql):
    t = tempfile.mktemp(); open(t, "wb").write(blob); c = sqlite3.connect(t); r = c.execute(sql).fetchall(); c.close(); return r


def _sync(fs):
    def f(store, bucket, token):
        with tempfile.TemporaryDirectory() as t:
            fs.pipe_file(f"buckets/{bucket}/riu-chat/riu_chat.sqlite3", store.snapshot(Path(t) / "s.sqlite3").read_bytes())
    return f


def test_red_caida_escrituras_vuelve_red_fusiona_sin_perder():
    snap, cid = _remota()
    fs = FS({f"{B}/riu_chat.sqlite3": snap})
    os.environ["RIU_RESTORE_RETRY_SECONDS"] = "0.2"; os.environ["RIU_PENDIENTE_SECONDS"] = "0.1"
    try:
        d = tempfile.mkdtemp()
        r = sl.restore_if_empty(d, "B", "t", fs)  # 1) arranque con la red caida
        assert r["status"].startswith("NO_REMOTE_SNAPSHOT:ConnectionError") and sl._restore_bloquea_sync()
        store = st.Store(d)  # base local vacia (como en el Space)
        mem = sqlite3.connect(str(store.db_path), timeout=5)  # memoria_yaiwes usa su propia conexion
        mem.execute("CREATE TABLE IF NOT EXISTS memoria_yaiwes (id INTEGER PRIMARY KEY AUTOINCREMENT, scope TEXT NOT NULL, key TEXT NOT NULL, data TEXT NOT NULL, created_at REAL NOT NULL)")
        sl._thread = None
        h = sl.start_autosync(lambda: store, _sync(fs), "B", "t", 0.05, fs_factory=fs)
        # 2) escrituras durante el bloqueo
        cl = store.new_conversation("nueva", None, "antonio")
        for i in range(4):
            store._exec("INSERT INTO messages(conv_id,role,content,provider,model,created_at) VALUES(?,?,?,?,?,?)", (cl, "user", f"local {i}", "p", "m", 5000 + i))
            mem.execute("INSERT INTO memoria_yaiwes(scope,key,data,created_at) VALUES(?,?,?,?)", ("s", f"local{i}", "{}", 6000 + i)); mem.commit()
        store.graph_node("memory:s:k0", "memory", "k0", data="v-local")
        time.sleep(0.8)
        assert sl._restore_bloquea_sync() and sl.STATUS["restore_intentos"] >= 1
        assert not any(p.endswith("riu-chat/riu_chat.sqlite3") for p, _ in fs.writes), "pisó la base principal estando bloqueado"
        pend = [p for p in fs.f if "/backups/pendiente-" in p]
        assert pend and all(p.startswith("buckets/B/backups/pendiente-") for p in pend)
        assert len(_cuenta(fs.f[pend[0]], "SELECT id FROM messages")) == 4  # el respaldo aparte ya trae lo local
        # 3) vuelve la red
        fs.red = True
        for _ in range(60):
            time.sleep(0.1)
            if sl.STATUS["restore"] == "RESTORED_MERGED" and any(p.endswith("riu-chat/riu_chat.sqlite3") for p, _ in fs.writes): break
        h["stop"].set()
        assert sl.STATUS["restore"] == "RESTORED_MERGED", sl.STATUS
        final = fs.f[f"{B}/riu_chat.sqlite3"]
        msgs = _cuenta(final, "SELECT id, content FROM messages ORDER BY id")
        assert msgs[:5] == [(i + 1, f"remoto {i}") for i in range(5)]  # ids del bucket intactos
        assert [m[1] for m in msgs[5:]] == [f"local {i}" for i in range(4)]  # lo local entra despues, sin duplicar
        mems = [r[0] for r in _cuenta(final, "SELECT key FROM memoria_yaiwes ORDER BY id")]
        assert mems == ["k0", "k1", "k2"] + [f"local{i}" for i in range(4)]
        convs = {r[0] for r in _cuenta(final, "SELECT id FROM conversations")}
        assert {cid, cl} <= convs
        assert _cuenta(final, "SELECT system_prompt FROM agents WHERE id='orquestador-g0'") == [("personalizado",)]  # no pisa el bucket
        conf = _cuenta(final, "SELECT tabla, fila FROM fusion_conflictos")
        assert any(t == "graph_nodes" and "v-local" in f for t, f in conf)  # la version local distinta no se pierde
        assert any(t == "agents" for t, _ in conf)
        # memoria_yaiwes sigue escribiendo despues de la fusion por su propia conexion
        mem.execute("INSERT INTO memoria_yaiwes(scope,key,data,created_at) VALUES('s','post','{}',7000)"); mem.commit()
        assert store._all("SELECT max(id) m FROM memoria_yaiwes")[0]["m"] == 8
        mem.close(); store.close()
    finally:
        os.environ.pop("RIU_RESTORE_RETRY_SECONDS"); os.environ.pop("RIU_PENDIENTE_SECONDS")


def test_fusion_idempotente():
    snap, _ = _remota()
    d = tempfile.mkdtemp(); store = st.Store(d)
    store._exec("INSERT INTO messages(conv_id,role,content,provider,model,created_at) VALUES('c','user','x','p','m',1)")
    t = Path(d) / "r.sqlite3"; t.write_bytes(snap)
    sl.fusionar(store, t); n1 = store._all("SELECT count(*) n FROM messages")[0]["n"]
    sl.fusionar(store, t); n2 = store._all("SELECT count(*) n FROM messages")[0]["n"]
    assert n1 == n2 == 6
    store.close()


def test_primera_instalacion_no_bloquea():
    fs = FS({}); fs.red = True
    assert sl.restore_if_empty(tempfile.mkdtemp(), "B", "t", fs)["status"] == "NO_REMOTE_SNAPSHOT:FileNotFoundError"
    assert not sl._restore_bloquea_sync()
