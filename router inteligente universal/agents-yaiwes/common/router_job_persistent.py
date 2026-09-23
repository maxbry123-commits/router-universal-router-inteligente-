"""Starts the ROUTER inside a persistent Hugging Face Job so that many agents (50-100) can all talk to the SAME running Router at once,
instead of a new one dying every time a GitHub Actions run finishes. Clones the repo fresh, places the encrypted bank, and runs uvicorn.
Before serving each request, a lightweight middleware re-reads `agents-yaiwes/ROUTER_JOB_PAUSE.flag`: if it contains "PAUSED", the Router
answers 503 instead of doing any work — this is the REMOTE pause switch: editing/pushing that one file pauses or resumes the Job without
touching it directly. The file is re-read from disk on every request (cheap), so a change takes effect within the same request, no restart.
"""
from __future__ import annotations

import base64
import gzip
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

REPO_URL = "https://github.com/maxbry123-commits/router-universal-router-inteligente-"
CLONE_DIR = Path("/tmp/r")
ROOT = CLONE_DIR / "router inteligente universal"
PAUSE_FLAG = CLONE_DIR / "router inteligente universal/agents-yaiwes/ROUTER_JOB_PAUSE.flag"


def sh(cmd: str) -> None:
    subprocess.run(cmd, shell=True, check=False)


def refresh_repo() -> None:
    if CLONE_DIR.exists():
        sh(f'cd "{CLONE_DIR}" && git pull --rebase origin main')
    else:
        sh(f'git clone --depth 1 "{REPO_URL}" "{CLONE_DIR}"')


def bank_text() -> str:
    mk = ROOT / "agent-microkernel"
    single = mk / "runtime-bank.db.gz.b64"
    if single.exists() and single.read_text().strip().startswith("H4sI"):
        return single.read_text().strip()
    return "".join(p.read_text().strip() for p in sorted(mk.glob("runtime-bank-v2.part*")))


def install_pause_middleware(app) -> None:  # noqa: ANN001
    from fastapi import Request
    from fastapi.responses import JSONResponse

    @app.middleware("http")
    async def pause_gate(request: Request, call_next):  # noqa: ANN001, ANN202
        try:
            paused = PAUSE_FLAG.exists() and "PAUSED" in PAUSE_FLAG.read_text()
        except OSError:
            paused = False
        if paused and request.url.path != "/health":
            return JSONResponse(status_code=503, content={"error": "ROUTER_JOB_PAUSED", "detail": "Pausado por el Director (ROUTER_JOB_PAUSE.flag). Sin cambios sin su autorización."})
        return await call_next(request)


def background_repull(interval: int = 60) -> None:
    while True:
        time.sleep(interval)
        refresh_repo()


def main() -> None:
    refresh_repo()
    vault = Path(os.environ.setdefault("RIU_VAULT_PATH", "/tmp/riu_vault.db"))
    os.environ.setdefault("RIU_DATA_DIR", "/tmp/riu")
    os.environ.setdefault("RIU_CHAT_ALLOW_PROVIDER_LIVE", "1")
    text = bank_text()
    if text:
        vault.write_bytes(gzip.decompress(base64.b64decode(text)))
    sys.path.insert(0, str(ROOT))
    threading.Thread(target=background_repull, daemon=True).start()
    from integration.chat_mvp.app import app  # noqa: E402
    install_pause_middleware(app)
    import uvicorn  # noqa: E402
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
