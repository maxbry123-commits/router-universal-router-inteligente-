"""Endpoints operativos Salida 3. Aditivo, no modifica código existente."""
from __future__ import annotations
import os, json, time, hashlib, uuid, statistics, difflib, pathlib
from pathlib import Path
from collections import deque
from typing import Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

_ART = Path(os.environ.get("ARTIFACT_DIR", "artifacts"))
_ROOT = _ART.parent if str(_ART.parent) else Path(".")
_AUDIT = _ROOT / ".audit.jsonl"
_AUDIT.parent.mkdir(parents=True, exist_ok=True)

def _audit(event, **kw):
    rec = {"ts": time.time(), "event": event, **kw}
    try:
        with open(_AUDIT, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
    except Exception: pass

# ---------------- providers health ----------------
PROVIDERS = ["local", "nvidia", "groq", "deterministic"]
_PSTATS = {p: {"ok": 0, "err": 0, "last": None, "lat": deque(maxlen=200)}
           for p in PROVIDERS}

def _p_probe():
    """Sonda rápida: lee variables de entorno para saber si el proveedor tiene claves."""
    return {
        "local": True,
        "nvidia": bool(os.environ.get("NVIDIA_KEYS") or os.environ.get("NVIDIA_KEY")),
        "groq": bool(os.environ.get("GROQ_KEYS") or os.environ.get("GROQ_KEY")),
        "deterministic": True,
    }

def _p_latency(p):
    xs = list(_PSTATS[p]["lat"])
    if not xs: return {"p50_ms": None, "p95_ms": None, "samples": 0}
    xs.sort()
    def _pct(pv): 
        i = max(0, int(len(xs)*pv)-1); return round(xs[i]*1000, 1)
    return {"p50_ms": _pct(0.5), "p95_ms": _pct(0.95),
            "samples": len(xs), "last_ms": round(xs[-1]*1000, 1)}

def record_provider_call(name, ok, seconds):
    if name in _PSTATS:
        st = _PSTATS[name]
        st["ok" if ok else "err"] += 1
        st["last"] = "ok" if ok else "err"
        st["lat"].append(seconds)

# ---------------- sandbox ----------------
SANDBOX_PROFILES = {
    "S0": {"id":"S0","name":"PLAN","isolated":True,"network":False,
           "disk":"none","exec":False,"timeout_s":60,
           "budget_tokens":0,"tier":0,"reversible":True,
           "acceptance":"outline_only","degrade_to":"S0"},
    "S1": {"id":"S1","name":"LOCAL-ISO","isolated":True,"network":False,
           "disk":"readonly","exec":True,"timeout_s":120,
           "budget_tokens":2000,"tier":1,"reversible":True,
           "acceptance":"read_ok","degrade_to":"S0"},
    "S2": {"id":"S2","name":"SNAPSHOT-GIT","isolated":True,"network":False,
           "disk":"git","exec":True,"timeout_s":300,
           "budget_tokens":8000,"tier":2,"reversible":True,
           "acceptance":"git_clean","degrade_to":"S1"},
    "S3": {"id":"S3","name":"DOCKER-SPACE","isolated":True,"network":False,
           "disk":"docker","exec":True,"timeout_s":600,
           "budget_tokens":20000,"tier":3,"reversible":True,
           "acceptance":"container_ok","degrade_to":"S2"},
    "S4": {"id":"S4","name":"PROXY-PUBLICO","isolated":True,"network":True,
           "disk":"sandbox","exec":True,"timeout_s":600,
           "budget_tokens":20000,"tier":4,"reversible":True,
           "acceptance":"proxy_logged","degrade_to":"S3"},
    "S5": {"id":"S5","name":"MCP-ALLOWLIST","isolated":True,"network":True,
           "disk":"sandbox","exec":True,"timeout_s":600,
           "budget_tokens":20000,"tier":5,"reversible":True,
           "acceptance":"allowlist_ok","degrade_to":"S4"},
}

# ---------------- secrets (session-scoped, memoria) ----------------
_SECRETS: dict = {}
_SECRET_TTL = float(os.environ.get("SECRET_TTL_S", "3600"))

def _cleanup_secrets():
    now = time.time()
    for k in list(_SECRETS):
        if _SECRETS[k]["expires_at"] < now:
            del _SECRETS[k]

# ---------------- rate limit ----------------
_RATE = {"window_s": 60, "max": int(os.environ.get("RATE_MAX_PER_MIN", "120")),
         "hits": deque(maxlen=1000)}
def rate_allow():
    now = time.time()
    while _RATE["hits"] and now - _RATE["hits"][0] > _RATE["window_s"]:
        _RATE["hits"].popleft()
    if len(_RATE["hits"]) >= _RATE["max"]:
        return False, len(_RATE["hits"])
    _RATE["hits"].append(now)
    return True, len(_RATE["hits"])

SERVICE_MODES = {
    "default": {"route":"/v1/chat/completions","status":"ok","adapter":"default"},
    "chat": {"route":"/v1/chat/completions","status":"ok","adapter":"chat"},
    "code_generate": {"route":"/v1/chat/completions","status":"ok","adapter":"code"},
    "recall": {"route":"/v1/recall","status":"ok","adapter":"recall"},
    "search": {"route":"/v1/chat/search","status":"ok","adapter":"search"},
    "file_ops": {"route":"/v1/artifacts","status":"ok","adapter":"files"},
    "sandbox_exec": {"route":"/v1/sandbox/profiles","status":"ok","adapter":"exec"},
    "embed": {"route":"/v1/embed","status":"degraded","adapter":"embed"},
    "vision": {"route":"/v1/chat/completions","status":"degraded","adapter":"vision"},
    "audio": {"route":"/v1/chat/completions","status":"degraded","adapter":"audio"},
    "translate": {"route":"/v1/chat/completions","status":"ok","adapter":"translate"},
    "summarize": {"route":"/v1/chat/completions","status":"ok","adapter":"summarize"},
}

ext_ops = APIRouter()

class SecretBody(BaseModel):
    name: str
    value: str
    ttl_s: int = 3600

# ---------------- providers ----------------
@ext_ops.get("/v1/providers/health")
async def providers_health():
    probe = _p_probe()
    items = []
    for p in PROVIDERS:
        st = _PSTATS[p]
        items.append({"id": p, "configured": probe[p],
                      "ok": st["ok"], "err": st["err"],
                      "last": st["last"]})
    return {"items": items, "count": len(items)}

@ext_ops.get("/v1/providers/latency")
async def providers_latency():
    return {"items": [{"id": p, **_p_latency(p)} for p in PROVIDERS]}

@ext_ops.get("/v1/providers/rate")
async def providers_rate():
    allow, used = rate_allow()
    return {"window_s": _RATE["window_s"], "max": _RATE["max"],
            "used": used, "allow_next": allow}

# ---------------- sandbox ----------------
@ext_ops.get("/v1/sandbox/profiles")
async def sandbox_profiles():
    return {"items": list(SANDBOX_PROFILES.values()),
            "count": len(SANDBOX_PROFILES)}

@ext_ops.get("/v1/sandbox/profiles/{pid}")
async def sandbox_profile(pid: str):
    p = SANDBOX_PROFILES.get(pid.upper())
    if not p: raise HTTPException(404, f"perfil {pid} no existe")
    return p

@ext_ops.get("/v1/sandbox/isolation")
async def sandbox_isolation():
    return {"current": os.environ.get("SANDBOX_PROFILE", "S2"),
            "network_default": False,
            "disk_default": "git",
            "degrade_on_missing": "S0",
            "policy": "sin sandbox → degrada a PLAN y avisa"}

@ext_ops.post("/v1/sandbox/secrets")
async def create_secret(b: SecretBody):
    _cleanup_secrets()
    token = str(uuid.uuid4())
    _SECRETS[b.name] = {"token": token, "value": b.value,
                        "scope": "session",
                        "expires_at": time.time() + b.ttl_s}
    _audit("secret.created", name=b.name, scope="session", ttl_s=b.ttl_s)
    # ADAPTACION DECLARADA: el smoke de 3B exige "scope" en la respuesta; el
    # endpoint lo guardaba pero no lo devolvia. Se expone (valor "session").
    return {"ok": True, "name": b.name, "token": token,
            "scope": _SECRETS[b.name]["scope"],
            "expires_at": _SECRETS[b.name]["expires_at"],
            "warning": "solo esta sesión; se borra al cerrar"}

@ext_ops.get("/v1/sandbox/secrets")
async def list_secrets():
    _cleanup_secrets()
    return {"items": [{"name": k, "scope": v["scope"],
                       "expires_at": v["expires_at"]}
                      for k, v in _SECRETS.items()]}

@ext_ops.delete("/v1/sandbox/secrets/{name}")
async def delete_secret(name: str):
    _cleanup_secrets()
    if name not in _SECRETS: raise HTTPException(404, "secret no existe")
    del _SECRETS[name]
    _audit("secret.deleted", name=name)
    return {"ok": True, "name": name}

# ---------------- audit ----------------
@ext_ops.get("/v1/audit")
async def get_audit(limit: int = 100):
    if not _AUDIT.exists(): return {"items": [], "count": 0}
    lines = _AUDIT.read_text(encoding="utf-8").splitlines()[-limit:]
    items = []
    for l in lines:
        try: items.append(json.loads(l))
        except Exception: pass
    return {"items": items, "count": len(items)}

# ---------------- artifacts diff/repro ----------------
@ext_ops.get("/v1/artifacts/{name}/diff")
async def artifacts_diff(name: str):
    safe = Path(name).name
    if not safe or safe in (".",".."): raise HTTPException(400, "nombre inválido")
    base = _ART / safe
    versions = []
    if base.exists(): versions.append(base)
    versions += sorted(_ART.glob(f"{safe}.v*"))
    if len(versions) < 2:
        return {"name": name, "diff": "", "versions": len(versions),
                "note": "menos de 2 versiones"}
    prev = versions[-2].read_text(encoding="utf-8", errors="replace")
    curr = versions[-1].read_text(encoding="utf-8", errors="replace")
    diff = "".join(difflib.unified_diff(prev.splitlines(True),
                                        curr.splitlines(True),
                                        fromfile=str(versions[-2].name),
                                        tofile=str(versions[-1].name)))
    return {"name": name, "versions": len(versions), "diff": diff}

@ext_ops.get("/v1/artifacts/{name}/repro")
async def artifacts_repro(name: str):
    safe = Path(name).name
    if not safe or safe in (".",".."): raise HTTPException(400, "nombre inválido")
    base = _ART / safe
    if not base.exists():
        raise HTTPException(404, f"artefacto {name} no existe")
    raw = base.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    seed = int(sha[:8], 16)
    return {"name": name, "sha256": sha, "size": len(raw),
            "seed": seed, "version": 1,
            "repro_hint": "misma semilla + mismo motor → mismo resultado",
            "mtime": base.stat().st_mtime}

# ---------------- service-modes ----------------
@ext_ops.get("/v1/service-modes")
async def service_modes():
    return {"items": [{"id": k, **v} for k, v in SERVICE_MODES.items()],
            "count": len(SERVICE_MODES)}
