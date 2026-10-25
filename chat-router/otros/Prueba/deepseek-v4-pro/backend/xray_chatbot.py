#!/usr/bin/env python3
"""
X-RAY Chatbot Backend — Python 3 stdlib
Prototipo de chat en memoria SIN servidores.
Soporta sesiones, mensajes, anclas ON/OFF, checklist, flags y serialización JSON.
"""

import json
import time
import uuid
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
ANCLAS_DEFAULT = {
    "contexto": True,
    "personalidad": True,
    "restricciones": False,
    "memoria": True,
    "historial": True,
}

FLAGS_DEFAULT = {
    "tools": False,
    "agente_tool": False,
    "llm_tool": False,
}


# ---------------------------------------------------------------------------
# Validación defensiva
# ---------------------------------------------------------------------------
def _validar_str(val, campo: str) -> str:
    if not isinstance(val, str) or not val.strip():
        raise ValueError(f"{campo} debe ser str no vacío")
    return val.strip()


def _validar_bool(val, campo: str) -> bool:
    if not isinstance(val, bool):
        raise ValueError(f"{campo} debe ser bool")
    return val


def _validar_dict(val, campo: str) -> dict:
    if not isinstance(val, dict):
        raise ValueError(f"{campo} debe ser dict")
    return val


def _validar_list(val, campo: str) -> list:
    if not isinstance(val, list):
        raise ValueError(f"{campo} debe ser list")
    return val


