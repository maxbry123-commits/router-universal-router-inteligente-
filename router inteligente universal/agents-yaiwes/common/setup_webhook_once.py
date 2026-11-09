"""One-time setup (no ongoing GitHub Actions involved): creates the always-on webhook-listener Space on HF, and registers a GitHub
Webhook on the repo pointing at it. From this point on, activation is: GitHub push -> GitHub Webhook -> HF Space -> HF Job. No Actions."""
from __future__ import annotations

import os
import secrets as pysecrets

import requests
from huggingface_hub import HfApi

SPACE_ID = "COMAND-CENTER-1/riu-router-webhook"


def main() -> None:
    hf_token = os.environ["HF_TOKEN"]
    gh_token = os.environ["GH_PUSH_TOKEN"]
    api = HfApi(token=hf_token)
    who = api.whoami()

    api.create_repo(SPACE_ID, repo_type="space", space_sdk="docker", exist_ok=True)
    api.add_space_secret(SPACE_ID, "HF_TOKEN", hf_token)
    api.add_space_secret(SPACE_ID, "GITHUB_TOKEN", gh_token)
    webhook_secret = pysecrets.token_hex(32)
    api.add_space_secret(SPACE_ID, "WEBHOOK_SECRET", webhook_secret)

    readme = "---\ntitle: RIU Router Webhook\nsdk: docker\napp_port: 7860\npinned: false\n---\n\nEscucha el Webhook de GitHub y mantiene vivo el Router. No tocar sin autorización.\n"
    dockerfile = ("FROM python:3.12-slim\nRUN pip install fastapi 'uvicorn[standard]' huggingface_hub requests\n"
                 "COPY app.py /app/app.py\nWORKDIR /app\nCMD [\"uvicorn\", \"app:app\", \"--host\", \"0.0.0.0\", \"--port\", \"7860\"]\n")
    app_code = open("router inteligente universal/agents-yaiwes/common/webhook_space_app.py", encoding="utf-8").read()

    import tempfile
    with tempfile.TemporaryDirectory() as td:
        open(f"{td}/README.md", "w", encoding="utf-8").write(readme)
        open(f"{td}/Dockerfile", "w", encoding="utf-8").write(dockerfile)
        open(f"{td}/app.py", "w", encoding="utf-8").write(app_code)
        api.upload_folder(folder_path=td, repo_id=SPACE_ID, repo_type="space")

    space_url = f"https://{SPACE_ID.split('/')[0].lower()}-{SPACE_ID.split('/')[1].lower()}.hf.space"
    print(f"::notice title=RIU_WEBHOOK_SPACE::{space_url} owner={who.get('name')}")

    hook_resp = requests.post(
        "https://api.github.com/repos/maxbry123-commits/router-universal-router-inteligente-/hooks",
        headers={"Authorization": f"Bearer {gh_token}", "Accept": "application/vnd.github+json"},
        json={"name": "web", "active": True, "events": ["push"],
              "config": {"url": space_url + "/webhook", "content_type": "json", "secret": webhook_secret, "insecure_ssl": "0"}},
        timeout=30)
    print(f"::notice title=RIU_WEBHOOK_REGISTER::status={hook_resp.status_code} body={hook_resp.text[:300]}")


if __name__ == "__main__":
    main()
