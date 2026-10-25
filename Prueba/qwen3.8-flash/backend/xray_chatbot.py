"""xray_chatbot.py — FASE BACKEND de prueba aislada (sin red).

Nucleo de chatbot solo con stdlib de Python 3: sesiones, mensajes, anclas
ON/OFF, checklist, historial, toggles (tools / agente_tool / llm_tool),
validaciones y construccion de payload JSON. No abre sockets ni se conecta
al chat real: es una prueba de backend independiente.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

ROLES_VALIDOS = ("system", "user", "assistant", "tool")
ESTADOS_ANCLA = ("ON", "OFF")
TOGGLES_VALIDOS = ("tools", "agente_tool", "llm_tool")


class ValidacionError(ValueError):
    """La entrada no cumple el contrato del backend xray."""


def _texto_requerido(valor: Any, campo: str) -> str:
    if not isinstance(valor, str) or not valor.strip():
        raise ValidacionError("el campo '%s' exige texto no vacio" % campo)
    return valor.strip()


def _entero_requerido(valor: Any, campo: str) -> int:
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise ValidacionError("el campo '%s' exige un entero" % campo)
    return valor


@dataclass
class Ancla:
    id: str
    etiqueta: str
    estado: str = "ON"
    prioridad: int = 0


@dataclass
class Mensaje:
    id: str
    rol: str
    contenido: str
    creado: float
    ancla_id: Optional[str] = None


@dataclass
class Pendiente:
    id: str
    texto: str
    hecho: bool = False


@dataclass
class Toggles:
    tools: bool = False
    agente_tool: bool = False
    llm_tool: bool = False


@dataclass
class Sesion:
    id: str
    titulo: str
    modelo: str
    mensajes: List[Mensaje] = field(default_factory=list)
    anclas: List[Ancla] = field(default_factory=list)
    checklist: List[Pendiente] = field(default_factory=list)
    historial: List[str] = field(default_factory=list)
    toggles: Toggles = field(default_factory=Toggles)

    @property
    def anclas_encendidas(self) -> List[Ancla]:
        activas = [a for a in self.anclas if a.estado == "ON"]
        return sorted(activas, key=lambda a: (-a.prioridad, a.etiqueta))

    @property
    def anclas_apagadas(self) -> List[Ancla]:
        return [a for a in self.anclas if a.estado == "OFF"]


class XrayChatbot:
    VERSION = "0.1-backend-aislado"
    MAX_MENSAJES = 200
    MAX_HISTORIAL = 50

    def __init__(self) -> None:
        self.sesiones: Dict[str, Sesion] = {}

    # ---------------- helpers internos ----------------
    def _registrar(self, sesion: Sesion, evento: str) -> None:
        sesion.historial.append("%s %s" % (time.strftime("%H:%M:%S"), evento))
        exceso = len(sesion.historial) - self.MAX_HISTORIAL
        if exceso > 0:
            del sesion.historial[:exceso]

    def _sesion(self, sid: str) -> Sesion:
        clave = _texto_requerido(sid, "sesion_id")
        sesion = self.sesiones.get(clave)
        if sesion is None:
            raise ValidacionError("sesion desconocida: %s" % clave)
        return sesion

    def _buscar_ancla(self, sesion: Sesion, referencia: str) -> Optional[Ancla]:
        for ancla in sesion.anclas:
            if ancla.id == referencia or ancla.etiqueta == referencia:
                return ancla
        return None

    # ---------------- sesiones ----------------
    def crear_sesion(self, titulo: str, modelo: str = "qwen3.8-flash") -> Dict[str, str]:
        sid = "ses-" + uuid.uuid4().hex[:8]
        if sid in self.sesiones:
            raise ValidacionError("colision de identificador: %s" % sid)
        sesion = Sesion(sid, _texto_requerido(titulo, "titulo"),
                        _texto_requerido(modelo, "modelo"))
        self.sesiones[sid] = sesion
        self._registrar(sesion, "crear_sesion modelo=%s" % sesion.modelo)
        return {"sesion_id": sid, "estado": "creada"}

    def listar_sesiones(self) -> List[Dict[str, Any]]:
        filas = []
        for s in self.sesiones.values():
            filas.append({"id": s.id, "titulo": s.titulo, "modelo": s.modelo,
                          "mensajes": len(s.mensajes), "anclas": len(s.anclas)})
        return filas

    # ---------------- mensajes ----------------
    def agregar_mensaje(self, sid: str, rol: str, contenido: str,
                        ancla_id: Optional[str] = None) -> Dict[str, Any]:
        sesion = self._sesion(sid)
        if rol not in ROLES_VALIDOS:
            raise ValidacionError("rol no permitido: %s" % rol)
        contenido = _texto_requerido(contenido, "contenido")
        if ancla_id is not None and self._buscar_ancla(sesion, ancla_id) is None:
            raise ValidacionError("ancla inexistente: %s" % ancla_id)
        if len(sesion.mensajes) >= self.MAX_MENSAJES:
            raise ValidacionError("limite de mensajes alcanzado")
        mid = "msg-" + uuid.uuid4().hex[:8]
        sesion.mensajes.append(Mensaje(mid, rol, contenido, time.time(), ancla_id))
        self._registrar(sesion, "agregar_mensaje rol=%s id=%s" % (rol, mid))
        return {"mensaje_id": mid, "total": len(sesion.mensajes)}

    def obtener_mensajes(self, sid: str) -> List[Dict[str, Any]]:
        return [asdict(m) for m in self._sesion(sid).mensajes]

    def obtener_historial(self, sid: str) -> List[str]:
        return list(self._sesion(sid).historial)

    # ---------------- anclas ----------------
    def fijar_ancla(self, sid: str, etiqueta: str, estado: str = "ON",
                    prioridad: int = 0) -> Dict[str, Any]:
        sesion = self._sesion(sid)
        etiqueta = _texto_requerido(etiqueta, "etiqueta")
        estado = str(estado).strip().upper()
        if estado not in ESTADOS_ANCLA:
            raise ValidacionError("estado de ancla invalido: %s" % estado)
        prioridad = _entero_requerido(prioridad, "prioridad")
        ancla = self._buscar_ancla(sesion, etiqueta)
        if ancla is None:
            ancla = Ancla("anc-" + uuid.uuid4().hex[:6], etiqueta, estado, prioridad)
            sesion.anclas.append(ancla)
            accion = "creada"
        else:
            ancla.estado = estado
            ancla.prioridad = prioridad
            accion = "actualizada"
        self._registrar(sesion, "fijar_ancla %s %s=%s" % (accion, etiqueta, estado))
        return asdict(ancla)

    # ---------------- checklist ----------------
    def agregar_item(self, sid: str, texto: str) -> Dict[str, str]:
        sesion = self._sesion(sid)
        item = Pendiente("chk-" + uuid.uuid4().hex[:6], _texto_requerido(texto, "texto"))
        sesion.checklist.append(item)
        self._registrar(sesion, "agregar_item %s" % item.id)
        return asdict(item)

    def marcar_item(self, sid: str, item_id: str, hecho: bool = True) -> Dict[str, Any]:
        sesion = self._sesion(sid)
        for item in sesion.checklist:
            if item.id == item_id:
                item.hecho = bool(hecho)
                self._registrar(sesion, "marcar_item %s hecho=%s" % (item_id, item.hecho))
                return asdict(item)
        raise ValidacionError("item inexistente: %s" % item_id)

    def estado_checklist(self, sid: str) -> Dict[str, Any]:
        sesion = self._sesion(sid)
        hechos = sum(1 for p in sesion.checklist if p.hecho)
        return {"total": len(sesion.checklist), "hechos": hechos,
                "items": [asdict(p) for p in sesion.checklist]}

    # ---------------- toggles ----------------
    def fijar_toggle(self, sid: str, nombre: str, valor: bool) -> Dict[str, bool]:
        sesion = self._sesion(sid)
        nombre = _texto_requerido(nombre, "toggle")
        if nombre not in TOGGLES_VALIDOS:
            raise ValidacionError("toggle no permitido: %s" % nombre)
        setattr(sesion.toggles, nombre, bool(valor))
        self._registrar(sesion, "fijar_toggle %s=%s" % (nombre, bool(valor)))
        return asdict(sesion.toggles)

    def leer_toggles(self, sid: str) -> Dict[str, bool]:
        return asdict(self._sesion(sid).toggles)

    # ---------------- payload ----------------
    def _herramientas(self, toggles: Toggles) -> List[str]:
        herramientas = []
        if toggles.tools:
            herramientas.append("tools")
        if toggles.agente_tool:
            herramientas.append("agente_tool")
        if toggles.llm_tool:
            herramientas.append("llm_tool")
        return herramientas

    def construir_payload(self, sid: str) -> Dict[str, Any]:
        """Arma el payload filtrando los mensajes anclados en anclas OFF."""
        sesion = self._sesion(sid)
        encendidas = {a.id for a in sesion.anclas_encendidas}
        mensajes = []
        filtrados = 0
        for m in sesion.mensajes:
            if m.ancla_id is not None:
                ancla = self._buscar_ancla(sesion, m.ancla_id)
                if ancla is None or ancla.id not in encendidas:
                    filtrados += 1
                    continue
            mensajes.append({"role": m.rol, "content": m.contenido, "ancla": m.ancla_id})
        return {
            "version": self.VERSION,
            "sesion_id": sesion.id,
            "titulo": sesion.titulo,
            "modelo": sesion.modelo,
            "mensajes": mensajes,
            "herramientas": self._herramientas(sesion.toggles),
            "toggles": asdict(sesion.toggles),
            "anclas_on": [a.etiqueta for a in sesion.anclas_encendidas],
            "anclas_off": [a.etiqueta for a in sesion.anclas_apagadas],
            "checklist": self.estado_checklist(sid)["items"],
            "mensajes_filtrados": filtrados,
            "sin_red": True,
        }

    def exportar_json(self, sid: str, indent: int = 2) -> str:
        _entero_requerido(indent, "indent")
        return json.dumps(self.construir_payload(sid), ensure_ascii=False, indent=indent)


def demostracion() -> Dict[str, Any]:
    """Flujo local de prueba: sesion -> anclas -> mensajes -> checklist -> payload."""
    bot = XrayChatbot()
    sid = bot.crear_sesion("prueba backend aislada")["sesion_id"]
    bot.fijar_ancla(sid, "normas", "ON", 10)
    bot.fijar_ancla(sid, "borrador", "OFF", 1)
    bot.agregar_mensaje(sid, "system", "Eres el backend xray.", "normas")
    bot.agregar_mensaje(sid, "user", "Mensaje dentro de ancla activa.", "normas")
    bot.agregar_mensaje(sid, "user", "Mensaje que debe filtrarse.", "borrador")
    bot.agregar_mensaje(sid, "assistant", "Recibido, sin red.")
    item = bot.agregar_item(sid, "validar payload")
    bot.marcar_item(sid, item["id"], True)
    bot.fijar_toggle(sid, "tools", True)
    bot.fijar_toggle(sid, "llm_tool", True)
    try:
        bot.agregar_mensaje(sid, "vecino", "deberia fallar")
    except ValidacionError as error:
        bot._registrar(bot._sesion(sid), "rechazado: %s" % error)
    return bot.construir_payload(sid)


if __name__ == "__main__":
    print(json.dumps(demostracion(), ensure_ascii=False, indent=2))
