
# ===================== WEBHOOK DEL ROUTER (añadido 2026-09-23, orden del Director) =====================
# GitHub -> POST https://comand-center-1-claude-github-mcp-backup.hf.space/webhook
# Si el Router central (LIVE_URL en ROUTER_JOB_PAUSE.flag) no responde, relanza el Job en HF (cpu-upgrade, 32 GB) en segundo plano
# y actualiza LIVE_URL en el repo. Todo protegido: si algo falla aquí, el conector MCP sigue funcionando igual.
import asyncio as _asyncio
import re as _re
import time as _time

_FLAG_PATH = "router inteligente universal/agents-yaiwes/ROUTER_JOB_PAUSE.flag"
_RELAUNCHING = {"busy": False}


async def _router_live_url() -> str | None:
    try:
        payload = await _github_request("GET", f"/repos/maxbry123-commits/router-universal-router-inteligente-/contents/{quote(_FLAG_PATH, safe='/')}")
        text = base64.b64decode(str(payload.get("content", "")).replace("\n", "")).decode("utf-8")
        m = _re.search(r"^LIVE_URL=(\S+)", text, _re.M)
        return m.group(1) if m else None
    except Exception:  # noqa: BLE001
        return None


async def _router_alive(url: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=8.0) as c:
            r = await c.get(url.rstrip("/") + "/health")
        return r.status_code == 200
    except Exception:  # noqa: BLE001
        return False


def _launch_router_job_sync() -> str | None:
    from huggingface_hub import HfApi
    api = HfApi(token=_required_env("HF_TOKEN"))
    cmd = ("set -e; apt-get update -qq >/dev/null 2>&1 || true; command -v git >/dev/null || apt-get install -y -qq git >/dev/null 2>&1; "
           "git clone --depth 1 https://github.com/maxbry123-commits/router-universal-router-inteligente- /tmp/r && cd /tmp/r && "
           "pip install -q fastapi 'uvicorn[standard]' pydantic huggingface_hub cryptography pyyaml requests && "
           "python 'router inteligente universal/agents-yaiwes/common/router_job_persistent.py'")
    job = api.run_job(image="python:3.12", command=["bash", "-lc", cmd], flavor="cpu-upgrade", timeout="6h", expose=[8000],
                      secrets={"GITHUB_TOKEN": _required_env("GITHUB_PERSONAL_ACCESS_TOKEN")})
    t0 = _time.time()
    while _time.time() - t0 < 300:
        info = api.inspect_job(job_id=job.id)
        if info.status.stage == "RUNNING":
            return f"https://{job.id}--8000.hf.jobs"
        if info.status.stage in ("ERROR", "COMPLETED", "CANCELED", "DELETED"):
            return None
        _time.sleep(8)
    return None


async def _relaunch_and_record() -> None:
    if _RELAUNCHING["busy"]:
        return
    _RELAUNCHING["busy"] = True
    try:
        url = await _asyncio.to_thread(_launch_router_job_sync)
        if not url:
            return
        for _ in range(30):
            if await _router_alive(url):
                break
            await _asyncio.sleep(10)
        path = f"/repos/maxbry123-commits/router-universal-router-inteligente-/contents/{quote(_FLAG_PATH, safe='/')}"
        cur = await _github_request("GET", path)
        body = {"message": "webhook: Router central relanzado (URL nueva)",
                "content": base64.b64encode(f"PAUSED=false\nLIVE_URL={url}\n".encode()).decode("ascii"), "sha": cur["sha"]}
        await _github_request("PUT", path, json_body=body)
    finally:
        _RELAUNCHING["busy"] = False


try:
    from starlette.requests import Request as _Request
    from starlette.responses import JSONResponse as _JSONResponse

    @mcp.custom_route("/webhook", methods=["POST", "GET"])
    async def _webhook(request: _Request) -> _JSONResponse:
        event = request.headers.get("X-GitHub-Event", "manual")
        live = await _router_live_url()
        if live and await _router_alive(live):
            return _JSONResponse({"event": event, "action": "ROUTER_YA_VIVO", "url": live})
        _asyncio.create_task(_relaunch_and_record())
        return _JSONResponse({"event": event, "action": "RELANZANDO_ROUTER", "previous_url": live}, status_code=202)
except Exception as _exc:  # noqa: BLE001 - never break the MCP connector because of the webhook add-on
    print(f"[webhook] no se pudo registrar la ruta /webhook: {type(_exc).__name__}: {_exc}")
