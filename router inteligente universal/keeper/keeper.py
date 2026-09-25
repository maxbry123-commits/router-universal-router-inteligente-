"""KEEPER — Job de HF cpu-basic (16 GB) siempre encendido.

Cada 5 minutos:
  1. Visita el Space del conector de Claude (MCP) y el chat de Vercel para que no se duerman; si el Space está dormido/parado, lo reinicia.
  2. Revisa el Router (/health) para saber si hay actividad de IA.
  3. Mide la RAM usada de esta máquina.
Si la RAM pasa de 10 GB o el Router tiene actividad de IA, enciende YA otro Job de 16 GB en espera (listo y preparado),
sin esperar a que haga falta. El Job en espera dura 60 minutos y se apaga solo si no se usa.
Registro: imprime una línea por vuelta (se ve en los logs del Job). Sin claves en código: HF_TOKEN llega como secreto del Job.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.request

HF = os.environ.get("HF_TOKEN", "")
SPACE = "COMAND-CENTER-1/claude-github-mcp-backup"
SPACE_URL = "https://comand-center-1-claude-github-mcp-backup.hf.space/"
CHAT_URL = "https://riu-jev-bridge.vercel.app/"
FLAG = "https://raw.githubusercontent.com/maxbry123-commits/router-universal-router-inteligente-/main/router%20inteligente%20universal/agents-yaiwes/ROUTER_JOB_PAUSE.flag"
RAM_LIMIT_GB = 10.0
EVERY = 300
STANDBY_MIN = 60
_last_standby = 0.0


def get(url: str, auth: bool = False, timeout: int = 30) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {HF}"} if auth else {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(200_000).decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception:
        return 0, ""


def post(url: str) -> int:
    req = urllib.request.Request(url, method="POST", headers={"Authorization": f"Bearer {HF}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


def ram_used_gb() -> float:
    info = {}
    with open("/proc/meminfo") as f:
        for line in f:
            k, v = line.split(":", 1)
            info[k] = int(v.split()[0])
    return (info["MemTotal"] - info.get("MemAvailable", info["MemFree"])) / 1024 / 1024


def router_active() -> bool:
    _, flag = get(FLAG)
    m = re.search(r"LIVE_URL=(\S+)", flag)
    if not m:
        return False
    code, body = get(m.group(1).rstrip("/") + "/health", auth=True)
    if code != 200:
        return False
    try:
        h = json.loads(body)
    except json.JSONDecodeError:
        return False
    # Actividad de IA: peticiones en curso o memoria del Router por encima del límite, si el Router lo informa.
    busy = int(h.get("in_flight") or h.get("active_requests") or 0)
    mem = float(h.get("ram_used_gb") or 0)
    return busy > 0 or mem > RAM_LIMIT_GB


def keep_space_awake() -> str:
    get(SPACE_URL, timeout=60)
    _, body = get(f"https://huggingface.co/api/spaces/{SPACE}/runtime", auth=True)
    try:
        stage = json.loads(body).get("stage", "?")
    except json.JSONDecodeError:
        stage = "?"
    if stage in ("SLEEPING", "PAUSED", "STOPPED", "RUNTIME_ERROR"):
        post(f"https://huggingface.co/api/spaces/{SPACE}/restart")
    return stage


def start_standby() -> str:
    global _last_standby
    if time.time() - _last_standby < STANDBY_MIN * 60:
        return "ya hay uno en espera"
    try:
        from huggingface_hub import HfApi
        job = HfApi(token=HF).run_job(image="python:3.12-slim", flavor="cpu-basic", timeout=f"{STANDBY_MIN}m",
                                      command=["python", "-c", f"import time; print('EN ESPERA LISTO'); time.sleep({STANDBY_MIN * 60})"])
        _last_standby = time.time()
        return f"en espera encendido: {job.id}"
    except Exception as e:  # noqa: BLE001
        return f"no se pudo encender el de espera: {type(e).__name__}"


def main() -> None:
    print("KEEPER encendido", flush=True)
    while True:
        stage = keep_space_awake()
        chat, _ = get(CHAT_URL)
        ram = ram_used_gb()
        active = router_active()
        note = ""
        if ram > RAM_LIMIT_GB or active:
            note = start_standby()
        print(f"{time.strftime('%H:%M:%S')} conector={stage} chat={chat} ram={ram:.1f}GB ia_activa={active} {note}", flush=True)
        time.sleep(EVERY)


if __name__ == "__main__":
    main()
