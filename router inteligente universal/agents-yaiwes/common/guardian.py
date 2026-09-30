"""guardian: vigilante autonomo del Router en Hugging Face (sin GitHub Actions).

Pensado para correr como un HF Job pequeno (cpu-basic). Cada ~60 s:
  1) lee LIVE_URL del flag del repo y comprueba /health del Router,
  2) mira la vida restante del Job del Router (API HF Jobs),
  3) si faltan < 6 h, o 3 fallos de /health seguidos, o no hay Router vivo:
     lanza un Router NUEVO (misma forma que el lanzador de riu-router-job-central.yml),
     espera /health 200, escribe LIVE_URL en el repo (API de contenidos) y SOLO ENTONCES cancela el viejo.
Vigilancia mutua: el guardian relanza al Router; el Router (plugins/lifeguard) relanza al guardian.
Las vidas se escalonan (Router 7d, guardian 5d) para que no venzan a la vez.

Anti-tormenta: 1 lanzamiento simultaneo (cerrojo), pausa minima entre relanzamientos, tope por hora,
GUARDIAN_DRY_RUN=1 (por defecto) no lanza nada: solo dice que haria.
Tokens SOLO por env: HF_CONTROL_JOBS_TOKEN, GH_AGENT_TOKEN. Nada de claves en el codigo.
Libreria estandar + huggingface_hub (import perezoso, solo para la API de Jobs).
"""
from __future__ import annotations

import base64
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

REPO = "maxbry123-commits/router-universal-router-inteligente-"
REPO_URL = "https://github.com/" + REPO
ROOT_DIR = "router inteligente universal"
FLAG_REL = ROOT_DIR + "/agents-yaiwes/ROUTER_JOB_PAUSE.flag"
ROUTER_SCRIPT = ROOT_DIR + "/agents-yaiwes/common/router_job_persistent.py"
GUARDIAN_SCRIPT = ROOT_DIR + "/agents-yaiwes/common/guardian.py"
MARKS = {"router": "router_job_persistent.py", "guardian": "guardian.py"}
ALIVE = ("RUNNING", "STARTING")
DEAD = ("ERROR", "COMPLETED", "CANCELED", "DELETED")
IMAGE = "python:3.12"
GROQ_MODEL_ENV = {"RIU_G2_GROQ_MODEL": "qwen/qwen3.8-27b"}
# Secretos que el Router necesita (mismos nombres que el lanzador actual). Se COPIAN del env del guardian.
PASSTHROUGH = (
    "GITHUB_TOKEN", "HF_CONTROL_JOBS_TOKEN", "HF_TOKEN_1", "GH_AGENT_TOKEN", "RIU_ROUTER_API_KEY", "RIU_AGENT_API_KEYS",
    *[f"NVIDIA_API_KEY_{i}" for i in range(1, 5)], *[f"GROQ_API_KEY_{i}" for i in range(2, 8)],
)
HttpFn = Callable[..., "tuple[int, bytes]"]


def parse_duration(text: Any, default: int = 0) -> int:
    """'7d' '48h' '90m' '30s' o numero de segundos -> segundos."""
    s = str(text or "").strip().lower()
    m = re.fullmatch("([0-9]+)[ ]*([smhd]?)", s)
    if not m:
        return default
    return int(m.group(1)) * {"": 1, "s": 1, "m": 60, "h": 3600, "d": 86400}[m.group(2)]


def _truthy(v: Any, default: bool) -> bool:
    if v is None or str(v).strip() == "":
        return default
    return str(v).strip().lower() not in ("0", "false", "no", "off")


