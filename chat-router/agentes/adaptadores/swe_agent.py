"""Adaptador SWE-agent: CLI real `sweagent run` (agentes/agentes-listos/SWE-agent/SWE-agent-main, pyproject [project.scripts] sweagent = sweagent.run.run:main).
Opciones verificadas en docs/usage/cl_tutorial.md: --agent.model.name/api_base/api_key (valor `$VAR` se lee del entorno), --env.repo.path,
--env.deployment.image, --problem_statement.text, --output_dir. Corre dentro de un contenedor Docker (despliegue por defecto): el repo se copia al
contenedor y el resultado es un parche/trayectoria en output_dir; el adaptador NO aplica el parche al repositorio ni usa deployment local."""
import glob
import os
import shutil
import tempfile

from . import _comun

AGENTE = "swe-agent"
IMAGEN_POR_DEFECTO = "riu-sweagent:latest"  # agentes-listos/SWE-agent/Dockerfile.riu: python:3.12-slim + git + swe-rex (la imagen python:3.12 pelada no tiene git)


def run(tarea_id, modelo, objetivo, contexto, permisos, checkpoint):
    try:
        p = _comun.preparar(AGENTE, tarea_id, modelo, objetivo, contexto, permisos, checkpoint)
        exe = _comun.binario("sweagent", "RIU_SWEAGENT_BIN")
        if not exe:
            return _comun.no_instalado(AGENTE, tarea_id)
        docker = _comun.binario("docker", "RIU_DOCKER_BIN")
        if not docker:
            return _comun.error(AGENTE, tarea_id, "AGENTE_NO_CONFIGURADO", "SWE-agent requiere Docker en el runtime", False)
        imagen = os.environ.get("RIU_SWEAGENT_IMAGE", "").strip() or IMAGEN_POR_DEFECTO
        # La comprobacion pasiva del Harness y esta comprobacion previa comparten
        # el mismo contrato: nunca ejecutar sweagent sin daemon e imagen reales.
        from . import disponibilidad
        docker_estado = disponibilidad._sonda_docker(docker, imagen)
        if docker_estado != "ok":
            causa = {"daemon_inactivo": "daemon Docker inaccesible",
                     "imagen_ausente": "imagen SWE-agent no instalada"}
            return _comun.error(AGENTE, tarea_id, "AGENTE_NO_CONFIGURADO",
                                causa.get(docker_estado, "Docker sin verificar"), False)
        ep = _comun.endpoint_modelo(modelo, AGENTE, tarea_id)
    except _comun.ErrorPrevio as e:
        return e.resultado
    salida = tempfile.mkdtemp(prefix="riu-sweagent-")
    try:
        argv = [exe, "run", "--agent.model.name=openai/" + ep["modelo"], "--agent.model.api_base=" + ep["base_url"],
                "--agent.model.api_key=$RIU_AGENTE_LLM_KEY", "--agent.model.per_instance_cost_limit=0", "--agent.model.total_cost_limit=0",
                "--env.repo.path=" + p["directorio"], "--env.deployment.image=" + imagen,
                "--problem_statement.text=" + p["prompt"], "--output_dir=" + salida]
        inicio = _comun.ahora()
        proc = _comun.ejecutar_proceso(argv, p["directorio"], _comun.entorno_base({"RIU_AGENTE_LLM_KEY": ep["api_key"]}))
        if proc["timeout"] or proc["exit_code"] != 0:
            return _comun.fallo_de_proceso(AGENTE, tarea_id, proc)
        parches = sorted(glob.glob(os.path.join(salida, "**", "*.patch"), recursive=True))
        trayectorias = sorted(glob.glob(os.path.join(salida, "**", "*.traj"), recursive=True))
        if not parches and not trayectorias:
            return _comun.error(AGENTE, tarea_id, "AGENTE_SIN_RESULTADO", "sweagent termino sin parche ni trayectoria en output_dir", True, proc["exit_code"])
        texto = ""
        for ruta in parches:
            with open(ruta, encoding="utf-8", errors="replace") as f:
                texto += f.read(_comun.MAX_SALIDA)
        texto = texto.strip() or "sweagent termino sin parche (ver trayectoria)"
        rel = [os.path.relpath(r, salida) for r in parches + trayectorias]
        return _comun.resultado_ok(AGENTE, tarea_id, proc, texto, ["sweagent run"], [exe] + rel, inicio, ep["modelo"])
    finally:
        shutil.rmtree(salida, ignore_errors=True)