"""Long-context compatibility layer for ``puente_chat``.

This module deliberately wraps the existing plugin instead of forking its
routing/tool/HF logic.  It patches only the pieces that were silently cutting
chat context:

* stored user turns were truncated to 4k chars;
* stored assistant turns were truncated to 8k chars;
* recalled turns were truncated to 500 + 500 chars;
* the provider payload was aggressively reduced to 20k chars.

The latest user input is NEVER truncated here.  Older context may be removed
when a provider payload exceeds its budget, but the current instruction is
kept byte-for-byte.  Local HF/L4 models have a finite 16k-token context, so an
oversized current input is rejected explicitly instead of being silently cut.
"""
from __future__ import annotations

import os
from typing import Any

from . import plugin as _p

# Character budgets are intentionally configurable.  They are character
# budgets (not token guesses), therefore they stay conservative enough for the
# API models while being far above the previous 20k ceiling.
STORE_INPUT_CHARS = int(os.getenv("RIU_CHAT_STORE_INPUT_CHARS") or "250000")
STORE_OUTPUT_CHARS = int(os.getenv("RIU_CHAT_STORE_OUTPUT_CHARS") or "250000")
CONTEXT_TURNS = int(os.getenv("RIU_CHAT_CONTEXT_TURNS") or "20")
CONTEXT_BUDGET_CHARS = int(os.getenv("RIU_CHAT_CONTEXT_BUDGET_CHARS") or "80000")
PROVIDER_BUDGET_CHARS = int(os.getenv("RIU_CHAT_PROVIDER_BUDGET_CHARS") or "120000")
TOOL_RESULT_CHARS = int(os.getenv("RIU_CHAT_TOOL_RESULT_CHARS") or "6000")
LOCAL_INPUT_CHARS = int(os.getenv("RIU_CHAT_LOCAL_INPUT_CHARS") or "48000")