@dataclass
class Config:
    hf_token: str = ""
    gh_token: str = ""
    dry_run: bool = True
    interval_s: int = 60
    renew_before_s: int = 6 * 3600
    fail_limit: int = 3
    min_pause_s: int = 600
    max_launches_per_hour: int = 3
    health_wait_s: int = 480
    poll_s: int = 10
    flavor_router: str = "cpu-basic"
    flavor_guardian: str = "cpu-basic"
    life_router: str = "7d"
    life_guardian: str = "5d"
    assumed_life_s: dict = field(default_factory=lambda: {"router": 24 * 3600, "guardian": 24 * 3600})
    expiry_overrides: dict = field(default_factory=dict)  # job_id -> epoch (p.ej. el Job vivo actual)
    state_path: str = "/tmp/guardian_state.json"
    ref: str = "main"
    live_url_fallback: str = ""
    own_job_id: str = ""
    environ: dict = field(default_factory=dict)

    @classmethod
    def from_env(cls, environ: "dict | None" = None) -> "Config":
        e = dict(os.environ if environ is None else environ)
        ov: dict = {}
        for part in (e.get("GUARDIAN_EXPIRY_OVERRIDES") or "").split(","):  # id=2026-10-01T21:49:00Z
            if "=" in part:
                jid, iso = part.split("=", 1)
                try:
                    import calendar
                    ov[jid.strip()] = calendar.timegm(time.strptime(iso.strip(), "%Y-%m-%dT%H:%M:%SZ"))
                except ValueError:
                    pass
        assumed = parse_duration(e.get("GUARDIAN_ASSUMED_LIFE"), 24 * 3600)
        return cls(
            hf_token=e.get("HF_CONTROL_JOBS_TOKEN", ""), gh_token=e.get("GH_AGENT_TOKEN", ""),
            dry_run=_truthy(e.get("GUARDIAN_DRY_RUN"), True),
            interval_s=parse_duration(e.get("GUARDIAN_INTERVAL"), 60),
            renew_before_s=parse_duration(e.get("GUARDIAN_RENEW_BEFORE"), 6 * 3600),
            fail_limit=int(e.get("GUARDIAN_FAIL_LIMIT") or 3),
            min_pause_s=parse_duration(e.get("GUARDIAN_MIN_PAUSE"), 600),
            max_launches_per_hour=int(e.get("GUARDIAN_MAX_PER_HOUR") or 3),
            flavor_router=e.get("GUARDIAN_ROUTER_FLAVOR", "cpu-basic"),
            flavor_guardian=e.get("GUARDIAN_FLAVOR", "cpu-basic"),
            life_router=e.get("GUARDIAN_ROUTER_LIFE", "7d"), life_guardian=e.get("GUARDIAN_LIFE", "5d"),
            assumed_life_s={"router": assumed, "guardian": assumed}, expiry_overrides=ov,
            state_path=e.get("GUARDIAN_STATE", "/tmp/guardian_state.json"),
            ref=e.get("GUARDIAN_REF", "main"), live_url_fallback=e.get("ROUTER_LIVE_URL", ""),
            own_job_id=e.get("JOB_ID", ""), environ=e,
        )


# ---------------------------------------------------------------- HTTP / HF (inyectables para tests)
def default_http(method: str, url: str, headers: "dict | None" = None, data: "bytes | None" = None, timeout: int = 20):
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read() or b""
    except Exception as e:  # noqa: BLE001
        return 0, str(e).encode()[:200]


def hf_api(cfg: Config):
    from huggingface_hub import HfApi  # perezoso
    return HfApi(token=cfg.hf_token)


def _stage(job: Any) -> str:
    st = getattr(getattr(job, "status", None), "stage", "") or ""
    return str(getattr(st, "value", st)).upper()


def _cmd_text(job: Any) -> str:
    return " ".join(str(x) for x in (getattr(job, "command", None) or []))


def alive_jobs(api: Any, kind: str) -> list:
    """Jobs vivos del tipo (router|guardian), el mas nuevo primero."""
    out = [j for j in api.list_jobs() if _stage(j) in ALIVE and MARKS[kind] in _cmd_text(j)]
    out.sort(key=lambda j: getattr(j, "created_at").timestamp(), reverse=True)
    return out


