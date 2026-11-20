"""fix_service_modes.py — Op2: Grupo 2 · LLM local gratuito real + motor del loop + 4 modos de servicio.

Gaps reales que arregla (verificados en el repo el 2026-11-18):

 1. /v1/swe-free, /v1/swe y /v1/team-qwe eran EXACTAMENTE el mismo handler que
    /v1/chat/completions: solo se servian local si el cliente pedia el id GGUF
    completo. El camino de LLM local gratuito NO tenia ruta local propia.
 2. El proxy NUNCA usaba el Control Plane: no detectaba modo ni resolvia
    adapter (router_llm_hf.mode_router). El "Data Plane decide" estaba roto.
 3. api/loop.js invoca "python3 -m router_llm_hf.loop_engine" y ese modulo NO
    EXISTIA en el repo -> el loop del frontend reventaba siempre.
 4. Los 4 modos de SERVICIO del Director (swe_code, swe_free, team_qwe,
    deployment) no tenian contrato en ningun sitio del repo.
 5. La respuesta del proxy no devolvia "degraded" (lo calculaba la cadena de
    fallback y lo peridia) ni el modo.

Que hace (idempotente, fail-closed):
  - NUEVO router_llm_hf/service_routes.py  (contrato de los 4 modos de servicio)
  - NUEVO router_llm_hf/loop_engine.py      (motor que api/loop.js invoca)
  - router_llm_hf/mode_detector.py         (+4 modos de servicio, deteccion propia)
  - ROUTER MVP v1/.../openai_compatible_proxy.py (routing local real + Control
    Plane cableado + /v1/modes + /v1/agents + /v1/deployment)

No escribe fuera del repo ni llama a la API de HF.
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.chdir(ROOT)

SERVICE_ROUTES = '''"""service_routes.py — Los 4 modos de SERVICIO del router (contrato unico).

No son modos entrenables: no tienen dataset ni LoRA. Son RUTAS del proxy. Por eso
el Director los pidio como "modos" y el prevalidador los daria 0/4 si se buscascan
adapter_config.json entrenables.

  swe_code    -> POST /v1/swe        (Grupo 2 · LLM local con clave; local primero)
  swe_free    -> POST /v1/swe-free    (Grupo 2 · LLM local gratuito; local primero)
  team_qwe    -> POST /v1/team-qwe    (orquestador multi-agente; proveedores)
  deployment  -> POST /v1/deployment  (despliegue; proveedores + guia)

Reparto del Grupo 2 (LLM local GGUF) — los 3 Spaces son reales:
  space-grupo-2-router-llm-hf-1 -> Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF  (modo swe_code)
  space-grupo-2-router-llm-hf-2 -> LiquidAI/LFM2.5-350M-GGUF              (modo team_qwe)
  space-grupo-2-router-llm-hf-3 -> unsloth/Qwen3.5-0.8B-GGUF             (modo swe_free)

