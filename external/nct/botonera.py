"""botonera.py — 9+1 botones + estado activo (NCT/APEX)"""
import logging, time
from typing import Dict, Any, Callable, List

logger = logging.getLogger(__name__)

BOTONES_BASE = ["HANDOFF", "CRAZY_WALL", "INPUT_SHARK", "AUDIT_XRAY",
                "MENTAL_MAP", "QUEUE", "WATCHDOG", "HITL", "ARTIFACTS"]
BOTON_MAESTRO = "RESET"

class Botonera:
    def __init__(self):
        self._botones: List[str] = BOTONES_BASE + [BOTON_MAESTRO]
        self._activo: str = None
        self._acciones: Dict[str, Callable] = {}
        self._historial: List[Dict[str, Any]] = []

    def registrar(self, nombre: str, fn: Callable) -> None:
        if nombre not in self._botones:
            logger.warning("Boton no registrado: %s", nombre)
            return
        self._acciones[nombre] = fn

    def presionar(self, nombre: str, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        if nombre not in self._botones:
            return {"error": f"boton desconocido: {nombre}"}
        self._activo = nombre
        self._historial.append({"ts": time.time(), "boton": nombre,
                                "payload": payload or {}})
        if nombre == BOTON_MAESTRO:
            return self._reset()
        fn = self._acciones.get(nombre)
        if fn is None:
            return {"estado": "SIN_ACCION", "boton": nombre}
        try:
            result = fn(payload or {})
            return {"estado": "OK", "boton": nombre, "resultado": result}
        except Exception as e:
            return {"estado": "FAIL", "boton": nombre, "error": str(e)}

    def _reset(self) -> Dict[str, Any]:
        self._activo = None
        self._historial = []
        return {"estado": "RESET", "historial_borrado": True}

    def estado(self) -> Dict[str, Any]:
        return {"botones": self._botones, "activo": self._activo,
                "historial_count": len(self._historial),
                "ultimos_10": self._historial[-10:],
                "acciones_registradas": list(self._acciones.keys())}

BOTONERA = Botonera()
