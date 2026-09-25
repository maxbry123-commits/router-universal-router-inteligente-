"""Chat Router YAIWES — HF Space (cpu-basic 16 GB, se despierta al abrirlo).
Sirve la pantalla del chat y reenvía todo al Router con las claves guardadas como secretos del Space (nunca en el navegador ni en el repo).
Botones de energía: encender/apagar el Router (Job de HF) y encender/apagar el procesador de los agentes.
Secretos del Space: HF_TOKEN, RIU_ROUTER_API_KEY, GH_TOKEN.
"""
from __future__ import annotations

import base64
import os
import re

import requests
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, Response

REPO = "maxbry123-commits/router-universal-router-inteligente-"
FLAG = "router inteligente universal/agents-yaiwes/ROUTER_JOB_PAUSE.flag"
AGENTS_FLAG = "router inteligente universal/agents-yaiwes/AGENTS_PAUSE.flag"
ROUTER_WF = "riu-router-job-central.yml"
AGENT_WFS = ("riu-agents-run.yml", "riu-watchdog.yml", "riu-agent-inbox-poller.yml")
HF = os.getenv("HF_TOKEN", "")
KEY = os.getenv("RIU_ROUTER_API_KEY", "")
GH = os.getenv("GH_TOKEN", "")
PROXY = ("v1/", "chat/", "gh/", "control/", "groups", "health")

app = FastAPI()


def gh(method: str, path: str, **kw) -> requests.Response:
    return requests.request(method, f"https://api.github.com/repos/{REPO}{path}", timeout=20,
                            headers={"Authorization": f"Bearer {GH}", "Accept": "application/vnd.github+json"}, **kw)


def read(path: str) -> tuple[str, str | None]:
    r = gh("GET", f"/contents/{requests.utils.quote(path)}")
    if r.status_code != 200:
        return "", None
    d = r.json()
    return base64.b64decode(d["content"]).decode(), d["sha"]


def write(path: str, text: str, msg: str) -> None:
    _, sha = read(path)
    body = {"message": msg, "content": base64.b64encode(text.encode()).decode()}
    if sha:
        body["sha"] = sha
    gh("PUT", f"/contents/{requests.utils.quote(path)}", json=body)


def set_paused(path: str, paused: bool) -> None:
    text, _ = read(path)
    rest = [ln for ln in text.splitlines() if ln and not ln.startswith("PAUSED=")]
    write(path, "\n".join([f"PAUSED={'true' if paused else 'false'}"] + rest) + "\n", f"chat: PAUSED={paused}")


def live_url() -> str:
    m = re.search(r"LIVE_URL=(\S+)", read(FLAG)[0])
    return m.group(1).rstrip("/") if m else ""


def router_alive(url: str) -> bool:
    if not url:
        return False
    try:
        return requests.get(url + "/health", headers={"Authorization": f"Bearer {HF}"}, timeout=8).status_code == 200
    except requests.RequestException:
        return False


@app.get("/")
def index() -> FileResponse:
    return FileResponse("index.html")


@app.get("/power/status")
def status() -> dict:
    url = live_url()
    return {"router": "encendido" if router_alive(url) else "apagado",
            "agentes": "pausados" if "PAUSED=true" in read(AGENTS_FLAG)[0] else "activos"}


@app.post("/power/router/on")
def router_on() -> dict:
    if router_alive(live_url()):
        set_paused(FLAG, False)
        return {"ok": True, "estado": "ya estaba encendido"}
    set_paused(FLAG, False)
    r = gh("POST", f"/actions/workflows/{ROUTER_WF}/dispatches", json={"ref": "main", "inputs": {"lifetime": "6h"}})
    return {"ok": r.status_code == 204, "estado": "encendiendo (tarda 2 a 5 minutos)"}


@app.post("/power/router/off")
def router_off() -> dict:
    url = live_url()
    m = re.match(r"https://([0-9a-f]+)--", url)
    stopped = False
    if m:
        try:
            from huggingface_hub import HfApi
            HfApi(token=HF).cancel_job(job_id=m.group(1))
            stopped = True
        except Exception:
            stopped = False
    set_paused(FLAG, True)
    return {"ok": True, "estado": "apagado" if stopped else "en pausa"}


@app.post("/power/agents/{accion}")
def agents(accion: str) -> dict:
    on = accion == "on"
    for wf in AGENT_WFS:
        gh("PUT", f"/actions/workflows/{wf}/{'enable' if on else 'disable'}")
    set_paused(AGENTS_FLAG, not on)
    return {"ok": True, "estado": "agentes encendidos" if on else "agentes apagados"}


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy(path: str, request: Request) -> Response:
    if not path.startswith(PROXY):
        return JSONResponse({"error": "ruta desconocida"}, status_code=404)
    url = live_url()
    if not router_alive(url):
        return JSONResponse({"error": "El Router está apagado. Dale a Encender Router."}, status_code=503)
    headers = {"Authorization": f"Bearer {HF}", "X-API-Key": KEY}
    ct = request.headers.get("content-type")
    if ct:
        headers["Content-Type"] = ct
    r = requests.request(request.method, f"{url}/{path}", params=dict(request.query_params), data=await request.body(),
                         headers=headers, timeout=180)
    return Response(content=r.content, status_code=r.status_code, media_type=r.headers.get("content-type"))
