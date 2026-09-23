import os
import requests
from openai import OpenAI

def check_release_and_ping() -> dict:
    # 1) Obtener última release de Grok Build
    url = "https://api.github.com/repos/xai-org/grok-build/releases/latest"
    resp = requests.get(url, headers={"Accept": "application/vnd.github.v3+json"})
    data = resp.json()
    
    release_tag = data.get("tag_name")
    asset_names = [a["name"] for a in data.get("assets", [])]
    
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
        "release_tag": release_tag,
        "asset_names": asset_names,
        "reply": reply
    }
