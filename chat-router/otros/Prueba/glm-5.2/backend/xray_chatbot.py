"""
xray_chatbot.py - Prototipo de chatbot en memoria (sin servidores)
Modelo: glm-5.2 | Repo: router-universal-router-inteligente-
Estandar: Python 3, solo biblioteca estandar.
Contrato comun: crear_sesion / agregar_mensaje / fijar_ancla / construir_payload
"""

import json
import uuid
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Excepciones
# ---------------------------------------------------------------------------

class XRayError(Exception):
    """Excepcion base del modulo xray."""

class SesionNoExiste(XRayError):
    """Se intento operar sobre una sesion inexistente."""

class AnclaInvalida(XRayError):
    """El id de ancla no es valido."""

class MensajeInvalido(XRayError):
    """El mensaje no cumple validacion defensiva."""

# ---------------------------------------------------------------------------
# Validadores defensivos
# ---------------------------------------------------------------------------

_ROL_VALIDO = {"usuario", "asistente", "sistema"}
_ANCLAS_PERMITIDAS = {"contexto", "resumen", "instrucciones", "memoria"}
_MAX_CONTENT = 5000


def _validar_texto(texto, campo):
    """Valida y sanitiza un texto de entrada."""
    if not isinstance(texto, str):
        raise MensajeInvalido(f"{campo} debe ser str, recibio {type(texto).__name__}")
    limpio = texto.strip()
    if not limpio:
        raise MensajeInvalido(f"{campo} no puede estar vacio")
    if len(limpio) > _MAX_CONTENT:
        raise MensajeInvalido(f"{campo} excede {_MAX_CONTENT} caracteres")
    return limpio


def _validar_id_sesion(sid):
    if not isinstance(sid, str) or not sid.strip():
        raise SesionNoExiste("id de sesion invalido")
    return sid.strip()


# ---------------------------------------------------------------------------
# Modelo de datos
# ---------------------------------------------------------------------------

class Ancla:
    """Ancla contextual activable/desactivable."""
    __slots__ = ("id", "texto", "activa")

    def __init__(self, id_ancla, texto, activa=True):
        if id_ancla not in _ANCLAS_PERMITIDAS:
            raise AnclaInvalida(
                f"Ancla '{id_ancla}' no permitida. Validas: {_ANCLAS_PERMITIDAS}")
        self.id = id_ancla
        self.texto = _validar_texto(texto, "texto_ancla")
        self.activa = bool(activa)

    def to_dict(self):
        return {"id": self.id, "texto": self.texto, "activa": self.activa}


class Mensaje:
    """Mensaje individual del historial."""
    __slots__ = ("id", "rol", "contenido", "timestamp")

    def __init__(self, rol, contenido):
        if rol not in _ROL_VALIDO:
            raise MensajeInvalido(f"Rol '{rol}' invalido. Validos: {_ROL_VALIDO}")
        self.id = uuid.uuid4().hex[:12]
        self.rol = rol
        self.contenido = _validar_texto(contenido, "contenido")
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self):
        return {"id": self.id, "rol": self.rol,
                "contenido": self.contenido, "ts": self.timestamp}


class ChecklistItem:
    """Item de checklist de tareas."""
    __slots__ = ("id", "texto", "hecho")

    def __init__(self, texto, hecho=False):
        self.id = uuid.uuid4().hex[:8]
        self.texto = _validar_texto(texto, "item_checklist")
        self.hecho = bool(hecho)

    def to_dict(self):
        return {"id": self.id, "texto": self.texto, "hecho": self.hecho}


# ---------------------------------------------------------------------------
# Sesion de chat
# ---------------------------------------------------------------------------

class Sesion:
    """Sesion de chat en memoria con historial, anclas, checklist y flags."""

    def __init__(self, sid):
        self.id = _validar_id_sesion(sid)
        self.mensajes = []
        self.anclas = {}
        self.checklist = []
        self.flags = {"tools": False, "agente_tool": False, "llm_tool": False}

    def agregar_mensaje(self, rol, contenido):
        msg = Mensaje(rol, contenido)
        self.mensajes.append(msg)
        return msg

    def fijar_ancla(self, id_ancla, texto, activa=True):
        ancla = Ancla(id_ancla, texto, activa)
        self.anclas[id_ancla] = ancla
        return ancla

    def toggle_ancla(self, id_ancla):
        if id_ancla not in self.anclas:
            raise AnclaInvalida(f"Ancla '{id_ancla}' no existe en la sesion")
        self.anclas[id_ancla].activa = not self.anclas[id_ancla].activa
        return self.anclas[id_ancla].activa

    def agregar_checklist(self, texto):
        item = ChecklistItem(texto)
        self.checklist.append(item)
        return item

    def marcar_checklist(self, item_id, hecho=True):
        for item in self.checklist:
            if item.id == item_id:
                item.hecho = bool(hecho)
                return True
        return False

    def set_flag(self, nombre, valor):
        if nombre not in self.flags:
            raise XRayError(f"Flag '{nombre}' no existe. Validos: {list(self.flags)}")
        self.flags[nombre] = bool(valor)

    def to_dict(self):
        return {
            "id": self.id,
            "mensajes": [m.to_dict() for m in self.mensajes],
            "anclas": [a.to_dict() for a in self.anclas.values()],
            "checklist": [c.to_dict() for c in self.checklist],
            "flags": dict(self.flags),
        }

    def to_json(self):
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Orquestador de sesiones (en memoria)
# ---------------------------------------------------------------------------

