"""Pruebas de los umbrales de autoescalado I3 (sin Job HF real)."""
from __future__ import annotations

import time
from typing import Any

import cola


class LanzadorFalso:
    def __init__(self) -> None:
        self.n = 0

    def lanzar(self, clase: str) -> cola.Worker:
        self.n += 1
        ahora = time.time()
        return cola.Worker(id=f"falso-{self.n}", clase=clase, pid=None,
                           arrancado=ahora, ultima_tarea=ahora)

    def apagar(self, worker: cola.Worker) -> None:
        self.n -= 1


def _limpiar() -> None:
    for p in (cola.TAREAS, cola.WORKERS):
        if p.exists():
            p.unlink()


def _vigilar(**kw: Any) -> dict[str, Any]:
    return cola.vigilar(LanzadorFalso(), **kw)


def test_no_escala_sin_tareas() -> None:
    _limpiar()
    r = _vigilar(metricas={"cpu": 0.99, "ram": 0.99})
    assert r["encendidos"] == []


def test_16gb_escala_al_80() -> None:
    _limpiar()
    cola.encolar("t", "16gb")
    assert _vigilar(metricas={"cpu": 0.79, "ram": 0.10})["encendidos"] == []
    assert len(_vigilar(metricas={"cpu": 0.81, "ram": 0.10})["encendidos"]) == 1


def test_32gb_escala_al_85_y_tiene_prioridad() -> None:
    _limpiar()
    cola.encolar("t", "32gb")
    assert _vigilar(metricas={"cpu": 0.84, "ram": 0.10})["encendidos"] == []
    r = _vigilar(metricas={"cpu": 0.86, "ram": 0.10})
    assert len(r["encendidos"]) == 1
    assert cola.registro()[0].clase == "32gb"


def test_topes_3_y_10() -> None:
    _limpiar()
    for _ in range(20):
        cola.encolar("t", "16gb")
    for _ in range(5):
        _vigilar(metricas={"cpu": 0.95, "ram": 0.10})
    assert len(cola.registro()) == cola.TOPE_16

    _limpiar()
    for _ in range(20):
        cola.encolar("t", "32gb")
    for _ in range(15):
        _vigilar(metricas={"cpu": 0.95, "ram": 0.10})
    assert len(cola.registro()) == cola.TOPE_32


def test_apaga_tras_15_minutos_sin_tareas() -> None:
    _limpiar()
    cola.encolar("t", "16gb")
    _vigilar(metricas={"cpu": 0.95, "ram": 0.10})
    assert len(cola.registro()) == 1
    r = _vigilar(ahora=time.time() + cola.INACTIVIDAD_S + 1, metricas={"cpu": 0.10, "ram": 0.10})
    assert len(r["apagados"]) == 1
    assert cola.registro() == []
    _limpiar()
