"""Contrato comun de tarea: el mismo para YAIWES y OpenClaw. El modelo es el LLM; el agente es el runtime que lo usa."""
import re
from dataclasses import asdict, dataclass, fields

from .modelos import validar_agente, validar_modelo, validar_workflow

_TASK_ID = re.compile(r"[A-Za-z0-9_-]{1,64}")
ORIGENES = ("yaiwes", "openclaw")


@dataclass
class TareaSWE:
    task_id: str
    origen: str
    mensaje: str
    workflow: str
    modelo_responde: str
    modelo_lector: str
    modelo_tool: str
    modelo_revisor: str
    agente_responde: str
    agente_tool: str
    agente_verificador: str
    modo_agentico: bool = False
    aprobacion: bool = False
    sesion: str = ""
    proyecto: str = ""

    def validar(self):
        if not isinstance(self.task_id, str) or not _TASK_ID.fullmatch(self.task_id):
            raise ValueError("TASK_ID_INVALIDO")
        if self.origen not in ORIGENES:
            raise ValueError("ORIGEN_INVALIDO")
        if not isinstance(self.mensaje, str) or not self.mensaje.strip():
            raise ValueError("MENSAJE_VACIO")
        validar_workflow(self.workflow)
        for m in (self.modelo_responde, self.modelo_lector, self.modelo_tool, self.modelo_revisor):
            validar_modelo(m)
        for a in (self.agente_responde, self.agente_tool, self.agente_verificador):
            validar_agente(a)
        if not isinstance(self.modo_agentico, bool) or not isinstance(self.aprobacion, bool) or not isinstance(self.sesion, str) or not isinstance(self.proyecto, str):
            raise ValueError("CAMPO_TIPO_INVALIDO")
        return asdict(self)

    @classmethod
    def desde_dict(cls, datos):
        """Estricto: ningun campo ajeno (p. ej. estado o aprobado_por) entra por el contrato."""
        if not isinstance(datos, dict):
            raise ValueError("CONTRATO_INVALIDO")
        nombres = {f.name for f in fields(cls)}
        if set(datos) - nombres:
            raise ValueError("CAMPOS_DESCONOCIDOS")
        obligatorios = {f.name for f in fields(cls)[:11]}
        if obligatorios - set(datos):
            raise ValueError("CAMPOS_FALTANTES")
        return cls(**datos)
