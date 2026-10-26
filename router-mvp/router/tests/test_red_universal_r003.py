"""Contract tests for R-003 RedUniversal canonical REUSE."""
from __future__ import annotations

import asyncio
import importlib
import sys
from pathlib import Path

RED = Path(__file__).resolve().parents[1] / "red"
if str(RED) not in sys.path:
    sys.path.insert(0, str(RED))

red_mod = importlib.import_module("red_universal")
RedUniversal = red_mod.RedUniversal
Mensaje = red_mod.Mensaje


def contrato(artifact_id: str = "test.node") -> dict:
    dt = {"family": "json", "type": "object", "version": 1}
    return {
        "artifact_id": artifact_id,
        "estado": "testing",
        "ejecucion": {"kind": "code", "transport": "importlib"},
        "seguridad": {
            "sandbox": "process",
            "limites": {"timeout_ms": 100, "deadline_ms": 200},
        },
        "contrato": {
            "rol": "service",
            "consume": {"datatype": dt},
            "expone": {"datatype": dt},
        },
    }


class FakeConnector:
    def __init__(self, conector_id: str, responses: list[dict] | None = None):
        self.conector_id = conector_id
        self.responses = list(responses or [{"status": "DONE", "output": conector_id}])
        self.payloads: list[dict] = []

    async def enviar(self, payload: dict) -> dict:
        self.payloads.append(payload)
        if self.responses:
            return self.responses.pop(0)
        return {"status": "FAIL", "error": "agotado"}

    async def sondear(self) -> bool:
        return True


def test_conectar_sin_contrato_falla() -> None:
    red = RedUniversal()
    try:
        red.conectar("bad.node", FakeConnector("bad"), {})
    except ValueError as exc:
        assert "enchufe_rechazado" in str(exc)
    else:
        raise AssertionError("contrato invalido no fue rechazado")


def test_ruta_patron_fnmatch_y_task_id() -> None:
    red = RedUniversal()
    c = FakeConnector("a")
    red.conectar("dest.api.one", c, contrato())
    red.ruta("r1", "core.*", "dest.api.*", cuando="tarea.*")

    sin_id = asyncio.run(red.enviar(Mensaje("tarea.run", "core.orq", {})))
    assert sin_id == {"status": "FAIL", "error": "task_id_obligatorio"}

    out = asyncio.run(red.enviar(Mensaje("tarea.run", "core.orq", {"x": 1}, task_id="T1")))
    assert out["status"] == "DONE"
    assert out["via"] == "dest.api.one"
    assert c.payloads[0]["task_id"] == "T1"


def test_failover_primero() -> None:
    red = RedUniversal()
    a = FakeConnector("a", [{"status": "FAIL", "error": "uno"}])
    b = FakeConnector("b", [{"status": "DONE", "output": "dos"}])
    red.conectar("dest.a", a, contrato("test.a"))
    red.conectar("dest.b", b, contrato("test.b"))
    red.ruta("r1", "core", "dest.*")

    out = asyncio.run(red.enviar(Mensaje("x", "core", {}, task_id="T2")))
    assert out["status"] == "DONE"
    assert out["via"] == "dest.b"
    assert a.n if hasattr(a, "n") else len(a.payloads) == 1
    assert len(b.payloads) == 1


def test_nodo_enfermo_a_los_5() -> None:
    red = RedUniversal()
    c = FakeConnector("bad", [{"status": "FAIL", "error": "x"}] * 5)
    red.conectar("dest.bad", c, contrato("test.bad"))
    red.ruta("r1", "core", "dest.bad")
    for i in range(5):
        asyncio.run(red.enviar(Mensaje("x", "core", {}, task_id=f"T{i}")))
    assert red.nodos["dest.bad"].sano is False
    assert red.nodos["dest.bad"].fallos == 5


def test_broadcast_y_mapa() -> None:
    red = RedUniversal()
    red.conectar("dest.a", FakeConnector("a"), contrato("test.a"), nivel="abajo")
    red.conectar("dest.b", FakeConnector("b"), contrato("test.b"), nivel="arriba")
    red.ruta("r1", "core", "dest.*", cuando="evt.*")
    out = asyncio.run(red.enviar(Mensaje("evt.go", "core", {}, task_id="T3"), modo="todos"))
    assert out["status"] == "DONE"
    assert set(out["resultados"]) == {"dest.a", "dest.b"}
    mapa = red.mapa()
    assert mapa["nodos"]["dest.a"]["nivel"] == "abajo"
    assert mapa["nodos"]["dest.a"]["dt_in"] == "json.object.v1"
    assert mapa["rutas"] == ["core --[evt.*]--> dest.*"]
