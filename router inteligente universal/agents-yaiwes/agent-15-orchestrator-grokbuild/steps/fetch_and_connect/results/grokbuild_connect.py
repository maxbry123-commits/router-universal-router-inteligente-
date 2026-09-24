import os
import requests
from openai import OpenAI

def check_release_and_ping() -> dict:
    # 1) GET latest release from xai-org/grok-build
    url = "https://api.github.com/repos/xai-org/grok-build/releases/latest"
    resp = requests.get(url)
    resp.raise_for_status()
    release_data = resp.json()
    release_tag = release_data["tag_name"]
    asset_names = [asset["name"] for asset in release_data["assets"]]
    
    # 2) Create OpenAI client pointing to Hugging Face router and ping DeepSeek-V4-Flash
    client = OpenAI(
        base_url="https://router.huggingface.co/v1",
        api_key=os.environ["HF_TOKEN"]
    )
    completion = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V4-Flash",
        messages=[{"role": "user", "content": "Responde solo con la palabra OK."}]
    )
    reply = completion.choices[0].message.content
    
    # 3) Return structured result
    return {
        "release_tag": release_tag,
        "asset_names": asset_names,
        "reply": reply
    }
