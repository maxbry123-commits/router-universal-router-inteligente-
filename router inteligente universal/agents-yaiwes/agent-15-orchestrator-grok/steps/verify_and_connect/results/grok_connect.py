import os
import requests
import openai

def verify_and_ping() -> dict:
    """Verify the latest Grok Build release and ping DeepSeek model.

    Returns:
        dict: Contains the release tag and the model's reply.
    """
    # 1. Get latest release info from GitHub with proper headers
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "python-requests"
    }
    releases_url = "https://api.github.com/repos/xai-org/grok-build/releases/latest"
    response = requests.get(releases_url, headers=headers)
    response.raise_for_status()
    release_info = response.json()
    tag_name = release_info.get("tag_name")
    if not tag_name:
        raise ValueError("Missing or empty 'tag_name' in release information")

    # 2. Send a single message to DeepSeek model via HuggingFace router
    client = openai.OpenAI(
        base_url="https://router.huggingface.co/v1",
        api_key=os.environ["HF_TOKEN"]
    )
    completion = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V4-Flash",
        messages=[{"role": "user", "content": "Responde solo con la palabra OK."}]
    )
    reply_text = completion.choices[0].message.content.strip()

    # 3. Return the gathered information
    return {"grok_build_release": tag_name, "reply": reply_text}
