"""SWE CODE y SWEN CODE free dentro del selector del chat: mismo acceso, sin cablear nada nuevo.
web-* y swecode-<modo> salen por el bridge (WEB_BRIDGE_URL); los modelos locales HF por la cola SWECODE_URL_S1..S3.
Si un modelo no responde: Groq -> NVIDIA -> HF local (mismas claves del banco que usa el chat con groq/ y nvidia/)."""
import importlib.util
import json
import os
import re
from pathlib import Path
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


# --- activacion: «SWEN CODE free ...» (puerto de SWE CODE free/activar.js) ---
CLAVE = re.compile(r"^\s*swen\s+code\s+free\b", re.I)
ALIAS = [(re.compile(p, re.I), i) for p, i in (
    (r"^(concilio|c[oó]ncil|consenso|todos|los\s*3)\b", "consenso"),
    (r"^(deepseek[- ]?v4[- ]?flash|deepseek[- ]?v4|dsv4[- ]?flash|dsv4|deepseek)\b", "web-dsv4-flash"),
    (r"^(qwen[- ]?3\.?7[- ]?max|qwen[- ]?3\.?7|qwen37[- ]?max|qwen37)\b", "web-qwen37max"),
    (r"^(qwen[- ]?3\.?8[- ]?max|qwen[- ]?3\.?8|qwen38[- ]?max|qwen38)\b", "web-qwen38max"),
    (r"^(lfm2\.?5|liquid|lfm)\b", "lfm2.5-350m"),
    (r"^(qwen[- ]?code|qwen2\.?5|coder)\b", "qwen2.5-coder-1.5b"))]
MARCA = re.compile(r"^<<SWEN(?: modo=(\w+))?(?: conv=([\w-]+))?>>\n")


def activar(texto):
    """None si el mensaje no empieza con «SWEN CODE free»; si no, {modo, modelo, conv_id, pipeline, prompt} o {error}."""
    if not CLAVE.match(texto or ""):
        return None
    resto, modo, modelo, conv, pipeline = CLAVE.sub("", texto, 1).strip(), "consulta", None, None, None
    cambio = True
    while cambio:
        cambio = False
        m = re.match(r"^modo\s+(\w+)\s*:?\s*", resto, re.I)
        if m:
            if m.group(1).lower() not in MODOS:
                return {"error": "modo desconocido: " + m.group(1).lower(), "modos": list(MODOS)}
            modo, resto, cambio = m.group(1).lower(), resto[m.end():].strip(), True
        m = re.match(r"^(?:con|solo|modelo)\s+(.+)", resto, re.I | re.S)
        for patron, id_ in ALIAS:
            base = m.group(1) if m else resto
            if patron.match(base):
                modelo, resto, cambio = id_, patron.sub("", base, 1).strip(), True
                break
        else:
            if m:
                return {"error": "modelo desconocido: " + m.group(1).split()[0]}
        m = re.match(r"^(?:chat|seccion|conv)\s+([\w-]+)", resto, re.I)
        if m:
            conv, resto, cambio = "chat-" + m.group(1), resto[m.end():].strip(), True
        m = re.match(r"^pipeline\b(?:\s+(code|free|auto)\b)?", resto, re.I)
        if m:
            pipeline, resto, cambio = (m.group(1) or "free").lower(), resto[m.end():].strip(), True
    return {"sistema": "SWEN CODE free", "modo": modo, "modelo": modelo or ("consenso" if modo == "consulta" else "web-qwen38max"), "conv_id": conv, "pipeline": pipeline, "prompt": resto}


def modelo_de(a):
    """Id del selector que atiende una activacion: el concilio sale por swecode-<modo>; un modelo concreto, por su id."""
    return "swecode-" + a["modo"] if a["modelo"] == "consenso" else a["modelo"]


def marcar(a):
    """Marca al inicio del ultimo mensaje: sobrevive al salto por el Harness HTTP y el bridge la recibe como campos modo/conv_id."""
    return "<<SWEN modo=%s%s>>\n%s" % (a["modo"], " conv=" + a["conv_id"] if a["conv_id"] else "", a["prompt"])


def _sin_marca(mensajes):
    """(mensajes sin la marca, {modo, conv_id}) del ultimo mensaje de usuario."""
    extra, limpios = {}, [dict(m) if isinstance(m, dict) else m for m in mensajes]
    for m in reversed(limpios):
        if isinstance(m, dict) and m.get("role") == "user" and isinstance(m.get("content"), str):
            f = MARCA.match(m["content"])
            if f:
                extra = {k: v for k, v in (("modo", f.group(1)), ("conv_id", f.group(2))) if v}
                m["content"] = m["content"][f.end():]
            break
    return limpios, extra


def catalogo():
    """Ids que ofrece el selector (los mismos del frontend), con su tipo."""
    return list(WEB) + ["swecode-" + m for m in MODOS] + list(LOCALES)


def proveedor(modelo):
    m = str(modelo or "")
    if m in WEB or (m.startswith("swecode-") and m[8:] in MODOS):
        return "web"
    return "local" if m in LOCALES else None


def plataforma(modelo):
    """Donde corre el modelo, para la linea de identidad que recibe: SWEN CODE free (web/bridge) o SWE CODE (cola HF)."""
    return {"web": "SWEN CODE free (cuentas web via bridge)", "local": "SWE CODE (Space de HF, cola S1-S3)"}.get(proveedor(modelo))


def _base(url):
    if not isinstance(url, str) or not (url.startswith("https://") or url.startswith(("http://127.0.0.1", "http://localhost"))):
        raise ValueError("la URL del bridge/Space debe ser HTTPS o loopback")
    return url.rstrip("/")


def _pedir(base, modelo, mensajes, opciones):
    mensajes, extra = _sin_marca(mensajes)
    payload = {"model": modelo, "messages": mensajes, **extra, **{k: v for k, v in (opciones or {}).items() if k in OPCIONES}}
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


_MINI = []


def _mini_router():
    """El mini_router de la cascada (chat-router/SWE CODE/mini_router.py), cargado desde su ruta: la carpeta lleva espacio en el nombre."""
    if not _MINI:
        ruta = Path(__file__).resolve().parents[3] / "SWE CODE" / "mini_router.py"
        spec = importlib.util.spec_from_file_location("swe_mini_router", ruta)
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); _MINI.append(mod)
    return _MINI[0]


def correr_pipeline(nombre, objetivo):
    """pipeline code|free|auto de «SWEN CODE free pipeline ...»: la cascada de cascada.json (liquid recibe y delega -> despliega; qwen-coder solo con [GAP])."""
    mini = _mini_router()
    pasos = mini.CASCADA.get("pipelines", {}).get("free" if nombre == "auto" else nombre)
    if not pasos:
        raise ValueError("pipeline desconocido: %s (hay: %s)" % (nombre, ", ".join(mini.CASCADA.get("pipelines", {}))))
    return mini.correr(objetivo, pasos)


def resumen_pipeline(nombre, r):
    recibos = "\n".join("- %s · %s%s" % (x["nodo"], x["estado"], " · " + x["modelo"] if x.get("modelo") else "") for x in r.get("recibos", []))
    cuerpo = r.get("resultado") or ("Falló el paso «%s»." % r.get("paso_fallido"))
    return "Pipeline %s · %s · %s\n\n%s\n\nRecibos:\n%s" % (nombre, r.get("estado"), r.get("pid"), cuerpo, recibos)
