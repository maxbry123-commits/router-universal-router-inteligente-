import os
import requests
from openai import OpenAI

def check_release_and_ping() -> dict:
    # 1) Buscar el release más reciente y su tag, get assets
    url = "https://api.github.com/repos/xai-org/grok-build/releases"
    resp = requests.get(url)
    resp.raise_for_status()
    releases = resp.json()
    
    # Buscar primer release no draft
    target_release = None
    for r in releases:
        if not r.get("draft", True):
            target_release = r
            break
    
    if target_release is None:
        raise RuntimeError("No non-draft release found")
    
    release_tag = target_release["tag_name"]
    asset_names = [a["name"] for a in target_release["assets"]]
    
    # 2) DeepSeek call via HF router
    client = OpenAI(
        base_url="https://router.huggingface.co/v1",
        api_key=os.environ["HF_TOKEN"]
    )
    completion = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V4-Flash",
        messages=[{"role": "user", "content": "Responde solo con la palabra OK."}]
    )
    reply = completion.choices[0].message.content
    
    # 3) Dict result
    return {
        "release_tag": release_tag,
        "asset_names": asset_names,
        "reply": reply
    }