def expiry_epoch(job: Any, cfg: Config, kind: str) -> float:
    jid = str(getattr(job, "id", ""))
    if jid in cfg.expiry_overrides:
        return float(cfg.expiry_overrides[jid])
    secs = getattr(job, "timeout", None)
    if not isinstance(secs, (int, float)) or secs <= 0:
        env = getattr(job, "environment", None) or {}
        secs = parse_duration(env.get("RIU_JOB_LIFETIME_S"), 0) or cfg.assumed_life_s.get(kind, 24 * 3600)
    return getattr(job, "created_at").timestamp() + float(secs)


def remaining_s(job: Any, cfg: Config, kind: str, now: float) -> float:
    return expiry_epoch(job, cfg, kind) - now


# ---------------------------------------------------------------- LIVE_URL / health
def _gh_headers(cfg: Config) -> dict:
    h = {"Accept": "application/vnd.github+json", "User-Agent": "riu-guardian"}
    if cfg.gh_token:
        h["Authorization"] = "Bearer " + cfg.gh_token
    return h


def _flag_api_url() -> str:
    return "https://api.github.com/repos/" + REPO + "/contents/" + FLAG_REL.replace(" ", "%20")


def read_flag(cfg: Config, http: HttpFn) -> dict:
    """{'paused': bool, 'live_url': str|None, 'sha': str|None}"""
    st, body = http("GET", _flag_api_url(), _gh_headers(cfg), None, 20)
    if st != 200:
        return {"paused": False, "live_url": None, "sha": None, "error": f"flag GET {st}"}
    try:
        j = json.loads(body)
        text = base64.b64decode(j.get("content", "")).decode("utf-8", "replace")
    except (ValueError, TypeError):
        return {"paused": False, "live_url": None, "sha": None, "error": "flag ilegible"}
    m = re.search("^LIVE_URL=([^ " + chr(10) + "]+)", text, re.M)
    return {"paused": bool(re.search(r"^PAUSED=true", text, re.M)), "live_url": m.group(1) if m else None, "sha": j.get("sha")}


def write_live_url(cfg: Config, http: HttpFn, job_id: str, url: str, sleep: Callable = time.sleep) -> bool:
    """Actualiza LIVE_URL conservando PAUSED. 3 intentos."""
    for _ in range(3):
        cur = read_flag(cfg, http)
        nl = chr(10)
        content = f"PAUSED={'true' if cur['paused'] else 'false'}{nl}LIVE_URL={url}{nl}"
        body = {"message": f"flag: LIVE_URL {job_id} (guardian) [skip ci]", "content": base64.b64encode(content.encode()).decode()}
        if cur.get("sha"):
            body["sha"] = cur["sha"]
        st, _ = http("PUT", _flag_api_url(), {**_gh_headers(cfg), "Content-Type": "application/json"}, json.dumps(body).encode(), 20)
        if st in (200, 201):
            return True
        sleep(3)
    return False


def check_health(url: "str | None", cfg: Config, http: HttpFn) -> bool:
    if not url:
        return False
    st, _ = http("GET", url.rstrip("/") + "/health", {"Authorization": "Bearer " + cfg.hf_token}, None, 15)
    return st == 200


# ---------------------------------------------------------------- estado anti-tormenta
class State:
    def __init__(self, path: str):
        self.path, self.fails, self.launches, self.lock = path, {"router": 0, "guardian": 0}, [], threading.Lock()
        try:
            d = json.loads(Path(path).read_text())
            self.fails.update(d.get("fails", {}))
            self.launches = [float(x) for x in d.get("launches", [])]
        except (OSError, ValueError):
            pass

    def save(self) -> None:
        try:
            Path(self.path).write_text(json.dumps({"fails": self.fails, "launches": self.launches[-20:]}))
        except OSError:
            pass


