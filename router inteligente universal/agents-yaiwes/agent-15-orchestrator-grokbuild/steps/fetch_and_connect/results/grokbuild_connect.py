import os
import requests
from openai import OpenAI

def check_release_and_ping() -> dict:
    # Step 1: Get latest release from GitHub
    url = "https://api.github.com/repos/xai-org/grok-build/releases"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    releases = resp.json()
    
    # Try latest first, otherwise fallback to first non-draft release
    latest = None
    for r in releases:
        if not r.get("draft"):
            latest = r
            break
    if latest is None:
        raise Exception("No releases found")
    
    release_tag = latest["tag_name"]
    asset_names = [asset["name"] for asset in latest["assets"]]
    
    # Step 2: Ping DeepSeek via HuggingFace router
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
