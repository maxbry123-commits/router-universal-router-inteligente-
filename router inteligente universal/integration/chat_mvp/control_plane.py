"""Control maestro del Router (Director 2026-10-03): banco auto-abierto, laboratorio de pruebas, fichas vivas y puente Hugging Face.

Todo cuelga del UNICO Router; nada aqui crea otro router. Ningun endpoint devuelve el valor de una clave: solo numero, proveedor,
cuenta y una huella sha256 de 8 caracteres.

* Banco:  RIU_VAULT_PASSPHRASE (secreto del entorno) abre el Secret Bank al arrancar. Si el archivo del banco no existe y
          RIU_VAULT_SOURCE apunta a un .b64 cifrado en un bucket/dataset HF, se baja primero (es texto cifrado: seguro).
* Lab:    /lab/run numera cada API/SDK del banco y del entorno, hace 3 pruebas (modelos, respuesta, tool-calling; o identidad,
          limite y repos para GitHub) y guarda el informe en SQLite (sincronizado al bucket HF) y en el bucket (lab/latest.json).
* Fichas: /fichas: plantillas vivas (single | queue | parallel | council) de 1 a 20 modelos con system prompt de anclaje,
          plantilla y dataset. Cada ficha nueva puede ser espejo de otra (parent + version). /fichas/catalog se recalcula
          solo con lo que haya en el banco y en HF: una API nueva aparece sin tocar codigo.
* HF:     /hf/*: estado, modelos, datasets, skills, computo (Jobs), modelo local en GPU y cambio de procesador del Router
          (lo aplica el micro-kernel de la puerta).
"""
from __future__ import annotations

import base64
import concurrent.futures as cf
import gzip
import hashlib
import importlib.util
import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from . import providers as prov
from .router import _auth, get_store

log = logging.getLogger("riu")
HF_NS = os.getenv("RIU_HF_NAMESPACE", "COMAND-CENTER-1")
REGISTRY_PATH = "control/router-current.json"
DESIRED_PATH = "control/router-desired.json"
MAX_MEMBERS = 20
SDK_MODULES = ("openai", "anthropic", "groq", "huggingface_hub", "mcp", "httpx", "google.genai")


def _fp(secret: str | None) -> str:
    return hashlib.sha256((secret or "").encode()).hexdigest()[:8]


def _hf_token() -> str:
    return os.getenv("HF_TOKEN") or os.getenv("HF_CONTROL_JOBS_TOKEN") or ""


def _fs():
    from huggingface_hub import HfFileSystem

    return HfFileSystem(token=_hf_token(), skip_instance_cache=True)  # no stale listings (control files change)


def _bucket() -> str | None:
    return os.getenv("HF_BUCKET_ID") or None


def bucket_write_json(path: str, data: Any) -> bool:
    bucket = _bucket()
    if not bucket or not _hf_token():
        return False
    try:
        _fs().pipe_file(f"buckets/{bucket}/{path}", json.dumps(data, ensure_ascii=False, indent=2).encode())
        return True
    except Exception as exc:  # noqa: BLE001
        log.warning("bucket write %s fallo: %s", path, type(exc).__name__)
        return False


def bucket_read_json(path: str) -> Any:
    bucket = _bucket()
    if not bucket or not _hf_token():
        return None
    try:
        return json.loads(_fs().cat_file(f"buckets/{bucket}/{path}"))
    except Exception:  # noqa: BLE001
        return None


