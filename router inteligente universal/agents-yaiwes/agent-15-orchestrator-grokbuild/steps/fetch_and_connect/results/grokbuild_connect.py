import os
import requests
from openai import OpenAI

def check_release_and_ping() -> dict:
    # 1) GET releases/latest desde GitHub API de xai-org/grok-build
    url = "https://api.github.com/repos/xai-org/grok-build/releases/latest"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    
    # Extraer tag de la release
    release_tag = data.get("tag_name", "")
    
    # Extraer nombres de los assets (lista de strings)
    assets = data.get("assets", [])
    asset_names = [a.get("name", "") for a in assets]
    
    # 2) Crear cliente OpenAI apuntando al router de HF
    hf_token = os.environ["HF_TOKEN"]
    client = OpenAI(
        base_url="https://router.huggingface.co/v1",
        api_key=hf_token
    )
    
    # Enviar mensaje a deepseek-ai/DeepSeek-V4-Flash
    completion = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V4-Flash",
        messages=[{"role": "user", "content": "Responde solo con la palabra OK."}],
        max_tokens=10,
        timeout=30
    )
    reply = completion.choices[0].message.content
    
    # 3) Devolver dict con los tres campos
    return {
        "release_tag": release_tag,
        "asset_names": asset_names,
        "reply": reply
    }
