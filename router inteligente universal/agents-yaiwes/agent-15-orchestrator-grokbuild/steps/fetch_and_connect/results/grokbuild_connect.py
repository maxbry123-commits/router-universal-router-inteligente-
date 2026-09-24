import os
import requests
from openai import OpenAI

def check_release_and_ping() -> dict:
    # 1) Obtener última release de Grok Build
    resp = requests.get("https://api.github.com/repos/xai-org/grok-build/releases/latest")
    resp.raise_for_status()
    data = resp.json()
    
    # Manejar caso de release vacío o no encontrada
    if not data or "tag_name" not in data:
        raise RuntimeError("No stable release found")
    
    release_tag = data["tag_name"]
    asset_names = [a["name"] for a in data.get("assets", [])]
    
    # 2) Llamada a DeepSeek via HF router
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
