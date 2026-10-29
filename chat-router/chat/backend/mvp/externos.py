"""Modelos de Groq y NVIDIA (APIs compatibles OpenAI) para el chat: id «groq/<modelo>» o «nvidia/<modelo>».
La clave sale del banco (GROQ_API_KEY / NVIDIA_API_KEY) o de las variables del Space (GROQ_API_KEY_2..7, NVIDIA_API_KEY_1..9)."""
import json
import os
import time
from urllib import request
from mvp import compute

PROVEEDORES = {
    "groq": {"label": "Groq", "base": "https://api.groq.com/openai/v1", "var": "GROQ_API_KEY"},
    "nvidia": {"label": "NVIDIA", "base": "https://integrate.api.nvidia.com/v1", "var": "NVIDIA_API_KEY"},
}
NO_CHAT = ("whisper", "tts", "guard", "embed", "rerank", "vision-", "distil-whisper", "playai", "orpheus", "parse", "clip", "nv-embed", "reward")
CACHE = {}  # proveedor -> (instante, lista de ids)


def proveedor(modelo):
    p = str(modelo or "").split("/", 1)[0]
    return p if p in PROVEEDORES and "/" in str(modelo) and str(modelo).split("/", 1)[1] else None


def claves(prov, banco=None):
    """Todas las claves del proveedor, en orden: banco (GROQ_API_KEY, GROQ_API_KEY_1..n) y luego el entorno; sin repetir."""
    var, out = PROVEEDORES[prov]["var"], []
    for n in [var] + [var + "_" + str(i) for i in range(1, 21)]:
        for v in ((banco.leer(n) if banco else None), os.environ.get(n)):
            if v and v not in out:
                out.append(v)
    return out


def clave(prov, banco=None):
    c = claves(prov, banco)
    return c[0] if c else None


def _get(url, k):
    req = request.Request(url, headers={"Authorization": "Bearer " + k, "User-Agent": "riu-router"})
    with request.urlopen(req, timeout=20) as r:
        return json.load(r)


def modelos(prov, banco=None):
    """Ids de chat que publica el proveedor (GET /models), con caché de 10 minutos."""
    if prov in CACHE and time.time() - CACHE[prov][0] < 600:
        return CACHE[prov][1]
    pool, datos, ultimo = claves(prov, banco), None, None
    if not pool:
        raise RuntimeError(PROVEEDORES[prov]["label"] + " sin clave (GROQ_API_KEY / NVIDIA_API_KEY)")
    for k in pool:  # la primera clave que el proveedor acepte
        try:
            datos = _get(PROVEEDORES[prov]["base"] + "/models", k); break
        except OSError as exc:
            ultimo = exc
    if datos is None:
        raise RuntimeError(PROVEEDORES[prov]["label"] + ": ninguna de las %d claves fue aceptada (%s)" % (len(pool), str(ultimo)[:80]))
    ids = sorted(m["id"] for m in datos.get("data", []) if not any(x in m["id"].lower() for x in NO_CHAT))
    CACHE[prov] = (time.time(), [prov + "/" + i for i in ids])
    return CACHE[prov][1]


def llamar(mensajes, modelo, banco=None, opciones=None):
    prov = proveedor(modelo)
    pool = claves(prov, banco)
    if not pool:
        raise PermissionError(PROVEEDORES[prov]["label"] + " sin clave (GROQ_API_KEY / NVIDIA_API_KEY en el banco o en el Space)")
    payload = {"model": modelo.split("/", 1)[1], "messages": mensajes}
    for n, v in (opciones or {}).items():
        if n in compute.OPCIONES and n not in ("enable_thinking", "reasoning_effort"):
            payload[n] = v
    ultimo = None
    for k in pool:  # una clave inválida o agotada (401/403/404) pasa a la siguiente del pool
        try:
            return {**compute._intentar(compute._endpoint(PROVEEDORES[prov]["base"]), payload, k, modelo), "modelo_solicitado": modelo}
        except compute._Alterna as exc:
            ultimo = exc
    raise RuntimeError(PROVEEDORES[prov]["label"] + ": ninguna de las %d claves fue aceptada (%s)" % (len(pool), str(ultimo).replace("Qwen ", "")))
