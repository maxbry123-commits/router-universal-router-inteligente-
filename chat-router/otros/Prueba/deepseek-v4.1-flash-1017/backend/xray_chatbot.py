#!/usr/bin/env python3
"""Prototipo AISLADO de chatbot X-ray. Sin red, sin repo, solo Python 3 estandar."""

import json
import uuid
from datetime import datetime, timezone

ROLES_VALIDOS = ("user", "assistant", "sistema")
ESTADOS_TOOL = ("inactivo", "activo", "pendiente")
CLAVES_TOOL = ("tools", "agente_tool", "llm_tool")
PREFIJO_EXPORT = "xray_deepseek-v4.1-flash-1017"


class ErrorPrototipo(ValueError):
    """Error de validacion del prototipo."""


def _ahora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _nuevo_id(prefijo):
    return "{}_{}".format(prefijo, uuid.uuid4().hex[:8])


def _texto(valor, campo, maximo=4000):
    if not isinstance(valor, str):
        raise ErrorPrototipo("{} debe ser texto".format(campo))
    limpio = valor.strip()
    if not limpio:
        raise ErrorPrototipo("{} no puede estar vacio".format(campo))
    if len(limpio) > maximo:
        raise ErrorPrototipo("{} supera {} caracteres".format(campo, maximo))
    return limpio


def crear_sesion(titulo="Chat sin titulo"):
    return {
        "id": _nuevo_id("ses"),
        "titulo": _texto(titulo, "titulo", 120),
        "creada": _ahora(),
        "actualizada": _ahora(),
        "mensajes": [],
        "anclas": [],
        "checklist": [],
        "estados": {clave: "inactivo" for clave in CLAVES_TOOL},
    }


def _tocar(sesion):
    sesion["actualizada"] = _ahora()


def agregar_mensaje(sesion, rol, texto):
    if rol not in ROLES_VALIDOS:
        raise ErrorPrototipo("rol invalido: {}".format(rol))
    mensaje = {
        "id": _nuevo_id("msg"),
        "rol": rol,
        "texto": _texto(texto, "texto"),
        "ts": _ahora(),
    }
    sesion["mensajes"].append(mensaje)
    _tocar(sesion)
    return mensaje


def fijar_ancla(sesion, etiqueta, activa=True):
    nombre = _texto(etiqueta, "etiqueta", 80)
    for ancla in sesion["anclas"]:
        if ancla["etiqueta"].lower() == nombre.lower():
            ancla["activa"] = bool(activa)
            _tocar(sesion)
            return ancla
    ancla = {"id": _nuevo_id("anc"), "etiqueta": nombre, "activa": bool(activa)}
    sesion["anclas"].append(ancla)
    _tocar(sesion)
    return ancla


def alternar_ancla(sesion, ancla_id):
    for ancla in sesion["anclas"]:
        if ancla["id"] == ancla_id:
            ancla["activa"] = not ancla["activa"]
            _tocar(sesion)
            return ancla
    raise ErrorPrototipo("ancla inexistente: {}".format(ancla_id))


def anclas_activas(sesion):
    return [{"etiqueta": a["etiqueta"]} for a in sesion["anclas"] if a["activa"]]


def agregar_tarea(sesion, texto):
    tarea = {"id": _nuevo_id("tsk"), "texto": _texto(texto, "tarea", 200), "hecho": False}
    sesion["checklist"].append(tarea)
    _tocar(sesion)
    return tarea


def marcar_tarea(sesion, tarea_id, hecho=True):
    for tarea in sesion["checklist"]:
        if tarea["id"] == tarea_id:
            tarea["hecho"] = bool(hecho)
            _tocar(sesion)
            return tarea
    raise ErrorPrototipo("tarea inexistente: {}".format(tarea_id))


def fijar_estado(sesion, clave, estado):
    if clave not in CLAVES_TOOL:
        raise ErrorPrototipo("tool invalida: {}".format(clave))
    if estado not in ESTADOS_TOOL:
        raise ErrorPrototipo("estado invalido: {}".format(estado))
    sesion["estados"][clave] = estado
    _tocar(sesion)
    return sesion["estados"][clave]


def ciclo_estado(sesion, clave):
    actual = sesion["estados"].get(clave, "inactivo")
    return fijar_estado(sesion, clave, ESTADOS_TOOL[(ESTADOS_TOOL.index(actual) + 1) % 3])


def validar_sesion(sesion):
    problemas = []
    if not sesion.get("id"):
        problemas.append("sesion sin id")
    for clave in CLAVES_TOOL:
        if sesion.get("estados", {}).get(clave) not in ESTADOS_TOOL:
            problemas.append("estado invalido en {}".format(clave))
    for tarea in sesion.get("checklist", []):
        if not tarea.get("texto"):
            problemas.append("tarea sin texto: {}".format(tarea.get("id")))
    return problemas


def construir_payload(sesion, texto_usuario=None, max_mensajes=20):
    if texto_usuario is not None:
        agregar_mensaje(sesion, "user", texto_usuario)
    activas = anclas_activas(sesion)
    historial = sesion["mensajes"][-max_mensajes:]
    return {
        "namespace": PREFIJO_EXPORT,
        "sesion_id": sesion["id"],
        "titulo": sesion["titulo"],
        "anclas_activas": [a["etiqueta"] for a in activas],
        "estados": dict(sesion["estados"]),
        "tareas_pendientes": [t["texto"] for t in sesion["checklist"] if not t["hecho"]],
        "mensajes": [{"rol": m["rol"], "texto": m["texto"]} for m in historial],
        "total_mensajes": len(sesion["mensajes"]),
    }


def exportar_json(sesion, indent=2):
    problemas = validar_sesion(sesion)
    if problemas:
        raise ErrorPrototipo("sesion invalida: " + "; ".join(problemas))
    return json.dumps(
        {"prototipo": PREFIJO_EXPORT, "sesion": sesion},
        ensure_ascii=False,
        indent=indent,
        sort_keys=True,
    )


def resumen(sesion):
    return {
        "sesion": sesion["id"],
        "mensajes": len(sesion["mensajes"]),
        "anclas_on": len(anclas_activas(sesion)),
        "anclas_off": len(sesion["anclas"]) - len(anclas_activas(sesion)),
        "tareas_hechas": sum(1 for t in sesion["checklist"] if t["hecho"]),
        "tareas_total": len(sesion["checklist"]),
        "estados": dict(sesion["estados"]),
    }


def demo():
    sesion = crear_sesion("Prueba aislada")
    agregar_mensaje(sesion, "user", "Hola, prototipo aislado")
    agregar_mensaje(sesion, "assistant", "Respuesta local, sin red")
    fijar_ancla(sesion, "contexto-xray", True)
    fijar_ancla(sesion, "borrador-descartado", False)
    agregar_tarea(sesion, "Revisar payload")
    ciclo_estado(sesion, "llm_tool")
    payload = construir_payload(sesion, "Siguiente paso")
    assert all(a != "borrador-descartado" for a in payload["anclas_activas"])
    assert len(payload["mensajes"]) == 3
    return sesion, payload


if __name__ == "__main__":
    sesion_demo, payload_demo = demo()
    print(json.dumps(resumen(sesion_demo), ensure_ascii=False))
    print(json.dumps(payload_demo, ensure_ascii=False, indent=2))