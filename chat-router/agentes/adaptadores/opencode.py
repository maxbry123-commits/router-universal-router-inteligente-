"""Adaptador OpenCode: CLI real `opencode run` (agentes/agentes-listos/opencode/opencode-dev, docs cli.mdx/config.mdx/permissions.mdx).
El proveedor OpenAI-compatible se inyecta con OPENCODE_CONFIG_CONTENT (config inline); la clave va por {env:RIU_AGENTE_LLM_KEY}, nunca en argv.
Los permisos son los de OpenCode (edit/bash/webfetch en allow|deny): sin --auto y sin 'ask' para que no haya preguntas interactivas."""
import json

from . import _comun

AGENTE = "opencode"


def _texto(eventos):
    partes = [(e.get("part") or {}).get("text") for e in eventos if e.get("type") == "text"]
    return "\n".join(t for t in partes if isinstance(t, str) and t.strip()).strip()


def run(tarea_id, modelo, objetivo, contexto, permisos, checkpoint):
    try:
        p = _comun.preparar(AGENTE, tarea_id, modelo, objetivo, contexto, permisos, checkpoint)
        exe = _comun.binario("opencode", "RIU_OPENCODE_BIN")
        if not exe:
            return _comun.no_instalado(AGENTE, tarea_id)
        ep = _comun.endpoint_modelo(modelo, AGENTE, tarea_id)
    except _comun.ErrorPrevio as e:
        return e.resultado
    cfg = {"$schema": "https://opencode.ai/config.json",
           "provider": {"riu": {"npm": "@ai-sdk/openai-compatible", "name": "RIU", "options": {"baseURL": ep["base_url"], "apiKey": "{env:RIU_AGENTE_LLM_KEY}"},
                                "models": {ep["modelo"]: {"name": ep["modelo"]}}}},
           "permission": {"*": "deny", "read": "allow", "glob": "allow", "grep": "allow", "list": "allow",
                          "external_directory": "deny",  # read/glob/grep/list no salen del directorio de la tarea (permissions.mdx: external_directory)
                          "edit": "allow" if p["escritura"] else "deny", "bash": "allow" if p["ejecucion"] else "deny", "webfetch": "deny"}}
    argv = [exe, "run", "--format", "json", "--dir", p["directorio"], "-m", "riu/" + ep["modelo"], p["prompt"]]
    env = _comun.entorno_base({"RIU_AGENTE_LLM_KEY": ep["api_key"], "OPENCODE_CONFIG_CONTENT": json.dumps(cfg)})
    inicio = _comun.ahora()
    proc = _comun.ejecutar_proceso(argv, p["directorio"], env)
    if proc["timeout"] or proc["exit_code"] != 0:
        return _comun.fallo_de_proceso(AGENTE, tarea_id, proc)
    eventos = _comun.jsonl(proc["stdout"])
    texto = _texto(eventos)
    if not texto:
        return _comun.error(AGENTE, tarea_id, "AGENTE_SIN_RESULTADO", "opencode termino sin texto de respuesta", True, proc["exit_code"])
    herramientas = _comun.tipos_de_evento([{"tool": (e.get("part") or {}).get("tool")} for e in eventos if e.get("type") == "tool_use"], "tool")
    return _comun.resultado_ok(AGENTE, tarea_id, proc, texto, herramientas, [exe, "modelo:riu/" + ep["modelo"], "permisos:" + json.dumps(cfg["permission"], sort_keys=True)], inicio, ep["modelo"])
