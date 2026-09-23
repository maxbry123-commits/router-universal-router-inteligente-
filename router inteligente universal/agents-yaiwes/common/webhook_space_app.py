"""HF Space: listens for GitHub Webhooks (push events) and keeps the central Router Job alive — NO GitHub Actions anywhere in this path.
Verifies the webhook's HMAC signature with a shared secret (env WEBHOOK_SECRET). On any push, checks if the Router Job is still RUNNING;
if not (or about to expire), relaunches it. Also self-pings every 5 minutes so it never needs an external trigger to stay alive.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import threading
import time

import requests
from fastapi import FastAPI, Header, Request
from huggingface_hub import HfApi

HF_TOKEN = os.environ["HF_TOKEN"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
WEBHOOK_SECRET = os.environ["WEBHOOK_SECRET"]
REPO_URL = "https://github.com/maxbry123-commits/router-universal-router-inteligente-"
STATE: dict = {"job_id": None, "endpoint": None, "last_check": 0}
api = HfApi(token=HF_TOKEN)
app = FastAPI()


def launch_cmd() -> list[str]:
    sh = ("set -e; apt-get update -qq >/dev/null 2>&1 || true; command -v git >/dev/null || apt-get install -y -qq git >/dev/null 2>&1; "
          f"git clone --depth 1 {REPO_URL} /tmp/r && cd /tmp/r && "
          "pip install -q fastapi 'uvicorn[standard]' pydantic huggingface_hub cryptography pyyaml requests && "
          "python 'router inteligente universal/agents-yaiwes/common/router_job_persistent.py'")
    return ["bash", "-lc", sh]


def job_is_healthy() -> bool:
    if not STATE["endpoint"]:
        return False
    try:
        r = requests.get(STATE["endpoint"].rstrip("/") + "/health", timeout=8)
        return r.status_code == 200
    except Exception:  # noqa: BLE001
        return False


def ensure_router_alive() -> None:
    if job_is_healthy():
        return
    job = api.run_job(image="python:3.12", command=launch_cmd(), flavor="cpu-upgrade", timeout="6h", expose=[8000],
                      secrets={"GITHUB_TOKEN": GITHUB_TOKEN})
    STATE["job_id"] = job.id
    for _ in range(40):
        info = api.inspect_job(job_id=job.id)
        if info.status.stage == "RUNNING":
            STATE["endpoint"] = f"https://{job.id}--8000.hf.jobs"
            break
        time.sleep(6)


def watchdog_loop() -> None:
    while True:
        try:
            ensure_router_alive()
        except Exception:  # noqa: BLE001
            pass
        STATE["last_check"] = time.time()
        time.sleep(300)


@app.on_event("startup")
def start() -> None:
    threading.Thread(target=watchdog_loop, daemon=True).start()


@app.get("/health")
def health() -> dict:
    return {"ok": True, "router_endpoint": STATE["endpoint"], "last_check": STATE["last_check"]}


@app.post("/webhook")
async def webhook(request: Request, x_hub_signature_256: str = Header(default="")) -> dict:
    body = await request.body()
    expected = "sha256=" + hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, x_hub_signature_256 or ""):
        return {"ok": False, "error": "BAD_SIGNATURE"}
    threading.Thread(target=ensure_router_alive, daemon=True).start()
    return {"ok": True, "router_endpoint": STATE["endpoint"]}
