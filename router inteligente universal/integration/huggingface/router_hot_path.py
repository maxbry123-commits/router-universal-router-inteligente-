"""HF hot-path through Enchufe Gate + RedUniversal.

This module is intentionally a thin adapter. It does not create a second
router: it reuses the persisted RedUniversal and its Enchufe Gate, then
attaches the Hugging Face chat adapter as one validated network node.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

_ROOT = Path(__file__).resolve().parents[2]
_RED = _ROOT / "red"
if str(_RED) not in sys.path:
    sys.path.insert(0, str(_RED))

from red_universal import Mensaje, RedUniversal  # noqa: E402

from .huggingface_openai_chat import chat_completion  # noqa: E402

Executor = Callable[..., dict[str, Any]]

_HF_NODE_ID = "ai.hf.chat"
_ORIGIN = "api.fastapi.hf"
_EVENT_TYPE = "chat.completion"


def hf_connection_contract() -> dict[str, Any]:
    """Minimal v1.5-compatible contract accepted by the Enchufe Gate."""
    return {
        "artifact_id": _HF_NODE_ID,
        "version": "1.0.0",
        "estado": "testing",
        "contract_hash": "",
        "contrato": {
            "rol": "transform",
            "consume": {
                "datatype": {"family": "riu", "type": "chat_request", "version": 1}
            },
            "expone": {
                "datatype": {"family": "riu", "type": "chat_response", "version": 1}
            },
        },
        "ejecucion": {"kind": "api", "transport": "sdk"},
        "seguridad": {
            "sandbox": "process",
            "permisos": [],
            "limites": {"timeout_ms": 120000, "deadline_ms": 120000},
        },
    }


class HuggingFaceChatConnector:
    """Network connector that delegates execution to the certified HF adapter."""

    conector_id = "hf.chat.adapter"

    def __init__(self, executor: Executor = chat_completion) -> None:
        self._executor = executor

    async def enviar(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            result = self._executor(
                model_id=payload["model_id"],
                messages=payload["messages"],
                max_tokens=int(payload.get("max_tokens", 256)),
            )
        except Exception as exc:  # fail-closed at the network boundary
            return {"status": "FAIL", "error": f"hf_adapter:{type(exc).__name__}:{exc}"}
        return {"status": "DONE", "output": result}

    async def sondear(self) -> bool:
        return True


def build_hf_red(*, executor: Executor = chat_completion) -> RedUniversal:
    """Build the HF slice of the existing RedUniversal and validate its node."""
    red = RedUniversal()
    red.conectar(
        _HF_NODE_ID,
        HuggingFaceChatConnector(executor),
        hf_connection_contract(),
        tags={"huggingface", "chat", "p01"},
        direccion="entrada",
        nivel="igual",
    )
    red.ruta(
        "route.fastapi.hf.chat",
        origen=_ORIGIN,
        destino=_HF_NODE_ID,
        cuando=_EVENT_TYPE,
        prioridad=10,
    )
    return red


async def route_chat_completion(
    *,
    model_id: str,
    messages: list[dict[str, str]],
    max_tokens: int = 256,
    task_id: str | None = None,
    trace_id: str | None = None,
    executor: Executor = chat_completion,
) -> dict[str, Any]:
    """FastAPI -> Enchufe Gate -> RedUniversal -> HF adapter."""
    red = build_hf_red(executor=executor)
    routed = await red.enviar(
        Mensaje(
            tipo=_EVENT_TYPE,
            origen=_ORIGIN,
            payload={
                "model_id": model_id,
                "messages": messages,
                "max_tokens": max_tokens,
            },
            task_id=task_id or f"hf-{uuid4().hex}",
            trace_id=trace_id or uuid4().hex,
        ),
        modo="primero",
    )
    if routed.get("status") != "DONE":
        raise RuntimeError(f"HF_ROUTER_HOT_PATH_FAILED:{routed.get('error', 'unknown')}")
    output = routed.get("output")
    if not isinstance(output, dict):
        raise RuntimeError("HF_ROUTER_HOT_PATH_INVALID_OUTPUT")
    return output
