#!/usr/bin/env python3
"""Single-model llama-server manager (one model in memory per Space).
- OpenAI API on :8080: /v1/models, /v1/chat/completions, /v1/completions, /health, /status
- Loads model on demand (hf_hub_download from dataset), ONE llama-server at a time.
- Switching model: requests serialized by a lock; current server stopped, new one started.
- Idle unload: if no calls for IDLE_UNLOAD_S (default 300s) the llama-server is killed.
"""
import json, os, signal, subprocess, sys, threading, time, urllib.request, urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DATASET = os.environ.get("GGUF_DATASET", "COMAND-CENTER-1/swe-code-hf-gguf")
MODEL_DIR = os.environ.get("MODEL_DIR", "/data/models")
TOKEN = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
IDLE_UNLOAD_S = float(os.environ.get("IDLE_UNLOAD_S", "300"))
CHECK_S = float(os.environ.get("IDLE_CHECK_S", "30"))
CTX = os.environ.get("LLAMA_CTX", "8192")
NPRED = os.environ.get("LLAMA_NPREDICT", "512")
BATCH = os.environ.get("LLAMA_BATCH", "2048")
UBATCH = os.environ.get("LLAMA_UBATCH", "512")
BACKEND_PORT = 8081
BACKEND = f"http://127.0.0.1:{BACKEND_PORT}"

