"""Launches a REAL local model server on the Director's OWN Hugging Face account (his compute, his Job, NOT a third-party paid API, NOT
downloaded anywhere else): llama.cpp's official server image, mounting the model weights straight from the Hub (hf://…:/model:ro, no download
into any other machine), on cpu-basic (free flavor). Exposes a port; the Router's local_pool.py can then call it as just another endpoint."""
from __future__ import annotations

import os
import time

import requests
from huggingface_hub import HfApi

MODEL_REPO = "ggml-org/Qwen3.5-0.8B-GGUF"
MODEL_FILE = "Qwen3.5-0.8B-Q4_0.gguf"
PORT = 8080


def note(title: str, msg: str, level: str = "notice") -> None:
    print(f"::{level} title=RIU_OWNSERVER_{title}::{msg}".replace("\n", " ")[:900], flush=True)


def main() -> int:
    token = os.environ["HF_TOKEN"]
    api = HfApi(token=token)
    cmd = ["/app/llama-server", "-m", f"/model/{MODEL_FILE}", "--host", "0.0.0.0", "--port", str(PORT), "-c", "8192", "-np", "4", "-cb",
           "--cache-prompt", "--cache-reuse", "256", "--cache-ram", "512", "-fa", "on", "-ctk", "q8_0", "-ctv", "q8_0"]
    try:
        job = api.run_job(image="ghcr.io/ggml-org/llama.cpp:server", command=cmd, flavor="cpu-basic", timeout="30m",
                          expose=[PORT], volumes=[f"hf://models/{MODEL_REPO}:/model:ro"])
    except Exception as exc:  # noqa: BLE001
        note("LAUNCH_ERROR", f"{type(exc).__name__}: {str(exc)[:400]}", "warning")
        return 1
    note("JOB_ID", str(job.id))
    t0, ok, url, urls, stage = time.time(), None, None, [], None
    while time.time() - t0 < 480 and ok is None:
        info = api.inspect_job(job_id=job.id)
        stage = info.status.stage
        cand = [getattr(info, "endpoint", None), getattr(job, "endpoint", None), f"https://{job.id}--{PORT}.hf.jobs"]
        urls = [u for u in dict.fromkeys(cand) if u]
        if stage == "RUNNING":
            for u in urls:
                try:
                    r = requests.get(str(u).rstrip("/") + "/health", headers={"Authorization": "Bearer " + token}, timeout=15)
                    if r.status_code == 200:
                        ok = u
                        break
                except Exception:  # noqa: BLE001
                    pass
        if stage in ("ERROR", "COMPLETED", "CANCELED", "DELETED"):
            break
        time.sleep(10)
    logs = []
    try:
        for line in api.fetch_job_logs(job_id=job.id):
            logs.append(str(line))
    except Exception as exc:  # noqa: BLE001
        logs.append(f"logs: {type(exc).__name__}")
    note("STATE", f"stage={stage} health_ok_url={ok} urls_probadas={urls} logs_final={' | '.join(logs[-6:])[:500]}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
