"""Webhook receiver, as a Gradio Space (free hardware, no payment method needed) instead of Docker.
Gradio's own FastAPI app (`demo.app`) gets the real /webhook route mounted on it — same logic as before, just a different Space type."""
from __future__ import annotations

import base64
import os
import re
import time

import gradio as gr
import requests
from fastapi import Request
from huggingface_hub import HfApi

REPO_RAW = "https://raw.githubusercontent.com/maxbry123-commits/router-universal-router-inteligente-/main/router%20inteligente%20universal/agents-yaiwes/ROUTER_JOB_PAUSE.flag"
GH_CONTENTS_API = "https://api.github.com/repos/maxbry123-commits/router-universal-router-inteligente-/contents/router%20inteligente%20universal/agents-yaiwes/ROUTER_JOB_PAUSE.flag"


def current_live_url() -> str | None:
    try:
        text = requests.get(REPO_RAW, timeout=10).text
        m = re.search(r"^LIVE_URL=(\S+)", text, re.M)
        return m.group(1) if m else None
    except Exception:  # noqa: BLE001
        return None


def router_alive(url: str) -> bool:
    try:
        r = requests.get(url.rstrip("/") + "/health", timeout=8)
        return r.status_code == 200
    except Exception:  # noqa: BLE001
        return False


def launch_router_job() -> str | None:
    hf_token, gh_token = os.environ["HF_TOKEN"], os.environ["GH_JOB_PUSH_TOKEN"]
    api = HfApi(token=hf_token)
    cmd = ("set -e; apt-get update -qq >/dev/null 2>&1 || true; command -v git >/dev/null || apt-get install -y -qq git >/dev/null 2>&1; "
           "git clone --depth 1 https://github.com/maxbry123-commits/router-universal-router-inteligente- /tmp/r && cd /tmp/r && "
           "pip install -q fastapi 'uvicorn[standard]' pydantic huggingface_hub cryptography pyyaml requests && "
           "python 'router inteligente universal/agents-yaiwes/common/router_job_persistent.py'")
    job = api.run_job(image="python:3.12", command=["bash", "-lc", cmd], flavor="cpu-upgrade", timeout="6h", expose=[8000],
                      secrets={"GITHUB_TOKEN": gh_token})
    t0, ok = time.time(), None
    while time.time() - t0 < 300 and ok is None:
        info = api.inspect_job(job_id=job.id)
        if info.status.stage == "RUNNING":
            url = f"https://{job.id}--8000.hf.jobs"
            if router_alive(url):
                ok = url
        elif info.status.stage in ("ERROR", "COMPLETED", "CANCELED", "DELETED"):
            break
        time.sleep(8)
    if not ok:
        return None
    get = requests.get(GH_CONTENTS_API, headers={"Authorization": "Bearer " + gh_token}, timeout=15).json()
    new_content = f"PAUSED=false\nLIVE_URL={ok}\n"
    requests.put(GH_CONTENTS_API, headers={"Authorization": "Bearer " + gh_token},
                json={"message": "webhook: relanzado el Router central (URL nueva)", "content": base64.b64encode(new_content.encode()).decode(), "sha": get["sha"]}, timeout=15)
    return ok


def status_check() -> str:
    live = current_live_url()
    if live and router_alive(live):
        return f"Router vivo: {live}"
    return f"Router NO responde (última URL conocida: {live}). Usa el webhook o el botón para relanzarlo."


with gr.Blocks(title="RIU Webhook Receiver") as demo:
    gr.Markdown("# Receptor de webhook del Router Inteligente Universal\nSiempre despierto. Revisa/relanza el Job del Router.")
    out = gr.Textbox(label="Estado")
    gr.Button("Revisar ahora").click(status_check, outputs=out)

app = demo.app


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "receiver": "alive"}


@app.post("/webhook")
async def webhook(request: Request) -> dict:
    event = request.headers.get("X-GitHub-Event", "unknown")
    live = current_live_url()
    if live and router_alive(live):
        return {"event": event, "action": "ROUTER_YA_VIVO", "url": live}
    new_url = launch_router_job()
    return {"event": event, "action": "ROUTER_RELANZADO" if new_url else "FALLO_AL_RELANZAR", "url": new_url}


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
