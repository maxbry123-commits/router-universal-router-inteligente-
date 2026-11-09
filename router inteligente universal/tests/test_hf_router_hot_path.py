from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integration.huggingface.router_hot_path import (  # noqa: E402
    build_hf_red,
    hf_connection_contract,
    route_chat_completion,
)


def fake_executor(*, model_id: str, messages: list[dict[str, str]], max_tokens: int):
    return {
        "model": model_id,
        "message": {"role": "assistant", "content": "RIU_HOT_PATH_OK"},
        "finish_reason": "stop",
        "max_tokens_seen": max_tokens,
        "message_count": len(messages),
    }


def test_enchufe_accepts_hf_contract_and_route_exists():
    red = build_hf_red(executor=fake_executor)
    assert "ai.hf.chat" in red.nodos
    assert red.mapa()["rutas"] == ["api.fastapi.hf --[chat.completion]--> ai.hf.chat"]
    assert hf_connection_contract()["estado"] == "testing"


def test_fastapi_enchufe_router_adapter_path():
    result = asyncio.run(
        route_chat_completion(
            model_id="Qwen/Qwen3-0.6B",
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=17,
            task_id="test-task",
            trace_id="test-trace",
            executor=fake_executor,
        )
    )
    assert result["model"] == "Qwen/Qwen3-0.6B"
    assert result["message"]["content"] == "RIU_HOT_PATH_OK"
    assert result["max_tokens_seen"] == 17
    assert result["message_count"] == 1
