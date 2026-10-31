"""Adaptador Codex: CLI real `codex exec` (agentes/agentes-listos/codex/codex-main, codex-rs/exec). Prompt por stdin, sandbox del propio Codex.
Interfaz verificada en codex-rs/exec/src/cli.rs y utils/cli/src/shared_options.rs: -C/--cd, -m, -s/--sandbox, --json, -o/--output-last-message,
--skip-git-repo-check, -c clave=valor. Codex solo habla la API Responses (wire_api="chat" fue retirada): RIU_CODEX_BASE_URL debe apuntar a un endpoint
compatible con /responses; si el endpoint no lo es, Codex falla y el adaptador devuelve ok False (nunca finge)."""
import json
import os
import shutil
import tempfile

from . import _comun

AGENTE = "codex"


def run(tarea_id, modelo, objetivo, contexto, permisos, checkpoint):
    try:
        p = _comun.preparar(AGENTE, tarea_id, modelo, objetivo, contexto, permisos, checkpoint)
        exe = _comun.binario("codex", "RIU_CODEX_BIN")
        if not exe:
            return _comun.no_instalado(AGENTE, tarea_id)
        ep = _comun.endpoint_modelo(modelo, AGENTE, tarea_id)
    except _comun.ErrorPrevio as e:
        return e.resultado
    base = (os.environ.get("RIU_CODEX_BASE_URL") or ep["base_url"]).strip()
    sandbox = "workspace-write" if p["escritura"] else "read-only"  # nunca danger-full-access ni --yolo
    tmp = tempfile.mkdtemp(prefix="riu-codex-")
    salida = os.path.join(tmp, "ultimo.txt")
    try:
        argv = [exe, "exec", "--json", "--skip-git-repo-check", "-C", p["directorio"], "-m", ep["modelo"], "-s", sandbox, "-o", salida,
                "-c", 'model_provider="riu"',
                "-c", "model_providers.riu={name=\"riu\",base_url=%s,env_key=\"RIU_AGENTE_LLM_KEY\",wire_api=\"responses\"}" % json.dumps(base), "-"]
        inicio = _comun.ahora()
        proc = _comun.ejecutar_proceso(argv, p["directorio"], _comun.entorno_base({"RIU_AGENTE_LLM_KEY": ep["api_key"]}), entrada=p["prompt"])
        if proc["timeout"] or proc["exit_code"] != 0:
            return _comun.fallo_de_proceso(AGENTE, tarea_id, proc)
        texto = ""
        if os.path.isfile(salida):
            with open(salida, encoding="utf-8", errors="replace") as f:
                texto = f.read(_comun.MAX_SALIDA).strip()
        if not texto:
            return _comun.error(AGENTE, tarea_id, "AGENTE_SIN_RESULTADO", "codex termino sin mensaje final", True, proc["exit_code"])
        return _comun.resultado_ok(AGENTE, tarea_id, proc, texto, _comun.tipos_de_evento(_comun.jsonl(proc["stdout"])),
                                   [exe, "sandbox:" + sandbox, "modelo:" + ep["modelo"]], inicio)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