def launch_allowed(state: State, cfg: Config, now: float) -> "tuple[bool, str]":
    if state.lock.locked():
        return False, "lanzamiento en curso (cerrojo)"
    recent = [t for t in state.launches if now - t < 3600]
    if recent and now - max(recent) < cfg.min_pause_s:
        return False, f"pausa minima {cfg.min_pause_s}s entre relanzamientos"
    if len(recent) >= cfg.max_launches_per_hour:
        return False, f"tope {cfg.max_launches_per_hour} lanzamientos/hora"
    return True, "ok"


# ---------------------------------------------------------------- forma del lanzamiento
def router_command() -> str:
    """Identico al lanzador de riu-router-job-central.yml."""
    return (
        "set -e; apt-get update -qq >/dev/null 2>&1 || true; "
        "command -v git >/dev/null || apt-get install -y -qq git >/dev/null 2>&1; "
        f"git clone --depth 1 {REPO_URL} /tmp/r && cd /tmp/r && "
        "pip install -q fastapi 'uvicorn[standard]' pydantic huggingface_hub cryptography pyyaml requests httpx psutil && "
        f"python '{ROUTER_SCRIPT}'"
    )


def guardian_command(ref: str = "main") -> str:
    """El guardian es autonomo (1 archivo): se baja solo ese archivo, sin clonar el repo."""
    raw = f"https://raw.githubusercontent.com/{REPO}/{ref}/" + GUARDIAN_SCRIPT.replace(" ", "%20")
    return f"set -e; pip install -q huggingface_hub && curl -fsSL '{raw}' -o /tmp/guardian.py && python /tmp/guardian.py"


def build_spec(kind: str, cfg: Config, life: "str | None" = None) -> dict:
    """Argumentos exactos de HfApi.run_job para el tipo pedido."""
    life = life or (cfg.life_router if kind == "router" else cfg.life_guardian)
    src = cfg.environ
    secrets = {k: src[k] for k in PASSTHROUGH if src.get(k)}
    if "GITHUB_TOKEN" not in secrets and src.get("GH_AGENT_TOKEN"):
        secrets["GITHUB_TOKEN"] = src["GH_AGENT_TOKEN"]
    if "HF_TOKEN_1" not in secrets and cfg.hf_token:
        secrets["HF_TOKEN_1"] = cfg.hf_token
    if cfg.hf_token:
        secrets["HF_CONTROL_JOBS_TOKEN"] = cfg.hf_token
    if kind == "router":
        cmd, flavor, expose, env = router_command(), cfg.flavor_router, [8000], dict(GROQ_MODEL_ENV)
    else:
        cmd, flavor, expose, env = guardian_command(cfg.ref), cfg.flavor_guardian, None, {"GUARDIAN_DRY_RUN": "0"}
        for k in ("GUARDIAN_EXPIRY_OVERRIDES", "GUARDIAN_ASSUMED_LIFE", "GUARDIAN_REF", "GUARDIAN_MIN_PAUSE", "GUARDIAN_MAX_PER_HOUR"):
            if src.get(k):
                env[k] = src[k]
    env["RIU_JOB_LIFETIME_S"] = str(parse_duration(life))
    spec = {"image": IMAGE, "command": ["bash", "-lc", cmd], "flavor": flavor, "timeout": life, "secrets": secrets, "env": env}
    if expose:
        spec["expose"] = expose
    return spec


def describe_spec(spec: dict) -> dict:
    """Vista sin valores secretos (solo nombres)."""
    d = {k: v for k, v in spec.items() if k != "secrets"}
    d["secrets"] = sorted(spec.get("secrets", {}))
    return d


