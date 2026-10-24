"""Motor de permisos de agentes y selector independiente de herramientas.

Modulo aislado para la carpeta Prueba: APAGADO por defecto, sin red, sin
secretos y sin dependencias externas (solo biblioteca estandar). No importa
ni es importado por el chatbot productivo.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Set, Tuple

NOMBRE_VALIDO = re.compile(r"^[a-z][a-z0-9_]{1,31}$")
MAX_HERRAMIENTAS_POR_AGENTE = 32
LIMITE_SELECCION_POR_DEFECTO = 5


class ErrorMotorPermisos(Exception):
    """Error base del motor de permisos."""


class ErrorValidacion(ErrorMotorPermisos):
    """Entrada invalida: tipo, formato o duplicado."""


class ErrorPermisoDenegado(ErrorMotorPermisos):
    """El agente no tiene permiso para la herramienta solicitada."""


def validar_nombre(valor: object, campo: str) -> str:
    """Normaliza y valida un identificador corto en minusculas."""
    if not isinstance(valor, str):
        raise ErrorValidacion(f"{campo} debe ser texto, recibido {type(valor).__name__}")
    limpio = valor.strip().lower()
    if not NOMBRE_VALIDO.match(limpio):
        raise ErrorValidacion(f"{campo} invalido: {valor!r} (2-32 minusculas, digito o guion bajo)")
    return limpio


@dataclass(frozen=True)
class Herramienta:
    """Descripcion inmutable de una herramienta seleccionable."""

    nombre: str
    etiquetas: Tuple[str, ...] = ()
    descripcion: str = ""

    def __post_init__(self) -> None:
        validar_nombre(self.nombre, "herramienta.nombre")
        if not isinstance(self.etiquetas, tuple):
            raise ErrorValidacion("herramienta.etiquetas debe ser una tupla")
        for etiqueta in self.etiquetas:
            validar_nombre(etiqueta, "herramienta.etiqueta")
        if not isinstance(self.descripcion, str):
            raise ErrorValidacion("herramienta.descripcion debe ser texto")

    def puntuar(self, termino: str) -> int:
        """Puntua la coincidencia con un termino; 0 significa descartada."""
        buscado = termino.strip().lower()
        if not buscado:
            raise ErrorValidacion("termino de busqueda vacio")
        puntos = 0
        if buscado == self.nombre:
            puntos += 5
        elif buscado in self.nombre:
            puntos += 3
        if any(buscado in etiqueta for etiqueta in self.etiquetas):
            puntos += 2
        if buscado in self.descripcion.lower():
            puntos += 1
        return puntos


@dataclass
class Agente:
    """Agente con la lista de herramientas que declara poder usar."""

    nombre: str
    herramientas: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.nombre = validar_nombre(self.nombre, "agente.nombre")
        if not isinstance(self.herramientas, list):
            raise ErrorValidacion("agente.herramientas debe ser una lista")
        if len(self.herramientas) > MAX_HERRAMIENTAS_POR_AGENTE:
            raise ErrorValidacion(f"agente.herramientas excede {MAX_HERRAMIENTAS_POR_AGENTE} elementos")
        self.herramientas = [validar_nombre(h, "agente.herramienta") for h in self.herramientas]
        if len(set(self.herramientas)) != len(self.herramientas):
            raise ErrorValidacion("agente.herramientas contiene duplicados")


class MotorPermisos:
    """Registro de agentes y concesiones explicitas. Apagado por defecto."""

    def __init__(self, activado: bool = False) -> None:
        if not isinstance(activado, bool):
            raise ErrorValidacion("activado debe ser booleano")
        self._activado = activado
        self._agentes: Dict[str, Agente] = {}
        self._concedidas: Dict[str, Set[str]] = {}

    @property
    def activado(self) -> bool:
        return self._activado

    def activar(self) -> None:
        self._activado = True

    def desactivar(self) -> None:
        self._activado = False
        for conjunto in self._concedidas.values():
            conjunto.clear()

    def registrar(self, agente: Agente) -> None:
        if not isinstance(agente, Agente):
            raise ErrorValidacion("se esperaba una instancia de Agente")
        if agente.nombre in self._agentes:
            raise ErrorValidacion(f"agente duplicado: {agente.nombre}")
        self._agentes[agente.nombre] = agente
        self._concedidas[agente.nombre] = set()

    def _exigir_agente(self, nombre: object) -> str:
        clave = validar_nombre(nombre, "agente")
        if clave not in self._agentes:
            raise ErrorPermisoDenegado(f"agente desconocido: {clave}")
        return clave

    def conceder(self, agente: object, herramienta: object) -> None:
        clave = self._exigir_agente(agente)
        nombre_herramienta = validar_nombre(herramienta, "herramienta")
        if nombre_herramienta not in self._agentes[clave].herramientas:
            raise ErrorPermisoDenegado(
                f"la herramienta {nombre_herramienta} no esta declarada por el agente {clave}"
            )
        self._concedidas[clave].add(nombre_herramienta)

    def revocar(self, agente: object, herramienta: object) -> None:
        clave = self._exigir_agente(agente)
        self._concedidas[clave].discard(validar_nombre(herramienta, "herramienta"))

    def puede(self, agente: object, herramienta: object) -> bool:
        """Devuelve False sin lanzar cuando el motor esta apagado."""
        if not self._activado:
            return False
        try:
            clave = self._exigir_agente(agente)
            nombre_herramienta = validar_nombre(herramienta, "herramienta")
        except ErrorMotorPermisos:
            return False
        return nombre_herramienta in self._concedidas[clave]

    def exigir(self, agente: object, herramienta: object) -> bool:
        """Igual que puede() pero lanza ErrorPermisoDenegado si no autoriza."""
        if not self.puede(agente, herramienta):
            raise ErrorPermisoDenegado(f"permiso denegado: {agente!r} -> {herramienta!r}")
        return True

    def concedidas(self, agente: object) -> List[str]:
        return sorted(self._concedidas[self._exigir_agente(agente)])


class SelectorHerramientas:
    """Selector independiente: no consulta ni modifica el motor de permisos."""

    def __init__(self, herramientas: Sequence[Herramienta] = ()) -> None:
        self._herramientas: Dict[str, Herramienta] = {}
        for herramienta in herramientas:
            self.registrar(herramienta)

    def registrar(self, herramienta: Herramienta) -> None:
        if not isinstance(herramienta, Herramienta):
            raise ErrorValidacion("se esperaba una instancia de Herramienta")
        if herramienta.nombre in self._herramientas:
            raise ErrorValidacion(f"herramienta duplicada: {herramienta.nombre}")
        self._herramientas[herramienta.nombre] = herramienta

    def seleccionar(self, termino: str, limite: int = LIMITE_SELECCION_POR_DEFECTO) -> List[Herramienta]:
        if not isinstance(limite, int) or isinstance(limite, bool):
            raise ErrorValidacion("limite debe ser un entero")
        if limite < 1:
            raise ErrorValidacion("limite debe ser mayor que cero")
        ranking = []
        for herramienta in self._herramientas.values():
            puntos = herramienta.puntuar(termino)
            if puntos > 0:
                ranking.append((puntos, herramienta.nombre, herramienta))
        ranking.sort(key=lambda item: (-item[0], item[1]))
        return [item[2] for item in ranking[:limite]]

    def nombres(self) -> List[str]:
        return sorted(self._herramientas)


def prueba_motor_apagado_deniega() -> None:
    motor = MotorPermisos()
    motor.registrar(Agente("analista", ["buscar"]))
    motor.conceder("analista", "buscar")
    assert motor.activado is False
    assert motor.puede("analista", "buscar") is False
    try:
        motor.exigir("analista", "buscar")
    except ErrorPermisoDenegado:
        pass
    else:
        raise AssertionError("exigir() debe lanzar con el motor apagado")


def prueba_activacion_y_concesion() -> None:
    motor = MotorPermisos(activado=True)
    motor.registrar(Agente("analista", ["buscar", "resumir"]))
    motor.conceder("analista", "buscar")
    assert motor.puede("analista", "buscar") is True
    assert motor.puede("analista", "resumir") is False
    motor.revocar("analista", "buscar")
    assert motor.puede("analista", "buscar") is False
    assert motor.concedidas("analista") == []


def prueba_concesion_no_declarada_falla() -> None:
    motor = MotorPermisos(activado=True)
    motor.registrar(Agente("analista", ["buscar"]))
    try:
        motor.conceder("analista", "borrar_todo")
    except ErrorPermisoDenegado:
        return
    raise AssertionError("conceder() debe rechazar herramientas no declaradas")


def prueba_validaciones_y_duplicados() -> None:
    for valor in ("", "A", "1abc", "con espacio", "ñ", "x" * 40, None, 7):
        try:
            validar_nombre(valor, "prueba")
        except ErrorValidacion:
            continue
        raise AssertionError(f"validar_nombre debe rechazar {valor!r}")
    motor = MotorPermisos()
    motor.registrar(Agente("uno"))
    try:
        motor.registrar(Agente("uno"))
    except ErrorValidacion:
        return
    raise AssertionError("registrar() debe rechazar agentes duplicados")


def prueba_selector_ordena_e_independiza() -> None:
    selector = SelectorHerramientas(
        [
            Herramienta("buscar_web", ("web", "busqueda"), "consulta externa simulada"),
            Herramienta("buscar_local", ("local",), "indice local"),
            Herramienta("resumir", ("texto",), "resume documentos"),
        ]
    )
    resultados = selector.seleccionar("BUSCAR")
    assert [h.nombre for h in resultados] == ["buscar_web", "buscar_local"], resultados
    assert selector.seleccionar("resumir")[0].nombre == "resumir"
    assert selector.seleccionar("inexistente") == []
    motor = MotorPermisos()
    assert motor.puede("nadie", "buscar_web") is False
    try:
        selector.seleccionar("buscar", limite=0)
    except ErrorValidacion:
        return
    raise AssertionError("seleccionar() debe rechazar limite invalido")


def ejecutar_pruebas() -> Dict[str, bool]:
    pruebas = {
        "motor_apagado_deniega": prueba_motor_apagado_deniega,
        "activacion_y_concesion": prueba_activacion_y_concesion,
        "concesion_no_declarada_falla": prueba_concesion_no_declarada_falla,
        "validaciones_y_duplicados": prueba_validaciones_y_duplicados,
        "selector_ordena_e_independiza": prueba_selector_ordena_e_independiza,
    }
    informe: Dict[str, bool] = {}
    for nombre, prueba in pruebas.items():
        try:
            prueba()
        except AssertionError as error:
            informe[nombre] = False
            print(f"FALLO {nombre}: {error}")
        else:
            informe[nombre] = True
    return informe


if __name__ == "__main__":
    resultado = ejecutar_pruebas()
    total = len(resultado)
    correctas = sum(1 for valor in resultado.values() if valor)
    print(f"pruebas: {correctas}/{total} correctas")
    raise SystemExit(0 if correctas == total else 1)