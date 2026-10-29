"""
xray_chatbot.py — Módulo aislado de chatbot para prueba X-RAY.
Solo stdlib de Python 3. Sin servidor, sin sockets, sin eval.
Estado por sesión en memoria. Export/import JSON. Auditoría.
"""

from __future__ import annotations
import json
import re
import uuid
import copy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# --- Constantes de validación ---
MAX_LEN_MENSAJE = 4000
MAX_LEN_ANCLA = 200
MAX_LEN_ID_SESION = 64
PATRON_ID = re.compile(r"^[a-zA-Z0-9_\-]{1,64}$")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _nuevo_id(prefijo: str = "ses") -> str:
    return f"{prefijo}_{uuid.uuid4().hex[:12]}"


def validar_id(valor: str) -> bool:
    """Valida que un ID sea alfanumérico con guiones/bajos y longitud <=64."""
    return isinstance(valor, str) and bool(PATRON_ID.match(valor))


def validar_longitud(texto: str, maximo: int) -> bool:
    """Valida longitud de texto dentro del límite dado."""
    return isinstance(texto, str) and 0 < len(texto) <= maximo


# --- Almacén de sesiones (en memoria) ---
_SESIONES: Dict[str, Dict[str, Any]] = {}
_AUDITORIA: List[Dict[str, Any]] = []


def _registrar(evento: str, sesion_id: str, detalle: Any = None) -> None:
    _AUDITORIA.append({
        "ts": _now_iso(),
        "evento": evento,
        "sesion": sesion_id,
        "detalle": detalle,
    })


def crear_sesion(nombre: Optional[str] = None) -> Dict[str, Any]:
    """Crea una nueva sesión vacía y la devuelve."""
    sid = _nuevo_id("ses")
    sesion = {
        "id": sid,
        "nombre": nombre or sid,
        "creada": _now_iso(),
        "mensajes": [],
        "anclas": {},
        "pendientes": [],
        "tools": {"tools": True, "agente_tool": True, "llm_tool": True},
    }
    _SESIONES[sid] = sesion
    _registrar("crear_sesion", sid, {"nombre": sesion["nombre"]})
    return copy.deepcopy(sesion)


def obtener_sesion(sesion_id: str) -> Optional[Dict[str, Any]]:
    if not validar_id(sesion_id):
        return None
    sesion = _SESIONES.get(sesion_id)
    return copy.deepcopy(sesion) if sesion else None


def agregar_mensaje(sesion_id: str, rol: str, contenido: str) -> Dict[str, Any]:
    """Agrega un mensaje a la sesión. Valida rol, longitud y ID."""
    if rol not in ("usuario", "asistente", "sistema"):
        raise ValueError("rol inválido")
    if not validar_id(sesion_id):
        raise ValueError("sesion_id inválido")
    if not validar_longitud(contenido, MAX_LEN_MENSAJE):
        raise ValueError("contenido fuera de longitud")
    sesion = _SESIONES.get(sesion_id)
    if sesion is None:
        raise KeyError("sesión no existe")
    msg = {
        "id": _nuevo_id("msg"),
        "rol": rol,
        "contenido": contenido,
        "ts": _now_iso(),
    }
    sesion["mensajes"].append(msg)
    _registrar("agregar_mensaje", sesion_id, {"rol": rol, "msg_id": msg["id"]})
    return copy.deepcopy(msg)


def fijar_ancla(sesion_id: str, nombre: str, contenido: str, activo: bool = True) -> None:
    """Crea o actualiza un ancla de archivo con estado ON/OFF."""
    if not validar_id(sesion_id):
        raise ValueError("sesion_id inválido")
    if not validar_longitud(nombre, MAX_LEN_ANCLA):
        raise ValueError("nombre de ancla inválido")
    if not isinstance(contenido, str):
        raise ValueError("contenido debe ser str")
    sesion = _SESIONES.get(sesion_id)
    if sesion is None:
        raise KeyError("sesión no existe")
    sesion["anclas"][nombre] = {"activo": bool(activo), "contenido": contenido}
    _registrar("fijar_ancla", sesion_id, {"nombre": nombre, "activo": activo})


def toggle_ancla(sesion_id: str, nombre: str) -> bool:
    """Alterna el estado de un ancla. Devuelve el nuevo estado."""
    sesion = _SESIONES.get(sesion_id)
    if sesion is None or nombre not in sesion["anclas"]:
        raise KeyError("ancla no existe")
    sesion["anclas"][nombre]["activo"] = not sesion["anclas"][nombre]["activo"]
    estado = sesion["anclas"][nombre]["activo"]
    _registrar("toggle_ancla", sesion_id, {"nombre": nombre, "activo": estado})
    return estado


