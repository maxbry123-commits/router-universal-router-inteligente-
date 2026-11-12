"""swe_code_free_tool.py — Tool MCP "swe_code_free" (cierre-v1, G5).
Wrapper determinista: delega en la puerta llm_call existente (puente_chat),
la misma que usa deepseek_harness. Nunca inventa parches ni ejecuta shell.
Fail-closed: sin harness configurado -> degraded.
Acciones: schema, status, run. Registro MCP: TOOL_SCHEMA.
El parche propuesto se devuelve como texto y se persiste como liga en
plugins/memoria (resumen, no texto completo duplicado).
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SWE_AGENT_PATH = (ROOT / "chat-router" / "agentes" / "agentes-listos"
                  / "SWE-agent" / "SWE-agent-main")

TOOL_SCHEMA: dict[str, Any] = {
    "name": "swe_code_free",
    "description": (
        "Agente de codigo gratuito: recibe un issue y devuelve una propuesta "
        "de parche + tests como texto, via la puerta llm_call del harness. "
        "No aplica cambios al repo; la aplicacion requiere aprobacion humana."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "issue": {"type": "string", "description": "Descripcion del bug o tarea"},
            "context": {"type": "string", "description": "Fragmentos de codigo relevantes"},
            "max_steps": {"type": "integer", "default": 4, "minimum": 1, "maximum": 8},
        },
        "required": ["issue"],
    },
}


def _degraded(reason: str) -> dict[str, Any]:
    return {"status": "degraded", "reason": reason}


def _harness_status() -> dict[str, Any]:
    try:
        from plugins.deepseek_harness.plugin import handle
        return handle("status", {})
    except Exception as exc:  # noqa: BLE001
        return {"status": "degraded", "reason": "harness: " + type(exc).__name__}


def _status() -> dict[str, Any]:
    agent_present = SWE_AGENT_PATH.is_dir()
    h = _harness_status()
    return {
        "status": "ok",
        "tool": TOOL_SCHEMA["name"],
        "agent_present": agent_present,
        "agent_path": str(SWE_AGENT_PATH),
        "harness": h,
        "listo_para_run": bool(agent_present and h.get("status") == "ok"),
    }


def _build_messages(issue: str, context: str) -> list[dict[str, str]]:
    sys_msg = (
        "Eres un agente de codigo. Devuelve SOLO: (1) parche en formato diff "
        "unificado, (2) tests minimos en Python. No ejecutes nada. "
        "Si falta informacion, lista exactamente que archivos necesitas."
    )
    user = "ISSUE:\n" + issue
    if context:
        user += "\n\nCONTEXTO:\n" + context[:8000]
    return [{"role": "system", "content": sys_msg},
            {"role": "user", "content": user}]


def _run(payload: dict[str, Any]) -> dict[str, Any]:
    issue = str(payload.get("issue") or "").strip()
    if not issue:
        return _degraded("run: falta 'issue'")
    st = _status()
    if not st["listo_para_run"]:
        return _degraded("run: no listo (agent_present="
                         + str(st["agent_present"]) + ", harness="
                         + str(st["harness"].get("status")) + ")")
    try:
        from plugins.puente_chat.plugin import llm_call
    except Exception as exc:  # noqa: BLE001
        return _degraded("run: llm_call no importable: " + type(exc).__name__)
    req = {
        "caller_id": "swe_code_free",
        "plugin_id": "swe_code_free",
        "messages": _build_messages(issue, str(payload.get("context") or "")),
        "max_steps": int(payload.get("max_steps", 4)),
    }
    try:
        resp = llm_call(req)
    except Exception as exc:  # noqa: BLE001
        return _degraded("run: llm_call: " + type(exc).__name__)
    if not isinstance(resp, dict) or resp.get("status") not in ("ok", None):
        return _degraded("run: respuesta no ok: "
                         + json.dumps(resp, ensure_ascii=False)[:200])
    patch = str(resp.get("content") or resp.get("response") or "")
    if not patch:
        return _degraded("run: respuesta sin contenido")
    key = "swe_" + hashlib.sha256(issue.encode("utf-8")).hexdigest()[:16]
    liga = None
    try:
        from plugins.memoria.plugin import handle as mem
        saved = mem("save", {"key": key, "data": {
            "issue": issue[:500],
            "summary": patch[:200],
            "ts": time.time(),
        }})
        if saved.get("status") == "ok":
            liga = key
    except Exception:  # noqa: BLE001
        liga = None
    return {"status": "ok", "tool": "swe_code_free", "patch_propuesto": patch,
            "liga_memoria": liga, "aplicado": False,
            "nota": "propuesta; aplicar requiere aprobacion humana (HITL)"}


def handle(action: str, payload: dict[str, Any] | None) -> dict[str, Any]:
    payload = payload or {}
    if action == "schema":
        return {"status": "ok", "tool": TOOL_SCHEMA}
    if action == "status":
        return _status()
    if action == "run":
        return _run(payload)
    return _degraded("accion desconocida")
