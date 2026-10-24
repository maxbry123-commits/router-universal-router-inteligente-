#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prototipo AISLADO de chatbot (modo rayos X, sin conexión).

Ofrece una API local de funciones para gestionar sesiones, historial de
mensajes, anclas activas/inactivas, checklist de tareas y el estado
independiente de tres herramientas (tools, agente_tool, llm_tool).

No importa módulos del repositorio, no abre red, no usa claves ni secretos.
"""

import json
import uuid
from datetime import datetime, timezone

ESTADOS_ANCLA = ("activa", "inactiva")
ESTADOS_TOOL = ("idle", "ok", "error")
ESTADOS_TAREA = ("pendiente", "hecha", "cancelada")
TOOLS_VALIDAS = ("tools", "agente_tool", "llm_tool")


def _ahora():
    """Marca de tiempo UTC en formato ISO 8601."""
    return datetime.now(timezone.utc).isoformat()


def _id():
    """Identificador corto y único para cada entidad."""
    return uuid.uuid4().hex[:12]


def validar_texto(valor, campo, max_len=2000):
    """Valida un texto: debe ser str, no vacío y con tope de longitud."""
    if not isinstance(valor, str):
        raise ValueError(f"{campo} debe ser una cadena de texto.")
    texto = valor.strip()
    if not texto:
        raise ValueError(f"{campo} no puede quedar vacío.")
    if len(texto) > max_len:
        raise ValueError(f"{campo} supera el máximo de {max_len} caracteres.")
    return texto


def validar_dominio(valor, dominio, campo):
    """Valida que un valor pertenezca a un conjunto permitido."""
    if valor not in dominio:
        raise ValueError(f"{campo} '{valor}' no válido. Usar: {sorted(dominio)}.")
    return valor


class XrayChatbot:
    """Almacén local de una o varias sesiones de conversación aisladas."""

    def __init__(self):
        self.sesiones = {}

    # ---------- Sesiones ----------
    def crear_sesion(self, nombre="sesion"):
        nombre = validar_texto(nombre, "nombre", 80)
        sid = _id()
        sesion = {
            "id": sid,
            "nombre": nombre,
            "creada": _ahora(),
            "mensajes": [],
            "anclas": [],
            "checklist": [],
            "estados_tools": {"tools": "idle", "agente_tool": "idle", "llm_tool": "idle"},
        }
        self.sesiones[sid] = sesion
        return sesion

    def obtener_sesion(self, sid):
        if sid not in self.sesiones:
            raise KeyError(f"sesión '{sid}' no existe.")
        return self.sesiones[sid]

    def listar_sesiones(self):
        return [
            {"id": s["id"], "nombre": s["nombre"], "creada": s["creada"]}
            for s in self.sesiones.values()
        ]

    # ---------- Mensajes ----------
    def agregar_mensaje(self, sid, autor, texto):
        sesion = self.obtener_sesion(sid)
        autor = validar_texto(autor, "autor", 60)
        texto = validar_texto(texto, "texto")
        mensaje = {"id": _id(), "autor": autor, "texto": texto, "ts": _ahora()}
        sesion["mensajes"].append(mensaje)
        return mensaje

    def historial(self, sid):
        sesion = self.obtener_sesion(sid)
        return list(sesion["mensajes"])

    # ---------- Anclas ----------
    def fijar_ancla(self, sid, nombre, estado="activa"):
        sesion = self.obtener_sesion(sid)
        nombre = validar_texto(nombre, "ancla", 60)
        estado = validar_dominio(estado, ESTADOS_ANCLA, "estado de ancla")
        for ancla in sesion["anclas"]:
            if ancla["nombre"] == nombre:
                ancla["estado"] = estado
                ancla["ts"] = _ahora()
                return ancla
        ancla = {"id": _id(), "nombre": nombre, "estado": estado, "ts": _ahora()}
        sesion["anclas"].append(ancla)
        return ancla

    def alternar_ancla(self, sid, aid):
        sesion = self.obtener_sesion(sid)
        for ancla in sesion["anclas"]:
            if ancla["id"] == aid:
                ancla["estado"] = "inactiva" if ancla["estado"] == "activa" else "activa"
                ancla["ts"] = _ahora()
                return ancla
        raise KeyError(f"ancla '{aid}' no existe.")

    def anclas_activas(self, sid):
        sesion = self.obtener_sesion(sid)
        return [a for a in sesion["anclas"] if a["estado"] == "activa"]

    # ---------- Checklist de tareas ----------
    def agregar_tarea(self, sid, texto, estado="pendiente"):
        sesion = self.obtener_sesion(sid)
        texto = validar_texto(texto, "tarea", 300)
        estado = validar_dominio(estado, ESTADOS_TAREA, "estado de tarea")
        tarea = {"id": _id(), "texto": texto, "estado": estado, "ts": _ahora()}
        sesion["checklist"].append(tarea)
        return tarea

    def marcar_tarea(self, sid, tid, estado):
        sesion = self.obtener_sesion(sid)
        estado = validar_dominio(estado, ESTADOS_TAREA, "estado de tarea")
        for tarea in sesion["checklist"]:
            if tarea["id"] == tid:
                tarea["estado"] = estado
                tarea["ts"] = _ahora()
                return tarea
        raise KeyError(f"tarea '{tid}' no existe.")

    # ---------- Estado independiente de herramientas ----------
    def fijar_estado_tool(self, sid, tool, estado):
        sesion = self.obtener_sesion(sid)
        tool = validar_dominio(tool, TOOLS_VALIDAS, "herramienta")
        estado = validar_dominio(estado, ESTADOS_TOOL, "estado de tool")
        sesion["estados_tools"][tool] = estado
        return {"tool": tool, "estado": estado}

    # ---------- Payload y exportación ----------
    def construir_payload(self, sid):
        sesion = self.obtener_sesion(sid)
        return {
            "sesion": {"id": sesion["id"], "nombre": sesion["nombre"], "creada": sesion["creada"]},
            "mensajes": list(sesion["mensajes"]),
            "anclas_activas": self.anclas_activas(sid),
            "checklist": list(sesion["checklist"]),
            "estados_tools": dict(sesion["estados_tools"]),
        }

    def exportar_json(self, sid, indent=2):
        return json.dumps(self.construir_payload(sid), ensure_ascii=False, indent=indent)


def demo():
    cb = XrayChatbot()
    sid = cb.crear_sesion("demo")["id"]
    cb.agregar_mensaje(sid, "usuario", "hola, prototipo")
    cb.agregar_mensaje(sid, "bot", "respuesta aislada")
    cb.fijar_ancla(sid, "contexto A")
    cb.fijar_ancla(sid, "contexto B", "inactiva")
    cb.agregar_tarea(sid, "revisar anclas", "pendiente")
    cb.agregar_tarea(sid, "validar payload", "hecha")
    cb.fijar_estado_tool(sid, "agente_tool", "ok")
    cb.fijar_estado_tool(sid, "llm_tool", "error")
    print(cb.exportar_json(sid))


if __name__ == "__main__":
    demo()