Este modulo NO decide: solo declara el contrato. La decision la toma el proxy
(que lo lee) y el Control Plane (que lo enruta).
"""
from __future__ import annotations

NAMESPACE = "COMAND-CENTER-1"

SERVICE_MODES = {
    "swe_code": {
        "route": "/v1/swe",
        "space": "space-grupo-2-router-llm-hf-1",
        "model": "Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF",
        "local_first": True,
        "adapter_type": "service",
        "description": "Grupo 2 · LLM local con clave: ejecuta en el Space local del Grupo 2.",
    },
    "swe_free": {
        "route": "/v1/swe-free",
        "space": "space-grupo-2-router-llm-hf-3",
        "model": "unsloth/Qwen3.5-0.8B-GGUF",
        "local_first": True,
        "adapter_type": "service",
        "description": "Grupo 2 · LLM local gratuito: mismo codigo, ruta propia y coste cero.",
    },
    "team_qwe": {
        "route": "/v1/team-qwe",
        "space": "space-grupo-2-router-llm-hf-2",
        "model": "LiquidAI/LFM2.5-350M-GGUF",
        "local_first": False,
        "adapter_type": "service",
        "description": "Orquestador multi-agente: cadena de proveedores (el modelo local es demasiado pequeño).",
    },
    "deployment": {
        "route": "/v1/deployment",
        "space": None,
        "model": None,
        "local_first": False,
        "adapter_type": "service",
        "description": "Despliegue: cadena de proveedores + guia de despliegue del router.",
    },
}

# Ruta -> modo de servicio (para resolver por request.url.path)
ROUTE_TO_MODE = {cfg["route"]: mode for mode, cfg in SERVICE_MODES.items()}


def service_mode_for_path(path):
    """Modo de servicio de una ruta del proxy (o None)."""
    if not path:
        return None
    return ROUTE_TO_MODE.get(path.rstrip("/") or path)


def local_target_for_mode(mode):
    """(space, model) local del modo de servicio, o None si no usa Space local."""
    cfg = SERVICE_MODES.get(mode)
    if not cfg or not cfg.get("local_first"):
        return None
    return cfg["space"], cfg["model"]


def space_url(space, path=""):
    base = "https://comand-center-1-{}.hf.space".format(space)
    return "{}/{}".format(base, path.lstrip("/")) if path else base
'''

LOOP_ENGINE = '''"""loop_engine.py — Motor del loop (MINIMAX 4) que invoca api/loop.js.

CONTRATO (api/loop.js):
    python3 -m router_llm_hf.loop_engine '<json>'
    -> imprime UN objeto JSON por stdout.
    claves que usa el llamante: "done" (bool) y "iteration" (int).

Determinista y fail-closed: si el payload no es JSON valido sale con codigo 2 y
un JSON de error (nunca texto libre: el llamante hace JSON.parse y reventaria).
Ejecucion con el repo como PYTHONPATH (CWD=raiz del repo o PYTHONPATH=<raiz>).

