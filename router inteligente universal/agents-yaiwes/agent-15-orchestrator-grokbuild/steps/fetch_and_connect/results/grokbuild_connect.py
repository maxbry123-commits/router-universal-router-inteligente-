import os
import requests
from openai import OpenAI

def check_release_and_ping() -> dict:
    # Step 1: Get latest release from xai-org/grok-build
    url = "https://api.github.com/repos/xai-org/grok-build/releases/latest"
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    release_tag = data.get("tag_name", "unknown")
    asset_names = [asset["name"] for asset in data.get("assets", [])]
    
    # Step 2: Ping DeepSeek via HF router using OpenAI-compatible client
    hf_token = os.environ["HF_TOKEN"]
    client = OpenAI(base_url="https://router.huggingface.co/v1", api_key=hf_token)
    completion = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V4-Flash",
        messages=[{"role": "user", "content": "Responde solo con la palabra OK."}],
        max_tokens=10
    )
    reply = completion.choices[0].message.content.strip()
    
    return {"release_tag": release_tag, "asset_names": asset_names, "reply": reply}
