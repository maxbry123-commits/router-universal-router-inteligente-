import asyncio
import os
import sys
from pathlib import Path

os.environ["SIMULADO"] = "1"
sys.path.insert(0, str(Path(__file__).parents[1]))

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from action_registry import ejecutar, comando_a_accion, acciones
from council import ask_council
from rewind import guardar, volver
from compact import compactar
from archify_cmd import archify, validar_mermaid
import work
from rutas import build_router

def test_action_registry_basico_y_comandos():
    assert ejecutar("watchdog.start", {})["running"] is True
    assert ejecutar("watchdog.stop", {})["running"] is False
    assert ejecutar("workflow.run", {"workflow": "x"})["status"] == "PASS"
    assert ejecutar("workflow.pause", {})["status"] == "PASS"
    assert ejecutar("workflow.resume", {})["status"] == "PASS"
    assert ejecutar("task.schedule", {"task_id": "T1"})["task"]["status"] == "SCHEDULED"
    assert ejecutar("task.cancel", {"task_id": "T1"})["task"]["status"] == "CANCELLED"
    assert ejecutar("pool.dispatch", {"task": "x"})["queued"] >= 1
    assert ejecutar("document.attach", {"document": "a.md"})["count"] >= 1
    assert ejecutar("command.execute", {"command": "echo"})["command"] == "echo"
    assert ejecutar("memory.search", {"query": "x"})["results"] == []
    assert ejecutar("browser.open", {"url": "https://example.com"})["status"] == "PASS"
    assert ejecutar("council.ask", {"pregunta": "q"})["status"] == "PASS"
    assert ejecutar("rewind", {"conv_id": "c"})["pasos"] == 1
    assert ejecutar("compact", {"historial": []})["status"] == "PASS"
    assert ejecutar("archify", {"texto": "x"})["status"] == "PASS"
    assert comando_a_accion("/council hola") == ("council.ask", {"pregunta": "hola"})
    assert "workflow.run" in acciones()
    with pytest.raises(KeyError):
        ejecutar("no.existe", {})

def test_council_paralelo():
    out = asyncio.run(ask_council("¿qué hacemos?", 3))
    assert out["status"] == "PASS"
    assert len(out["respuestas"]) == 3
    assert len(out["revisiones"]) == 3
    assert out["sintesis"]

def test_rewind_checkpoints():
    cid = "conv-test"
    guardar(cid, {"n": 1})
    guardar(cid, {"n": 2})
    guardar(cid, {"n": 3})
    assert volver(cid, 1) == {"n": 2}
    with pytest.raises(ValueError):
        volver(cid, 0)

def test_compact_y_archify():
    r = compactar([
        {"objetivo": "cerrar", "decisiones": ["A"], "archivos": ["x.py"], "estado": "RUNNING"},
        {"decisiones": ["B"], "archivos": ["x.py", "y.py"], "estado": "PASS", "siguiente_paso": "publicar"},
    ])
    assert r["objetivo"] == "cerrar"
    assert r["estado"] == "PASS"
    assert r["archivos"] == ["x.py", "y.py"]
    assert "parche_recuperacion" in r
    a = archify("hacer tarea")
    assert a["mermaid"].startswith("flowchart")
    assert validar_mermaid("graph LR\nA-->B").startswith("graph")
    with pytest.raises(ValueError):
        validar_mermaid("A-->B")

def test_work_estados():
    wid = "w-test"
    assert work.crear(wid)["status"] == "RUNNING"
    assert work.progreso(wid, 50)["progress"] == 50
    assert work.pausar(wid)["status"] == "PAUSED"
    assert work.reintentar(wid)["status"] == "RUNNING"
    assert work.cancelar(wid)["status"] == "CANCELLED"
    assert work.reintentar(wid)["status"] == "RUNNING"
    assert work.aprobar(wid)["status"] == "DONE"
    assert work.obtener(wid)["progress"] == 100

@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(build_router())
    return TestClient(app)

def test_rutas_acciones_council_compact_archify(client):
    assert client.post("/acciones/watchdog.start", json={"payload": {}}).status_code == 200
    c = client.post("/council", json={"pregunta": "q", "modelos": 2})
    assert c.status_code == 200 and len(c.json()["respuestas"]) == 2
    cp = client.post("/compact", json={"historial": [{"objetivo": "x"}]})
    assert cp.status_code == 200 and cp.json()["objetivo"] == "x"
    ar = client.post("/archify", json={"texto": "x"})
    assert ar.status_code == 200 and ar.json()["mermaid"].startswith("flowchart")

def test_rutas_rewind_y_work(client):
    assert client.post("/rewind", json={"conv_id": "api", "estado": {"n": 1}}).status_code == 200
    assert client.post("/rewind", json={"conv_id": "api", "estado": {"n": 2}}).status_code == 200
    rw = client.post("/rewind", json={"conv_id": "api", "pasos": 1})
    assert rw.status_code == 200 and rw.json()["estado"] == {"n": 1}
    cr = client.post("/work", json={"work_id": "api-w", "action": "create"})
    assert cr.status_code == 200 and cr.json()["status"] == "RUNNING"
    assert client.post("/work", json={"work_id": "api-w", "action": "pause"}).json()["status"] == "PAUSED"
    assert client.post("/work", json={"work_id": "api-w", "action": "progress", "progress": 100}).json()["status"] == "DONE"
    items = client.get("/work")
    assert items.status_code == 200 and any(x["id"] == "api-w" for x in items.json()["items"])