# ---------------------------------------------------------------- banco auto-abierto
def vault_autounlock() -> dict[str, Any]:
    from .vault_bridge import bridge

    passphrase = os.getenv("RIU_VAULT_PASSPHRASE", "")
    if not passphrase:
        return {"status": "SKIPPED", "reason": "RIU_VAULT_PASSPHRASE ausente"}
    path = bridge.path()
    source = os.getenv("RIU_VAULT_SOURCE", "")  # buckets/<ns>/<bucket>/.../vault.db.gz.b64 (ciphertext)
    if not path.is_file() and source and _hf_token():
        try:
            raw = _fs().cat_file(source)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(gzip.decompress(base64.b64decode(raw)))
        except Exception as exc:  # noqa: BLE001
            return {"status": "GAP", "reason": f"VAULT_DOWNLOAD:{type(exc).__name__}"}
    prov_src = os.getenv("RIU_VAULT_PROVIDERS_SOURCE", "")  # providers.json kept next to the bank: new SDKs without touching code
    if prov_src and _hf_token() and not os.getenv("RIU_VAULT_PROVIDERS_FILE"):
        try:
            local = path.parent / "bank_providers.json"
            local.write_bytes(_fs().cat_file(prov_src))
            json.loads(local.read_text(encoding="utf-8"))
            os.environ["RIU_VAULT_PROVIDERS_FILE"] = str(local)
        except Exception as exc:  # noqa: BLE001 - built-in providers keep working
            log.warning("providers del banco no cargados: %s", type(exc).__name__)
    try:
        count = bridge.unlock(passphrase)
        return {"status": "UNLOCKED", "credentials": count}
    except Exception as exc:  # noqa: BLE001
        return {"status": "GAP", "reason": f"VAULT_UNLOCK:{str(exc)[:60]}"}


# ---------------------------------------------------------------- laboratorio
def _credentials() -> list[dict[str, Any]]:
    """Numbered inventory: every key of the bank (by ref) and of the environment (by var name). Values stay inside."""
    from .vault_bridge import bridge, provider_map

    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    vp_to_router = {v: k for k, v in provider_map().items()}
    if bridge._alive():  # noqa: SLF001 - same package
        for rec in bridge._open.list():  # noqa: SLF001
            if not rec.get("enabled", True) or rec.get("provider") == "router":
                continue
            try:
                secret = bridge._open.get_secret(rec["credential_ref"])  # noqa: SLF001
            except Exception:  # noqa: BLE001
                continue
            fp = _fp(secret)
            seen.add(fp)
            out.append({"source": "banco", "provider": vp_to_router.get(rec["provider"], rec["provider"]), "vault_provider": rec["provider"],
                        "account": rec["account"], "fp": fp, "_secret": secret})
    for name, entry in prov.registry().items():
        for var in entry.get("env", ()):
            secret = os.getenv(var)
            if secret and _fp(secret) not in seen:
                seen.add(_fp(secret))
                out.append({"source": "entorno", "provider": name, "vault_provider": name, "account": var, "fp": _fp(secret), "_secret": secret})
    for i, c in enumerate(out, 1):
        c["n"] = f"N{i:02d}"
    return out


def _pick_model(provider: str, models: list[str]) -> str | None:
    prefs = {"nvidia": ["moonshotai/kimi-k3", "z-ai/glm-5.3", "meta/llama-3.3-70b-instruct"],
             "hf": ["Qwen/Qwen3-32B", "Qwen/Qwen2.5-72B-Instruct", "meta-llama/Llama-3.3-70B-Instruct"],
             "groq": ["qwen/qwen3.8-27b", "llama-3.3-70b-versatile"], "openai": ["gpt-5.4", "gpt-4.1-mini", "gpt-4o-mini"],
             "anthropic": ["claude-haiku-4-5", "claude-sonnet-4-5"]}
    for m in prefs.get(provider, []):
        if m in models:
            return m
    chatty = [m for m in models if any(t in m.lower() for t in ("instruct", "chat", "qwen", "llama", "gpt", "claude", "kimi", "glm"))]
    chatty = [m for m in chatty if not any(t in m.lower() for t in ("embed", "audio", "tts", "whisper", "image", "realtime", "transcribe", "guard"))]
    return (chatty or models or [None])[0]


