#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""XrayChatbot: prototipo aislado de gestión de sesiones conversacionales.

Este módulo usa únicamente la biblioteca estándar de Python 3 y no realiza
ninguna operación de red, no lee secretos ni depende de otros archivos del
repositorio.

Responsabilidades:

* crear_sesion       -> alta de una sesión local con estado inicial completo.
* agregar_mensaje    -> alta de un mensaje validado en el historial.
* fijar_ancla        -> crear o actualizar un ancla (activa / inactiva).
* construir_payload  -> montar el JSON de salida omitiendo anclas OFF.
* checklist          -> tareas pendientes con transición de estados.
* flags de tools     -> estado independiente de tools, agente_tool y llm_tool.

Todas las entradas externas se validan antes de mutar el estado interno.
"""

import json
import re
import uuid
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Constantes de dominio permitido
# ---------------------------------------------------------------------------
ESTADOS_ANCLA = ("activa", "inactiva")
ESTADOS_TAREA = ("pendiente", "hecha", "cancelada")
ESTADOS_TOOL = ("idle", "ok", "error")
TOOLS_VALIDAS = ("tools", "agente_tool", "llm_tool")

LIMITE_NOMBRE = 80
LIMITE_AUTOR = 60
LIMITE_MENSAJE = 2000
LIMITE_TAREA = 300


# ---------------------------------------------------------------------------
# Utilidades puras
# ---------------------------------------------------------------------------
def _ahora() -> str:
    """Devuelve la marca de tiempo UTC actual en formato ISO 8601."""
    return datetime.now(timezone.utc).isoformat()


def _id() -> str:
    """Devuelve un identificador corto pseudo-único."""
    return uuid.uuid4().hex[:12]


def validar_texto(valor, campo: str, max_len: int = LIMITE_MENSAJE) -> str:
    """Valida que ``valor`` sea una cadena no vacía dentro del tope."""
    if not isinstance(valor, str):
        raise ValueError(f"{campo} debe ser una cadena de texto.")
    texto = valor.strip()
    if not texto:
        raise ValueError(f"{campo} no puede quedar vacío.")
    if len(texto) > max_len:
        raise ValueError(f"{campo} supera el máximo de {max_len} caracteres.")
    return texto


def validar_sid(valor) -> str:
    """Valida que ``valor`` sea un identificador de sesión con formato de 12 hex."""
    if not isinstance(valor, str) or not re.fullmatch(r"[0-9a-f]{12}", valor):
        raise ValueError("identificador de sesión no válido.")
    return valor


def validar_dominio(valor, dominio, campo: str):
    """Valida que ``valor`` pertenezca al conjunto ``dominio``."""
    if valor not in dominio:
        raise ValueError(f"{campo} '{valor}' no válido. Usar: {sorted(dominio)}.")
    return valor


# ---------------------------------------------------------------------------
# Modelo
# ---------------------------------------------------------------------------
class XrayChatbot:
    """Almacén local de sesiones con historial, anclas, tareas y tools."""

    def __init__(self):
        self.sesiones = {}

    # ------------------------- Sesiones -------------------------
    def crear_sesion(self, nombre: str = "sesion") -> dict:
        """Crea una sesión con estado inicial y la registra internamente."""
        nombre = validar_texto(nombre, "nombre", LIMITE_NOMBRE)
        sid = _id()
        sesion = {
            "id": sid,
            "nombre": nombre,
            "creada": _ahora(),
            "mensajes": [],
            "anclas": [],
            "checklist": [],
            "estados_tools": {t: "idle" for t in TOOLS_VALIDAS},
        }
        self.sesiones[sid] = sesion
        return sesion

    def obtener_sesion(self, sid: str) -> dict:
        """Obtiene una sesión por identificador o lanza ``KeyError``."""
        sid = validar_sid(sid)
        if sid not in self.sesiones:
            raise KeyError(f"sesión '{sid}' no existe.")
        return self.sesiones[sid]

    def listar_sesiones(self) -> list:
        """Lista el resumen público de todas las sesiones."""
        return [
            {"id": s["id"], "nombre": s["nombre"], "creada": s["creada"]}
            for s in self.sesiones.values()
        ]

    # ------------------------- Mensajes -------------------------
    def agregar_mensaje(self, sid: str, autor: str, texto: str) -> dict:
        """Agrega un mensaje validado al historial de la sesión."""
        sesion = self.obtener_sesion(sid)
        autor = validar_texto(autor, "autor", LIMITE_AUTOR)
        texto = validar_texto(texto, "texto", LIMITE_MENSAJE)
        mensaje = {
            "id": _id(),
            "autor": autor,
            "texto": texto,
            "ts": _ahora(),
        }
        sesion["mensajes"].append(mensaje)
        return mensaje

    def historial(self, sid: str) -> list:
        """Devuelve una copia del historial de mensajes de la sesión."""
        sesion = self.obtener_sesion(sid)
        return list(sesion["mensajes"])

    # ------------------------- Anclas -------------------------
    def fijar_ancla(self, sid: str, nombre: str, estado: str = "activa") -> dict:
        """Crea o actualiza un ancla; solo ``activa`` se incluirá en el payload."""
        sesion = self.obtener_sesion(sid)
        nombre = validar_texto(nombre, "ancla", LIMITE_NOMBRE)
        estado = validar_dominio(estado, ESTADOS_ANCLA, "estado de ancla")
        for ancla in sesion["anclas"]:
            if ancla["nombre"] == nombre:
                ancla["estado"] = estado
                ancla["ts"] = _ahora()
                return ancla
        ancla = {"id": _id(), "nombre": nombre, "estado": estado, "ts": _ahora()}
        sesion["anclas"].append(ancla)
        return ancla

    def alternar_ancla(self, sid: str, aid: str) -> dict:
        """Alterna el estado activa/inactiva de un ancla existente."""
        sesion = self.obtener_sesion(sid)
        for ancla in sesion["anclas"]:
            if ancla["id"] == aid:
                ancla["estado"] = "inactiva" if ancla["estado"] == "activa" else "activa"
                ancla["ts"] = _ahora()
                return ancla
        raise KeyError(f"ancla '{aid}' no existe.")

    def anclas_activas(self, sid: str) -> list:
        """Devuelve solo las anclas con estado ``activa``."""
        sesion = self.obtener_sesion(sid)
        return [a for a in sesion["anclas"] if a["estado"] == "activa"]

    # ------------------------- Checklist -------------------------
    def agregar_tarea(self, sid: str, texto: str, estado: str = "pendiente") -> dict:
        """Agrega una tarea al checklist de pendientes de la sesión."""
        sesion = self.obtener_sesion(sid)
        texto = validar_texto(texto, "tarea", LIMITE_TAREA)
        estado = validar_dominio(estado, ESTADOS_TAREA, "estado de tarea")
        tarea = {"id": _id(), "texto": texto, "estado": estado, "ts": _ahora()}
        sesion["checklist"].append(tarea)
        return tarea

    def marcar_tarea(self, sid: str, tid: str, estado: str) -> dict:
        """Cambia el estado de una tarea existente del checklist."""
        sesion = self.obtener_sesion(sid)
        estado = validar_dominio(estado, ESTADOS_TAREA, "estado de tarea")
        for tarea in sesion["checklist"]:
            if tarea["id"] == tid:
                tarea["estado"] = estado
                tarea["ts"] = _ahora()
                return tarea
        raise KeyError(f"tarea '{tid}' no existe.")

    def checklist(self, sid: str) -> list:
        """Devuelve una copia del checklist completo de la sesión."""
        sesion = self.obtener_sesion(sid)
        return list(sesion["checklist"])

    # ------------------------- Tools -------------------------
    def fijar_estado_tool(self, sid: str, tool: str, estado: str) -> dict:
        """Fija el estado independiente de una de las tres tools."""
        sesion = self.obtener_sesion(sid)
        tool = validar_dominio(tool, TOOLS_VALIDAS, "herramienta")
        estado = validar_dominio(estado, ESTADOS_TOOL, "estado de tool")
        sesion["estados_tools"][tool] = estado
        return {"tool": tool, "estado": estado}

    def estados_tools(self, sid: str) -> dict:
        """Devuelve una copia del estado actual de las tres tools."""
        sesion = self.obtener_sesion(sid)
        return dict(sesion["estados_tools"])

    # ------------------------- Payload -------------------------
    def construir_payload(self, sid: str) -> dict:
        """Construye el payload JSON; las anclas OFF quedan excluidas."""
        sesion = self.obtener_sesion(sid)
        return {
            "sesion": {
                "id": sesion["id"],
                "nombre": sesion["nombre"],
                "creada": sesion["creada"],
            },
            "mensajes": list(sesion["mensajes"]),
            "anclas_activas": self.anclas_activas(sid),
            "checklist": list(sesion["checklist"]),
            "estados_tools": self.estados_tools(sid),
        }

    def exportar_json(self, sid: str, indent: int = 2) -> str:
        """Serializa a JSON el payload de la sesión sin anclas OFF."""
        return json.dumps(
            self.construir_payload(sid),
            ensure_ascii=False,
            indent=indent,
        )


# ---------------------------------------------------------------------------
# Demostración local
# ---------------------------------------------------------------------------
def demo() -> None:
    """Ejercita el flujo principal sin red y vuelca el JSON resultante."""
    cb = XrayChatbot()
    sid = cb.crear_sesion("demo")["id"]
    cb.agregar_mensaje(sid, "usuario", "hola, prototipo aislado")
    cb.agregar_mensaje(sid, "bot", "respuesta sin red")
    cb.fijar_ancla(sid, "contexto A")
    cb.fijar_ancla(sid, "contexto B", "inactiva")
    cb.agregar_tarea(sid, "revisar anclas", "pendiente")
    cb.agregar_tarea(sid, "validar payload", "hecha")
    cb.fijar_estado_tool(sid, "agente_tool", "ok")
    cb.fijar_estado_tool(sid, "llm_tool", "error")
    print(cb.exportar_json(sid))


if __name__ == "__main__":
    demo()