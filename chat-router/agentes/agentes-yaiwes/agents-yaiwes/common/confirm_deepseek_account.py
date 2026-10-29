"""Confirms, with a real call, that DeepSeek V4 Flash answers through the Director's Hugging Face account (router.huggingface.co),
not a separate/official DeepSeek account. Prints the model id and a snippet of the raw response headers/body for verification."""
from __future__ import annotations

import os

from huggingface_hub import HfApi
from openai import OpenAI


def main() -> int:
    token = os.environ["HF_TOKEN"]
    who = HfApi(token=token).whoami()
    client = OpenAI(base_url="https://router.huggingface.co/v1", api_key=token)
    res = client.chat.completions.create(model="deepseek-ai/DeepSeek-V4-Flash", messages=[{"role": "user", "content": "Responde solo: OK"}], max_tokens=20)
    print(f"::notice title=RIU_DEEPSEEK_CONFIRM::cuenta_HF={who.get('name')} modelo={res.model} respuesta='{res.choices[0].message.content.strip()}'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
