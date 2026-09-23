import os
import requests
from openai import OpenAI

def check_release_and_ping() -> dict:
    # 1) Obtener última release de grok-build
    url = "https://api.github.com/repos/xai-org/grok-build/releases/latest"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    release = resp.json()
    if not release:
        raise Exception("No releases found")
    
    asset_names = [asset["name"] for asset in release.get("assets", [])]
    release_tag = release.get("tag_name", "unknown")
    
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
    
    # 3) Resultado
    return {
        "release_tag": release_tag,
        "asset_names": asset_names,
        "reply": reply
    }
