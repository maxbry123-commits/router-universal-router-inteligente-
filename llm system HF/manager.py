"""
manager.py — Proxy + llama-server + stream SSE + verificacion SHA-256 (Salida 1/3 HF)
Ubicacion: llm system HF/manager.py
Carga bajo demanda, idle unload, stream opcional, health con sha256.
"""
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse, StreamingResponse
import httpx
import os
import json
import hashlib
import subprocess
import time
import signal

ROUTER_API_KEY = os.getenv("ROUTER_API_KEY")
if not ROUTER_API_KEY:
    raise RuntimeError("FATAL: ROUTER_API_KEY no configurada.")

MODEL_ID = os.getenv("MODEL_ID", "Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF")
MODEL_FILE = os.getenv("MODEL_FILE", "qwen2.5-coder-0.5b-instruct-q5_k_m.gguf")
MODEL_PATH = os.getenv("MODEL_PATH", f"/data/models/{MODEL_FILE}")
IDLE_UNLOAD_S = int(os.getenv("IDLE_UNLOAD_S", "900"))
LLAMA_TIMEOUT_S = int(os.getenv("LLAMA_TIMEOUT_S", "300"))
LLAMA_PORT = 8081


def _detect_threads(default: int = 8,
                    cgroup_v2: str = "/sys/fs/cgroup/cpu.max",
                    cgroup_v1_quota: str = "/sys/fs/cgroup/cpu/cpu.cfs_quota_us",
                    cgroup_v1_period: str = "/sys/fs/cgroup/cpu/cpu.cfs_period_us") -> int:
    """Numero real de hilos para llama-server.

    En un Space de HF (cpu-upgrade = 8 vCPU) el contenedor ve NPROC=64 (los
    nucleos del host), pero la cuota real es de 8 vCPU. Sin --threads,
    llama.cpp usa std::thread::hardware_concurrency() -> 64 hilos sobre 8 vCPU
    (oversubscribcion) y se pierde 3-7x de velocidad de generacion.
    Aqui se lee la cuota real del cgroup (v2 y v1). Override: LLAMA_THREADS.
    """
    env = os.getenv("LLAMA_THREADS")
    if env:
        try:
            n = int(env)
            if n > 0:
                return n
        except ValueError:
            pass
    try:  # cgroup v2: "<quota> <period>" o "max <period>"
        with open(cgroup_v2, "r", encoding="utf-8") as f:
            parts = f.read().split()
        if len(parts) >= 2 and parts[0] != "max":
            quota, period = int(parts[0]), int(parts[1])
            if quota > 0 and period > 0:
                return max(1, int(round(quota / period)))
    except Exception:
        pass
    try:  # cgroup v1
        with open(cgroup_v1_quota, "r", encoding="utf-8") as f:
            quota = int(f.read().strip())
        with open(cgroup_v1_period, "r", encoding="utf-8") as f:
            period = int(f.read().strip())
        if quota > 0 and period > 0:
            return max(1, int(round(quota / period)))
    except Exception:
        pass
    return default


LLAMA_THREADS = _detect_threads()
HERE = os.path.dirname(os.path.abspath(__file__))
REGISTRY_PATH = os.path.join(HERE, "registry.json")

app = FastAPI()
_llama_proc = None
_last_call = 0.0
_model_loaded = False
_model_sha256 = None


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _verify_model():
    global _model_sha256
    if not os.path.exists(MODEL_PATH):
        return False
    actual = _sha256_file(MODEL_PATH)
    _model_sha256 = actual
    try:
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            reg = json.load(f)
        space = os.getenv("SPACE_ID", "s1")
        entry = reg.get("models", {}).get(space, {})
        expected = entry.get("sha256")
        if not expected:
            entry["sha256"] = actual
            entry["path"] = MODEL_PATH
            reg.setdefault("models", {})[space] = entry
            with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
                json.dump(reg, f, indent=2, ensure_ascii=False)
            return True
        return expected == actual
    except Exception:
        return True


