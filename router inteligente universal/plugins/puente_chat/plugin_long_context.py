"""Long-context compatibility layer for ``puente_chat``.

This module wraps the existing plugin instead of forking its routing/tool/HF
logic. It fixes historical silent cuts and also keeps automatic model recovery
inside real API fichas only.

Policy:
- browser/input transport: no artificial truncation here;
- persisted user/assistant turns: up to 500k characters each;
- recalled conversation context: up to 300k characters;
- provider payload budget: up to 350k characters;
- the newest user input is NEVER sliced by this layer;
- local HF/L4 16K-token models reject oversized input explicitly rather than
  silently cutting it;
- consil/motor/xray/auditor fichas remain selectable explicitly, but are never
  used as automatic API-model reserve candidates.
"""
from __future__ import annotations

import os
from typing import Any

from . import plugin as _p

STORE_INPUT_CHARS = int(os.getenv("RIU_CHAT_STORE_INPUT_CHARS") or "500000")
STORE_OUTPUT_CHARS = int(os.getenv("RIU_CHAT_STORE_OUTPUT_CHARS") or "500000")
CONTEXT_TURNS = int(os.getenv("RIU_CHAT_CONTEXT_TURNS") or "40")
CONTEXT_BUDGET_CHARS = int(os.getenv("RIU_CHAT_CONTEXT_BUDGET_CHARS") or "300000")
PROVIDER_BUDGET_CHARS = int(os.getenv("RIU_CHAT_PROVIDER_BUDGET_CHARS") or "350000")
TOOL_RESULT_CHARS = int(os.getenv("RIU_CHAT_TOOL_RESULT_CHARS") or "12000")
LOCAL_INPUT_CHARS = int(os.getenv("RIU_CHAT_LOCAL_INPUT_CHARS") or "48000")