def agregar_pendiente(sesion_id: str, texto: str) -> Dict[str, Any]:
    if not validar_id(sesion_id):
        raise ValueError("sesion_id inválido")
    if not validar_longitud(texto, MAX_LEN_ANCLA):
        raise ValueError("texto de pendiente inválido")
    sesion = _SESIONES.get(sesion_id)
    if sesion is None:
        raise KeyError("sesión no existe")
    item = {"id": _nuevo_id("pen"), "texto": texto, "hecho": False}
    sesion["pendientes"].append(item)
    _registrar("agregar_pendiente", sesion_id, {"pendiente_id": item["id"]})
    return copy.deepcopy(item)


def marcar_pendiente(sesion_id: str, pendiente_id: str, hecho: bool) -> None:
    sesion = _SESIONES.get(sesion_id)
    if sesion is None:
        raise KeyError("sesión no existe")
    for p in sesion["pendientes"]:
        if p["id"] == pendiente_id:
            p["hecho"] = bool(hecho)
            _registrar("marcar_pendiente", sesion_id, {"pendiente_id": pendiente_id, "hecho": hecho})
            return
    raise KeyError("pendiente no existe")


def toggle_tool(sesion_id: str, tool: str) -> bool:
    """Alterna tools/agente_tool/llm_tool. Devuelve nuevo estado."""
    if tool not in ("tools", "agente_tool", "llm_tool"):
        raise ValueError("tool desconocida")
    sesion = _SESIONES.get(sesion_id)
    if sesion is None:
        raise KeyError("sesión no existe")
    sesion["tools"][tool] = not sesion["tools"][tool]
    _registrar("toggle_tool", sesion_id, {"tool": tool, "activo": sesion["tools"][tool]})
    return sesion["tools"][tool]


def construir_payload(sesion_id: str) -> Dict[str, Any]:
    """
    Construye el payload para enviar al modelo.
    REGLA: las anclas con activo=False NO aparecen en el payload.
    """
    sesion = _SESIONES.get(sesion_id)
    if sesion is None:
        raise KeyError("sesión no existe")
    anclas_activas = {
        k: v["contenido"] for k, v in sesion["anclas"].items() if v["activo"]
    }
    pendientes_abiertos = [p for p in sesion["pendientes"] if not p["hecho"]]
    return {
        "sesion_id": sesion_id,
        "mensajes": copy.deepcopy(sesion["mensajes"]),
        "anclas": anclas_activas,
        "pendientes_abiertos": copy.deepcopy(pendientes_abiertos),
        "tools": copy.deepcopy(sesion["tools"]),
        "generado": _now_iso(),
    }


def exportar_json(sesion_id: str) -> str:
    sesion = _SESIONES.get(sesion_id)
    if sesion is None:
        raise KeyError("sesión no existe")
    return json.dumps(sesion, ensure_ascii=False, indent=2)


def importar_json(texto: str) -> Dict[str, Any]:
    datos = json.loads(texto)
    sid = datos.get("id")
    if not validar_id(sid):
        raise ValueError("id inválido en JSON")
    _SESIONES[sid] = datos
    _registrar("importar_json", sid, None)
    return copy.deepcopy(datos)


def auditoria() -> List[Dict[str, Any]]:
    return list(_AUDITORIA)


# --- Pruebas manuales reproducibles (ejecutar en REPL o como script) ---
# 1) crear_sesion() devuelve dict con id que empieza por "ses_"
# 2) agregar_mensaje(sid, "usuario", "hola") agrega un mensaje y validar_longitud("x"*4001, 4000) es False
# 3) fijar_ancla(sid, "A", "data", activo=False); payload = construir_payload(sid); "A" NO está en payload["anclas"]
# 4) toggle_ancla(sid, "A") cambia a True; ahora construir_payload(sid)["anclas"]["A"] == "data"
# 5) toggle_tool(sid, "agente_tool") alterna; exportar_json + importar_json conserva el estado


if __name__ == "__main__":
    s = crear_sesion("demo")
    sid = s["id"]
    agregar_mensaje(sid, "usuario", "hola")
    fijar_ancla(sid, "archivo.py", "print(1)", activo=False)
    p = construir_payload(sid)
    assert "archivo.py" not in p["anclas"], "ancla OFF no debe aparecer"
    toggle_ancla(sid, "archivo.py")
    p2 = construir_payload(sid)
    assert p2["anclas"]["archivo.py"] == "print(1)"
    print("OK —", sid)