def _probe(cred: dict[str, Any]) -> dict[str, Any]:
    provider, key = cred["provider"], cred["_secret"]
    tests: list[dict[str, Any]] = []
    models: list[str] = []

    def t(name: str, fn) -> Any:  # noqa: ANN001
        t0 = time.monotonic()
        try:
            res = fn()
            tests.append({"test": name, "ok": True, "ms": int((time.monotonic() - t0) * 1000), "detail": res})
            return res
        except Exception as exc:  # noqa: BLE001
            msg = str(exc).replace(key, "***")[:160] if key else str(exc)[:160]
            tests.append({"test": name, "ok": False, "ms": int((time.monotonic() - t0) * 1000), "detail": msg})
            return None

    if cred["vault_provider"] == "github":
        def gh(path: str) -> Any:
            return prov._http("GET", "https://api.github.com" + path, key, None, 20)  # noqa: SLF001
        t("identidad", lambda: gh("/user").get("login"))
        t("limite", lambda: gh("/rate_limit").get("rate", {}).get("remaining"))
        t("repos", lambda: len(gh("/user/repos?per_page=5")))
    elif prov.base_url(provider):
        listed = t("modelos", lambda: prov.list_models(provider, key))
        models = listed if isinstance(listed, list) else []
        if listed is not None:
            tests[-1]["detail"] = {"count": len(models), "sample": models[:8]}
        model = _pick_model(provider, models)
        if model:
            t("respuesta", lambda: model + " -> " + (prov.chat(provider, key, model, [{"role": "user", "content": "Return exactly: OK"}], 256)["message"]["content"] or "")[:40])
            tool = {"type": "function", "function": {"name": "ping", "description": "ping", "parameters": {"type": "object", "properties": {}}}}

            def tools_test() -> str:
                tok = prov.EXTRA_PAYLOAD.set({"tools": [tool], "tool_choice": "auto"})
                try:
                    out = prov.chat(provider, key, model, [{"role": "user", "content": "Call the ping tool now."}], 64)
                finally:
                    prov.EXTRA_PAYLOAD.reset(tok)
                return "tool_calls" if out["message"].get("tool_calls") else "respondio sin tool_calls"
            t("herramientas", tools_test)
        else:
            tests.append({"test": "respuesta", "ok": False, "ms": 0, "detail": "sin modelo listado"})
            tests.append({"test": "herramientas", "ok": False, "ms": 0, "detail": "sin modelo listado"})
    else:
        tests.append({"test": "registro", "ok": False, "ms": 0, "detail": f"proveedor {provider} sin base_url en el banco"})
    passed = sum(1 for x in tests if x["ok"])
    status = "OK" if tests and passed == len(tests) else ("PARCIAL" if passed else "FALLA")
    return {"n": cred["n"], "source": cred["source"], "provider": provider, "account": cred["account"], "fp": cred["fp"],
            "status": status, "passed": f"{passed}/{len(tests)}", "tests": tests, "models_available": models[:200]}


def lab_run(store: Any = None) -> dict[str, Any]:
    creds = _credentials()
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(_probe, creds))
    sdks = [{"sdk": m, "instalado": importlib.util.find_spec(m.split(".")[0]) is not None} for m in SDK_MODULES]
    report = {"schema": "yaiwes.lab-report/v1", "run_id": uuid.uuid4().hex[:12], "ts": time.time(),
              "resumen": {"total": len(results), "ok": sum(r["status"] == "OK" for r in results),
                          "parcial": sum(r["status"] == "PARCIAL" for r in results), "falla": sum(r["status"] == "FALLA" for r in results)},
              "apis": results, "sdks": sdks}
    store = store or get_store()
    store._exec("CREATE TABLE IF NOT EXISTS lab_runs(run_id TEXT PRIMARY KEY, ts REAL, body TEXT)")  # noqa: SLF001
    store._exec("INSERT INTO lab_runs(run_id, ts, body) VALUES(?,?,?)", (report["run_id"], report["ts"], json.dumps(report, ensure_ascii=False)))  # noqa: SLF001
    report["bucket"] = bucket_write_json("lab/latest.json", report) and bucket_write_json(f"lab/reports/{report['run_id']}.json", report)
    return report