# ---------------------------------------------------------------------------
# Sesion
# ---------------------------------------------------------------------------
class Sesion:
    """Una sesión de chat con su historial, anclas, checklist y flags."""
    def __init__(self, nombre: str = "", sid: Optional[str] = None):
        self.sid = sid if sid else uuid.uuid4().hex[:12]
        self.nombre = nombre or f"sesion-{self.sid[:6]}"
        self.mensajes: list[dict] = []
        self.anclas: dict[str, bool] = dict(ANCLAS_DEFAULT)
        self.checklist: list[dict] = []  # [{"id":..., "texto":..., "hecho":bool}]
        self.flags: dict[str, bool] = dict(FLAGS_DEFAULT)
        self.creado = time.time()
        self._contador_msg = 0

    # --- Mensajes ---
    def agregar_mensaje(self, rol: str, contenido: str) -> dict:
        """Agrega un mensaje validado al historial."""
        _validar_str(rol, "rol")
        _validar_str(contenido, "contenido")
        if rol not in ("usuario", "sistema", "asistente"):
            raise ValueError("rol debe ser usuario|sistema|asistente")
        msg = {
            "id": self._contador_msg,
            "rol": rol,
            "contenido": contenido,
            "ts": time.time(),
        }
        self._contador_msg += 1
        self.mensajes.append(msg)
        return msg

    # --- Anclas ---
    def fijar_ancla(self, nombre: str, activa: bool) -> bool:
        """Activa/desactiva un ancla. Retorna el nuevo estado."""
        _validar_str(nombre, "nombre")
        _validar_bool(activa, "activa")
        if nombre not in self.anclas:
            raise KeyError(f"Ancla no existe: {nombre}")
        self.anclas[nombre] = activa
        return activa

    def anclas_activas(self) -> dict[str, bool]:
        """Retorna solo las anclas activas."""
        return {k: v for k, v in self.anclas.items() if v}

    def anclas_inactivas(self) -> dict[str, bool]:
        """Retorna solo las anclas inactivas."""
        return {k: v for k, v in self.anclas.items() if not v}

    # --- Checklist ---
    def agregar_tarea(self, texto: str) -> dict:
        """Agrega tarea a checklist."""
        _validar_str(texto, "texto")
        tarea = {
            "id": uuid.uuid4().hex[:8],
            "texto": texto,
            "hecho": False,
        }
        self.checklist.append(tarea)
        return tarea

    def marcar_tarea(self, tid: str, hecho: bool) -> dict:
        """Marca/desmarca tarea por id."""
        _validar_str(tid, "tid")
        _validar_bool(hecho, "hecho")
        for t in self.checklist:
            if t["id"] == tid:
                t["hecho"] = hecho
                return t
        raise KeyError(f"Tarea no encontrada: {tid}")

    def quitar_tarea(self, tid: str) -> None:
        """Elimina tarea por id."""
        _validar_str(tid, "tid")
        self.checklist = [t for t in self.checklist if t["id"] != tid]

    # --- Flags ---
    def fijar_flag(self, flag: str, valor: bool) -> bool:
        """Fija un flag (tools|agente_tool|llm_tool)."""
        _validar_str(flag, "flag")
        _validar_bool(valor, "valor")
        if flag not in self.flags:
            raise KeyError(f"Flag no existe: {flag}")
        self.flags[flag] = valor
        return valor

    # --- Payload ---
    def construir_payload(self, mensaje_actual: str = "") -> dict:
        """
        Construye payload para el modelo, EXCLUYENDO anclas OFF.
        El payload incluye: mensajes, anclas activas, checklist y flags.
        """
        _validar_str(mensaje_actual, "mensaje_actual")
        activas = self.anclas_activas()
        payload: dict[str, Any] = {
            "sid": self.sid,
            "nombre": self.nombre,
            "flags": dict(self.flags),
            "checklist": list(self.checklist),
            "anclas_activas": activas,
            "historial": list(self.mensajes),
            "mensaje_actual": mensaje_actual,
            "ts": time.time(),
        }
        # Construir sección de contexto combinado solo con anclas ON
        contexto_partes = []
        if activas.get("contexto"):
            contexto_partes.append("[CONTEXTO ACTIVO]")
        if activas.get("personalidad"):
            contexto_partes.append("Eres un asistente X-RAY conciso.")
        if activas.get("restricciones"):
            contexto_partes.append("Responde en español, máximo 3 frases.")
        if activas.get("memoria"):
            contexto_partes.append("Recuerda el historial previo.")
        if activas.get("historial"):
            contexto_partes.append(
                f"Historial ({len(self.mensajes)} mensajes previos)."
            )
        payload["contexto_combinado"] = "\n".join(contexto_partes)
        return payload

    # --- Serialización ---
    def a_dict(self) -> dict:
        return {
            "sid": self.sid,
            "nombre": self.nombre,
            "mensajes": self.mensajes,
            "anclas": self.anclas,
            "checklist": self.checklist,
            "flags": self.flags,
            "creado": self.creado,
            "_contador_msg": self._contador_msg,
        }

    @classmethod
    def desde_dict(cls, data: dict) -> "Sesion":
        _validar_dict(data, "data")
        s = cls(nombre=data.get("nombre", ""), sid=data.get("sid"))
        s.mensajes = data.get("mensajes", [])
        s.anclas = data.get("anclas", dict(ANCLAS_DEFAULT))
        s.checklist = data.get("checklist", [])
        s.flags = data.get("flags", dict(FLAGS_DEFAULT))
        s.creado = data.get("creado", time.time())
        s._contador_msg = data.get("_contador_msg", 0)
        return s

    def to_json(self) -> str:
        return json.dumps(self.a_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, raw: str) -> "Sesion":
        return cls.desde_dict(json.loads(raw))


# ---------------------------------------------------------------------------
# Gestor
# ---------------------------------------------------------------------------
class XRayChatbot:
    """Gestor principal de sesiones (en memoria)."""
    def __init__(self):
        self.sesiones: dict[str, Sesion] = {}

    def crear_sesion(self, nombre: str = "") -> Sesion:
        """Crea una nueva sesión y la registra."""
        ses = Sesion(nombre=nombre)
        self.sesiones[ses.sid] = ses
        return ses

    def obtener_sesion(self, sid: str) -> Sesion:
        """Obtiene sesión por id; lanza KeyError si no existe."""
        _validar_str(sid, "sid")
        if sid not in self.sesiones:
            raise KeyError(f"Sesión no encontrada: {sid}")
        return self.sesiones[sid]

    def listar_sesiones(self) -> list[dict]:
        """Lista resumen de sesiones."""
        return [
            {"sid": s.sid, "nombre": s.nombre, "n_mensajes": len(s.mensajes)}
            for s in self.sesiones.values()
        ]

    def eliminar_sesion(self, sid: str) -> None:
        """Elimina una sesión."""
        _validar_str(sid, "sid")
        self.sesiones.pop(sid, None)

    def exportar_todo(self) -> str:
        """Serializa todas las sesiones a JSON."""
        data = {sid: s.a_dict() for sid, s in self.sesiones.items()}
        return json.dumps(data, ensure_ascii=False, indent=2)

    def importar_todo(self, raw: str) -> int:
        """Carga sesiones desde JSON. Retorna cantidad cargada."""
        data = json.loads(raw)
        n = 0
        for sid, sdata in data.items():
            self.sesiones[sid] = Sesion.desde_dict(sdata)
            n += 1
        return n


