"""Recuperacion tras polling infinito, plazos y errores de herramientas.

Modulo aislado: no importa frontend, backend, Router, plugins ni tests.
Solo biblioteca estandar (enum, time, dataclasses, typing).
"""
from __future__ import annotations

import enum
import time
from dataclasses import dataclass, field
from typing import Callable, Optional


class EstadoRecuperacion(enum.Enum):
    PENDIENTE = "pendiente"
    REINTENTANDO = "reintentando"
    DETENIDO = "detenido"
    AGOTADO = "agotado"
    COMPLETADO = "completado"


class ErrorHerramienta(Exception):
    """Fallo controlado de una herramienta externa durante el sondeo."""

    def __init__(self, herramienta: str, detalle: str) -> None:
        super().__init__(f"{herramienta}: {detalle}")
        self.herramienta = herramienta
        self.detalle = detalle


@dataclass
class PoliticaPlazos:
    max_intentos: int = 3
    plazo_polling_s: float = 0.25
    plazo_total_s: float = 5.0
    backoff_base_s: float = 0.05
    backoff_max_s: float = 0.4

    def validar(self) -> None:
        if self.max_intentos < 1:
            raise ValueError("max_intentos debe ser >= 1")
        if self.plazo_total_s <= 0:
            raise ValueError("plazo_total_s debe ser > 0")

    def espera_intento(self, intento: int) -> float:
        if intento < 0:
            raise ValueError("intento no puede ser negativo")
        return min(self.backoff_base_s * (2 ** intento), self.backoff_max_s)


@dataclass
class ResultadoRecuperacion:
    estado: EstadoRecuperacion
    intentos: int
    errores: list = field(default_factory=list)
    origen: Optional[str] = None

    @property
    def recuperado(self) -> bool:
        return self.estado is EstadoRecuperacion.COMPLETADO and not self.errores

    def resumen(self) -> str:
        return f"{self.estado.value} intentos={self.intentos} errores={len(self.errores)}"


class GestorRecuperacion:
    """Corta el polling infinito, respeta plazos y aisla errores de herramientas."""

    def __init__(self, politica: Optional[PoliticaPlazos] = None,
                 reloj: Callable[[], float] = time.monotonic,
                 dormir: Callable[[float], None] = time.sleep) -> None:
        self.politica = politica or PoliticaPlazos()
        self.politica.validar()
        self.reloj = reloj
        self.dormir = dormir

    def _dentro_de_plazo(self, inicio: float) -> bool:
        return (self.reloj() - inicio) < self.politica.plazo_total_s

    def recuperar(self, sondeo: Callable[[], Optional[str]]) -> ResultadoRecuperacion:
        inicio = self.reloj()
        errores: list = []
        for intento in range(self.politica.max_intentos):
            if not self._dentro_de_plazo(inicio):
                return ResultadoRecuperacion(EstadoRecuperacion.AGOTADO, intento, errores, "plazo_total")
            try:
                dato = sondeo()
            except ErrorHerramienta as exc:
                errores.append(str(exc))
                self.dormir(self.politica.espera_intento(intento))
                continue
            except Exception as exc:  # defensa: nunca burbujea al hilo del chat
                errores.append(f"inesperado:{type(exc).__name__}")
                continue
            if dato is not None:
                return ResultadoRecuperacion(EstadoRecuperacion.COMPLETADO, intento + 1, errores, dato)
            self.dormir(self.politica.plazo_polling_s)
        return ResultadoRecuperacion(EstadoRecuperacion.AGOTADO, self.politica.max_intentos, errores, "max_intentos")

    def detener(self, resultado: ResultadoRecuperacion) -> ResultadoRecuperacion:
        if resultado.recuperado:
            raise ValueError("no se puede detener una recuperacion completada")
        resultado.estado = EstadoRecuperacion.DETENIDO
        return resultado


def _reloj_falso(pasos: float = 0.0) -> Callable[[], float]:
    t = [0.0]

    def leer() -> float:
        t[0] += pasos
        return t[0]

    return leer


def _gestor(max_intentos: int = 2, plazo_total: float = 5.0,
            reloj: Optional[Callable[[], float]] = None) -> GestorRecuperacion:
    politica = PoliticaPlazos(max_intentos=max_intentos, plazo_polling_s=0.0,
                              plazo_total_s=plazo_total, backoff_base_s=0.0,
                              backoff_max_s=0.0)
    return GestorRecuperacion(politica=politica, reloj=reloj or time.monotonic,
                              dormir=lambda _s: None)


def prueba_exito_primer_intento() -> None:
    res = _gestor().recuperar(lambda: "listo")
    assert res.estado is EstadoRecuperacion.COMPLETADO
    assert res.recuperado and res.intentos == 1 and res.errores == []


def prueba_error_herramienta_se_registra() -> None:
    def sondeo():
        raise ErrorHerramienta("fetch", "timeout")

    res = _gestor(max_intentos=2).recuperar(sondeo)
    assert res.estado is EstadoRecuperacion.AGOTADO
    assert len(res.errores) == 2 and res.origen == "max_intentos"


def prueba_agotado_por_plazo_total() -> None:
    res = _gestor(plazo_total=0.5, reloj=_reloj_falso(1.0)).recuperar(lambda: None)
    assert res.estado is EstadoRecuperacion.AGOTADO and res.origen == "plazo_total"


def prueba_detener_corta_recuperacion() -> None:
    res = _gestor().recuperar(lambda: None)
    detenido = _gestor().detener(res)
    assert detenido.estado is EstadoRecuperacion.DETENIDO and not detenido.recuperado


def prueba_backoff_con_tope() -> None:
    politica = PoliticaPlazos(backoff_base_s=0.1, backoff_max_s=0.25)
    assert politica.espera_intento(0) == 0.1
    assert politica.espera_intento(9) == 0.25


def prueba_validaciones_de_entrada() -> None:
    for malo in (0, -3):
        try:
            PoliticaPlazos(max_intentos=malo).validar()
        except ValueError:
            continue
        raise AssertionError("max_intentos invalido aceptado")
    try:
        PoliticaPlazos().espera_intento(-1)
    except ValueError:
        return
    raise AssertionError("intento negativo aceptado")


def ejecutar_pruebas() -> int:
    pruebas = [v for k, v in sorted(globals().items()) if k.startswith("prueba_")]
    fallos = 0
    for prueba in pruebas:
        try:
            prueba()
        except AssertionError as exc:
            fallos += 1
            print(f"FALLO {prueba.__name__}: {exc}")
    print(f"ejecutadas={len(pruebas)} fallos={fallos}")
    return fallos


if __name__ == "__main__":
    raise SystemExit(1 if ejecutar_pruebas() else 0)