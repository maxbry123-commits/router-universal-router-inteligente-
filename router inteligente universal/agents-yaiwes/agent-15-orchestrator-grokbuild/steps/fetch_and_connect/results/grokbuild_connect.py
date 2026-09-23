import os
import requests
import openai

def check_release_and_ping() -> dict:
    # 1) Obtener la última release de Grok Build
    url = "https://api.github.com/repos/xai-org/grok-build/releases/latest"
    headers = {"User-Agent": "grokbuild_connect"}  # GitHub requiere User-Agent
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # propagar excepción si falla
    release_data = response.json()
    release_tag = release_data.get("tag_name")
    asset_names = [asset["name"] for asset in release_data.get("assets", [])]

    # 2) Cliente OpenAI apuntando al router de HuggingFace
    client = openai.OpenAI(
        base_url="https://router.huggingface.co/v1",
        api_key=os.environ["HF_TOKEN"]
    )
    # Envío de un solo mensaje pidiendo que responda solo "OK"
    completion = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V4-Flash",
        messages=[{"role": "user", "content": "Responde solo con la palabra OK."}],
        max_tokens=10,
        temperature=0,
    )
    reply = completion.choices[0].message.content.strip()

    # 3) Devolver el diccionario solicitado
    return {
        "release_tag": release_tag,
        "asset_names": asset_names,
        "reply": reply
    }