# ===========================================================================
# TESTS MANUALES (ejecutar con: python xray_chatbot.py)
# ===========================================================================
if __name__ == "__main__":
    print("=== TEST 1: Crear sesión y agregar mensajes ===")
    bot = XRayChatbot()
    s = bot.crear_sesion("prueba-1")
    s.agregar_mensaje("usuario", "Hola, ¿cómo estás?")
    s.agregar_mensaje("asistente", "¡Bien! ¿En qué te ayudo?")
    assert len(s.mensajes) == 2, "Fallo: deben ser 2 mensajes"
    print(f"  OK — {len(s.mensajes)} mensajes en sesión {s.sid}")

    print("=== TEST 2: Anclas ON/OFF y payload ===")
    s.fijar_ancla("restricciones", True)
    s.fijar_ancla("personalidad", False)
    payload = s.construir_payload("mensaje de prueba")
    assert "restricciones" in payload["anclas_activas"], "Fallo: restricciones ON"
    assert "personalidad" not in payload["anclas_activas"], "Fallo: personalidad OFF"
    assert "Responde en español" in payload["contexto_combinado"], "Fallo: restriccion en contexto"
    assert "asistente X-RAY" not in payload["contexto_combinado"], "Fallo: personalidad excluida"
    print(f"  OK — Anclas activas: {list(payload['anclas_activas'].keys())}")

    print("=== TEST 3: Checklist ===")
    t1 = s.agregar_tarea("Revisar payload")
    t2 = s.agregar_tarea("Validar JSON")
    s.marcar_tarea(t1["id"], True)
    assert s.checklist[0]["hecho"] is True
    assert s.checklist[1]["hecho"] is False
    print(f"  OK — Checklist: {[(t['texto'], t['hecho']) for t in s.checklist]}")

    print("=== TEST 4: Flags ===")
    s.fijar_flag("tools", True)
    s.fijar_flag("llm_tool", True)
    assert s.flags["tools"] is True
    assert s.flags["agente_tool"] is False
    payload2 = s.construir_payload("test flags")
    assert payload2["flags"]["tools"] is True
    assert payload2["flags"]["agente_tool"] is False
    print(f"  OK — Flags: {s.flags}")

    print("=== TEST 5: Serialización JSON ida y vuelta ===")
    js = s.to_json()
    s2 = Sesion.from_json(js)
    assert s2.sid == s.sid
    assert len(s2.mensajes) == len(s.mensajes)
    assert s2.anclas == s.anclas
    assert s2.checklist == s.checklist
    assert s2.flags == s.flags
    print(f"  OK — Serialización: {len(js)} bytes, ida y vuelta coherente")

    print("=== TEST 6: Validación defensiva ===")
    try:
        s.agregar_mensaje("", "vacio")
        assert False, "Debió lanzar ValueError"
    except ValueError:
        print("  OK — ValueError por rol vacío")

    try:
        s.fijar_ancla("inexistente", True)
        assert False, "Debió lanzar KeyError"
    except KeyError:
        print("  OK — KeyError por ancla inexistente")

    try:
        s.fijar_flag("flag_falso", True)
        assert False, "Debió lanzar KeyError"
    except KeyError:
        print("  OK — KeyError por flag inexistente")

    print("=== TEST 7: Exportar/Importar todas las sesiones ===")
    bot.crear_sesion("extra")
    raw = bot.exportar_todo()
    bot2 = XRayChatbot()
    n = bot2.importar_todo(raw)
    assert n == 2, f"Fallo: esperaba 2 sesiones, cargadas {n}"
    print(f"  OK — {n} sesiones exportadas/importadas")

    print("\n✅ TODOS LOS TESTS PASARON")