def _rows(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return next((v for v in value.values() if isinstance(v, list)), [])
    return []


def _contexto(sesion: str, pregunta: str) -> str:
    """Recover recent turns without the old 500-character per-side cut.

    Newest complete turns are preferred.  If an older turn would overflow the
    context budget it is skipped rather than cutting the current user input.
    """
    del pregunta  # kept in the signature for compatibility with plugin.py
    try:
        mem, scope_for = _p._memoria()
        res = mem.search(scope_for(_p.DUENO, "chat:" + sesion), "", CONTEXT_TURNS + 8)
        turns: list[str] = []
        for f in reversed(_rows(res)):
            d = f.get("data", f) if isinstance(f, dict) else f
            if not isinstance(d, dict) or "pregunta" not in d:
                continue
            block = "Usuario: " + str(d.get("pregunta") or "") + "\nAsistente: " + str(d.get("respuesta") or "")
            if len(block) > CONTEXT_BUDGET_CHARS:
                # One single historical turn can itself be huge.  Keep both
                # ends and make the reduction explicit instead of silently
                # pretending the whole turn was supplied.
                head = CONTEXT_BUDGET_CHARS // 2
                tail = CONTEXT_BUDGET_CHARS - head
                block = block[:head] + "\n[...CONTEXTO_HISTORICO_MUY_LARGO...]\n" + block[-tail:]
            if sum(len(x) + 2 for x in turns) + len(block) > CONTEXT_BUDGET_CHARS:
                continue
            turns.append(block)
            if len(turns) >= CONTEXT_TURNS:
                break
        return "\n\n".join(reversed(turns))
    except Exception:  # memory must never take the chat down
        return ""


def _guardar(sesion: str, modelo: str, pregunta: str, respuesta: str) -> bool:
    """Persist long turns instead of the historical 4k/8k slices."""
    try:
        mem, scope_for = _p._memoria()
        import time

        mem.save(
            scope_for(_p.DUENO, "chat:" + sesion),
            "turno-%d" % int(time.time() * 1000),
            {
                "modelo": modelo,
                "pregunta": str(pregunta)[:STORE_INPUT_CHARS],
                "respuesta": str(respuesta)[:STORE_OUTPUT_CHARS],
                "pregunta_chars": len(str(pregunta)),
                "respuesta_chars": len(str(respuesta)),
            },
        )
        return True
    except Exception:
        return False


def _recortar(mensajes: list[dict[str, Any]], limite: int = PROVIDER_BUDGET_CHARS) -> list[dict[str, Any]]:
    """Budget old context while preserving the latest user input exactly.

    Previous code used a 20k-character hard ceiling and could discard useful
    conversation state.  This implementation first shortens tool payloads,
    then removes the oldest non-system messages.  The most recent user message
    is protected and is never sliced.
    """
    import json

    ms = [dict(m) for m in mensajes]
    if not ms:
        return ms

    latest_user = max((i for i, m in enumerate(ms) if m.get("role") == "user"), default=-1)

    for i, m in enumerate(ms):
        if m.get("role") == "tool" and i != latest_user:
            content = str(m.get("content") or "")
            if len(content) > TOOL_RESULT_CHARS:
                m["content"] = content[:TOOL_RESULT_CHARS] + " ...[tool recortado por presupuesto]"

    def size() -> int:
        return sum(
            len(str(m.get("content") or "")) + len(json.dumps(m.get("tool_calls") or "", ensure_ascii=False))
            for m in ms
        )

    # Remove oldest conversation/tool material first.  Never remove system
    # instructions and never remove the latest user input.
    while len(ms) > 2 and size() > limite:
        removed = False
        # Recalculate the protected user index after each mutation.
        protected = max((i for i, m in enumerate(ms) if m.get("role") == "user"), default=-1)
        for i, m in enumerate(ms):
            if m.get("role") == "system" or i == protected:
                continue
            old = ms.pop(i)
            # Preserve tool-call pairing when an assistant tool-call is pruned.
            if old.get("tool_calls"):
                while i < len(ms) and ms[i].get("role") == "tool":
                    ms.pop(i)
            removed = True
            break
        if not removed:
            break
    return ms


def _chat(payload: dict[str, Any]) -> dict[str, Any]:
    """Guard local 16k-context models from silent input loss."""
    model = str(payload.get("model") or "")
    messages = list(payload.get("messages") or [])
    latest = next((str(m.get("content") or "") for m in reversed(messages) if m.get("role") == "user"), "")
    if model in _p.RESPALDO and len(latest) > LOCAL_INPUT_CHARS:
        return {
            "error": "INPUT_EXCEDE_CONTEXTO_MODELO_LOCAL",
            "detalle": (
                "El input tiene %d caracteres. Este modelo HF local usa un contexto de 16K tokens; "
                "el texto no fue cortado. Usa un modelo API de contexto largo o divide la tarea."
            ) % len(latest),
            "input_chars": len(latest),
            "input_conservado": True,
        }
    return _ORIGINAL_CHAT(payload)


# Patch the original module globals.  Functions defined in plugin.py resolve
# these names at call time, so routing, tools, sentinela and HF behaviour remain
# unchanged while all callers get the long-context policy.
_ORIGINAL_CHAT = _p._chat
_p._contexto = _contexto
_p._guardar = _guardar
_p._recortar = _recortar
_p._chat = _chat


def handle(action: str, payload: dict[str, Any]) -> dict[str, Any]:
    result = _p.handle(action, payload)
    if action == "status" and isinstance(result, dict):
        result = dict(result)
        result["long_context"] = {
            "enabled": True,
            "store_input_chars": STORE_INPUT_CHARS,
            "context_turns": CONTEXT_TURNS,
            "context_budget_chars": CONTEXT_BUDGET_CHARS,
            "provider_budget_chars": PROVIDER_BUDGET_CHARS,
            "latest_user_input_preserved": True,
        }
    return result
