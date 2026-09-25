import os
import requests
from openai import OpenAI

def check_release_and_ping() -> dict:
    # 1) GET última release de grok-build
    url = "https://api.github.com/repos/xai-org/grok-build/releases/latest"
    resp = requests.get(url)
    resp.raise_for_status()
    release = resp.json()
    
    # Extraer tag y nombres de assets
    release_tag = release.get("tag_name", "")
    assets = release.get("assets", [])
    asset_names = [a["name"] for a in assets]
    
    # 2) Llamada a DeepSeek vía router HF
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
        "release_tag": release_tag,
        "asset_names": asset_names,
        "reply": reply
    }