def launch_with_ladder(kind: str, cfg: Config, api: Any) -> "tuple[Any, dict]":
    """Vida 7d/5d -> 48h -> 24h si HF rechaza (igual que el lanzador actual)."""
    want = cfg.life_router if kind == "router" else cfg.life_guardian
    last: "Exception | None" = None
    for life in dict.fromkeys([want, "48h", "24h"]):
        spec = build_spec(kind, cfg, life)
        try:
            return api.run_job(**spec), spec
        except Exception as e:  # noqa: BLE001
            last = e
    raise RuntimeError(f"HF rechazo todas las vidas: {str(last)[:120]}")


# ---------------------------------------------------------------- plan (puro) y ejecucion
def gather(kind: str, cfg: Config, api: Any, http: HttpFn, state: State, now: float, health_tries: int = 1) -> dict:
    jobs = alive_jobs(api, kind)
    info: dict = {"kind": kind, "alive": [str(j.id) for j in jobs], "fails": state.fails.get(kind, 0)}
    if jobs:
        info["newest"] = str(jobs[0].id)
        info["remaining_s"] = int(remaining_s(jobs[0], cfg, kind, now))
    if kind == "router":
        flag = read_flag(cfg, http)
        url = flag.get("live_url") or cfg.live_url_fallback or (f"https://{jobs[0].id}--8000.hf.jobs" if jobs else None)
        info["live_url"], info["paused"] = url, flag.get("paused", False)
        info["health_ok"] = any(check_health(url, cfg, http) for _ in range(max(1, health_tries)))
    return info


def decide(info: dict, cfg: Config) -> dict:
    """Decision pura: {'action': 'none'|'relaunch', 'reason': str}"""
    if not info.get("alive"):
        return {"action": "relaunch", "reason": "ausente: ningun Job vivo"}
    if info["kind"] == "router" and info.get("fails", 0) >= cfg.fail_limit:
        return {"action": "relaunch", "reason": f"/health fallo {info['fails']} veces seguidas"}
    if info.get("remaining_s", 1 << 40) < cfg.renew_before_s:
        return {"action": "relaunch", "reason": f"vence en {info['remaining_s'] // 60} min (< {cfg.renew_before_s // 3600} h)"}
    return {"action": "none", "reason": "sano"}


def relaunch(kind: str, cfg: Config, api: Any, http: HttpFn, state: State, reason: str = "manual",
             dry_run: "bool | None" = None, now: Callable = time.time, sleep: Callable = time.sleep) -> dict:
    dry = cfg.dry_run if dry_run is None else dry_run
    spec = build_spec(kind, cfg)
    res: dict = {"kind": kind, "reason": reason, "dry_run": dry, "would_run": describe_spec(spec), "steps": []}
    if not cfg.hf_token:
        return {**res, "ok": False, "error": "falta HF_CONTROL_JOBS_TOKEN"}
    ok_launch, why = launch_allowed(state, cfg, now())
    if not ok_launch:
        return {**res, "ok": False, "blocked": why}
    if dry:
        return {**res, "ok": True, "note": "dry_run: no se lanzo nada"}
    try:  # pausa entre procesos: otro guardian pudo lanzar hace poco
        young = [j for j in alive_jobs(api, kind) if now() - getattr(j, "created_at").timestamp() < cfg.min_pause_s]
    except Exception:  # noqa: BLE001
        young = []
    if young:
        return {**res, "ok": False, "blocked": f"ya hay un {kind} lanzado hace < {cfg.min_pause_s}s ({young[0].id})"}
    if not state.lock.acquire(blocking=False):
        return {**res, "ok": False, "blocked": "lanzamiento en curso (cerrojo)"}
    try:
        old = [str(j.id) for j in alive_jobs(api, kind)]
        state.launches.append(now())
        state.save()
        job, used = launch_with_ladder(kind, cfg, api)
        jid = str(job.id)
        res.update(new_job_id=jid, timeout=used["timeout"], old=old)
        res["steps"].append("lanzado " + jid)
        url = f"https://{jid}--8000.hf.jobs" if kind == "router" else None
        t0, good, stage = now(), False, ""
        while now() - t0 < cfg.health_wait_s:
            stage = _stage(api.inspect_job(job_id=jid))
            if stage in DEAD:
                break
            if stage == "RUNNING" and (kind == "guardian" or check_health(url, cfg, http)):
                good = True
                break
            sleep(cfg.poll_s)
        if not good:
            try:
                api.cancel_job(job_id=jid)  # el nuevo no arranco: se apaga, el viejo SIGUE
            except Exception:  # noqa: BLE001
                pass
            state.fails[kind] = state.fails.get(kind, 0)
            state.save()
            return {**res, "ok": False, "error": f"el nuevo no llego a sano (stage={stage}); viejo intacto"}
        res["steps"].append("sano")
        if kind == "router":
            if not write_live_url(cfg, http, jid, url, sleep):
                # no se apaga el viejo: LIVE_URL seguiria apuntando a el
                return {**res, "ok": False, "error": "no se pudo escribir LIVE_URL; viejo intacto", "new_url": url}
            res["steps"].append("LIVE_URL=" + url)
            res["live_url"] = url
        cancelled = []
        for oid in old:
            if oid == jid:
                continue
            try:
                api.cancel_job(job_id=oid)
                cancelled.append(oid)
            except Exception:  # noqa: BLE001
                pass
        res["cancelled"] = cancelled
        state.fails[kind] = 0
        state.save()
        return {**res, "ok": True}
    finally:
        state.lock.release()


