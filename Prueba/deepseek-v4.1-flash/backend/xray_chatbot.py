"""xray_chatbot.py - Prototipo AISLADO de chatbot con anclas, tareas y estados.
Solo biblioteca estandar de Python 3. Sin red, sin imports del repositorio.
Namespace local: xray_deepseek-v4.1-flash
"""
from __future__ import annotations

import datetime
import json
import uuid

NAMESPACE = "xray_deepseek-v4.1-flash"
ROLES_VALIDOS = ("usuario", "asistente")
ESTADOS_TOOL = ("tool", "agente_tool", "llm_tool")
LARGO_MAX_MENSAJE = 4000
LARGO_MAX_TITULO = 80


class ErrorPrototipo(ValueError):
    """Error de validacion del prototipo aislado."""


def _ahora():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def _id(prefijo):
    return "{}-{}".format(prefijo, uuid.uuid4().hex[:8])


def _texto(valor, campo, largo_max):
    if not isinstance(valor, str):
        raise ErrorPrototipo("{} debe ser texto".format(campo))
    limpio = valor.strip()
    if not limpio:
        raise ErrorPrototipo("{} no puede estar vacio".format(campo))
    if len(limpio) > largo_max:
        raise ErrorPrototipo("{} supera {} caracteres".format(campo, largo_max))
    return limpio


def crear_sesion(titulo="Nueva sesion"):
    """Crea una sesion nueva e independiente del sistema real."""
    return {
        "namespace": NAMESPACE,
        "id": _id("ses"),
        "titulo": _texto(titulo, "titulo", LARGO_MAX_TITULO),
        "creada": _ahora(),
        "mensajes": [],
        "anclas": {},
        "tareas": [],
        "estados": dict.fromkeys(ESTADOS_TOOL, True),
        "historial": [],
    }


def validar_sesion(sesion):
    """Devuelve la lista de errores encontrados; vacia si la sesion es valida."""
    if not isinstance(sesion, dict):
        return ["sesion debe ser un diccionario"]
    errores = []
    if sesion.get("namespace") != NAMESPACE:
        errores.append("namespace distinto de {}".format(NAMESPACE))
    for clave in ("id", "titulo", "creada"):
        if not sesion.get(clave):
            errores.append("falta el campo {}".format(clave))
    for clave in ("mensajes", "tareas", "historial"):
        if not isinstance(sesion.get(clave), list):
            errores.append("{} debe ser una lista".format(clave))
    if not isinstance(sesion.get("anclas"), dict):
        errores.append("anclas debe ser un diccionario")
    for nombre, activa in sesion.get("anclas", {}).items():
        if not isinstance(nombre, str) or not isinstance(activa, bool):
            errores.append("ancla invalida: {}".format(nombre))
    for clave in ESTADOS_TOOL:
        if not isinstance(sesion.get("estados", {}).get(clave), bool):
            errores.append("estado {} debe ser booleano".format(clave))
    return errores


def agregar_mensaje(sesion, rol, texto, registrar_historial=True):
    """Anade un mensaje conservando el historial de la sesion."""
    if rol not in ROLES_VALIDOS:
        raise ErrorPrototipo("rol invalido: {}".format(rol))
    mensaje = {
        "id": _id("msg"),
        "rol": rol,
        "texto": _texto(texto, "texto", LARGO_MAX_MENSAJE),
        "creado": _ahora(),
    }
    sesion["mensajes"].append(mensaje)
    if registrar_historial:
        sesion["historial"].append({"evento": "mensaje", "id": mensaje["id"], "rol": rol})
    return mensaje


def fijar_ancla(sesion, nombre, activa=True):
    """Fija el estado de un ancla (activa o inactiva)."""
    clave = _texto(nombre, "ancla", 60)
    if not isinstance(activa, bool):
        raise ErrorPrototipo("activa debe ser booleano")
    sesion["anclas"][clave] = activa
    sesion["historial"].append({"evento": "ancla", "ancla": clave, "activa": activa})
    return sesion["anclas"]


def alternar_ancla(sesion, nombre):
    if nombre not in sesion["anclas"]:
        raise ErrorPrototipo("ancla inexistente: {}".format(nombre))
    return fijar_ancla(sesion, nombre, not sesion["anclas"][nombre])


def anclas_activas(sesion):
    return sorted(n for n, activa in sesion["anclas"].items() if activa)


def anclas_inactivas(sesion):
    return sorted(n for n, activa in sesion["anclas"].items() if not activa)


def agregar_tarea(sesion, texto):
    tarea = {"id": _id("tar"), "texto": _texto(texto, "tarea", 200), "hecha": False}
    sesion["tareas"].append(tarea)
    sesion["historial"].append({"evento": "tarea_alta", "id": tarea["id"]})
    return tarea


def marcar_tarea(sesion, id_tarea, hecha=True):
    if not isinstance(hecha, bool):
        raise ErrorPrototipo("hecha debe ser booleano")
    for tarea in sesion["tareas"]:
        if tarea["id"] == id_tarea:
            tarea["hecha"] = hecha
            sesion["historial"].append({"evento": "tarea_estado", "id": id_tarea, "hecha": hecha})
            return tarea
    raise ErrorPrototipo("tarea inexistente: {}".format(id_tarea))


def fijar_estado(sesion, nombre, activo):
    """Estados independientes para tool, agente_tool y llm_tool."""
    if nombre not in ESTADOS_TOOL:
        raise ErrorPrototipo("estado desconocido: {}".format(nombre))
    if not isinstance(activo, bool):
        raise ErrorPrototipo("activo debe ser booleano")
    sesion["estados"][nombre] = activo
    sesion["historial"].append({"evento": "estado", "nombre": nombre, "activo": activo})
    return sesion["estados"]


def construir_payload(sesion, mensaje_usuario=None):
    """Construye el payload del prototipo; nunca incluye anclas inactivas."""
    errores = validar_sesion(sesion)
    if errores:
        raise ErrorPrototipo("; ".join(errores))
    if mensaje_usuario is not None:
        agregar_mensaje(sesion, "usuario", mensaje_usuario)
    payload = {
        "namespace": sesion["namespace"],
        "sesion": sesion["id"],
        "titulo": sesion["titulo"],
        "anclas": anclas_activas(sesion),
        "tareas": [dict(t) for t in sesion["tareas"]],
        "estados": dict(sesion["estados"]),
        "mensajes": [dict(m) for m in sesion["mensajes"]],
        "historial_total": len(sesion["historial"]),
    }
    if set(payload["anclas"]) & set(anclas_inactivas(sesion)):
        raise ErrorPrototipo("el payload contiene anclas inactivas")
    return payload


def exportar_json(sesion, indent=2):
    return json.dumps(construir_payload(sesion), ensure_ascii=False, indent=indent)


if __name__ == "__main__":
    demo = crear_sesion("Demo aislada")
    fijar_ancla(demo, "contexto_proyecto", True)
    fijar_ancla(demo, "borrador_antiguo", False)
    agregar_tarea(demo, "Revisar prototipo")
    agregar_mensaje(demo, "usuario", "Hola prototipo")
    agregar_mensaje(demo, "asistente", "Sesion aislada lista")
    fijar_estado(demo, "agente_tool", False)
    print(exportar_json(demo))