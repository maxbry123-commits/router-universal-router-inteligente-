"""SWE CODE y SWEN CODE free dentro del selector del chat: mismo acceso, sin cablear nada nuevo.
web-* y swecode-<modo> salen por el bridge (WEB_BRIDGE_URL); los modelos locales HF por la cola SWECODE_URL_S1..S3.
Si un modelo no responde: Groq -> NVIDIA -> HF local (mismas claves del banco que usa el chat con groq/ y nvidia/)."""
import json
import os
from urllib import error, request
from mvp import externos

WEB = ("web-qwen38max", "web-qwen37max", "web-dsv4-flash")
MODOS = ("consulta", "revision", "solucion", "arquitectura", "archivos", "prompt_code", "despliega")
LOCALES = {"lfm2.5-350m": "lfm2.5-350m", "qwen2.5-coder-1.5b": "qwen2.5-coder-1.5b", "qwen3.5-0.8b": "qwen3.5-0.8b", "qwen3-0.6b": "qwen3-0.6b",
           "hf-liquid-lfm25": "lfm2.5-350m", "swe-agent-lfm25": "lfm2.5-350m", "swe-openhands-lfm25": "lfm2.5-350m",  # ids del selector -> id real de la cola
           "swe-codex-qwen25-15b": "qwen2.5-coder-1.5b", "hf-qwen25-coder-15b": "qwen2.5-coder-1.5b", "swe-opencode-qwen35-08b": "qwen3.5-0.8b"}
RESPALDO = (("groq", "RIU_SWE_GROQ_MODELO", "llama-3.3-70b-versatile"), ("nvidia", "RIU_SWE_NVIDIA_MODELO", "meta/llama-3.3-70b-instruct"))
LOCAL_RESPALDO = "lfm2.5-350m"
OPCIONES = {"temperature", "top_p", "max_tokens", "tools", "tool_choice"}


def catalogo():
    """Ids que ofrece el selector (los mismos del frontend), con su tipo."""
    return list(WEB) + ["swecode-" + m for m in MODOS] + list(LOCALES)


def proveedor(modelo):
    m = str(modelo or "")
    if m in WEB or (m.startswith("swecode-") and m[8:] in MODOS):
        return "web"
    return "local" if m in LOCALES else None


def _base(url):
    if not isinstance(url, str) or not (url.startswith("https://") or url.startswith(("http://127.0.0.1", "http://localhost"))):
        raise ValueError("la URL del bridge/Space debe ser HTTPS o loopback")
    return url.rstrip("/")


def _pedir(base, modelo, mensajes, opciones):
    payload = {"model": modelo, "messages": mensajes, **{k: v for k, v in (opciones or {}).items() if k in OPCIONES}}
    req = request.Request(_base(base) + "/v1/chat/completions", data=json.dumps(payload).encode(), method="POST",
                          headers={"Content-Type": "application/json", "User-Agent": "riu-router"})
    try:
        with request.urlopen(req, timeout=float(os.environ.get("RIU_SWE_TIMEOUT_S", "130"))) as r:
            bruto = json.load(r)
    except (error.URLError, TimeoutError, OSError, ValueError) as exc:
        raise RuntimeError("SWE " + modelo + ": " + str(exc)[:100]) from None
    try:
        m = bruto["choices"][0]["message"]
    except (KeyError, IndexError, TypeError):
        raise RuntimeError("SWE " + modelo + ": respuesta sin choices") from None
    texto = m.get("content") or ""
    if not texto.strip() and not m.get("tool_calls"):
        raise RuntimeError("SWE " + modelo + ": respuesta vacia")
    return {"texto": texto, "tool_calls": m.get("tool_calls") or [], "finish_reason": bruto["choices"][0].get("finish_reason"), "uso": bruto.get("usage") or {},
            "mensaje_asistente": m, "modelo_solicitado": modelo, "modelo_respuesta": bruto.get("model") or modelo}


def _local(mensajes, modelo, opciones):
    urls = [os.environ.get("SWECODE_URL_S%d" % i) for i in (1, 2, 3)]
    ultimo = RuntimeError("SWE local sin SWECODE_URL_S1..S3")
    for u in filter(None, urls):  # entrada S1, salto a S2/S3 si no responde
        try:
            return _pedir(u, LOCALES.get(modelo, modelo), mensajes, opciones)
        except (RuntimeError, ValueError) as exc:
            ultimo = exc
    raise ultimo


def llamar(mensajes, modelo, banco=None, opciones=None):
    """El modelo pedido; si falla: Groq, NVIDIA y por ultimo HF local (la respuesta dice cual via)."""
    try:
        if proveedor(modelo) == "web":
            return _pedir(os.environ.get("WEB_BRIDGE_URL") or "", modelo, mensajes, opciones)
        return _local(mensajes, modelo, opciones)
    except (RuntimeError, ValueError) as primero:
        for prov, var, defecto in RESPALDO:
            if not externos.claves(prov, banco):
                continue
            try:
                s = externos.llamar(mensajes, prov + "/" + os.environ.get(var, defecto), banco, opciones)
                return {**s, "modelo_solicitado": modelo, "via_respaldo": prov}
            except (RuntimeError, PermissionError, ValueError):
                continue
        if proveedor(modelo) == "local":
            raise primero
        try:
            return {**_local(mensajes, LOCAL_RESPALDO, opciones), "modelo_solicitado": modelo, "via_respaldo": "hf-local"}
        except (RuntimeError, ValueError):
            raise primero from None
