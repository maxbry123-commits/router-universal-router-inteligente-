"""Adaptador OpenHands: SDK real openhands-software-agent-sdk (agentes/agentes-listos/openhands-software-agent-sdk/code) ejecutado en un SUBPROCESO
con el Python indicado en RIU_OPENHANDS_PYTHON (por defecto el del Harness) mediante _openhands_runner.py. Si `openhands.sdk` no se puede importar
con ese Python, devuelve AGENTE_NO_INSTALADO. El SDK no tiene modo solo-lectura: sin escritura/ejecucion solo se le da TaskTracker."""
import json
import os
import sys

from . import _comun

AGENTE = "openhands"
RUNNER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_openhands_runner.py")
COMPROBACION = "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('openhands.sdk') and importlib.util.find_spec('openhands.tools') else 3)"


def run(tarea_id, modelo, objetivo, contexto, permisos, checkpoint):
    try:
        p = _comun.preparar(AGENTE, tarea_id, modelo, objetivo, contexto, permisos, checkpoint)
        py = os.environ.get("RIU_OPENHANDS_PYTHON", "").strip() or sys.executable
        if not (os.path.isfile(py) and os.access(py, os.X_OK)):
            return _comun.no_instalado(AGENTE, tarea_id, "RIU_OPENHANDS_PYTHON no es un ejecutable.")
        ep = _comun.endpoint_modelo(modelo, AGENTE, tarea_id)
    except _comun.ErrorPrevio as e:
        return e.resultado
    env = _comun.entorno_base()
    previa = _comun.ejecutar_proceso([py, "-c", COMPROBACION], p["directorio"], env, timeout=60)
    if previa["exit_code"] != 0:
        return _comun.no_instalado(AGENTE, tarea_id, "El Python %s no importa openhands.sdk/openhands.tools." % py)
    entrada = {"modelo": "openai/" + ep["modelo"], "base_url": ep["base_url"], "prompt": p["prompt"], "directorio": p["directorio"],
               "escritura": p["escritura"], "ejecucion": p["ejecucion"]}
    inicio = _comun.ahora()
    proc = _comun.ejecutar_proceso([py, RUNNER], p["directorio"], _comun.entorno_base({"RIU_AGENTE_LLM_KEY": ep["api_key"]}), entrada=json.dumps(entrada))
    if proc["timeout"] or proc["exit_code"] != 0:
        return _comun.fallo_de_proceso(AGENTE, tarea_id, proc)
    datos = None
    for ev in reversed(_comun.jsonl(proc["stdout"])):
        if "ok" in ev:
            datos = ev
            break
    if datos is None:
        return _comun.error(AGENTE, tarea_id, "AGENTE_SIN_RESULTADO", "el runner de OpenHands no devolvio JSON", True, proc["exit_code"])
    if datos.get("ok") is not True:
        return _comun.error(AGENTE, tarea_id, str(datos.get("codigo") or "OPENHANDS_FALLO"), str(datos.get("error") or "fallo"), True, proc["exit_code"], estado=datos.get("estado"))
    return _comun.resultado_ok(AGENTE, tarea_id, proc, str(datos.get("resultado") or ""), [str(h) for h in datos.get("herramientas") or []],
                               [py, "estado:" + str(datos.get("estado")), "eventos:%s" % datos.get("eventos")], inicio)
