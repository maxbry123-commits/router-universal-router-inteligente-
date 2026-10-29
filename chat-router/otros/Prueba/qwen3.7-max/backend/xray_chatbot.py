"""
XRay Chatbot Backend — Módulo aislado Python 3 stdlib.
Autor: qwen3.7-max | Contrato X-RAY.
Sin servidor, sin sockets, sin eval, sin secretos.
Estado por sesión en memoria; export/import JSON puro.
"""

import json
import uuid
import time
from typing import Dict, List, Optional, Any


class XRayChatbot:
    """Motor conversacional aislado con anclas, pendientes y permisos."""

    VERSION = "1.0.0"
    MAX_MSG_LEN = 4000
    MAX_ID_LEN = 64

    def __init__(self) -> None:
        self.sesiones: Dict[str, Dict[str, Any]] = {}
        self.auditoria: List[Dict[str, Any]] = []

    # ---------- Sesiones ----------
    def crear_sesion(self, nombre: str = "default") -> str:
        sid = str(uuid.uuid4())[:12]
        self.sesiones[sid] = {
            "id": sid,
            "nombre": nombre[:40],
            "creada": time.time(),
            "mensajes": [],
            "ancoras": {},
            "pendientes": [],
            "permisos": {"tools": True, "agente_tool": True, "llm_tool": True},
        }
        self._auditar("crear_sesion", sid)
        return sid

    def listar_sesiones(self) -> List[str]:
        return list(self.sesiones.keys())

    # ---------- Validación ----------
    def _validar_id(self, sid: str) -> bool:
        return isinstance(sid, str) and 1 <= len(sid) <= self.MAX_ID_LEN and sid in self.sesiones

    def _validar_texto(self, texto: str) -> bool:
        return isinstance(texto, str) and 1 <= len(texto) <= self.MAX_MSG_LEN

    # ---------- Mensajes ----------
    def agregar_mensaje(self, sid: str, rol: str, texto: str) -> Optional[Dict[str, Any]]:
        if not self._validar_id(sid) or not self._validar_texto(texto):
            return None
        if rol not in ("user", "assistant", "system"):
            return None
        msg = {"id": str(uuid.uuid4())[:8], "rol": rol, "texto": texto, "ts": time.time()}
        self.sesiones[sid]["mensajes"].append(msg)
        self._auditar("agregar_mensaje", sid, mid=msg["id"])
        return msg

    # ---------- Anclas ----------
    def fijar_ancla(self, sid: str, nombre: str, contenido: str, activa: bool = True) -> bool:
        if not self._validar_id(sid) or not nombre:
            return False
        self.sesiones[sid]["ancoras"][nombre] = {
            "contenido": contenido,
            "activa": bool(activa),
            "ts": time.time(),
        }
        self._auditar("fijar_ancla", sid, ancla=nombre, activa=activa)
        return True

    def toggle_ancla(self, sid: str, nombre: str) -> Optional[bool]:
        if not self._validar_id(sid):
            return None
        ancla = self.sesiones[sid]["ancoras"].get(nombre)
        if ancla is None:
            return None
        ancla["activa"] = not ancla["activa"]
        self._auditar("toggle_ancla", sid, ancla=nombre, activa=ancla["activa"])
        return ancla["activa"]

    # ---------- Pendientes ----------
    def pendientes(self, sid: str, accion: str = "listar",
                   texto: str = "", idx: int = -1) -> Any:
        if not self._validar_id(sid):
            return None
        lista = self.sesiones[sid]["pendientes"]
        if accion == "listar":
            return lista
        if accion == "agregar" and texto:
            item = {"id": str(uuid.uuid4())[:6], "texto": texto, "hecho": False}
            lista.append(item)
            self._auditar("pend_agregar", sid, item=item["id"])
            return item
        if accion == "marcar" and 0 <= idx < len(lista):
            lista[idx]["hecho"] = not lista[idx]["hecho"]
            self._auditar("pend_marcar", sid, idx=idx, hecho=lista[idx]["hecho"])
            return lista[idx]
        return None

    # ---------- Permisos ----------
    def set_permiso(self, sid: str, clave: str, valor: bool) -> bool:
        if not self._validar_id(sid):
            return False
        if clave not in ("tools", "agente_tool", "llm_tool"):
            return False
        self.sesiones[sid]["permisos"][clave] = bool(valor)
        self._auditar("set_permiso", sid, clave=clave, valor=valor)
        return True

    # ---------- Payload ----------
    def construir_payload(self, sid: str) -> Optional[Dict[str, Any]]:
        """Construye el payload de salida. Excluye anclas con activa=False."""
        if not self._validar_id(sid):
            return None
        ses = self.sesiones[sid]
        anc = {k: v["contenido"] for k, v in ses["ancoras"].items() if v["activa"]}
        return {
            "sesion": sid,
            "mensajes": ses["mensajes"],
            "ancoras_activas": anc,
            "permisos": dict(ses["permisos"]),
            "pendientes": ses["pendientes"],
        }

    # ---------- Export / Import ----------
    def exportar_json(self, sid: str) -> Optional[str]:
        if not self._validar_id(sid):
            return None
        return json.dumps(self.sesiones[sid], indent=2, default=str)

    def importar_json(self, data_json: str) -> Optional[str]:
        try:
            data = json.loads(data_json)
        except (json.JSONDecodeError, TypeError):
            return None
        sid = data.get("id")
        if not isinstance(sid, str) or len(sid) > self.MAX_ID_LEN:
            return None
        self.sesiones[sid] = data
        self._auditar("importar", sid)
        return sid

    # ---------- Auditoría ----------
    def _auditar(self, accion: str, sid: str, **kwargs: Any) -> None:
        self.auditoria.append({"ts": time.time(), "accion": accion, "sid": sid, **kwargs})

    def obtener_auditoria(self, limite: int = 50) -> List[Dict[str, Any]]:
        return self.auditoria[-limite:]


# ============================================================
# PRUEBAS MANUALES (ejecutar en intérprete)
# ============================================================
# P1) Crear sesión y añadir mensaje válido:
#     bot = XRayChatbot(); sid = bot.crear_sesion("demo")
#     assert bot.agregar_mensaje(sid, "user", "hola") is not None
#
# P2) Rechazar mensaje demasiado largo o rol inválido:
#     assert bot.agregar_mensaje(sid, "user", "x" * 5000) is None
#     assert bot.agregar_mensaje(sid, "hacker", "hola") is None
#
# P3) Ancla OFF no aparece en payload:
#     bot.fijar_ancla(sid, "doc", "texto", activa=False)
#     p = bot.construir_payload(sid)
#     assert "doc" not in p["ancoras_activas"]
#
# P4) Toggle ancla y verificar que ahora sí aparece:
#     bot.toggle_ancla(sid, "doc")
#     p2 = bot.construir_payload(sid)
#     assert "doc" in p2["ancoras_activas"]
#
# P5) Pendientes: agregar + marcar hecho + exportar JSON válido:
#     bot.pendientes(sid, "agregar", texto="tarea uno")
#     bot.pendientes(sid, "marcar", idx=0)
#     exp = bot.exportar_json(sid)
#     assert json.loads(exp)["pendientes"][0]["hecho"] is True
# ============================================================

if __name__ == "__main__":
    bot = XRayChatbot()
    s = bot.crear_sesion("demo")
    bot.agregar_mensaje(s, "user", "hola mundo")
    bot.fijar_ancla(s, "ref1", "contenido ref", activa=False)
    print(json.dumps(bot.construir_payload(s), indent=2, default=str))
