import os
import requests
from openai import OpenAI

def check_release_and_ping() -> dict:
    # Get latest release info
    resp = requests.get("https://api.github.com/repos/xai-org/grok-build/releases/latest")
    resp.raise_for_status()
    release = resp.json()
    tag = release["tag_name"]
    asset_names = [a["name"] for a in release["assets"]]
    
    # Ping DeepSeek via HF router
    client = OpenAI(
        base_url="https://router.huggingface.co/v1",
        api_key=os.environ["HF_TOKEN"]
    )
    chat = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V4-Flash",
        messages=[{"role": "user", "content": "Responde solo con la palabra OK."}]
    )
    reply = chat.choices[0].message.content
    
    return {
        "release_tag": tag,
        "asset_names": asset_names,
        "reply": reply
    }
