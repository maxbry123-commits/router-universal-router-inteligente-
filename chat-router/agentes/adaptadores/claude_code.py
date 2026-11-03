"""Adaptador Claude Code: CLI real `claude -p` (instalada; agentes/claude-code/ aporta la pasarela Anthropic->NVIDIA, pasarela.py/iniciar_claude_code.sh).
Flags verificados con `claude --help`: -p, --output-format json, --permission-mode, --allowedTools, --no-session-persistence. El prompt va por stdin.
Los modelos del catalogo no son modelos Anthropic: solo se admite un modelo NVIDIA servido por la pasarela (RIU_CLAUDE_PASARELA_URL), y la pasarela
usa UN modelo fijo (RIU_CLAUDE_PASARELA_MODELO); si el pedido no coincide -> MODELO_INCOMPATIBLE. Nunca --dangerously-skip-permissions."""
import json
import os

from . import _comun
from .modelos import validar_modelo

AGENTE = "claude-code"
# Bash NUNCA va sin patron (shell libre): solo comandos acotados de pruebas/lectura. El operador puede ampliar con RIU_CLAUDE_BASH_PERMITIDOS="make test, npm run lint".
BASH_DEFECTO = ("git status", "git diff", "git log", "git show", "ls", "cat", "pytest", "python -m pytest", "python3 -m pytest", "npm test", "npm run test", "node --test")


def _bash_permitidos():
    extra = [x.strip() for x in os.environ.get("RIU_CLAUDE_BASH_PERMITIDOS", "").split(",") if x.strip() and not x.strip().endswith("*")]
    return ["Bash(%s:*)" % c for c in list(BASH_DEFECTO) + extra]


def run(tarea_id, modelo, objetivo, contexto, permisos, checkpoint):
    try:
        p = _comun.preparar(AGENTE, tarea_id, modelo, objetivo, contexto, permisos, checkpoint)
        exe = _comun.binario("claude", "RIU_CLAUDE_BIN")
        if not exe:
            return _comun.no_instalado(AGENTE, tarea_id)
        cfg = validar_modelo(modelo)
        pasarela_modelo = os.environ.get("RIU_CLAUDE_PASARELA_MODELO", "").strip()
        if cfg["provider"] != "nvidia" or (pasarela_modelo and cfg["model"] != pasarela_modelo):
            return _comun.error(AGENTE, tarea_id, "MODELO_INCOMPATIBLE", "Claude Code solo usa modelos NVIDIA a traves de la pasarela (modelo servido: %s); pedido: %s" % (pasarela_modelo or "sin definir", modelo))
        url = os.environ.get("RIU_CLAUDE_PASARELA_URL", "").strip()
        if not url or not pasarela_modelo:
            return _comun.error(AGENTE, tarea_id, "AGENTE_NO_CONFIGURADO", "falta RIU_CLAUDE_PASARELA_URL y/o RIU_CLAUDE_PASARELA_MODELO (arranca agentes/claude-code/iniciar_claude_code.sh)")
    except _comun.ErrorPrevio as e:
        return e.resultado
    if p["ejecucion"] and not (permisos.get("autorizado_por_chat") is True or (isinstance(permisos.get("aprobado_por"), str) and permisos["aprobado_por"].strip())):
        return _comun.error(AGENTE, tarea_id, "APROBACION_REQUERIDA", "ejecutar comandos con Claude Code exige la aprobacion de un operador (permisos.aprobado_por)", False)
    herramientas = ["Read", "Glob", "Grep"] + (["Edit", "Write"] if p["escritura"] else []) + (_bash_permitidos() if p["ejecucion"] else [])
    modo = "acceptEdits" if p["escritura"] else "plan"
    argv = [exe, "-p", "--output-format", "json", "--no-session-persistence", "--permission-mode", modo, "--allowedTools", ",".join(herramientas)]
    env = _comun.entorno_base({"ANTHROPIC_BASE_URL": url, "ANTHROPIC_AUTH_TOKEN": os.environ.get("RIU_CLAUDE_AUTH_TOKEN", "pasarela-local")})
    inicio = _comun.ahora()
    proc = _comun.ejecutar_proceso(argv, p["directorio"], env, entrada=p["prompt"])
    if proc["timeout"] or proc["exit_code"] != 0:
        return _comun.fallo_de_proceso(AGENTE, tarea_id, proc)
    final = None
    for ev in reversed(_comun.jsonl(proc["stdout"])):
        if ev.get("type") == "result" or "result" in ev:
            final = ev
            break
    if final is None:
        return _comun.error(AGENTE, tarea_id, "AGENTE_SIN_RESULTADO", "claude no devolvio el JSON de resultado", True, proc["exit_code"])
    if final.get("is_error"):
        return _comun.error(AGENTE, tarea_id, "AGENTE_REPORTO_ERROR", str(final.get("result") or "is_error")[:500], True, proc["exit_code"])
    texto = str(final.get("result") or "").strip()
    if not texto:
        return _comun.error(AGENTE, tarea_id, "AGENTE_SIN_RESULTADO", "claude devolvio resultado vacio", True, proc["exit_code"])
    return _comun.resultado_ok(AGENTE, tarea_id, proc, texto, herramientas, [exe, "modo:" + modo, "turnos:%s" % final.get("num_turns"), "modelo:" + cfg["model"]], inicio, cfg["model"])