class XRayChatbot:
    """Orquestador de sesiones de chat en memoria."""

    def __init__(self):
        self.sesiones = {}

    def crear_sesion(self, sid=None):
        sid = _validar_id_sesion(sid) if sid else f"ses_{uuid.uuid4().hex[:8]}"
        if sid in self.sesiones:
            raise XRayError(f"Sesion '{sid}' ya existe")
        ses = Sesion(sid)
        self.sesiones[sid] = ses
        return ses

    def obtener_sesion(self, sid):
        sid = _validar_id_sesion(sid)
        if sid not in self.sesiones:
            raise SesionNoExiste(f"Sesion '{sid}' no encontrada")
        return self.sesiones[sid]

    def agregar_mensaje(self, sid, rol, contenido):
        return self.obtener_sesion(sid).agregar_mensaje(rol, contenido)

    def fijar_ancla(self, sid, id_ancla, texto, activa=True):
        return self.obtener_sesion(sid).fijar_ancla(id_ancla, texto, activa)

    def construir_payload(self, sid):
        """Construye payload excluyendo anclas OFF.
        El historial completo se conserva; las anclas inactivas se omiten."""
        ses = self.obtener_sesion(sid)
        anclas_on = [a.to_dict() for a in ses.anclas.values() if a.activa]
        payload = {
            "sesion": ses.id,
            "anclas": anclas_on,
            "flags": dict(ses.flags),
            "mensajes": [m.to_dict() for m in ses.mensajes],
            "checklist": [c.to_dict() for c in ses.checklist],
            "total_mensajes": len(ses.mensajes),
            "anclas_activas": len(anclas_on),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        json.dumps(payload, ensure_ascii=False)  # valida serializacion
        return payload

    def listar_sesiones(self):
        return list(self.sesiones.keys())

    def serializar_todo(self):
        return json.dumps(
            {sid: s.to_dict() for sid, s in self.sesiones.items()},
            ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Tests manuales (ejecutar: python xray_chatbot.py)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    bot = XRayChatbot()

    # 1. Crear sesion
    s = bot.crear_sesion("test-001")
    assert s.id == "test-001"
    print(f"[OK] Sesion creada: {s.id}")

    # 2. Agregar mensajes
    bot.agregar_mensaje("test-001", "usuario", "Hola, necesito ayuda")
    bot.agregar_mensaje("test-001", "asistente", "Claro, en que puedo ayudarte")
    assert len(s.mensajes) == 2
    print(f"[OK] Mensajes: {len(s.mensajes)}")

    # 3. Fijar anclas (una ON, una OFF)
    bot.fijar_ancla("test-001", "contexto", "Proyecto X-Ray", activa=True)
    bot.fijar_ancla("test-001", "memoria", "Recordar preferencias", activa=False)
    assert len(s.anclas) == 2
    print(f"[OK] Anclas: {len(s.anclas)} (1 ON, 1 OFF)")

    # 4. Construir payload (debe excluir anclas OFF)
    payload = bot.construir_payload("test-001")
    assert len(payload["anclas"]) == 1
    assert payload["anclas"][0]["id"] == "contexto"
    assert payload["total_mensajes"] == 2
    print(f"[OK] Payload: anclas_activas={payload['anclas_activas']}, "
          f"mensajes={payload['total_mensajes']}")

    # 5. Toggle ancla OFF -> ON
    s.toggle_ancla("memoria")
    payload2 = bot.construir_payload("test-001")
    assert len(payload2["anclas"]) == 2
    print(f"[OK] Toggle memoria ON: anclas_activas={payload2['anclas_activas']}")

    # 6. Checklist
    s.agregar_checklist("Revisar payload")
    s.agregar_checklist("Validar anclas")
    s.marcar_checklist(s.checklist[0].id, True)
    payload3 = bot.construir_payload("test-001")
    assert payload3["checklist"][0]["hecho"] is True
    print(f"[OK] Checklist: {len(payload3['checklist'])} items, 1 hecho")

    # 7. Flags
    s.set_flag("tools", True)
    s.set_flag("llm_tool", True)
    payload4 = bot.construir_payload("test-001")
    assert payload4["flags"]["tools"] is True
    assert payload4["flags"]["agente_tool"] is False
    print(f"[OK] Flags: {payload4['flags']}")

    # 8. Serializacion JSON valida
    json_str = s.to_json()
    parsed = json.loads(json_str)
    assert parsed["id"] == "test-001"
    print(f"[OK] JSON valido ({len(json_str)} bytes)")

    # 9. Validacion defensiva: contenido vacio
    try:
        bot.agregar_mensaje("test-001", "usuario", "")
        assert False
    except MensajeInvalido:
        print("[OK] Contenido vacio rechazado")

    # 10. Validacion defensiva: sesion inexistente
    try:
        bot.construir_payload("no-existe")
        assert False
    except SesionNoExiste:
        print("[OK] Sesion inexistente rechazada")

    # 11. Validacion: ancla no permitida
    try:
        bot.fijar_ancla("test-001", "desconocida", "x")
        assert False
    except AnclaInvalida:
        print("[OK] Ancla invalida rechazada")

    # 12. Serializar todo
    todo = bot.serializar_todo()
    assert "test-001" in todo
    print(f"[OK] Serializacion global ({len(todo)} bytes)")

    print(f"\n[FIN] {len(bot.sesiones)} sesion(es), "
          f"{payload4['total_mensajes']} msgs, "
          f"{payload4['anclas_activas']} anclas ON")