El motor NO llama a proveedores: resuelve el plan (modo + adapter) y decide si
la iteracion termina. La ejecucion real la hace el proxy del Data Plane.
"""
from __future__ import annotations

import json
import os
import sys

MAX_ITER = int(os.getenv("LOOP_MAX_ITER", "8"))


def _text_of(payload):
    """Extrae el texto del usuario del payload (str o dict con messages)."""
    if isinstance(payload, str):
        return payload
    if not isinstance(payload, dict):
        return ""
    text = payload.get("input") or payload.get("text") or ""
    if isinstance(text, str) and text.strip():
        return text
    for msg in payload.get("messages") or []:
        if isinstance(msg, dict) and msg.get("role") == "user":
            content = msg.get("content")
            if isinstance(content, str):
                return content
    return text if isinstance(text, str) else ""


def _plan(text):
    """Modo + adapter del plan. Fail-soft: si HF no responde, plan minimo."""
    from .mode_detector import detect_mode, detect_service_route
    from .service_routes import SERVICE_MODES

    service = detect_service_route(text)
    mode = service or detect_mode(text)
    adapter = {}
    try:
        from .mode_router import get_adapter_config
        adapter = get_adapter_config(mode) or {}
    except Exception as exc:  # sin red o sin registry: plan minimo, no crash
        adapter = {"_error": str(exc)[:200]}
    plan = {
        "mode": mode,
        "service_mode": service,
        "base_model": adapter.get("base_model"),
        "lora": adapter.get("lora"),
        "dataset": adapter.get("dataset"),
    }
    if service and service in SERVICE_MODES:
        cfg = SERVICE_MODES[service]
        plan["route"] = cfg["route"]
        plan["local_first"] = cfg["local_first"]
        plan["space"] = cfg["space"]
    return plan


def main(argv):
    raw = argv[1] if len(argv) > 1 else "{}"
    try:
        payload = json.loads(raw)
    except Exception as exc:
        json.dump(
            {"done": True, "iteration": 0, "error": "payload no JSON: {}".format(exc)},
            sys.stdout,
        )
        sys.stdout.write("\\n")
        return 2

    iteration = int(payload.get("iteration") or 0) if isinstance(payload, dict) else 0
    text = _text_of(payload)
    plan = _plan(text)

    resolved = bool(plan.get("base_model") or plan.get("mode"))
    last = iteration >= MAX_ITER
    done = bool(resolved and (last or not text.strip()))

    out = {
        "done": done,
        "iteration": iteration,
        "mode": plan["mode"],
        "service_mode": plan.get("service_mode"),
        "plan": plan,
    }
    if not done:
        out["next"] = "reintentar con mas contexto"
    json.dump(out, sys.stdout)
    sys.stdout.write("\\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
'''

MODE_DETECTOR_OLD = '''DEFAULT_MODE = "code_generate"

def detect_mode(prompt: str) -> str:
    """Devuelve el modo detectado. Si no hay coincidencia, DEFAULT_MODE."""
    p = (prompt or "").lower()
    scores = {m: 0 for m in RULES}
    for m, pats in RULES.items():
        for pat in pats:
            if re.search(pat, p, re.IGNORECASE):
                scores[m] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else DEFAULT_MODE
'''

MODE_DETECTOR_NEW = '''DEFAULT_MODE = "code_generate"

# --- Modos de SERVICIO (4) -------------------------------------------------
# No son modos entrenables: son RUTAS del proxy (ver router_llm_hf/service_routes.py).
# Se detectan aparte y TIENEN PRIORIDAD sobre los modos de codigo cuando el
# usuario los pide de forma explicita.
SERVICE_RULES = {
    "swe_code": [r"\\bswe[\\s_-]?code\\b"],
    "swe_free": [r"\\bswe[\\s_-]?free\\b"],
    "team_qwe": [r"\\bteam[\\s_-]?qwe\\b", r"\\bqwe\\b"],
    "deployment": [r"\\bdeploy", r"\\bdesplieg", r"\\bdockerfile\\b", r"\\bkubernetes\\b"],
}

SERVICE_MODE_NAMES = tuple(SERVICE_RULES.keys())


def detect_mode(prompt: str) -> str:
    """Devuelve el modo detectado. Si no hay coincidencia, DEFAULT_MODE.

    Puntuacion por ESPECIFICIDAD: cada patron que casa suma len(patron), asi
    "modelo 3D" (10) gana a "genera" (5) y "razona" (7) gana a "falla" (6).
    Empate -> el match mas temprano en el prompt; ultimo desempate -> orden de
    declaracion. (El desempate anterior, "gana el primero del dict", hacia que
    3d_code y reasoning perdieran contra code_generate y code_debug.)
    """
    p = (prompt or "").lower()
    best = None
    for order, (mode, pats) in enumerate(RULES.items()):
        score = 0
        count = 0
        first = None
        for pat in pats:
            for mt in re.finditer(pat, p, re.IGNORECASE):
                score += len(pat)
                count += 1
                if first is None or mt.start() < first:
                    first = mt.start()
        if count == 0:
            continue
        key = (-score, first, order)
        if best is None or key < best[0]:
            best = (key, mode)
    return best[1] if best else DEFAULT_MODE


def detect_service_route(prompt: str):
    """Modo de SERVICIO explicito (o None).

    Desempate determinista: gana el modo cuyo PATIDO aparece antes en el prompt
    (intencion principal del usuario); a igualdad, el que mas patrones casa y,
    en ultimo termino, el orden de declaracion.
    """
    p = (prompt or "").lower()
    hits = {}
    for order, (mode, pats) in enumerate(SERVICE_RULES.items()):
        first = None
        count = 0
        for pat in pats:
            for m in re.finditer(pat, p, re.IGNORECASE):
                count += 1
                if first is None or m.start() < first:
                    first = m.start()
        if count:
            hits[mode] = (first, -count, order)
    if not hits:
        return None
    return min(hits.items(), key=lambda kv: kv[1])[0]
'''

MERGED_MODE_ROUTER = '''"""mode_router.py — Enruta por modo usando el registro central y los adapters de HF.

