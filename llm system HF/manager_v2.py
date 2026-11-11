"""manager_v2.py — Idle unload 15 min (HF Plane, v2)
NOTA: NO reemplaza manager.py existente (commit 3fa2974). Corre paralelo.
"""
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse, StreamingResponse
import httpx, os, json, hashlib, subprocess, time, signal

ROUTER_API_KEY = os.getenv("ROUTER_API_KEY")
if not ROUTER_API_KEY:
    raise RuntimeError("FATAL: ROUTER_API_KEY no configurada.")

MODEL_ID = os.getenv("MODEL_ID", "Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF")
MODEL_FILE = os.getenv("MODEL_FILE", "qwen2.5-coder-0.5b-instruct-q5_k_m.gguf")
MODEL_PATH = os.getenv("MODEL_PATH", f"/data/models/{MODEL_FILE}")
IDLE_UNLOAD_S = int(os.getenv("IDLE_UNLOAD_S", "900"))
LLAMA_TIMEOUT_S = int(os.getenv("LLAMA_TIMEOUT_S", "300"))
LLAMA_PORT = 8082  # puerto distinto a manager.py (8081)
HERE = os.path.dirname(os.path.abspath(__file__))
REGISTRY_PATH = os.path.join(HERE, "registry.json")
API_PORT = 7861  # puerto distinto a manager.py (7860)

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
    cmd = ["llama-server", "--model", MODEL_PATH, "--port", str(LLAMA_PORT),
           "--ctx-size", "4096", "--n-gpu-layers", "0"]
    _llama_proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
    return {"status": "ok", "model_loaded": _model_loaded, "model_id": MODEL_ID,
            "model_file": MODEL_FILE, "sha256": _model_sha256,
            "idle_unload_s": IDLE_UNLOAD_S, "api_port": API_PORT}

@app.post("/v1/chat/completions")
async def chat_completions(request: Request, x_api_key: str = Header(None)):
    if x_api_key != ROUTER_API_KEY:
        raise HTTPException(401, "Invalid API Key")
    _idle_check()
    _load_llama()
    if not _model_loaded:
        raise HTTPException(503, "Modelo no disponible")
    body = await request.json()
    stream = bool(body.get("stream", False))
    global _last_call
    _last_call = time.time()
    payload = {"messages": body.get("messages", []),
               "temperature": body.get("temperature", 0.1),
               "max_tokens": body.get("max_tokens", 512), "stream": stream}
    if stream:
        async def sse():
            async with httpx.AsyncClient(timeout=LLAMA_TIMEOUT_S) as client:
                async with client.stream("POST",
                    f"http://127.0.0.1:{LLAMA_PORT}/v1/chat/completions",
                    json=payload) as r:
                    async for line in r.aiter_lines():
                        yield line + "\n"
        return StreamingResponse(sse(), media_type="text/event-stream")
    async with httpx.AsyncClient(timeout=LLAMA_TIMEOUT_S) as client:
        r = await client.post(
            f"http://127.0.0.1:{LLAMA_PORT}/v1/chat/completions", json=payload)
        if r.status_code >= 400:
            raise HTTPException(502, r.text[:300])
        return JSONResponse(r.json())

@app.on_event("shutdown")
def shutdown():
    _unload_llama()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=API_PORT)
