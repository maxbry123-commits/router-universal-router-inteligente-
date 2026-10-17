"""Tests del watchdog: detecta, repara (sync de fichas, rearranque de autosync, sync manual, reiniciar agente) y avisa solo en cambios."""
import time

import pytest

from plugins.watchdog import plugin as W


class FakeHost:
    def __init__(self):
        self.plugins = {"puente_chat": "ok", "fichas_qwen": "ok", "secretos": "ok", "agentes_orq": "ok", "otro": "ok"}
        self.syncs = 0
        self.arreglar_en_sync = set()
        self.reinicios = []

    def list_plugins(self):
        return [{"id": k, "status": "ready" if v == "ok" else "degraded"} for k, v in self.plugins.items()]

    def get(self, pid):
        if pid not in self.plugins:
            return None
        return {"id": pid, "status": "ready" if self.plugins[pid] == "ok" else "degraded", "last_error": None if self.plugins[pid] == "ok" else "boom"}

    def health(self, pid):
        return {"status": "ok"} if self.plugins[pid] == "ok" else {"status": "degraded", "reason": "boom"}

    def sync(self):
        self.syncs += 1
        for p in self.arreglar_en_sync:
            self.plugins[p] = "ok"
        return {}

    def call(self, pid, action, payload=None, timeout_s=None):
        if pid == "puente_chat" and action == "modelos":
            return {"status": "ok", "result": {"modelos": [{"id": "m1"}]}}
        if action == "reiniciar":
            self.reinicios.append(pid)
            self.plugins[pid] = "ok"
            return {"status": "ok", "result": {}}
        return {"status": "degraded", "reason": "accion no permitida por la ficha"}


@pytest.fixture()
def deps():
    host = FakeHost()
    salud = {"ok": True}
    st = {"vivo": True, "last_sync": time.time(), "last_error": None, "reinicios": 0, "syncs": 0}

    def storage():
        def reiniciar():
            st["reinicios"] += 1
            st["vivo"] = True

        def sync():
            st["syncs"] += 1
            st["last_sync"], st["last_error"] = time.time(), None
        return {"status": {"last_sync": st["last_sync"], "last_error": st["last_error"]}, "vivo": st["vivo"], "configurado": True,
                "reiniciar": reiniciar, "sync": sync, "cada_s": 60.0}

    guardadas = []

    W.set_deps(host=host, health=lambda: (salud["ok"], "HTTP 200" if salud["ok"] else "URLError"),
               mem=lambda k, d: guardadas.append((k, d)), storage=storage)  # storage: se evalua en cada ronda
    yield host, salud, st, guardadas
    W.detener()
    W.set_deps()


def test_todo_bien_sin_avisos(deps):
    r = W.revisar()
    assert r["ok"] and r["caidos"] == []
    assert W.handle("alertas", {})["alertas"] == []


def test_health_cae_y_se_recupera_avisos_sin_repetir(deps):
    host, salud, st, guardadas = deps
    salud["ok"] = False
    W.revisar(); W.revisar()
    al = W.handle("alertas", {})["alertas"]
    assert len(al) == 1 and al[0]["nivel"] == "error" and "health" in al[0]["mensaje"]
    salud["ok"] = True
    W.revisar()
    al = W.handle("alertas", {})["alertas"]
    assert len(al) == 2 and al[1]["nivel"] == "ok" and "recuperado" in al[1]["mensaje"]
    assert len(guardadas) == 2  # tambien quedan en la memoria SQLite
    assert W.handle("alertas", {"desde": al[0]["ts"]})["alertas"] == [al[1]]


def test_ficha_degradada_se_repara_con_sync(deps):
    host, *_ = deps
    host.plugins["fichas_qwen"] = "mal"
    host.arreglar_en_sync = {"fichas_qwen"}
    r = W.revisar()
    assert host.syncs == 1 and "ficha:fichas_qwen" not in r["caidos"]
    assert any("reparado" in a["mensaje"] for a in W.handle("alertas", {})["alertas"])


def test_ficha_que_no_se_repara_queda_caida(deps):
    host, *_ = deps
    host.plugins["secretos"] = "mal"
    r = W.revisar()
    assert "ficha:secretos" in r["caidos"]


def test_memoria_hilo_muerto_y_sync_viejo(deps):
    host, salud, st, _ = deps
    st["vivo"] = False
    st["last_sync"] = time.time() - 1000
    r = W.revisar()
    assert st["reinicios"] == 1 and st["syncs"] == 1
    assert "memoria:sync" not in r["caidos"]
    assert any("autosync rearrancado" in (a.get("accion") or "") for a in W.handle("alertas", {})["alertas"])


def test_agente_caido_se_reinicia(deps):
    host, *_ = deps
    host.plugins["agentes_orq"] = "mal"
    W.revisar()
    assert host.reinicios == ["agentes_orq"]
    assert W._estado["agente:agentes_orq"]["ok"]


def test_hilo_arranca_y_para(deps):
    r = W.handle("arrancar", {"cada_s": 10})
    assert r["ok"] and W.handle("status", {})["hilo"]
    assert W.handle("arrancar", {})["ya_corria"]
    W.handle("detener", {})
    assert W.handle("accion-x", {})["error"] == "ACCION_DESCONOCIDA"