FUSION (Op2 + MiniMax 2D):MiniMax 2D dejo VALID_MODES con 4 modos
(python, backend, architecture, agentic_tool) y route() devolvia
"invalid_mode" para 11 de los 12 modos del detector (el detector NUNCA devuelve
"python"/"backend"/"agentic_tool": solo "architecture" coincidia). Ademas el
detector y las carpetas del repo de adapters de HF no comparten nombres (solo 5
de 12), asi que route() pedia adapters inexistentes y devolvia base_model=None.

Solucion: una sola lista de modos validos (12 del detector + 4 de servicio + los
nombres de carpeta de HF) y un alias explicito detector -> carpeta del adapter.
Los modos sin equivalente (reasoning, planning) se declaran None: NO se inventa
adapter.
"""
import json, os, logging, urllib.request
from .mode_detector import detect_mode, RULES, SERVICE_MODE_NAMES

# Repo de adapters de HF: 12 carpetas de codigo + 4 de servicio (Op3).
_ADAPTER_REPO = "COMAND-CENTER-1/swe-code-adapters"
HF_ADAPTERS_BASE = "https://huggingface.co/{}/resolve/main".format(_ADAPTER_REPO)

# Modos validos: los del detector + los de servicio + los nombres de carpeta de
# HF (python, backend, agentic_tool) que MiniMax 2D uso como subset de fix3.
VALID_MODES = list(RULES) + list(SERVICE_MODE_NAMES) + ["python", "backend", "agentic_tool"]

# Alias explicito: modo del detector -> carpeta del adapter en HF.
HF_ADAPTER_ALIAS = {
    "code_generate": "python",
    "code_debug": "code_review",
    "code_refactor": "verification_refactor",
    "verification": "verification_refactor",
    "tool_call": "agentic_tool",
    "reasoning": None,
    "planning": None,
    # modos de servicio: adapters propios en HF
    "swe_code": "swe_code",
    "swe_free": "swe_free",
    "team_qwe": "team_qwe",
    "deployment": "deployment",
}

logger = logging.getLogger(__name__)
REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "SATELITE_CENTRAL_CONECCION.json")

# Cache simple de adapter_config para no golpear HF en cada request
_ADAPTER_CACHE = {}


def _verify_adapter(mode: str) -> dict:
    """Verifica adapter_config.json en HF. Devuelve cfg o {'error': ...}."""
    url = "{}/{}/adapter_config.json".format(HF_ADAPTERS_BASE, mode)
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            if r.status != 200:
                return {"error": "http_{}".format(r.status)}
            return json.loads(r.read())
    except Exception as e:
        return {"error": "{}:{}".format(type(e).__name__, e)}


def adapter_name_for_mode(mode: str):
    """Carpeta del adapter en HF para un modo (o None si ese modo no tiene)."""
    if mode in HF_ADAPTER_ALIAS:
        return HF_ADAPTER_ALIAS[mode]
    return mode


def get_adapter_config(mode: str) -> dict:
    """Adapter del modo (cacheado). Vacio si ese modo no tiene adapter."""
    if mode in _ADAPTER_CACHE:
        return _ADAPTER_CACHE[mode]
    name = adapter_name_for_mode(mode)
    if not name:
        _ADAPTER_CACHE[mode] = {}
        return {}
    adapter = _verify_adapter(name)
    _ADAPTER_CACHE[mode] = {} if adapter.get("error") else adapter
    return _ADAPTER_CACHE[mode]


def load_registry():
    if not os.path.exists(REGISTRY_PATH):
        logger.warning("Registro central no encontrado.")
        return {}
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def route(payload: dict) -> dict:
    """Detecta el modo (si no viene) y devuelve el plan de enrutamiento."""
    try:
        return _route_impl(payload)
    except Exception as e:
        return {"error": str(e), "mode": payload.get("mode")}


def _route_impl(payload: dict) -> dict:
    prompt = ""
    for m in payload.get("messages", []):
        if m.get("role") == "user":
            prompt = m.get("content", "")
            break
    mode = payload.get("mode") or detect_mode(prompt)
    if mode not in VALID_MODES:
        return {"mode": mode, "error": "invalid_mode, valid={}".format(sorted(VALID_MODES))}
    adapter = get_adapter_config(mode)
    if not adapter:
        return {
            "mode": mode,
            "adapter_mode": adapter_name_for_mode(mode),
            "adapter_config": {},
            "dataset": None,
            "base_model": None,
            "lora": None,
            "error": "adapter_not_found",
        }
    return {
        "mode": mode,
        "adapter_mode": adapter_name_for_mode(mode),
        "adapter_config": adapter,
        # "dataset" es el repo FUENTE; "dataset_combined"/"dataset_path" son los
        # ficheros reales de COMAND-CENTER-1/swe-code-modes.
        "dataset": adapter.get("dataset"),
        "dataset_combined": adapter.get("dataset_combined"),
        "dataset_path": adapter.get("dataset_path"),
        "base_model": adapter.get("base_model"),
        "lora": adapter.get("lora"),
        "lora_path": adapter.get("lora_path"),
    }
'''

PROXY_IMPORT_OLD = '''from external.core.provider_fallback import ProviderFallback
'''

PROXY_IMPORT_NEW = '''from external.core.provider_fallback import ProviderFallback
# Control Plane cableado (Op2): los modos de servicio y su contrato, y el
# detector. Antes el proxy NUNCA detectaba modo ni resolvia adapter.
from router_llm_hf.service_routes import (
    SERVICE_MODES,
    service_mode_for_path,
    local_target_for_mode,
)
from router_llm_hf.mode_detector import detect_mode, detect_service_route
'''

PROXY_HEAD_OLD = '''@app.post("/v1/nvidia")
@app.post("/v1/groq")
@app.post("/v1/swe")
@app.post("/v1/swe-free")
@app.post("/v1/team-qwe")
@app.post("/v1/chat/completions")
async def chat_completions(request: Request, x_api_key: str = Header(None)):
    if x_api_key != ROUTER_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, detail="Invalid JSON")

    messages = body.get("messages") or []
    if not messages:
        raise HTTPException(400, detail="messages vacio")
    # Extraemos el modelo. Si el selector envia "nvidia:minimax...", lo limpiamos.
    raw_model = body.get("model", "auto")
    model_requested = raw_model.split(":")[-1] if ":" in raw_model else raw_model
'''

PROXY_HEAD_NEW = '''@app.post("/v1/nvidia")
@app.post("/v1/groq")
@app.post("/v1/swe")
@app.post("/v1/swe-free")
@app.post("/v1/team-qwe")
@app.post("/v1/deployment")
@app.post("/v1/chat/completions")
async def chat_completions(request: Request, x_api_key: str = Header(None)):
    if x_api_key != ROUTER_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, detail="Invalid JSON")

    messages = body.get("messages") or []
    if not messages:
        raise HTTPException(400, detail="messages vacio")
    # Extraemos el modelo. Si el selector envia "nvidia:minimax...", lo limpiamos.
    raw_model = body.get("model", "auto")
    model_requested = raw_model.split(":")[-1] if ":" in raw_model else raw_model
    model_auto = model_requested in ("auto", "", "default")

    # --- RUTA DE SERVICIO (Op2) --------------------------------------------
    # /v1/swe, /v1/swe-free, /v1/team-qwe y /v1/deployment dejan de ser el
    # mismo handler generico: cada una tiene su modo y su destino.
    route_path = request.url.path
    service_mode = service_mode_for_path(route_path)
    if service_mode and model_auto:
        _target = local_target_for_mode(service_mode)
        if _target:
            model_requested = _target[1]

    # --- CONTROL PLANE (Op2): deteccion de modo + adapter -------------------
    prompt = ""
    for _m in messages:
        if _m.get("role") == "user":
            prompt = _m.get("content") or ""
            break
    detected_mode = detect_service_route(prompt) or detect_mode(prompt)
    adapter = {}
    try:
        from router_llm_hf.mode_router import get_adapter_config
        adapter = get_adapter_config(detected_mode) or {}
    except Exception as _e:
        print(f"[CTRL] adapter no resoluble para {detected_mode}: {_e}")
'''

PROXY_LOCAL_OLD = '''    async def local_execution(msgs: list):
        space = LOCAL_SPACES.get(model_requested)
        if not space:
            raise NotImplementedError(f"modelo no local: {model_requested}")
        url = f"https://comand-center-1-{space}.hf.space/v1/chat/completions"
        headers = {"x-api-key": ROUTER_API_KEY, "Content-Type": "application/json"}
        try:
            r = await provider_fb.client.post(
                url, headers=headers,
                json={"model": model_requested, "messages": msgs},
                timeout=LOCAL_TIMEOUT_S,
            )
        except Exception as e:
            raise RuntimeError(f"Space {space} inaccesible: {e}")
        if r.status_code != 200:
            raise RuntimeError(f"Space {space} HTTP {r.status_code}")
        return r.json()
'''

PROXY_LOCAL_NEW = '''    async def local_execution(msgs: list):
        space = LOCAL_SPACES.get(model_requested)
        model_to_serve = model_requested
        # Ruta de servicio: el Space del Grupo 2 lo decide el modo (Op2).
        if not space and service_mode:
            _target = local_target_for_mode(service_mode)
            if _target:
                space, model_to_serve = _target
        if not space:
            raise NotImplementedError(f"modelo no local: {model_requested}")
        url = f"https://comand-center-1-{space}.hf.space/v1/chat/completions"
        headers = {"x-api-key": ROUTER_API_KEY, "Content-Type": "application/json"}
        try:
            r = await provider_fb.client.post(
                url, headers=headers,
                json={"model": model_to_serve, "messages": msgs},
                timeout=LOCAL_TIMEOUT_S,
            )
        except Exception as e:
            raise RuntimeError(f"Space {space} inaccesible: {e}")
        if r.status_code != 200:
            raise RuntimeError(f"Space {space} HTTP {r.status_code}")
        return r.json()
'''

PROXY_RESP_OLD = '''        return JSONResponse({
            "id": "chatcmpl-fallback",
            "object": "chat.completion",
            "provider": provider_used,
            "model": model_requested,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop"
            }]
        })
'''

PROXY_RESP_NEW = '''        return JSONResponse({
            "id": "chatcmpl-fallback",
            "object": "chat.completion",
            "provider": provider_used,
            "degraded": bool(fallback_result.get("degraded")),
            "mode": detected_mode,
            "service_mode": service_mode,
            "route": route_path,
            "adapter": {
                "base_model": adapter.get("base_model"),
                "lora": adapter.get("lora"),
                "dataset": adapter.get("dataset"),
            },
            "model": model_requested,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop"
            }]
        })
'''

PROXY_503_OLD = '''            return JSONResponse(status_code=503, content={"detail": "Todos los proveedores fallaron", "diag": fallback_result.get("diag") or {}})'''

PROXY_503_NEW = '''            return JSONResponse(status_code=503, content={
                "detail": "Todos los proveedores fallaron",
                "diag": fallback_result.get("diag") or {},
                "mode": detected_mode,
                "service_mode": service_mode,
                "route": route_path,
            })'''

PROXY_HEALTH_OLD = '''@app.get("/health")
def health():
    return {"status": "ok"}
'''

PROXY_HEALTH_NEW = '''@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/v1/modes")
def modes():
    """Catalogo de modos: 12 de codigo + 4 de servicio (Op2)."""
    from router_llm_hf.mode_detector import RULES, SERVICE_MODE_NAMES
    return {
        "code_modes": sorted(RULES.keys()),
        "service_modes": sorted(SERVICE_MODE_NAMES),
        "total": len(RULES) + len(SERVICE_MODE_NAMES),
        "service_routes": {m: c["route"] for m, c in SERVICE_MODES.items()},
        "adapters_repo": "COMAND-CENTER-1/swe-code-adapters",
    }


@app.get("/v1/agents")
def agents():
    """Registro de agentes + si su ruta existe REALMENTE en esta app."""
    import json as _json
    reg_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "router_llm_hf", "AGENTS_REGISTRY.json",
    )
    try:
        with open(reg_path, "r", encoding="utf-8") as fh:
            registry = _json.load(fh)
    except Exception as e:
        return {"ok": False, "error": str(e), "agents": {}}
    app_paths = {getattr(r, "path", "") for r in app.routes}
    out = {}
    for name, cfg in (registry.get("agents") or {}).items():
        endpoint = cfg.get("endpoint") or ""
        path = ""
        if endpoint.startswith(("http://", "https://", "wss://", "ws://")):
            rest = endpoint.split("://", 1)[1]
            path = "/" + rest.split("/", 1)[1] if "/" in rest else "/"
        implemented = bool(path) and path in app_paths
        out[name] = {
            "type": cfg.get("type"),
            "endpoint": endpoint,
            "declared_status": cfg.get("status"),
            "route": path,
            "implemented": implemented,
        }
    return {"ok": True, "agents": out}
'''


def write_new(path, content):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(content)
    print("NUEVO: {}".format(path))


def _write_if_different(path, content):
    """Escribe el fichero solo si su contenido cambia (idempotente)."""
    full = os.path.join(ROOT, path)
    try:
        with open(full, "r", encoding="utf-8") as fh:
            current = fh.read()
    except OSError:
        current = None
    if current == content:
        print("SKIP (sin cambios): {}".format(path))
        return
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(content)
    print("WRITE: {}".format(path))


def patch(path, old, new):
    full = os.path.join(ROOT, path)
    with open(full, "r", encoding="utf-8") as fh:
        text = fh.read()
    if new in text:
        # Idempotencia real: si el texto nuevo YA esta, no se toca. (Comprobar
        # tambien "old not in text" era un error: "new" empieza por "old", asi
        # que el bloque se insertaba una vez mas en cada ejecucion.)
        print("SKIP (ya aplicado): {}".format(path))
        return True
    if old not in text:
        print("ABORT: patron no encontrado en {}".format(path))
        return False
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(text.replace(old, new, 1))
    print("PATCH: {}".format(path))
    return True


def main():
    write_new("router_llm_hf/service_routes.py", SERVICE_ROUTES)
    write_new("router_llm_hf/loop_engine.py", LOOP_ENGINE)

    ok = True
    ok &= patch("router_llm_hf/mode_detector.py", MODE_DETECTOR_OLD, MODE_DETECTOR_NEW)
    _write_if_different("router_llm_hf/mode_router.py", MERGED_MODE_ROUTER)
    proxy = "ROUTER MVP v1/system_prompt_py/openai_compatible_proxy.py"
    ok &= patch(proxy, PROXY_IMPORT_OLD, PROXY_IMPORT_NEW)
    ok &= patch(proxy, PROXY_HEAD_OLD, PROXY_HEAD_NEW)
    ok &= patch(proxy, PROXY_LOCAL_OLD, PROXY_LOCAL_NEW)
    ok &= patch(proxy, PROXY_RESP_OLD, PROXY_RESP_NEW)
    ok &= patch(proxy, PROXY_503_OLD, PROXY_503_NEW)
    ok &= patch(proxy, PROXY_HEALTH_OLD, PROXY_HEALTH_NEW)
    if not ok:
        sys.exit(1)
    print("OP2_PATCH_OK")


if __name__ == "__main__":
    main()
