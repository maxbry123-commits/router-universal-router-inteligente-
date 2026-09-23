import os
import requests
from openai import OpenAI

def check_release_and_ping() -> dict:
    # 1) GET releases de xai-org/grok-build (sin /latest que da 404)
    resp = requests.get("https://api.github.com/repos/xai-org/grok-build/releases?per_page=1")
    resp.raise_for_status()
    releases = resp.json()
    if not releases:
        raise ValueError("No releases found")
    latest = releases[0]
    tag = latest["tag_name"]
    asset_names = [a["name"] for a in latest.get("assets", [])]

    # 2) Llamada a DeepSeek vía HF router
    client = OpenAI(
        base_url="https://router.huggingface.co/v1",
        api_key=os.environ["HF_TOKEN"]
    )
    completion = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V4-Flash",
        messages=[{"role": "user", "content": "Responde solo con la palabra OK."}]
    )
    reply = completion.choices[0].message.content

    return {
        "release_tag": tag,
        "asset_names": asset_names,
        "reply": reply
    }
