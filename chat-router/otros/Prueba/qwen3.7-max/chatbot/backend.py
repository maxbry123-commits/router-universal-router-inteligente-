"""
Backend aislado: máquina de estados de mensajes, historial y recuperación.
Python 3 estándar, sin dependencias, sin servidor, sin red.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable, List, Dict
import time
import uuid
import copy


class Estado(Enum):
    NUEVO = "nuevo"
    ENVIADO = "enviado"
    ENTREGADO = "entregado"
    FALLIDO = "fallido"
    REINTENTANDO = "reintentando"
    CANCELADO = "cancelado"


TRANSICIONES = {
    Estado.NUEVO: {Estado.ENVIADO, Estado.CANCELADO},
    Estado.ENVIADO: {Estado.ENTREGADO, Estado.FALLIDO, Estado.CANCELADO},
    Estado.ENTREGADO: set(),
    Estado.FALLIDO: {Estado.REINTENTANDO, Estado.CANCELADO},
    Estado.REINTENTANDO: {Estado.ENVIADO, Estado.FALLIDO, Estado.CANCELADO},
    Estado.CANCELADO: set(),
}


class ErrorValidacion(Exception):
    pass


class ErrorTransicion(Exception):
    pass


@dataclass
class Mensaje:
    contenido: str
    remitente: str
    id_mensaje: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    estado: Estado = Estado.NUEVO
    intentos: int = 0
    max_intentos: int = 3
    timestamps: Dict[str, float] = field(default_factory=dict)
    error_detalle: Optional[str] = None

    def __post_init__(self):
        if not isinstance(self.contenido, str) or not self.contenido.strip():
            raise ErrorValidacion("contenido vacío o inválido")
        if not isinstance(self.remitente, str) or not self.remitente.strip():
            raise ErrorValidacion("remitente vacío o inválido")
        if self.max_intentos < 1 or self.max_intentos > 20:
            raise ErrorValidacion("max_intentos fuera de rango [1,20]")
        self.timestamps[self.estado.value] = time.time()

    def transicionar(self, nuevo: Estado, error: Optional[str] = None) -> None:
        if nuevo not in TRANSICIONES[self.estado]:
            raise ErrorTransicion(
                f"transición inválida {self.estado.value} -> {nuevo.value}"
            )
        self.estado = nuevo
        self.timestamps[nuevo.value] = time.time()
        if nuevo == Estado.REINTENTANDO:
            self.intentos += 1
        if error is not None:
            self.error_detalle = error

    def puede_reintentar(self) -> bool:
        return (
            self.estado == Estado.FALLIDO
            and self.intentos < self.max_intentos
        )

    def resumen(self) -> Dict[str, object]:
        return {
            "id": self.id_mensaje,
            "remitente": self.remitente,
            "contenido": self.contenido,
            "estado": self.estado.value,
            "intentos": self.intentos,
            "error": self.error_detalle,
            "timestamps": copy.deepcopy(self.timestamps),
        }


class Historial:
    """Almacén en memoria con búsqueda y snapshot."""

    def __init__(self, capacidad: int = 1000):
        if capacidad < 1:
            raise ErrorValidacion("capacidad inválida")
        self.capacidad = capacidad
        self._mensajes: List[Mensaje] = []
        self._indice: Dict[str, Mensaje] = {}

    def agregar(self, mensaje: Mensaje) -> str:
        if mensaje.id_mensaje in self._indice:
            raise ErrorValidacion("id duplicado en historial")
        if len(self._mensajes) >= self.capacidad:
            self._mensajes.pop(0)
        self._mensajes.append(mensaje)
        self._indice[mensaje.id_mensaje] = mensaje
        return mensaje.id_mensaje

    def obtener(self, id_mensaje: str) -> Optional[Mensaje]:
        return self._indice.get(id_mensaje)

    def por_estado(self, estado: Estado) -> List[Mensaje]:
        return [m for m in self._mensajes if m.estado == estado]

    def buscar(self, texto: str) -> List[Mensaje]:
        if not isinstance(texto, str):
            raise ErrorValidacion("texto de búsqueda inválido")
        t = texto.lower()
        return [m for m in self._mensajes if t in m.contenido.lower()]

    def listar(self, limite: int = 50) -> List[Dict[str, object]]:
        return [m.resumen() for m in self._mensajes[-limite:]]

    def tamaño(self) -> int:
        return len(self._mensajes)


class ChatBackend:
    """Orquesta mensajes, transiciones y recuperación."""

    def __init__(
        self,
        historial: Optional[Historial] = None,
        simulador_fallo: Optional[Callable[[Mensaje], bool]] = None,
    ):
        self.historial = historial or Historial()
        self._simulador = simulador_fallo or (lambda m: False)
        self.observadores: List[Callable[[Mensaje], None]] = []

    def suscribir(self, callback: Callable[[Mensaje], None]) -> None:
        if not callable(callback):
            raise ErrorValidacion("observador no callable")
        self.observadores.append(callback)

    def _notificar(self, mensaje: Mensaje) -> None:
        for cb in self.observadores:
            try:
                cb(mensaje)
            except Exception:
                pass

    def enviar(self, contenido: str, remitente: str) -> Mensaje:
        mensaje = Mensaje(contenido=contenido, remitente=remitente)
        self.historial.agregar(mensaje)
        self._intentar_envio(mensaje)
        return mensaje

    def _intentar_envio(self, mensaje: Mensaje) -> None:
        origen = mensaje.estado
        if origen == Estado.FALLIDO:
            mensaje.transicionar(Estado.REINTENTANDO)
        elif origen == Estado.NUEVO:
            mensaje.transicionar(Estado.ENVIADO)
        else:
            mensaje.transicionar(Estado.ENVIADO)
        self._notificar(mensaje)
        try:
            if self._simulador(mensaje):
                raise RuntimeError("fallo simulado en transporte")
            mensaje.transicionar(Estado.ENTREGADO)
        except Exception as e:
            mensaje.transicionar(Estado.FALLIDO, error=str(e))
        self._notificar(mensaje)

    def reintentar(self, id_mensaje: str) -> Mensaje:
        mensaje = self.historial.obtener(id_mensaje)
        if mensaje is None:
            raise ErrorValidacion("mensaje no encontrado")
        if not mensaje.puede_reintentar():
            raise ErrorTransicion(
                f"no reintentable (estado={mensaje.estado.value}, "
                f"intentos={mensaje.intentos}/{mensaje.max_intentos})"
            )
        self._intentar_envio(mensaje)
        return mensaje

    def cancelar(self, id_mensaje: str) -> Mensaje:
        mensaje = self.historial.obtener(id_mensaje)
        if mensaje is None:
            raise ErrorValidacion("mensaje no encontrado")
        mensaje.transicionar(Estado.CANCELADO)
        self._notificar(mensaje)
        return mensaje

    def estado(self) -> Dict[str, int]:
        conteo: Dict[str, int] = {e.value: 0 for e in Estado}
        for m in self.historial._mensajes:
            conteo[m.estado.value] += 1
        return {"total": self.historial.tamaño(), "estados": conteo}


# --- Pruebas integradas (no arrancan servidor) -----------------------------

def _contador_fallo(cada: int):
    estado_local = {"n": 0}

    def _fn(m: Mensaje) -> bool:
        estado_local["n"] += 1
        return estado_local["n"] % cada == 0

    return _fn


def prueba_envio_exitoso() -> bool:
    backend = ChatBackend()
    m = backend.enviar("hola mundo", "alice")
    assert m.estado == Estado.ENTREGADO, m.estado
    assert backend.historial.tamaño() == 1
    return True


def prueba_envio_con_fallo_y_recuperacion() -> bool:
    backend = ChatBackend(simulador_fallo=_contador_fallo(1))
    m = backend.enviar("mensaje doomed", "bob")
    assert m.estado == Estado.FALLIDO
    assert m.puede_reintentar()
    backend2 = ChatBackend(
        historial=backend.historial, simulador_fallo=lambda x: False
    )
    backend2.observadores = backend.observadores
    m2 = backend2.reintentar(m.id_mensaje)
    assert m2.estado == Estado.ENTREGADO
    assert m2.intentos == 1
    return True


def prueba_limite_reintentos() -> bool:
    backend = ChatBackend(simulador_fallo=lambda m: True)
    m = backend.enviar("siempre falla", "carol")
    for _ in range(2):
        try:
            backend.reintentar(m.id_mensaje)
        except ErrorTransicion:
            pass
    assert m.intentos >= m.max_intentos
    assert not m.puede_reintentar()
    return True


def prueba_cancelacion() -> bool:
    backend = ChatBackend()
    m = backend.enviar("cancelame", "dave")
    try:
        backend.cancelar(m.id_mensaje)
        return False
    except ErrorTransicion:
        return True


def prueba_historial_busqueda() -> bool:
    backend = ChatBackend()
    backend.enviar("saludo cordial", "eve")
    backend.enviar("otro tema", "frank")
    res = backend.historial.buscar("cordial")
    return len(res) == 1 and res[0].remitente == "eve"


def prueba_validaciones() -> bool:
    try:
        Mensaje(contenido="   ", remitente="x")
    except ErrorValidacion:
        pass
    else:
        return False
    try:
        Historial(capacidad=0)
    except ErrorValidacion:
        return True
    return False


def prueba_estado_global() -> bool:
    backend = ChatBackend()
    backend.enviar("a", "u1")
    backend.enviar("b", "u2")
    estado = backend.estado()
    return estado["total"] == 2 and estado["estados"]["entregado"] == 2


EJECUTAR_PRUEBAS = {
    "envio_exitoso": prueba_envio_exitoso,
    "fallo_recuperacion": prueba_envio_con_fallo_y_recuperacion,
    "limite_reintentos": prueba_limite_reintentos,
    "cancelacion": prueba_cancelacion,
    "busqueda": prueba_historial_busqueda,
    "validaciones": prueba_validaciones,
    "estado_global": prueba_estado_global,
}


def ejecutar_pruebas() -> Dict[str, bool]:
    return {k: fn() for k, fn in EJECUTAR_PRUEBAS.items()}


if __name__ == "__main__":
    resultados = ejecutar_pruebas()
    for k, v in resultados.items():
        print(f"{k}: {'OK' if v else 'FALLO'}")
