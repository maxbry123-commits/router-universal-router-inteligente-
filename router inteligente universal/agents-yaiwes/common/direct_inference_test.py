"""Fastest possible check: call small models DIRECTLY through Hugging Face's serverless Inference API (InferenceClient),
with NO Job, NO Space, NO llama-server — this is what the Director pointed out and that we had missed. Real result only."""
from __future__ import annotations

import os
import time

from huggingface_hub import InferenceClient

MODELS = ["Qwen/Qwen3-0.6B", "LiquidAI/LFM2.5-1.2B-Instruct", "Qwen/Qwen2.5-1.5B-Instruct", "HuggingFaceTB/SmolLM3-3B"]


def note(title: str, msg: str, level: str = "notice") -> None:
    print(f"::{level} title=RIU_DIRECT_{title}::{msg}".replace("\n", " ")[:900], flush=True)


def main() -> int:
    token = os.environ.get("HF_TOKEN")
    for model_id in MODELS:
        tag = model_id.upper().replace("/", "_").replace(".", "_").replace("-", "_")
        client = InferenceClient(model=model_id, token=token, timeout=40)
        t0 = time.perf_counter()
        try:
            out = client.chat_completion(messages=[{"role": "user", "content": "Responde solo con la palabra OK."}], max_tokens=20)
            text = out.choices[0].message.content
            note(tag, f"FUNCIONA sin desplegar nada: {(time.perf_counter() - t0) * 1000:.0f} ms, respuesta='{text.strip()[:60]}'")
        except Exception as exc:  # noqa: BLE001
            note(tag, f"NO disponible por Inference API directa: {type(exc).__name__}: {str(exc)[:180]}", "warning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