def _load_llama():
    global _llama_proc, _model_loaded, _last_call
    if _llama_proc is not None:
        return
    if not _verify_model():
        _model_loaded = False
        return
    cmd = [
        "llama-server",
        "--model", MODEL_PATH,
        "--port", str(LLAMA_PORT),
        "--ctx-size", "4096",
        "--n-gpu-layers", "0",
    ]
    # --threads explicito: evita la oversubscribcion del cgroup de HF
    # (NPROC=64 con cuota de 8 vCPU -> 3-7x mas lento). Se anade FUERA de la
    # lista para no romper el parche --reasoning off que aplica entrypoint_v5.sh
    # (sed sobre '"--n-gpu-layers", "0"]').
    cmd += ["--threads", str(LLAMA_THREADS),
            "--threads-batch", str(LLAMA_THREADS)]
    # Flags de CPU medidos/verificados contra el binario oficial b12000:
    #   --cpu-strict 1  : colocacion estricta de CPU (+5% medido en la literatura)
    #   -ub 1024        : micro-lote mayor (el Job de flags medio +12% en el 0.8B)
    #   --cache-reuse   : reuso del prefijo de prompt (TTFT en bucles agenticos;
    #                     en los modelos con rope por secciones es un no-op)
    cmd += ["--cpu-strict", os.getenv("LLAMA_CPU_STRICT", "1"),
            "-ub", os.getenv("LLAMA_UBATCH", "1024"),
            "--cache-reuse", os.getenv("LLAMA_CACHE_REUSE", "256")]
    _llama_proc = subprocess.Popen(
        cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    _model_loaded = True
    _last_call = time.time()


def _unload_llama():
    global _llama_proc, _model_loaded
    if _llama_proc is not None:
        _llama_proc.send_signal(signal.SIGTERM)
        try:
            _llama_proc.wait(timeout=10)
        except Exception:
            _llama_proc.kill()
        _llama_proc = None
    _model_loaded = False


def _idle_check():
    if _llama_proc is not None and (time.time() - _last_call) > IDLE_UNLOAD_S:
        _unload_llama()


@app.get("/health")
def health():
    _idle_check()
    return {
        "status": "ok",
        "model_loaded": _model_loaded,
        "model_id": MODEL_ID,
        "model_file": MODEL_FILE,
        "sha256": _model_sha256,
        "idle_unload_s": IDLE_UNLOAD_S,
        "llama_threads": LLAMA_THREADS,
    }


def _check_key(x_api_key):
    if x_api_key != ROUTER_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")


@app.post("/v1/chat/completions")
async def chat_completions(request: Request, x_api_key: str = Header(None)):
    _check_key(x_api_key)
    _idle_check()
    _load_llama()
    if not _model_loaded:
        raise HTTPException(503, detail="Modelo no disponible (modo degradado)")
    body = await request.json()
    stream = bool(body.get("stream", False))
    global _last_call
    _last_call = time.time()
    payload = {
        "messages": body.get("messages", []),
        "temperature": body.get("temperature", 0.1),
        "max_tokens": body.get("max_tokens", 512),
        "stream": stream,
    }
    if stream:
        return StreamingResponse(_sse_proxy(payload), media_type="text/event-stream")
    async with httpx.AsyncClient(timeout=LLAMA_TIMEOUT_S) as client:
        r = await client.post(
            f"http://127.0.0.1:{LLAMA_PORT}/v1/chat/completions", json=payload
        )
        if r.status_code >= 400:
            raise HTTPException(502, detail=r.text[:300])
        return JSONResponse(r.json())


async def _sse_proxy(payload):
    async with httpx.AsyncClient(timeout=LLAMA_TIMEOUT_S) as client:
        async with client.stream(
            "POST",
            f"http://127.0.0.1:{LLAMA_PORT}/v1/chat/completions",
            json=payload,
        ) as r:
            async for line in r.aiter_lines():
                yield line + "\n"


@app.on_event("shutdown")
def shutdown():
    _unload_llama()