def tick(kinds: "tuple[str, ...]", cfg: Config, api: Any, http: HttpFn, state: State,
         now: Callable = time.time, sleep: Callable = time.sleep) -> list:
    """Un ciclo: para cada tipo vigilado, reune, decide y (si toca) relanza."""
    out = []
    for kind in kinds:
        info = gather(kind, cfg, api, http, state, now())
        if kind == "router":
            state.fails[kind] = 0 if info["health_ok"] else state.fails.get(kind, 0) + 1
            info["fails"] = state.fails[kind]
        d = decide(info, cfg)
        entry = {"info": info, "decision": d}
        if d["action"] == "relaunch":
            entry["result"] = relaunch(kind, cfg, api, http, state, d["reason"], None, now, sleep)
        out.append(entry)
    state.save()
    return out


def run_forever(kinds: "tuple[str, ...]", cfg: Config, api: Any = None, http: HttpFn = default_http, state: "State | None" = None,
                sleep: Callable = time.sleep, now: Callable = time.time, max_ticks: "int | None" = None) -> None:
    api = api or hf_api(cfg)
    state = state or State(cfg.state_path)
    n = 0
    while max_ticks is None or n < max_ticks:
        n += 1
        try:
            for e in tick(kinds, cfg, api, http, state, now, sleep):
                r = e.get("result") or {}
                print(json.dumps({"t": int(now()), "kind": e["info"]["kind"], "decision": e["decision"], "ok": r.get("ok"),
                                  "blocked": r.get("blocked"), "new": r.get("new_job_id"), "dry": cfg.dry_run}), flush=True)
        except Exception as ex:  # noqa: BLE001  (el guardian nunca muere por un error de red)
            print(json.dumps({"t": int(now()), "error": str(ex)[:160]}), flush=True)
        sleep(cfg.interval_s)


def main(argv: "list[str] | None" = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    cfg = Config.from_env()
    if "--print-command" in argv:  # muestra lo que lanzaria, sin ejecutar
        print(json.dumps({k: describe_spec(build_spec(k, cfg)) for k in ("router", "guardian")}, indent=1))
        return 0
    if not cfg.hf_token:
        print("falta HF_CONTROL_JOBS_TOKEN", file=sys.stderr)
        return 2
    if "--once" in argv:
        api, st = hf_api(cfg), State(cfg.state_path)
        print(json.dumps(tick(("router", "guardian"), cfg, api, default_http, st), indent=1, default=str))
        return 0
    run_forever(("router", "guardian"), cfg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
