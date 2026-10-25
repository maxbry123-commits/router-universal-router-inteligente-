"""Imagen, voz, ASR y video del Token Plan por HTTP (sin dependencias). La salida son marcas [[tipo:url]] que el chat convierte en medios."""
import base64
import json
import re
import time
from urllib import error, request
from mvp import modelos, sdk_qwen

RUTAS = {**sdk_qwen.RUTAS, "tts": sdk_qwen.RUTAS["voz"]}  # rutas del input block (sdk_qwen.py)
MAX_AUDIO = 2_000_000


def _http(url, clave, cuerpo=None, extra=None):
    cab = {"Content-Type": "application/json", "Authorization": "Bearer " + clave, "User-Agent": "qwencloud-skills", **(extra or {})}  # User-Agent: obligatorio en Token Plan
    sol = request.Request(url, data=None if cuerpo is None else json.dumps(cuerpo).encode(), headers=cab, method="GET" if cuerpo is None else "POST")
    try:
        with request.urlopen(sol, timeout=180) as r:
            return r.headers.get("Content-Type", ""), r.read(MAX_AUDIO * 2)
    except error.HTTPError as exc:
        raise RuntimeError("Qwen multimedia HTTP " + str(exc.code)) from None
    except (error.URLError, TimeoutError, OSError):
        raise RuntimeError("Qwen multimedia error de red") from None


def _json(url, clave, cuerpo=None, extra=None):
    try:
        return json.loads(_http(url, clave, cuerpo, extra)[1])
    except ValueError:
        raise RuntimeError("Qwen multimedia respuesta invalida") from None


def raiz(base_url):
    return base_url.split("/compatible-mode")[0].rstrip("/")


def _contenido(doc):
    try:
        return [c for c in doc["output"]["choices"][0]["message"]["content"] if isinstance(c, dict)]
    except (KeyError, IndexError, TypeError):
        raise RuntimeError("Qwen multimedia: " + str(doc.get("message") or doc.get("code") or "respuesta vacia")[:120]) from None


def imagen(b, clave, modelo, prompt):
    doc = _json(b + RUTAS["imagen"], clave, sdk_qwen.cuerpo_imagen(modelo, prompt))
    url = next((c["image"] for c in _contenido(doc) if c.get("image")), None)
    if not url:
        raise RuntimeError("Qwen imagen: la respuesta no trae imagen")
    return "[[imagen:" + url + "]]"


def video(b, clave, modelo, prompt, url_media=None, progreso=None, espera=5, tope=540):
    doc = _json(b + RUTAS["video"], clave, sdk_qwen.cuerpo_video(modelo, prompt, sdk_qwen.media_de(modelo, url_media) if url_media else None), {"X-DashScope-Async": "enable"})
    tarea = (doc.get("output") or {}).get("task_id")
    if not tarea:
        raise RuntimeError("Qwen video sin task_id: " + str(doc.get("message") or doc.get("code") or "respuesta vacia")[:120])
    t0 = time.monotonic()
    while time.monotonic() - t0 < tope:
        time.sleep(espera)
        out = _json(b + RUTAS["tarea"] + tarea, clave).get("output") or {}
        if out.get("task_status") == "SUCCEEDED" and out.get("video_url"):
            return "[[video:" + out["video_url"] + "]]"
        if out.get("task_status") in ("FAILED", "CANCELED", "UNKNOWN"):
            raise RuntimeError("Qwen video " + out["task_status"] + ": " + str(out.get("message") or "")[:120])
        if progreso:
            progreso("Generando video… %d s" % (time.monotonic() - t0))
    raise RuntimeError("Qwen video: tiempo agotado; la tarea " + tarea + " sigue en el proveedor")


def voz(b, clave, texto):
    tipo, datos = _http(b + RUTAS["tts"], clave, sdk_qwen.cuerpo_voz(texto))
    if "json" in tipo:
        url = (((json.loads(datos).get("output") or {}).get("audio")) or {}).get("url")
        if not url:
            raise RuntimeError("Qwen voz: la respuesta no trae audio")
        return "[[audio:" + url + "]]"
    if not datos or len(datos) > MAX_AUDIO:
        raise RuntimeError("Qwen voz: audio vacio o demasiado largo")
    return "[[audio:data:audio/mpeg;base64," + base64.b64encode(datos).decode() + "]]"


def asr(b, clave, url_audio):
    doc = _json(b + RUTAS["asr"], clave, sdk_qwen.cuerpo_asr(url_audio))
    return "".join(c.get("text", "") for c in _contenido(doc)).strip() or "(sin texto reconocido)"


def generar(modelo, tipo, base_url, clave, texto, progreso=None):
    """Prueba la URL base oficial y, si no acepta la clave o no responde (401/403/404/red), la de QwenCloud."""
    ultimo = None
    for base in modelos.bases(base_url):
        try:
            return _generar(modelo, tipo, base, clave, texto, progreso)
        except RuntimeError as exc:
            ultimo = exc
            if not any(x in str(exc) for x in ("HTTP 401", "HTTP 403", "HTTP 404", "error de red")):
                raise
    raise ultimo


def _generar(modelo, tipo, base_url, clave, texto, progreso=None):
    b, enlaces = raiz(base_url), re.findall(r"https?://[^\s\"'<>)]+", texto)
    prompt = re.sub(r"https?://[^\s\"'<>)]+", "", texto).strip() or texto
    if "realtime" in modelo:
        raise RuntimeError("audio realtime usa WebSocket: no esta disponible en el chat de texto")
    if "tts" in modelo:
        return voz(b, clave, texto)
    if ("asr" in modelo or modelo.endswith(("i2v", "r2v"))) and not enlaces:
        raise ValueError("este modelo necesita una URL (audio o imagen) dentro del mensaje")
    if "asr" in modelo:
        return asr(b, clave, enlaces[0])
    return imagen(b, clave, modelo, prompt) if tipo == "imagen" else video(b, clave, modelo, prompt, enlaces[0] if enlaces else None, progreso)
