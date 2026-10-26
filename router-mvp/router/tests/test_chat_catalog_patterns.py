from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integration.huggingface.chat_catalog import family_of  # noqa: E402

CASES = {
    "deepseek-ai/DeepSeek-V4.1-Flash": "deepseek-v4-flash",
    "deepseek-ai/DeepSeek-V4-Flash": "deepseek-v4-flash",
    "deepseek-ai/DeepSeek-V4-Flash-0731": "deepseek-v4-flash",
    "deepseek-ai/DeepSeek-V4-Flash-Vision-Exp": None,
    "deepseek-ai/DeepSeek-V4-Pro": "deepseek-v4-pro",
    "deepseek-ai/DeepSeek-V4.1-Pro": "deepseek-v4-pro",
    "MiniMaxAI/MiniMax-M3": "minimax",
    "minimaxai/minimax-m2.7": "minimax",
    "MiniMaxAI/MiniMax-H3": None,
    "moonshotai/Kimi-K3": "kimi-k3",
    "moonshotai/Kimi-K2.5": None,
    "Qwen/Qwen3.8-27B": None,
}


def test_family_patterns_match_requested_models_only():
    for model_id, expected in CASES.items():
        got = (family_of(model_id) or {}).get("family")
        assert got == expected, (model_id, got, expected)