def lab_last(store: Any = None) -> dict[str, Any] | None:
    store = store or get_store()
    store._exec("CREATE TABLE IF NOT EXISTS lab_runs(run_id TEXT PRIMARY KEY, ts REAL, body TEXT)")  # noqa: SLF001
    rows = store._all("SELECT body FROM lab_runs ORDER BY ts DESC LIMIT 1")  # noqa: SLF001
    return json.loads(rows[0]["body"]) if rows else None


# ---------------------------------------------------------------- fichas vivas
class Member(BaseModel):
    model: str = Field(min_length=1, max_length=160)  # "auto" | group | "provider:model"
    system_prompt: str = Field(default="", max_length=20000)
    template: str = Field(default="{input}", max_length=20000)
    dataset: dict[str, str] | None = None  # {"repo": "...", "file": "..."}: anchor text from an HF dataset
    max_tokens: int = Field(default=1024, ge=1, le=32768)
    temperature: float | None = None


class Ficha(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    mode: str = Field(default="single", pattern=r"^(single|queue|parallel|council)$")
    anchor_system_prompt: str = Field(default="", max_length=20000)
    members: list[Member] = Field(min_length=1, max_length=MAX_MEMBERS)
    judge: Member | None = None  # council: synthesises the members' answers
    notes: str = Field(default="", max_length=4000)


class FichaReq(BaseModel):
    base_id: str | None = None  # mirror: copy this ficha, apply the changes, version+1
    ficha: dict[str, Any] = Field(default_factory=dict)


class RunReq(BaseModel):
    input: str = Field(min_length=1, max_length=200000)


def _ftable(store: Any) -> None:
    store._exec("CREATE TABLE IF NOT EXISTS fichas(id TEXT PRIMARY KEY, version INTEGER, parent TEXT, body TEXT, created REAL)")  # noqa: SLF001


def ficha_get(store: Any, fid: str) -> dict[str, Any]:
    _ftable(store)
    rows = store._all("SELECT id, version, parent, body, created FROM fichas WHERE id=?", (fid,))  # noqa: SLF001
    if not rows:
        raise HTTPException(status_code=404, detail="FICHA_NOT_FOUND")
    r = rows[0]
    return {"id": r["id"], "version": r["version"], "parent": r["parent"], "created": r["created"], **json.loads(r["body"])}


def ficha_save(store: Any, req: FichaReq) -> dict[str, Any]:
    _ftable(store)
    body: dict[str, Any] = {}
    parent, version = None, 1
    if req.base_id:
        base = ficha_get(store, req.base_id)
        parent, version = base["id"], int(base["version"]) + 1
        body = {k: v for k, v in base.items() if k not in {"id", "version", "parent", "created"}}
    body.update(req.ficha)
    ficha = Ficha(**body)  # validates (1..20 members, modes)
    fid = "F-" + uuid.uuid4().hex[:10]
    store._exec("INSERT INTO fichas(id, version, parent, body, created) VALUES(?,?,?,?,?)",  # noqa: SLF001
                (fid, version, parent, ficha.model_dump_json(), time.time()))
    return ficha_get(store, fid)


def _dataset_text(ds: dict[str, str] | None) -> str:
    if not ds or not ds.get("repo") or not ds.get("file"):
        return ""
    try:
        return _fs().cat_file(f"datasets/{ds['repo']}/{ds['file']}").decode("utf-8", errors="replace")[:20000]
    except Exception as exc:  # noqa: BLE001
        return f"[dataset no disponible: {type(exc).__name__}]"


def _member_call(f: Ficha, m: Member, text: str) -> dict[str, Any]:
    from .openai_route import run_chat

    system = "\n\n".join(x for x in (f.anchor_system_prompt, m.system_prompt, _dataset_text(m.dataset)) if x)
    msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": m.template.replace("{input}", text)}]
    t0 = time.monotonic()
    try:
        out = run_chat(m.model, msgs, m.max_tokens, m.temperature, None)
        return {"model": m.model, "route": f"{out['route']['provider']}/{out['route']['model']}", "ok": True,
                "ms": int((time.monotonic() - t0) * 1000), "content": out["message"].get("content") or ""}
    except Exception as exc:  # noqa: BLE001
        return {"model": m.model, "ok": False, "ms": int((time.monotonic() - t0) * 1000), "error": str(getattr(exc, "detail", exc))[:300]}


def ficha_run(store: Any, fid: str, text: str) -> dict[str, Any]:
    data = ficha_get(store, fid)
    f = Ficha(**{k: v for k, v in data.items() if k not in {"id", "version", "parent", "created"}})
    steps: list[dict[str, Any]] = []
    final: str | None
    if f.mode == "single":
        steps = [_member_call(f, f.members[0], text)]
        final = steps[0].get("content")
    elif f.mode == "queue":
        current = text
        for m in f.members:
            step = _member_call(f, m, current)
            steps.append(step)
            if step["ok"]:
                current = step["content"]
        final = current
    else:
        with cf.ThreadPoolExecutor(max_workers=min(len(f.members), MAX_MEMBERS)) as ex:
            steps = list(ex.map(lambda m: _member_call(f, m, text), f.members))
        final = None
        if f.mode == "council":
            judge = f.judge or f.members[0]
            joined = "\n\n".join(f"### Respuesta {i + 1} ({s['model']})\n{s.get('content') or s.get('error')}" for i, s in enumerate(steps))
            tmpl = "Pregunta:\n" + text + "\n\nRespuestas del consejo:\n{input}\n\nSintetiza la mejor respuesta final."
            verdict = _member_call(f, Member(**{**judge.model_dump(), "template": tmpl}), joined)
            steps.append({**verdict, "role": "juez"})
            final = verdict.get("content")
    return {"ficha": fid, "version": data["version"], "mode": f.mode, "final": final, "steps": steps}


def catalog() -> dict[str, Any]:
    """What the selector can offer right now: groups and every provider with keys (banco + entorno) with its listed models."""
    from . import resilience

    out: dict[str, Any] = {"groups": ["auto", *resilience.DEFAULT_POLICY], "providers": {}}

    def one(name: str) -> tuple[str, dict[str, Any]]:
        keys = prov.env_keys(name)
        if not keys and not (name == "local" and prov.base_url("local")):
            return name, {"configured": False}
        err = ""
        for key in (keys or [None])[:6]:  # first key that answers (a dead key must not hide the provider)
            try:
                models = prov.list_models(name, key)
                return name, {"configured": True, "keys": len(keys), "models": [f"{name}:{m}" for m in models[:300]]}
            except Exception as exc:  # noqa: BLE001
                err = str(exc)[:120]
        return name, {"configured": True, "keys": len(keys), "error": err}

    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        for name, info in ex.map(one, list(prov.registry())):
            out["providers"][name] = info
    return out


# ---------------------------------------------------------------- puente Hugging Face
GPU_ALLOWED = tuple(x for x in os.getenv("RIU_HF_GPU_FLAVORS", "t4-small,l4x1").split(",") if x)
CPU_ALLOWED = ("cpu-basic", "cpu-upgrade")


class ComputeReq(BaseModel):
    command: list[str] = Field(min_length=1, max_length=50)
    image: str = Field(default="python:3.12", max_length=200)
    flavor: str = Field(default="cpu-basic", max_length=40)
    timeout: str = Field(default="30m", pattern=r"^\d+[smhd]$")
    expose: list[int] = Field(default_factory=list, max_length=3)
    env: dict[str, str] = Field(default_factory=dict)


class ServeReq(BaseModel):
    repo: str = Field(min_length=3, max_length=200)  # HF model repo (local model stored on HF)
    flavor: str = Field(default="l4x1", max_length=40)
    timeout: str = Field(default="2h", pattern=r"^\d+[smhd]$")


class HardwareReq(BaseModel):
    flavor: str = Field(pattern=r"^(cpu-basic|cpu-upgrade|cpu-xl|cpu-performance)$")
    relaunch_now: bool = False


def _api():  # noqa: ANN202
    from huggingface_hub import HfApi

    if not _hf_token():
        raise HTTPException(status_code=503, detail="HF_TOKEN ausente")
    return HfApi(token=_hf_token())


def _check_flavor(flavor: str) -> None:
    if flavor not in CPU_ALLOWED + GPU_ALLOWED:
        raise HTTPException(status_code=400, detail=f"FLAVOR_NO_AUTORIZADO:{flavor} (permitidos {CPU_ALLOWED + GPU_ALLOWED})")


def build_control_router() -> APIRouter:
    r = APIRouter()

    @r.post("/vault/autounlock")
    def vault_open(_owner: str = Depends(_auth)) -> dict[str, Any]:
        return vault_autounlock()

    @r.post("/lab/run")
    def lab(_owner: str = Depends(_auth)) -> dict[str, Any]:
        return lab_run()

    @r.get("/lab/last")
    def lab_latest(_owner: str = Depends(_auth)) -> dict[str, Any]:
        return lab_last() or {"status": "SIN_INFORMES"}

    @r.get("/fichas")
    def fichas(_owner: str = Depends(_auth)) -> dict[str, Any]:
        store = get_store()
        _ftable(store)
        rows = store._all("SELECT id, version, parent, body, created FROM fichas ORDER BY created DESC LIMIT 500")  # noqa: SLF001
        out = []
        for x in rows:
            b = json.loads(x["body"])
            out.append({"id": x["id"], "version": x["version"], "parent": x["parent"], "name": b.get("name"), "mode": b.get("mode"),
                        "models": [m.get("model") for m in b.get("members", [])]})
        return {"fichas": out}

    @r.get("/fichas/catalog")
    def fichas_catalog(_owner: str = Depends(_auth)) -> dict[str, Any]:
        return catalog()

    @r.get("/fichas/{fid}")
    def ficha_read(fid: str, _owner: str = Depends(_auth)) -> dict[str, Any]:
        return ficha_get(get_store(), fid)

    @r.post("/fichas")
    def ficha_create(req: FichaReq, _owner: str = Depends(_auth)) -> dict[str, Any]:
        try:
            return ficha_save(get_store(), req)
        except HTTPException:
            raise
        except Exception as exc:  # validation
            raise HTTPException(status_code=422, detail=f"FICHA_INVALIDA:{str(exc)[:400]}") from exc

    @r.post("/fichas/{fid}/run")
    def ficha_exec(fid: str, req: RunReq, _owner: str = Depends(_auth)) -> dict[str, Any]:
        return ficha_run(get_store(), fid, req.input)

    @r.get("/hf/status")
    def hf_status(_owner: str = Depends(_auth)) -> dict[str, Any]:
        api = _api()
        who = api.whoami().get("name")
        reg = bucket_read_json(REGISTRY_PATH) or {}
        job_id = os.getenv("RIU_JOB_ID") or reg.get("job_id")
        info: dict[str, Any] = {}
        if job_id:
            try:
                j = api.inspect_job(job_id=job_id)
                info = {"job_id": job_id, "stage": str(getattr(j.status, "stage", "")), "flavor": getattr(j, "flavor", None)}
            except Exception as exc:  # noqa: BLE001
                info = {"job_id": job_id, "error": type(exc).__name__}
        return {"account": who, "router_compute": info, "registry": reg, "desired": bucket_read_json(DESIRED_PATH),
                "bucket": _bucket(), "gpu_flavors": GPU_ALLOWED}

    @r.post("/hf/hardware")
    def hf_hardware(req: HardwareReq, _owner: str = Depends(_auth)) -> dict[str, Any]:
        """Change the Router processor remotely: the micro-kernel relaunches it with this flavor (now, or at the next renewal)."""
        desired = {"flavor": req.flavor, "relaunch_now": req.relaunch_now, "ts": time.time()}
        if not bucket_write_json(DESIRED_PATH, desired):
            raise HTTPException(status_code=503, detail="BUCKET_NO_DISPONIBLE")
        return {"status": "ACCEPTED", "desired": desired}

    @r.get("/hf/models")
    def hf_models(search: str | None = None, author: str | None = None, limit: int = 30, _owner: str = Depends(_auth)) -> dict[str, Any]:
        rows = _api().list_models(search=search, author=author or (None if search else HF_NS), limit=min(limit, 100))
        return {"models": [{"id": m.id, "downloads": getattr(m, "downloads", None), "pipeline": getattr(m, "pipeline_tag", None)} for m in rows]}

    @r.get("/hf/datasets")
    def hf_datasets(repo: str | None = None, _owner: str = Depends(_auth)) -> dict[str, Any]:
        api = _api()
        if repo:
            return {"repo": repo, "files": api.list_repo_files(repo, repo_type="dataset")[:500]}
        return {"datasets": [d.id for d in api.list_datasets(author=HF_NS, limit=100)]}

    @r.get("/hf/datasets/file")
    def hf_dataset_file(repo: str, path: str, _owner: str = Depends(_auth)) -> dict[str, Any]:
        return {"repo": repo, "path": path, "content": _dataset_text({"repo": repo, "file": path})}

    @r.get("/hf/skills")
    def hf_skills(_owner: str = Depends(_auth)) -> dict[str, Any]:
        reg = Path(__file__).resolve().parents[1] / "huggingface" / "hf_skills_registry.json"
        try:
            data = json.loads(reg.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            data = {}
        return {"registry": data.get("skills", []), "upstream": data.get("upstream"), "hub_repo": "https://github.com/huggingface/skills"}

    @r.post("/hf/compute/run")
    def hf_compute(req: ComputeReq, _owner: str = Depends(_auth)) -> dict[str, Any]:
        """Compute for anything connected to the Router: one paid HF Job, no new router or process to open by hand."""
        _check_flavor(req.flavor)
        job = _api().run_job(image=req.image, command=req.command, flavor=req.flavor, timeout=req.timeout,
                             expose=req.expose or None, env=req.env or None)
        return {"job_id": job.id, "flavor": req.flavor, "urls": [f"https://{job.id}--{p}.hf.jobs" for p in req.expose]}

    @r.get("/hf/compute/{job_id}")
    def hf_compute_status(job_id: str, _owner: str = Depends(_auth)) -> dict[str, Any]:
        j = _api().inspect_job(job_id=job_id)
        return {"job_id": job_id, "stage": str(getattr(j.status, "stage", "")), "message": getattr(j.status, "message", None)}

    @r.delete("/hf/compute/{job_id}")
    def hf_compute_cancel(job_id: str, _owner: str = Depends(_auth)) -> dict[str, Any]:
        _api().cancel_job(job_id=job_id)
        return {"job_id": job_id, "status": "CANCELED"}

    @r.post("/hf/local/serve")
    def hf_local_serve(req: ServeReq, _owner: str = Depends(_auth)) -> dict[str, Any]:
        """Serve a model stored on HF (vLLM, OpenAI API) on a GPU Job and plug it as provider `local` of the Router."""
        _check_flavor(req.flavor)
        job = _api().run_job(image="vllm/vllm-openai:latest", command=["vllm", "serve", req.repo, "--port", "8000"],
                             flavor=req.flavor, timeout=req.timeout, expose=[8000],
                             secrets={"HF_TOKEN": _hf_token()} if _hf_token() else None)
        url = f"https://{job.id}--8000.hf.jobs/v1"
        os.environ["RIU_LOCAL_BASE_URL"] = url
        os.environ["RIU_LOCAL_API_KEY"] = _hf_token()  # the hf.jobs proxy wants an HF token with read access
        return {"job_id": job.id, "base_url": url, "provider": "local", "model": f"local:{req.repo}",
                "nota": "usable cuando el Job este RUNNING y vLLM haya cargado el modelo"}

    return r
