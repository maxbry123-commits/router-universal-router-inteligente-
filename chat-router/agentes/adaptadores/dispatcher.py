"""Dispatcher de agentes: unico punto por el que el Harness ejecuta un agente real. Exige dict, ok True y recibo."""
from importlib import import_module

ADAPTADORES = {"codex": "codex", "opencode": "opencode", "swe-agent": "swe_agent", "openhands": "openhands",
               "claude-code": "claude_code", "openclaw": "openclaw"}


class AgenteError(ValueError):
    """ValueError con el codigo del contrato y el dict de resultado del adaptador (para decidir RECONCILIAR o GAP)."""
    def __init__(self, codigo, resultado=None):
        super().__init__(codigo)
        self.codigo, self.resultado = codigo, resultado


def ejecutar_agente(agente, tarea_id, modelo, objetivo, contexto, permisos, checkpoint):
    modulo = ADAPTADORES.get(agente) if isinstance(agente, str) else None
    if not modulo:
        raise ValueError("AGENTE_NO_AUTORIZADO")
    try:
        resultado = import_module("agentes.adaptadores.%s" % modulo).run(tarea_id, modelo, objetivo, contexto, permisos, checkpoint)
    except Exception as exc:  # noqa: BLE001 - un adaptador roto no es "no ejecutado": pudo haber efectos
        raise AgenteError("EJECUCION_AGENTE_FALLIDA", {"ok": False, "agente": agente, "task_id": tarea_id, "codigo": "ADAPTADOR_EXCEPCION",
                                                      "error": type(exc).__name__, "efectos_posibles": True, "recibo": None}) from None
    if not isinstance(resultado, dict):
        raise AgenteError("RESULTADO_AGENTE_INVALIDO", None)
    if resultado.get("ok") is not True:
        raise AgenteError("EJECUCION_AGENTE_FALLIDA", resultado)
    if not isinstance(resultado.get("recibo"), str) or not resultado["recibo"].strip():
        raise AgenteError("AGENTE_SIN_RECIBO", resultado)
    # Un recibo no prueba el trabajo de otro agente o tarea.
    if resultado.get("agente") != agente or resultado.get("task_id") != tarea_id:
        raise AgenteError("IDENTIDAD_RECIBO_INCORRECTA", resultado)
    if not resultado["recibo"].startswith("%s:%s:" % (agente, tarea_id)):
        raise AgenteError("RECIBO_NO_CORRESPONDE", resultado)
    if type(resultado.get("exit_code")) is not int or resultado["exit_code"] != 0:
        raise AgenteError("EXIT_CODE_NO_CONFIRMADO", resultado)
    if resultado.get("truncado") is True:
        raise AgenteError("SALIDA_AGENTE_TRUNCADA", resultado)
    if not isinstance(resultado.get("resultado"), str) or not resultado["resultado"].strip():
        raise AgenteError("RESULTADO_AGENTE_VACIO", resultado)
    if not isinstance(resultado.get("herramientas"), list) or not isinstance(resultado.get("evidencias"), list):
        raise AgenteError("EVIDENCIA_AGENTE_INVALIDA", resultado)
    return resultado
