"""/memoria/* con PIN (public_chat_app.ChatAccess): sin PIN = como antes; con PIN exige X-Memoria-Pin; el resto del chat no cambia."""
import importlib
import sys
import types
from pathlib import Path

import pytest
from fastapi import FastAPI, Header
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def cliente(monkeypatch):
    def hacer(env):
        for k in ("RIU_MEMORIA_PIN", "RIU_SECRETOS_PIN", "RIU_PUBLIC_CHAT_KEY"):
            monkeypatch.delenv(k, raising=False)
        for k, v in env.items():
            monkeypatch.setenv(k, v)
        interna = FastAPI()

        @interna.get("/memoria/health")
        def mh(x_api_key: str | None = Header(default=None, alias="X-API-Key")):
            return {"ok": True, "key": bool(x_api_key)}

        @interna.get("/chat/conversations")
        def conv():
            return {"ok": True}

        fake = types.ModuleType("integration.chat_mvp.app")
        fake.app = interna
        monkeypatch.setitem(sys.modules, "integration.chat_mvp.app", fake)
        monkeypatch.syspath_prepend(str(ROOT))
        sys.modules.pop("public_chat_app", None)
        mod = importlib.import_module("public_chat_app")
        return TestClient(mod.app)
    return hacer


def test_sin_pin_sigue_igual(cliente):
    c = cliente({"RIU_PUBLIC_CHAT_KEY": "k"})
    r = c.get("/memoria/health")
    assert r.status_code == 200 and r.json()["key"] is True


def test_con_pin_bloquea_sin_cabecera_o_mal(cliente):
    c = cliente({"RIU_PUBLIC_CHAT_KEY": "k", "RIU_MEMORIA_PIN": "4821"})
    r = c.get("/memoria/health")
    assert r.status_code == 401 and r.json()["detail"] == "MEMORIA_PIN_REQUERIDO"
    assert c.get("/memoria/health", headers={"X-Memoria-Pin": "0000"}).status_code == 401
    r = c.get("/memoria/health", headers={"X-Memoria-Pin": "4821"})
    assert r.status_code == 200 and r.json()["key"] is True


def test_reusa_pin_de_secretos(cliente):
    c = cliente({"RIU_SECRETOS_PIN": "9911"})
    assert c.get("/memoria/health").status_code == 401
    assert c.get("/memoria/health", headers={"X-Memoria-Pin": "9911"}).status_code == 200


def test_memoria_pin_tiene_prioridad(cliente):
    c = cliente({"RIU_SECRETOS_PIN": "9911", "RIU_MEMORIA_PIN": "1234"})
    assert c.get("/memoria/health", headers={"X-Memoria-Pin": "9911"}).status_code == 401
    assert c.get("/memoria/health", headers={"X-Memoria-Pin": "1234"}).status_code == 200


def test_otras_rutas_y_cors_no_cambian(cliente):
    c = cliente({"RIU_MEMORIA_PIN": "4821"})
    assert c.get("/chat/conversations").status_code == 200
    r = c.options("/memoria/health")
    assert r.status_code != 401
