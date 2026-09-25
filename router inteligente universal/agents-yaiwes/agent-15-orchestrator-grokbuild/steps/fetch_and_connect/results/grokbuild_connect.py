import os
import requests
from openai import OpenAI

def check_release_and_ping() -> dict:
    # 1) Get latest release from GitHub
    url = "https://api.github.com/repos/xai-org/grok-build/releases/latest"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    release_data = resp.json()
    
    # Handle case where assets might be empty or release doesn't exist
    if not release_data or "tag_name" not in release_data:
        raise ValueError("No releases found")
    
    release_tag = release_data["tag_name"]
    asset_names = [asset["name"] for asset in release_data.get("assets", [])]
    
    # 2) Ping DeepSeek via HF router
    client = OpenAI(
        base_url="https://router.huggingface.co/v1",
        api_key=os.environ["HF_TOKEN"]
    )
    completion = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V4-Flash",
        messages=[{"role": "user", "content": "Responde solo con la palabra OK."}]
    )
    reply = completion.choices[0].message.content
    
    # 3) Return result
    return {
        "release_tag": release_tag,
        "asset_names": asset_names,
        "reply": reply
    }