def _rows(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return next((v for v in value.values() if isinstance(v, list)), [])
    return []


def _contexto(sesion: str, pregunta: str) -> str:
    """Recover recent turns without the old 500-character per-side cut."""
    del pregunta
    try:
        mem, scope_for = _p._memoria()
        # solo turnos: los checkpoints del bucle de herramientas (4-10 por turno) desplazaban los turnos de la ventana
        res = mem.search(scope_for(_p.DUENO, "chat:" + sesion), "turno-", CONTEXT_TURNS + 12)
        turns: list[str] = []
        total = 0
        for f in reversed(_rows(res)):
            d = f.get("data", f) if isinstance(f, dict) else f
            if not isinstance(d, dict) or "pregunta" not in d:
                continue
            block = "Usuario: " + str(d.get("pregunta") or "") + "\nAsistente: " + str(d.get("respuesta") or "")
            if len(block) > CONTEXT_BUDGET_CHARS:
                head = CONTEXT_BUDGET_CHARS // 2
                tail = CONTEXT_BUDGET_CHARS - head
                block = block[:head] + "\n[...CONTEXTO_HISTORICO_MUY_LARGO...]\n" + block[-tail:]
            if total + len(block) + 2 > CONTEXT_BUDGET_CHARS:
                continue
            turns.append(block)
            total += len(block) + 2
            if len(turns) >= CONTEXT_TURNS:
                break
        return "\n\n".join(turns)
    except Exception:
        return ""


def _guardar(sesion: str, modelo: str, pregunta: str, respuesta: str) -> bool:
    """Persist long turns instead of the historical 4k/8k slices."""
    try:
        mem, scope_for = _p._memoria()
        import time
        q = str(pregunta)
        a = str(respuesta)
        mem.save(
            scope_for(_p.DUENO, "chat:" + sesion),
            "turno-%d" % int(time.time() * 1000),
            {
                "modelo": modelo,
                "pregunta": q[:STORE_INPUT_CHARS],
                "respuesta": a[:STORE_OUTPUT_CHARS],
                "pregunta_chars": len(q),
                "respuesta_chars": len(a),
                "pregunta_completa": len(q) <= STORE_INPUT_CHARS,
                "respuesta_completa": len(a) <= STORE_OUTPUT_CHARS,
            },
        )
        return True
    except Exception:
        return False


def _recortar(mensajes: list[dict[str, Any]], limite: int = PROVIDER_BUDGET_CHARS) -> list[dict[str, Any]]:
    """Budget OLD context while preserving the latest user input exactly."""
    import json

    ms = [dict(m) for m in mensajes]
    if not ms:
        return ms

    for m in ms:
        if m.get("role") == "tool":
            content = str(m.get("content") or "")
            if len(content) > TOOL_RESULT_CHARS:
                m["content"] = content[:TOOL_RESULT_CHARS] + " ...[tool recortado por presupuesto]"

    def size() -> int:
        return sum(
            len(str(m.get("content") or "")) + len(json.dumps(m.get("tool_calls") or "", ensure_ascii=False))
            for m in ms
        )

    while len(ms) > 2 and size() > limite:
        removed = False
        protected = max((i for i, m in enumerate(ms) if m.get("role") == "user"), default=-1)
        for i, m in enumerate(ms):
            if m.get("role") == "system" or i == protected:
                continue
            old = ms.pop(i)
            if old.get("tool_calls"):
                while i < len(ms) and ms[i].get("role") == "tool":
                    ms.pop(i)
            removed = True
            break
        if not removed:
            break
    return ms


_ORIGINAL_CHAT = _p._chat
_ORIGINAL_SENTINELA = _p._sentinela


def _sentinela_api_safe():
    """Return the normal sentinela but remove special pipelines from auto-reserve.

    ``plugin._chat`` builds its recovery plan from FICHAS, and FICHAS also
    contains consil/motor/xray/auditor entries. Those entries use the synthetic
    provider ``pipeline`` and must never reach ``_llamar_api``. Filtering the
    plan here preserves explicit special-ficha execution while making normal
    API recovery deterministic and thread-safe.
    """
    sen = _ORIGINAL_SENTINELA()
    if sen is None:
        return None
    original_execute = sen.ejecutar

    def ejecutar(plan, mensajes, *args, **kwargs):
        safe_plan = []
        for name, step in plan:
            target = str(name).split(":", 1)[1] if str(name).startswith("reserva:") else ""
            if target and target in _p.ESPECIALES:
                continue
            safe_plan.append((name, step))
        return original_execute(safe_plan, mensajes, *args, **kwargs)

    sen.ejecutar = ejecutar
    return sen


def _chat(payload: dict[str, Any]) -> dict[str, Any]:
    """Never silently truncate the newest input; guard 16K local models."""
    model = str(payload.get("model") or "")
    messages = list(payload.get("messages") or [])
    latest = next((str(m.get("content") or "") for m in reversed(messages) if m.get("role") == "user"), "")
    if model in _p.RESPALDO and len(latest) > LOCAL_INPUT_CHARS:
        return {
            "error": "INPUT_EXCEDE_CONTEXTO_MODELO_LOCAL",
            "detalle": (
                "El input tiene %d caracteres. Este modelo HF local usa un contexto de 16K tokens; "
                "el texto NO fue cortado. Usa un modelo API de contexto largo o divide la tarea."
            ) % len(latest),
            "input_chars": len(latest),
            "input_conservado": True,
        }
    return _ORIGINAL_CHAT(payload)


_p._contexto = _contexto
_p._guardar = _guardar
_p._recortar = _recortar
_p._sentinela = _sentinela_api_safe
_p._chat = _chat


def handle(action: str, payload: dict[str, Any]) -> dict[str, Any]:
    result = _p.handle(action, payload)
    if action == "status" and isinstance(result, dict):
        result = dict(result)
        result["long_context"] = {
            "enabled": True,
            "store_input_chars": STORE_INPUT_CHARS,
            "store_output_chars": STORE_OUTPUT_CHARS,
            "context_turns": CONTEXT_TURNS,
            "context_budget_chars": CONTEXT_BUDGET_CHARS,
            "provider_budget_chars": PROVIDER_BUDGET_CHARS,
            "latest_user_input_preserved": True,
            "budgets_are_characters": True,
            "automatic_reserve_api_only": True,
            "special_fichas_explicit_only": True,
        }
    return result