def _detect_threads():
    """Threads for llama-server. Prefer LLAMA_THREADS, else cgroup quota, else affinity capped at 8.
    Never use os.cpu_count() (HF Spaces host often reports 32)."""
    env = os.environ.get("LLAMA_THREADS")
    if env:
        return max(1, int(env))
    try:
        with open("/sys/fs/cgroup/cpu.max") as f:
            parts = f.read().split()
            if len(parts) >= 2 and parts[0] != "max":
                return max(1, int(parts[0]) // int(parts[1]))
    except Exception:
        pass
    try:
        with open("/sys/fs/cgroup/cpu/cpu.cfs_quota_us") as f:
            q = int(f.read())
        with open("/sys/fs/cgroup/cpu/cpu.cfs_period_us") as f:
            p = int(f.read())
        if q > 0 and p > 0:
            return max(1, q // p)
    except Exception:
        pass
    try:
        n = len(os.sched_getaffinity(0))
        return max(1, min(n, int(os.environ.get("LLAMA_THREADS_MAX", "8"))))
    except Exception:
        return 8

THREADS = _detect_threads()
MODELS = {
    "qwen2.5-coder-0.5b": "Qwen__Qwen2.5-Coder-0.5B-Instruct-GGUF__qwen2.5-coder-0.5b-instruct-q5_k_m.gguf",
    "qwen3.5-0.8b": "unsloth__Qwen3.5-0.8B-GGUF__Qwen3.5-0.8B-IQ4_XS.gguf",
    "lfm2.5-350m": "LiquidAI__LFM2.5-350M-GGUF__LFM2.5-350M-Q4_K_M.gguf",
}

# Flags de servidor MEDIDOS en cpu-upgrade (8 vCPU / 32 GB) por modelo — job 6aee67b6 (2026-11-06).
# -t 4 -tb 8 resulto PEOR en los 3 modelos -> se mantiene -t 8 -tb 8.
# 0.5B Q5_K_M : 59.3 -> 62.2 t/s (+5%)  con KV q8_0
# 0.8B IQ4_XS : 38.4 -> 84.0 t/s (+119%) con -ub 1024 + speculacion n-gram (IQ4_XS la aprovecha mucho)
# LFM 350M    : 143.1 -> 156.9 t/s (+10%) con KV q8_0
SERVER_FLAGS = {
    "qwen2.5-coder-0.5b": ["-ctk", "q8_0", "-ctv", "q8_0"],
    # 0.8B: SIN -ctk/-ctv q8_0 — medido: la KV cuantizada hace que el modelo se salte leer_archivo
    # y conteste mal (2 turnos, "MODO=config"); con KV f16 cierra en 3 turnos con la respuesta correcta.
    "qwen3.5-0.8b": ["-b", "2048", "-ub", "1024", "--spec-type", "ngram-mod",
                     "--spec-ngram-mod-n-max", "16", "--spec-ngram-mod-n-match", "8",
                     "--spec-ngram-mod-n-min", "4"],
    "lfm2.5-350m": ["-ctk", "q8_0", "-ctv", "q8_0"],
}
PRIMARY = os.environ.get("PRIMARY_MODEL", "qwen2.5-coder-0.5b")
# Optional GGUF LoRA adapters per model. Request field "lora" or env CODER_LORA / QWEN35_LORA / LFM_LORA.
LORA_DATASET = os.environ.get("LORA_DATASET", "COMAND-CENTER-1/swe-code-loras")  # repo_type=dataset, NOT GGUF_DATASET

# Acopladores instalados en swe-code-loras (modelos ya fusionados) -> alias de modelo adicional.
MODELS_EXT = {
    "qwen3.5-0.8b-agentic": (LORA_DATASET, "10_qwen3.5-0.8b-agentic-reasoning.gguf", "dataset"),
    "lfm2.5-350m-agente":   (LORA_DATASET, "11_lfm2.5-350m-agente-frontend.gguf", "dataset"),
    "lfm2.5-350m-tool":     (LORA_DATASET, "12_lfm2.5-350m-tool-shellai.gguf", "dataset"),
    "lfm2.5-350m-coder":    (LORA_DATASET, "13_lfm2.5-350m-coder.gguf", "dataset"),
}
LORAS_BY_MODEL = {
    "qwen2.5-coder-0.5b": {
        "agente-merge-resolver": (LORA_DATASET, "21_qwen2.5-coder-0.5b-agente-merge-resolver.gguf", "dataset"),
        "prog-cg-oss": (LORA_DATASET, "22_qwen2.5-coder-0.5b-prog-cg-oss.gguf", "dataset"),
    },
    "qwen3.5-0.8b": {
        "acrouter": (LORA_DATASET, "7_acrouter-lora-f16.gguf", "dataset"),
    },
    "lfm2.5-350m": {
        "python": ("Parallax-labs-1/LFM-2.5-350M-Python-Lora", "LFM2.5v350M-Python-Lora.gguf", "model"),
        "planner": ("Parallax-labs-1/LFM2.5v350M-Planner-Lora", "LFM2.5v350M-Planner-Lora.gguf", "model"),
    },
}
LORAS = sorted({a for d in LORAS_BY_MODEL.values() for a in d})
LORA_MODELS = set(LORAS_BY_MODEL)
DEFAULT_LORA = {
    "qwen2.5-coder-0.5b": (os.environ.get("CODER_LORA") or "none").strip().lower(),
    "qwen3.5-0.8b": (os.environ.get("QWEN35_LORA") or "none").strip().lower(),
    "lfm2.5-350m": (os.environ.get("LFM_LORA") or "none").strip().lower(),
}
LORA_SCALE = os.environ.get("LORA_SCALE", "1.0")

def resolve_lora(alias, req):
    if alias not in LORA_MODELS: return None
    v = str(req.pop("lora", None) or DEFAULT_LORA.get(alias, "none")).strip().lower()
    return v if v in LORAS_BY_MODEL[alias] else None

lock = threading.Lock()          # serializes load/switch AND inference (1 model, queue)
state = {"proc": None, "model": None, "lora": None, "last_used": 0.0, "loads": 0, "unloads": 0}

import re as _re
import hashlib as _hashlib

def _tool_names(req):
    out = set()
    for t in (req.get("tools") or []):
        f = t.get("function") or t
        n = f.get("name")
        if n: out.add(str(n))
    return out

def _extract_calls(o, names):
    """Saca llamadas a herramienta de varias formas: {name,arguments}, {function:{...}}, {tool_call:{...}}, lista."""
    calls = []
    def add(name, args):
        if not name: return
        if names and str(name) not in names:
            low = {str(n).lower() for n in names}
            if str(name).lower() not in low: return
        if isinstance(args, str):
            try: args = json.loads(args)
            except Exception: args = {"_raw": args}
        if not isinstance(args, dict): args = {"value": args}
        calls.append({"id": f"call_{len(calls)}", "type": "function",
                      "function": {"name": str(name), "arguments": json.dumps(args)}})
    if isinstance(o, list):
        for it in o: calls.extend(_extract_calls(it, names))
    elif isinstance(o, dict):
        if "tool_call" in o and isinstance(o["tool_call"], (dict, list)):
            calls.extend(_extract_calls(o["tool_call"], names))
        fn = o.get("function")
        if isinstance(fn, dict):
            add(fn.get("name"), fn.get("arguments") or fn.get("parameters") or {})
        if o.get("name") and (not fn or not isinstance(fn, dict)):
            add(o.get("name"), o.get("arguments") or o.get("parameters") or {})
        if not calls and o.get("type") == "function" and isinstance(o.get("function"), dict):
            add(o["function"].get("name"), o["function"].get("arguments") or {})
    return calls

def _all_json_objs(txt):
    """Todos los objetos JSON balanceados de un texto (el modelo puede repetir la llamada dentro del content)."""
    out = []
    t = _re.sub(r"^```(?:json)?\s*|\s*```\s*$", "", (txt or "").strip())
    i = t.find("{")
    while i != -1:
        depth = 0
        for j in range(i, len(t)):
            if t[j] == "{": depth += 1
            elif t[j] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        o = json.loads(t[i:j+1])
                        if isinstance(o, dict): out.append(o)
                    except Exception:
                        pass
                    break
        i = t.find("{", i+1)
    return out

def _fix_tool_calls(raw, req):
    """Fallback: el modelo imprimio la llamada como JSON de texto; se convierte a tool_calls de OpenAI."""
    if not req.get("tools") or req.get("stream"): return raw
    try:
        d = json.loads(raw); m = d["choices"][0]["message"]
        if m.get("tool_calls") or not m.get("content"): return raw
        txt = m["content"].strip()
        txt = _re.sub(r"^```(?:json)?\s*|\s*```\s*$", "", txt)
        txt = _re.sub(r"^<tool_call>\s*|\s*</tool_call>$", "", txt)
        names = _tool_names(req)
        calls = []
        for cand in _all_json_objs(txt):
            calls = _extract_calls(cand, names)
            if calls: break
        if not calls: return raw
        m["tool_calls"] = calls
        m["content"] = None
        d["choices"][0]["finish_reason"] = "tool_calls"
        return json.dumps(d).encode()
    except Exception:
        return raw

def _first_json_obj(txt):
    """Primer objeto JSON balanceado dentro de un texto (fences, prosa, etc.)."""
    t = _re.sub(r"^```(?:json)?\s*|\s*```\s*$", "", (txt or "").strip())
    try:
        o = json.loads(t)
        if isinstance(o, dict): return o
    except Exception:
        pass
    i = t.find("{")
    while i != -1:
        depth = 0
        for j in range(i, len(t)):
            if t[j] == "{": depth += 1
            elif t[j] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        o = json.loads(t[i:j+1])
                        if isinstance(o, dict): return o
                    except Exception:
                        pass
                    break
        i = t.find("{", i+1)
    return None

def _call_signature(m):
    """Firma de la llamada a herramienta de un mensaje assistant (nativa o en texto JSON)."""
    tc = m.get("tool_calls") or []
    if tc:
        fn = (tc[0].get("function") or {})
        return (str(fn.get("name") or ""), json.dumps(fn.get("arguments") or {}, sort_keys=True))
    fc = m.get("function_call")
    if isinstance(fc, dict) and fc.get("name"):
        return (str(fc.get("name")), json.dumps(fc.get("arguments") or {}, sort_keys=True))
    obj = _first_json_obj(m.get("content") or "")
    if obj:
        calls = _extract_calls(obj, set())
        if calls:
            fn = calls[0]["function"]
            return (str(fn["name"]), fn["arguments"])
    return None

def _reps(messages):
    """Numero de veces consecutivas que se repite la misma llamada a herramienta al final del historial."""
    sigs = []
    for m in (messages or []):
        if m.get("role") == "assistant":
            s = _call_signature(m)
            if s: sigs.append(s)
    if not sigs: return 0, None
    last = sigs[-1]; n = 0
    for s in reversed(sigs):
        if s == last: n += 1
        else: break
    return n, last

NUDGE = ("AVISO DE CONTROL DEL AGENTE: acabas de repetir la misma llamada a herramienta ({name}) {n} veces. "
         "YA TIENES su resultado en el historial (mensaje de rol 'tool'). NO vuelvas a llamar a {name}. "
         "Si te falta algun dato, llama a OTRA herramienta distinta. Si ya tienes todo, RESPONDE AL USUARIO "
         "ahora mismo con la conclusion.")

def _distinct_called(msgs):
    names = set()
    for m in (msgs or []):
        if m.get("role") == "assistant":
            s = _call_signature(m)
            if s: names.add(str(s[0]))
    return names

def _force_tool(req):
    """Si el cliente pasa herramientas y aun no se ha hecho NINGUNA llamada, se fuerza la primera
    (tool_choice=required). Sin esto, los modelos 0.5B/0.8B a temperatura 0 a veces responden
    'necesito mas detalles' en vez de actuar (medido: 0.8B 1 turno, sin llamar la herramienta)."""
    msgs = req.get("messages") or []
    if not req.get("tools") or req.get("tool_choice") not in (None, "", "auto"):
        return False
    ya_llamo = any(m.get("role") == "assistant" and (m.get("tool_calls") or m.get("function_call")) for m in msgs)
    ultimo_es_tool = bool(msgs) and msgs[-1].get("role") == "tool"
    if ya_llamo and not ultimo_es_tool:
        return False
    req["tool_choice"] = "required"
    log("force-tool: primera llamada forzada (tool_choice=required)")
    return True

def _anti_loop(req):
    """Anti-bucle agentico. Si el cliente repite la misma llamada a herramienta:
       1) la retira de la lista de tools de ESA peticion (el modelo no puede repetirla),
       2) si ya se han usado TODAS las herramientas, las quita todas: el modelo debe responder,
       3) inyecta un nudge de control,
       4) rompe el determinismo (temperature 0) subiendo la temperatura de esa peticion.
    Devuelve (n_reps, firma)."""
    msgs = req.get("messages") or []
    n, sig = _reps(msgs)
    if n < 2 or not sig:
        return n, sig
    name = sig[0]
    tools = req.get("tools")
    if tools:
        keep = [t for t in tools if str(((t.get("function") or t).get("name") or "")) != str(name)]
        if len(keep) != len(tools):
            req["tools"] = keep
            log(f"anti-loop: herramienta {name} retirada de la lista (quedan {len(keep)})")
        usadas = _distinct_called(msgs)
        disponibles = {str(((t.get("function") or t).get("name") or "")) for t in (req.get("tools") or [])}
        if disponibles and usadas and usadas >= disponibles:
            req.pop("tools", None)
            log("anti-loop: todas las herramientas ya usadas -> se quitan, el modelo debe responder")
    req.setdefault("messages", []).append({"role": "user", "content": NUDGE.format(name=name, n=n)})
    try:
        t = float(req.get("temperature") or 0)
    except Exception:
        t = 0.0
    if t <= 0.01:
        req["temperature"] = 0.6
        req["top_p"] = 0.95
        log("anti-loop: temperature 0 -> 0.6 para romper la repeticion determinista")
    log(f"anti-loop nudge: {n} reps de {name}")
    return n, sig

def log(*a): print("[manager]", *a, flush=True)

def resolve(name):
    n = str(name or "").strip()
    if n in MODELS or n in MODELS_EXT: return n
    low = n.lower()
    for k, f in list(MODELS.items()) + [(k, v[1]) for k, v in MODELS_EXT.items()]:
        if low and (low in k or k in low or low in f.lower()): return k
    return PRIMARY

def _stop():
    p = state["proc"]
    if p and p.poll() is None:
        log("stopping", state["model"], "pid", p.pid)
        p.send_signal(signal.SIGTERM)
        try: p.wait(20)
        except subprocess.TimeoutExpired: p.kill(); p.wait()
        state["unloads"] += 1
    state["proc"] = None; state["model"] = None; state["lora"] = None

def _healthy():
    try:
        with urllib.request.urlopen(BACKEND + "/health", timeout=3) as r: return r.status == 200
    except Exception: return False

def _ensure(alias, lora=None):
    """Must hold lock. Changing lora restarts llama-server (one model in RAM)."""
    p = state["proc"]
    if state["model"] == alias and state["lora"] == lora and p and p.poll() is None: return
    _stop()
    from huggingface_hub import hf_hub_download
    if alias in MODELS_EXT:
        _repo, _fn, _rt = MODELS_EXT[alias]
        path = hf_hub_download(repo_id=_repo, repo_type=_rt, filename=_fn,
                               local_dir=os.path.join(MODEL_DIR, "ext"), token=TOKEN)
    else:
        path = hf_hub_download(repo_id=DATASET, repo_type="dataset", filename=MODELS[alias],
                               local_dir=MODEL_DIR, token=TOKEN)
    log("loading", alias, path)
    cmd = ["llama-server", "-m", path, "--host", "127.0.0.1",
        "--port", str(BACKEND_PORT), "-c", CTX, "-n", NPRED,
        "-t", str(THREADS), "-tb", str(THREADS),
        "--alias", alias, "--jinja", "-fa", "on", "--parallel", "1",
        "--no-webui", "--cache-reuse", "256",
        "-b", str(BATCH), "-ub", str(UBATCH)]
    cmd += SERVER_FLAGS.get(alias, [])
    if lora:
        repo, fn, rtype = LORAS_BY_MODEL[alias][lora]
        lpath = hf_hub_download(repo_id=repo, repo_type=rtype, filename=fn,
                                local_dir=os.path.join(MODEL_DIR, "loras"), token=TOKEN)
        cmd += ["--lora-scaled", lpath, LORA_SCALE] if LORA_SCALE != "1.0" else ["--lora", lpath]
    log("spawn", " ".join(cmd))
    state["proc"] = subprocess.Popen(cmd)
    state["model"] = alias; state["lora"] = lora; state["loads"] += 1
    for _ in range(300):
        if state["proc"].poll() is not None: raise RuntimeError("llama-server exited")
        if _healthy(): log("ready", alias); return
        time.sleep(1)
    raise RuntimeError("llama-server not healthy")

def idle_loop():
    while True:
        time.sleep(CHECK_S)
        with lock:
            if state["proc"] and time.time() - state["last_used"] >= IDLE_UNLOAD_S:
                log(f"idle >= {IDLE_UNLOAD_S}s -> unload {state['model']}")
                _stop()

class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, fmt, *a): print("[http]", fmt % a, flush=True)
    def _json(self, code, obj):
        raw = json.dumps(obj).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def do_GET(self):
        if self.path.startswith("/v1/models"):
            _all = dict(MODELS)
            _all.update({k: v[1] for k, v in MODELS_EXT.items()})
            return self._json(200, {"object": "list", "data": [
                {"id": k, "object": "model", "owned_by": "swe-code", "file": f,
                 "loaded": state["model"] == k, "primary": k == PRIMARY} for k, f in _all.items()]})
        if self.path in ("/", "/health", "/healthz", "/status"):
            p = state["proc"]
            return self._json(200, {"status": "ok", "primary": PRIMARY, "loaded_model": state["model"], "lora": state["lora"], "loras": {k: list(v) for k, v in LORAS_BY_MODEL.items()},
                "backend_alive": bool(p and p.poll() is None), "idle_unload_s": IDLE_UNLOAD_S,
                "idle_for_s": round(time.time() - state["last_used"], 1) if state["last_used"] else None,
                "loads": state["loads"], "unloads": state["unloads"]})
        self._json(404, {"error": "not found"})
    def do_POST(self):
        if self.path not in ("/v1/chat/completions", "/v1/completions", "/completion"):
            return self._json(404, {"error": "not found"})
        n = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(n) if n else b"{}"
        try: req = json.loads(body or b"{}")
        except Exception: return self._json(400, {"error": "bad json"})
        _force_tool(req)
        _anti_loop(req)
        alias = resolve(req.get("model")); req["model"] = alias
        lora = resolve_lora(alias, req); req.pop("lora", None)
        with lock:
            try: _ensure(alias, lora)
            except Exception as e:
                log("load error", e); return self._json(503, {"error": f"load failed: {e}"})
            state["last_used"] = time.time()
            r = urllib.request.Request(BACKEND + self.path, data=json.dumps(req).encode(),
                                       method="POST", headers={"Content-Type": "application/json"})
            try:
                resp = urllib.request.urlopen(r, timeout=900)
            except urllib.error.HTTPError as e:
                resp = e
            try:
                self.send_response(resp.status if hasattr(resp, "status") else resp.code)
                self.send_header("Content-Type", resp.headers.get("Content-Type", "application/json"))
                self.send_header("X-Model-Loaded", alias)
                self.send_header("X-Lora-Loaded", lora or "none")
                if req.get("stream"):
                    self.send_header("Connection", "close"); self.end_headers()
                    while True:
                        c = resp.read1(8192) if hasattr(resp, "read1") else resp.read(8192)
                        if not c: break
                        self.wfile.write(c); self.wfile.flush()
                    self.close_connection = True
                else:
                    raw = resp.read()
                    if self.path == "/v1/chat/completions": raw = _fix_tool_calls(raw, req)
                    self.send_header("Content-Length", str(len(raw)))
                    self.end_headers(); self.wfile.write(raw)
            finally:
                state["last_used"] = time.time()

if __name__ == "__main__":
    log(f"primary={PRIMARY} idle_unload_s={IDLE_UNLOAD_S} threads={THREADS} models={list(MODELS)}")
    threading.Thread(target=idle_loop, daemon=True).start()
    ThreadingHTTPServer(("0.0.0.0", 8080), H).serve_forever()
