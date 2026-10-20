"""Tests de los 4 puentes (mocks, sin red, sin gasto)."""
import base64
import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
IDS = ["hf_storage", "hf_datasets", "hf_skills", "hf_compute"]


def load(pid):
    spec = importlib.util.spec_from_file_location("t_" + pid, ROOT / "plugins" / pid / "plugin.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def mock(m, status=200, body=b"{}"):
    calls = []

    def fake(method, url, headers=None, data=None, timeout=30):
        calls.append((method, url, headers or {}, data))
        return status, (body if isinstance(body, bytes) else json.dumps(body).encode())
    m._http = fake
    return calls


@pytest.mark.parametrize("pid", IDS)
def test_ficha_y_estructura(pid, monkeypatch):
    f = json.loads((ROOT / "plugins" / pid / "ficha.json").read_text(encoding="utf-8"))
    assert f["plugin_host"]["enabled_default"] is False
    assert f["ejecucion"]["entry_point"] == "plugins.%s.plugin:handle" % pid
    assert f["plugin_host"]["health_action"] in f["ejecucion"]["allowed_actions"]
    m = load(pid)
    mock(m)
    assert m.handle("status", {})["status"] == "ok"
    assert m.handle("nope", {})["status"] == "error"


@pytest.mark.parametrize("pid", IDS)
def test_ficha_valida_contra_host(pid):
    try:
        from integration.plugin_host.host import check_v1
    except Exception as exc:
        pytest.skip("host no importable: %s" % exc)
    f = json.loads((ROOT / "plugins" / pid / "ficha.json").read_text(encoding="utf-8"))
    assert check_v1(f, pid) == []


def test_no_hay_tokens_en_codigo():
    for pid in IDS:
        for fn in ("plugin.py", "ficha.json"):
            txt = (ROOT / "plugins" / pid / fn).read_text(encoding="utf-8")
            assert "ghp_" not in txt and "hf_" + "GP" not in txt and "hf_" + "mF" not in txt


def test_storage_list_read_write(monkeypatch):
    m = load("hf_storage")
    monkeypatch.setenv("HF_TOKEN", "tok-fake")
    calls = mock(m, 200, [{"path": "a.txt", "type": "file", "size": 3}])
    r = m.handle("list", {})
    assert r["entries"][0]["path"] == "a.txt" and calls[0][1].endswith("/api/datasets/COMAND-CENTER-1/yaiwes-hf-memoria/tree/main")
    assert calls[0][2]["Authorization"] == "Bearer tok-fake"
    mock(m, 200, b"hola")
    assert m.handle("read", {"path": "a.txt"})["content"] == "hola"
    calls = mock(m, 200, {"commitOid": "x"})
    r = m.handle("write", {"path": "d/b.txt", "content": "hey"})
    assert r["status"] == "ok" and calls[0][0] == "POST" and calls[0][1].endswith("/commit/main")
    lines = calls[0][3].decode().strip().split("\n")
    assert base64.b64decode(json.loads(lines[1])["value"]["content"]) == b"hey"


def test_storage_seguridad(monkeypatch, tmp_path):
    m = load("hf_storage")
    monkeypatch.delenv("HF_TOKEN", raising=False)
    calls = mock(m)
    assert m.handle("write", {"path": "x", "content": "1"})["error"] == "HF_TOKEN ausente" and not calls
    monkeypatch.setenv("HF_TOKEN", "t")
    assert m.handle("read", {"path": "../etc/passwd"})["status"] == "error"
    monkeypatch.setenv("HF_STORAGE_REPO", "mal repo")
    assert m.handle("list", {})["status"] == "error"
    monkeypatch.delenv("HF_STORAGE_REPO")
    db = tmp_path / "m.db"
    db.write_bytes(b"SQLITE")
    mock(m, 200, {})
    assert m.handle("backup_sqlite", {"db_path": str(db)})["path"] == "sqlite/memoria_yaiwes.db"
    mock(m, 500, b"boom")
    assert m.handle("write", {"path": "x", "content": "1"})["status"] == "error"


def test_datasets():
    m = load("hf_datasets")
    calls = mock(m, 200, {"rows": []})
    assert m.handle("rows", {"dataset": "HuggingFaceH4/ultrachat_200k", "length": 999})["status"] == "ok"
    assert "datasets-server.huggingface.co/rows" in calls[0][1] and "length=100" in calls[0][1]
    m.handle("search", {"query": "chat"})
    assert "api/datasets?search=chat" in calls[1][1]
    m.handle("repo_tree", {})
    assert "COMAND-CENTER-1/yaiwes-hf-memoria/tree/main" in calls[2][1]
    assert m.handle("info", {"dataset": "a b"})["status"] == "error"
    assert m.handle("status", {})["stores_data"] is False
    assert all(c[0] == "GET" for c in calls)


def test_skills():
    m = load("hf_skills")
    calls = mock(m, 200, [{"name": "hf-cli", "type": "dir", "path": "hf-cli", "size": 0}])
    r = m.handle("list", {})
    assert r["entries"][0]["name"] == "hf-cli" and "repos/huggingface/skills/contents/" in calls[0][1] and m.PINNED_COMMIT in calls[0][1]
    mock(m, 200, b"# skill")
    assert m.handle("read", {"path": "hf-cli/SKILL.md"})["content"] == "# skill"
    assert m.handle("read", {"path": "../x"})["status"] == "error"
    assert m.handle("write", {})["status"] == "error"
    assert "hf-cli" in m.handle("registry", {})["skills"]


class FakePool:
    def __init__(self, cpu, ram, workers):
        self.s = {"cpu_percent": cpu, "ram_percent": ram, "workers": workers}
        self.launched = []

    def status(self):
        return self.s

    def launch(self, flavor, reason):
        self.launched.append((flavor, reason))
        return types.SimpleNamespace(public=lambda: {"flavor": flavor})

    async def invoke(self, payload):
        return {"status": "ok", "echo": payload}


def install_pool(monkeypatch, pool):
    mod = types.ModuleType("integration.hf_worker_pool")
    mod.POOL = pool
    monkeypatch.setitem(sys.modules, "integration.hf_worker_pool", mod)
    if "integration" not in sys.modules:
        monkeypatch.setitem(sys.modules, "integration", types.ModuleType("integration"))


def test_compute_plan_por_tramos():
    m = load("hf_compute")
    cfg = m.load_config()
    assert cfg["umbral_pct"] == 80 and [t["ram_gb"] for t in cfg["tramos"]] == [16, 16, 32]
    b, u = {"flavor": "cpu-basic"}, {"flavor": "cpu-upgrade"}
    assert m.plan(cfg, 79, 10, [])["launch"] is None
    assert m.plan(cfg, 80, 10, [])["launch"] == "cpu-basic"
    assert m.plan(cfg, 10, 91, [b])["launch"] == "cpu-upgrade"
    assert m.plan(cfg, 95, 95, [b, u])["decision"] == "tope_alcanzado"
    assert m.plan(cfg, None, None, [])["decision"] == "sin_metricas"


def test_compute_ensure_dry_run_y_apply(monkeypatch):
    m = load("hf_compute")
    pool = FakePool(90, 10, [])
    install_pool(monkeypatch, pool)
    r = m.handle("ensure", {})
    assert r["dry_run"] is True and not pool.launched
    r = m.handle("ensure", {"apply": True})
    assert r["applied"] is True and pool.launched[0][0] == "cpu-basic"
    r = m.handle("invoke", {"body": {"q": 1}})
    assert r["result"]["echo"] == {"q": 1}


def test_compute_status_publica_workers_y_usuarios(monkeypatch):
    m = load("hf_compute")
    install_pool(monkeypatch, FakePool(5, 5, [{"flavor": "cpu-basic", "job_id": "j1"}]))
    monkeypatch.setenv("RIU_HERMES_URL", "http://hermes.test")
    monkeypatch.delenv("RIU_OPENCLAW_URL", raising=False)
    calls = mock(m, 200, b"ok")
    r = m.handle("status", {})
    assert r["workers_activos"][0]["job_id"] == "j1" and r["pool_disponible"] is True
    us = {u["id"]: u for u in r["usuarios"]}
    assert set(us) == {"vercel_chat", "hermes", "openclaw", "orquestador", "harness_deepseek"}
    assert us["hermes"]["activo"] is True and us["openclaw"]["activo"] is None
    assert calls[0][1] == "http://hermes.test/health"


def test_compute_sin_pool(monkeypatch):
    m = load("hf_compute")
    monkeypatch.setitem(sys.modules, "integration.hf_worker_pool", None)
    assert m.handle("ensure", {})["status"] == "error"
    assert m.handle("status", {})["pool_disponible"] is False
