"""audit_xray.py — 9 etapas forenses (NCT/APEX). Verificacion cruzada."""
import logging, time
from typing import Dict, Any, Callable

logger = logging.getLogger(__name__)

ETAPAS = [
    "lectura_origen", "extraccion_bloques", "validacion_input_block",
    "verificacion_sintaxis", "verificacion_dependencias", "commit_push",
    "lectura_raw", "comparacion_sha256", "limpieza_contenedor",
]

class AuditXRay:
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.started_at = time.time()
        self.etapas: Dict[str, Dict[str, Any]] = {
            e: {"estado": "PENDIENTE"} for e in ETAPAS
        }

    def marcar(self, etapa: str, estado: str,
               evidencia: Any = None, flag: str = None) -> None:
        if etapa not in self.etapas:
            logger.warning("Etapa desconocida: %s", etapa)
            return
        self.etapas[etapa] = {"estado": estado, "evidencia": evidencia,
                              "flag": flag, "ts": time.time()}

    def ejecutar_etapa(self, etapa: str, fn: Callable[[], Any]) -> Dict[str, Any]:
        try:
            result = fn()
            self.marcar(etapa, "OK", evidencia=result)
            return {"estado": "OK", "evidencia": result}
        except Exception as e:
            self.marcar(etapa, "FAIL", evidencia=str(e), flag="EXCEPCION")
            return {"estado": "FAIL", "error": str(e)}

    def resumen(self) -> Dict[str, Any]:
        ok = sum(1 for e in self.etapas.values() if e["estado"] == "OK")
        fail = sum(1 for e in self.etapas.values() if e["estado"] == "FAIL")
        pend = sum(1 for e in self.etapas.values() if e["estado"] == "PENDIENTE")
        flags = [e for e in self.etapas.values() if e.get("flag")]
        return {"task_id": self.task_id,
                "elapsed_s": round(time.time() - self.started_at, 2),
                "ok": ok, "fail": fail, "pendiente": pend, "total": len(ETAPAS),
                "flags": flags,
                "veredicto": "PASS" if fail == 0 and pend == 0
                             else "PARTIAL" if fail == 0 else "FAIL"}

    def run_all(self, handlers: Dict[str, Callable[[], Any]]) -> Dict[str, Any]:
        for etapa in ETAPAS:
            fn = handlers.get(etapa)
            if fn is None:
                self.marcar(etapa, "PENDIENTE", flag="SIN_HANDLER")
                continue
            self.ejecutar_etapa(etapa, fn)
        return self.reporte()

    def reporte(self) -> Dict[str, Any]:
        return {"resumen": self.resumen(), "etapas": self.etapas}
