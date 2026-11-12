"""swe_code_free_tool.py v2 — Tool MCP "swe_code_free" con bucle de verificacion.
Modos: run (propuesta, sin escritura) y run_verified (aplica con HITL + tests).
Fail-closed: sin harness, sin issue o sin gate -> degraded con reason_code.
Nunca emite "resuelto" sin tests verdes despues del parche.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from engine.swe_sandbox import pytest_target, ROOT
from engine.swe_patch import extract_diff, check, apply, revert, tests_for
from engine.swe_context import build_context, save_liga, load_ligas

SWE_AGENT_PATH = (ROOT / "chat-router" / "agentes" / "agentes-listos"
                  / "SWE-agent" / "SWE-agent-main")
MAX_STEPS = 8

TOOL_SCHEMA: dict[str, Any] = {
    "name": "swe_code_free",
    "description": (
        "Agente de codigo con bucle de verificacion. run: propone parche validado "
        "con git apply --check y linea base de tests, sin escribir. run_verified: "
        "aplica con aprobacion humana, corre tests y revierte si fallan."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "issue": {"type": "string"},
            "context": {"type": "string"},
            "max_steps": {"type": "integer", "default": 4, "minimum": 1, "maximum": 8},
            "approved_by": {"type": "string", "description": "obligatorio en run_verified"},
            "keep": {"type": "boolean", "default": False},
        },
        "required": ["issue"],
    },
}

SYS = (
    "Eres un agente de codigo. Responde SOLO con un bloque ```diff con un diff "
    "unificado valido (--- a/ruta, +++ b/ruta, @@). Sin prose fuera del bloque. "
    "Si el feedback indica que el diff no aplica, corrigelo. "
    "No inventes rutas: usa las del contexto."
)


def _deg(code: str, detail: str = "") -> dict[str, Any]:
    return {"status": "degraded", "reason_code": code, "reason": detail or code}


def _harness() -> dict[str, Any]:
    try:
        from plugins.deepseek_harness.plugin import handle
        return handle("status", {})
    except Exception as exc:  # noqa: BLE001
        return {"status": "degraded", "reason": type(exc).__name__}


def _status() -> dict[str, Any]:
    h = _harness()
    present = SWE_AGENT_PATH.is_dir()
    return {"status": "ok", "tool": "swe_code_free", "version": "2.0.0",
            "agent_present": present, "agent_path": str(SWE_AGENT_PATH),
            "harness": h, "modos": ["run", "run_verified"],
            "listo_para_run": bool(h.get("status") == "ok")}


def _llm(messages: list[dict[str, str]]) -> tuple[str, str | None]:
    try:
        from plugins.puente_chat.plugin import llm_call
    except Exception as exc:  # noqa: BLE001
        return "", "llm_no_importable:" + type(exc).__name__
    try:
        r = llm_call({"caller_id": "swe_code_free", "plugin_id": "swe_code_free",
                      "messages": messages})
    except Exception as exc:  # noqa: BLE001
        return "", "llm_error:" + type(exc).__name__
    if not isinstance(r, dict):
        return "", "llm_respuesta_invalida"
    if r.get("status") not in ("ok", None):
        return "", "llm_degraded:" + str(r.get("reason"))[:120]
    return str(r.get("content") or r.get("response") or ""), None


def _baseline(diff: str) -> list[dict[str, Any]]:
    out = []
    for t in tests_for(diff)[:3]:
        r = pytest_target(t, timeout=120)
        out.append({"target": t, "status": r.get("status"), "rc": r.get("rc"),
                    "stderr": (r.get("stderr") or "")[-600:]})
    return out


def _loop(issue: str, ctx: str, max_steps: int) -> dict[str, Any]:
    msgs = [{"role": "system", "content": SYS},
            {"role": "user", "content": f"ISSUE:\n{issue}\n\nCONTEXTO:\n{ctx[:12000]}"}]
    steps, diff = [], ""
    for n in range(1, max_steps + 1):
        t0 = time.monotonic()
        text, err = _llm(msgs)
        ms = int((time.monotonic() - t0) * 1000)
        if err:
            steps.append({"n": n, "accion": "llm", "ms": ms, "status": err})
            return {"ok": False, "code": "sin_harness" if "no_importable" in err else "llm_error",
                    "detail": err, "steps": steps, "diff": ""}
        diff = extract_diff(text)
        c = check(diff) if diff else {"status": "degraded", "reason": "sin bloque diff"}
        steps.append({"n": n, "accion": "diff+check", "ms": ms, "status": c.get("status")})
        if c.get("status") == "ok":
            return {"ok": True, "diff": diff, "steps": steps}
        msgs.append({"role": "assistant", "content": text[:4000]})
        msgs.append({"role": "user",
                     "content": "FEEDBACK: el diff no aplica. Motivo: "
                                + str(c.get("reason"))[:400] + ". Corrigelo."})
    return {"ok": False, "code": "diff_invalido", "detail": "max_steps_agotado",
            "steps": steps, "diff": diff}


def run(payload: dict[str, Any]) -> dict[str, Any]:
    issue = str(payload.get("issue") or "").strip()
    if not issue:
        return _deg("sin_issue")
    if _harness().get("status") != "ok":
        return _deg("sin_harness", "RIU_DEEPSEEK_HARNESS_URL no configurada")
    n = max(1, min(int(payload.get("max_steps", 4)), MAX_STEPS))
    c = build_context(issue)
    ctx = str(payload.get("context") or "") + "\n" + c["context"]
    r = _loop(issue, ctx, n)
    base = _baseline(r.get("diff", "")) if r.get("diff") else []
    arte = {"veredicto": "propuesto_no_verificado" if r["ok"] else r["code"],
            "patch": r.get("diff", "")[:20000], "tests_base": base,
            "steps": r["steps"], "fuentes": c["fuentes"], "keywords": c["keywords"]}
    liga = save_liga(issue, arte)
    if not r["ok"]:
        return {"status": "degraded", "reason_code": r["code"], "reason": r["detail"],
                "steps": r["steps"], "liga_memoria": liga}
    return {"status": "ok", "tool": "swe_code_free", "modo": "propuesta",
            "patch_propuesto": r["diff"], "aplicable": True, "aplicado": False,
            "tests_base": base, "steps": r["steps"], "fuentes": c["fuentes"],
            "liga_memoria": liga, "veredicto": "propuesto_no_verificado",
            "nota": "para verificar: run_verified con approved_by"}


def run_verified(payload: dict[str, Any]) -> dict[str, Any]:
    issue = str(payload.get("issue") or "").strip()
    if not issue:
        return _deg("sin_issue")
    who = str(payload.get("approved_by") or "").strip()
    if not who:
        return _deg("gate_rechazado", "run_verified requiere approved_by (HITL)")
    p = run(payload)
    if p.get("status") != "ok":
        return p
    diff = p["patch_propuesto"]
    a = apply(diff, approved_by=who)
    if a.get("status") != "ok":
        return _deg("diff_invalido", str(a.get("reason"))[:300])
    resultados = []
    for t in tests_for(diff)[:3]:
        r = pytest_target(t, timeout=180)
        resultados.append({"target": t, "status": r.get("status"), "rc": r.get("rc"),
                           "stderr": (r.get("stderr") or "")[-600:]})
    verdes = bool(resultados) and all(x["status"] == "ok" for x in resultados)
    if not verdes and not payload.get("keep"):
        revert()
    arte = {"veredicto": "resuelto_verificado" if verdes else "tests_rojos",
            "patch": diff[:20000], "tests_post": resultados,
            "approved_by": who, "revertido": (not verdes and not payload.get("keep"))}
    liga = save_liga(issue, arte)
    if not verdes:
        return {"status": "degraded", "reason_code": "tests_rojos",
                "tests_post": resultados, "revertido": not payload.get("keep"),
                "liga_memoria": liga}
    return {"status": "ok", "modo": "verificado", "aplicado": True,
            "tests_post": resultados, "veredicto": "resuelto_verificado",
            "approved_by": who, "liga_memoria": liga}


def handle(action: str, payload: dict[str, Any] | None) -> dict[str, Any]:
    payload = payload or {}
    if action == "schema":
        return {"status": "ok", "tool": TOOL_SCHEMA}
    if action == "status":
        return _status()
    if action == "run":
        return run(payload)
    if action == "run_verified":
        return run_verified(payload)
    if action == "history":
        return {"status": "ok", "ligas": load_ligas(str(payload.get("issue") or ""))}
    return _deg("accion_desconocida", action)
