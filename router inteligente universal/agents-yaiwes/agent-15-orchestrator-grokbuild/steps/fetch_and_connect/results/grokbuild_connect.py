import os
import requests
import openai

def check_release_and_ping() -> dict:
    # 1) GET releases de grok-build
    url = "https://api.github.com/repos/xai-org/grok-build/releases"
    resp = requests.get(url)
    resp.raise_for_status()
    releases = resp.json()
    
    # buscar la latest (primer release si no hay tag "latest")
    # filtrar drafts/prereleases
    latest = None
    for r in releases:
        if not r.get("draft") and not r.get("prerelease"):
            latest = r
            break
    if latest is None:
        raise RuntimeError("No hay release no-draft ni no-prerelease en xai-org/grok-build")
    
    release_tag = latest["tag_name"]
    asset_names = [a["name"] for a in latest.get("assets", [])]
    
    # 2) llamada a DeepSeek vía HF router
    client = openai.OpenAI(
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
