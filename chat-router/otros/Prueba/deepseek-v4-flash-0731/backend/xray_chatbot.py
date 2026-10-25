"""
xray_chatbot.py - Prototipo aislado de chatbot (prueba deepseek-v4-flash-0731).
Sin conexiones externas: solo Python 3 estandar. Estado en memoria.
Funciones: crear_sesion, agregar_mensaje, fijar_ancla, registrar_tarea,
marcar_tarea, cambiar_estado, construir_payload, exportar_json, listar_historial.
"""

import json
import re
import uuid
from datetime import datetime, timezone

ROLES_VALIDOS = {"usuario", "bot", "sistema"}
HERRAMIENTAS = {"tool", "agent_tool", "llm_tool"}
ESTADOS_VALIDOS = {"idle", "busy", "ok", "error"}


class ErrorValidacion(ValueError):
    """Error de validacion de datos de entrada del chatbot."""


def _timestamp():
    """Marca de tiempo UTC en formato ISO 8601."""
    return datetime.now(timezone.utc).isoformat()


def _id(prefix):
    """Genera un identificador corto y unico."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def crear_sesion(nombre="Anonimo", perfil=None):
    """Crea una sesion nueva con estructuras de datos vacias."""
    nombre = (nombre or "Anonimo").strip()
    if not 1 <= len(nombre) <= 60:
        raise ErrorValidacion("El nombre debe tener entre 1 y 60 caracteres.")
    return {
        "id": _id("ses"),
        "nombre": nombre,
        "creada": _timestamp(),
        "mensajes": [],
        "anclas": {},
        "tareas": [],
        "estados": {h: "idle" for h in HERRAMIENTAS},
        "perfil": perfil or {},
    }


def validar_sesion(sesiones, sesion_id):
    """Comprueba que la sesion exista y devuelve su objeto."""
    if not isinstance(sesiones, dict) or sesion_id not in sesiones:
        raise ErrorValidacion("Sesion inexistente o invalida.")
    sesion = sesiones[sesion_id]
    if not isinstance(sesion, dict):
        raise ErrorValidacion("La sesion tiene una estructura invalida.")
    return sesion


def validar_texto(texto, max_len=2000):
    """Normaliza y valida un texto, evitando vacios o excesos."""
    texto = (texto or "").strip()
    if not texto:
        raise ErrorValidacion("El texto no puede estar vacio.")
    if len(texto) > max_len:
        raise ErrorValidacion(f"El texto supera los {max_len} caracteres.")
    if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", texto):
        raise ErrorValidacion("El texto contiene caracteres de control.")
    return texto


def agregar_mensaje(sesiones, sesion_id, rol, texto):
    """Agrega un mensaje conservando el historial completo de la sesion."""
    if rol not in ROLES_VALIDOS:
        raise ErrorValidacion(f"Rol invalido: {rol}")
    sesion = validar_sesion(sesiones, sesion_id)
    texto = validar_texto(texto)
    mensaje = {"id": _id("msg"), "rol": rol, "texto": texto, "ts": _timestamp()}
    sesion["mensajes"].append(mensaje)
    return mensaje


def fijar_ancla(sesiones, sesion_id, ancla_id, texto=None, activa=True):
    """Crea o alterna una ancla; solo las activas salen en el payload."""
    sesion = validar_sesion(sesiones, sesion_id)
    ancla_id = validar_texto(ancla_id, 40)
    if ancla_id in sesion["anclas"] and texto is None:
        sesion["anclas"][ancla_id]["activa"] = bool(activa)
    else:
        texto = validar_texto(texto or ancla_id, 300)
        sesion["anclas"][ancla_id] = {"texto": texto, "activa": bool(activa)}
    return sesion["anclas"][ancla_id]


def registrar_tarea(sesiones, sesion_id, tarea, hecha=False):
    """Anade una tarea a la checklist de la sesion."""
    sesion = validar_sesion(sesiones, sesion_id)
    tarea = validar_texto(tarea, 200)
    item = {"id": _id("tarea"), "texto": tarea, "hecha": bool(hecha)}
    sesion["tareas"].append(item)
    return item


def marcar_tarea(sesiones, sesion_id, tarea_id, hecha):
    """Actualiza el estado de una tarea existente."""
    sesion = validar_sesion(sesiones, sesion_id)
    for item in sesion["tareas"]:
        if item["id"] == tarea_id:
            item["hecha"] = bool(hecha)
            return item
    raise ErrorValidacion("Tarea inexistente en la checklist.")


def cambiar_estado(sesiones, sesion_id, herramienta, estado):
    """Mueve el estado de una herramienta sin afectar a las demas."""
    if herramienta not in HERRAMIENTAS:
        raise ErrorValidacion(f"Herramienta desconocida: {herramienta}")
    if estado not in ESTADOS_VALIDOS:
        raise ErrorValidacion(f"Estado invalido: {estado}")
    sesion = validar_sesion(sesiones, sesion_id)
    sesion["estados"][herramienta] = estado
    return sesion["estados"][herramienta]


def listar_historial(sesiones, sesion_id):
    """Devuelve copia del historial de mensajes sin modificarlo."""
    sesion = validar_sesion(sesiones, sesion_id)
    return [dict(m) for m in sesion["mensajes"]]


def construir_payload(sesiones, sesion_id):
    """Genera el payload de salida excluyendo anclas inactivas."""
    sesion = validar_sesion(sesiones, sesion_id)
    anclas_activas = {
        k: {"texto": v["texto"]}
        for k, v in sesion["anclas"].items()
        if v["activa"]
    }
    ultimo = sesion["mensajes"][-1] if sesion["mensajes"] else None
    return {
        "sesion_id": sesion["id"],
        "ultimo_mensaje": ultimo,
        "anclas_activas": anclas_activas,
        "tareas": [dict(t) for t in sesion["tareas"]],
        "estados": dict(sesion["estados"]),
    }


def exportar_json(sesiones, sesion_id):
    """Serializa la sesion completa a JSON legible."""
    sesion = validar_sesion(sesiones, sesion_id)
    return json.dumps(sesion, ensure_ascii=False, indent=2)


def demo():
    """Ejecuta un flujo completo de ejemplo y devuelve el payload final."""
    sesiones = {}
    ses_id = crear_sesion("Demo Prueba")["id"]
    sesiones[ses_id] = crear_sesion("Demo Prueba")
    agregar_mensaje(sesiones, ses_id, "usuario", "Hola, necesito diagnosticar.")
    agregar_mensaje(sesiones, ses_id, "bot", "Listo, reviso las anclas.")
    fijar_ancla(sesiones, ses_id, "contexto", "Diagnostico en curso", True)
    fijar_ancla(sesiones, ses_id, "resumen", "Resumen final pendiente", False)
    registrar_tarea(sesiones, ses_id, "Revisar logs", True)
    registrar_tarea(sesiones, ses_id, "Confirmar fix")
    cambiar_estado(sesiones, ses_id, "tool", "ok")
    cambiar_estado(sesiones, ses_id, "agent_tool", "busy")
    cambiar_estado(sesiones, ses_id, "llm_tool", "idle")
    return construir_payload(sesiones, ses_id)


if __name__ == "__main__":
    resultado = demo()
    print(json.dumps(resultado, ensure_ascii=False, indent=2))