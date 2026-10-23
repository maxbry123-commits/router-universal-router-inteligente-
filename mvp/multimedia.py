"""Imagen, voz, ASR y video del Token Plan por HTTP (sin dependencias). La salida son marcas [[tipo:url]] que el chat convierte en medios."""
import base64
import json
import re
import time
from urllib import error, request

RUTAS = {"imagen": "/api/v1/services/aigc/multimodal-generation/generation", "video": "/api/v1/services/aigc/video-generation/video-synthesis",
         "tts": "/api/v1/services/audio/tts/SpeechSynthesizer", "tarea": "/api/v1/tasks/"}
MAX_AUDIO = 2_000_000


def _http(url, clave, cuerpo=None, extra=None):
    cab = {"Content-Type": "application/json", "Authorization": "Bearer " + clave, **(extra or {})}
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
    doc = _json(b + RUTAS["imagen"], clave, {"model": modelo, "input": {"messages": [{"role": "user", "content": [{"text": prompt}]}]}, "parameters": {"size": "1024*1024", "n": 1}})
    url = next((c["image"] for c in _contenido(doc) if c.get("image")), None)
    if not url:
        raise RuntimeError("Qwen imagen: la respuesta no trae imagen")
    return "[[imagen:" + url + "]]"


def video(b, clave, modelo, prompt, url_media=None, progreso=None, espera=5, tope=540):
    entrada = {"prompt": prompt}
    if url_media:
        entrada["media"] = [{"type": "reference_image" if modelo.endswith("r2v") else "first_frame", "url": url_media}]
    doc = _json(b + RUTAS["video"], clave, {"model": modelo, "input": entrada, "parameters": {"resolution": "720P", "duration": 5}}, {"X-DashScope-Async": "enable"})
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
    tipo, datos = _http(b + RUTAS["tts"], clave, {"model": "qwen-audio-3.0-tts-plus", "input": {"text": texto, "voice": "longanlingxin", "format": "mp3", "sample_rate": 24000}})
    if "json" in tipo:
        url = (((json.loads(datos).get("output") or {}).get("audio")) or {}).get("url")
        if not url:
            raise RuntimeError("Qwen voz: la respuesta no trae audio")
        return "[[audio:" + url + "]]"
    if not datos or len(datos) > MAX_AUDIO:
        raise RuntimeError("Qwen voz: audio vacio o demasiado largo")
    return "[[audio:data:audio/mpeg;base64," + base64.b64encode(datos).decode() + "]]"


def asr(b, clave, url_audio):
    doc = _json(b + RUTAS["imagen"], clave, {"model": "qwen-audio-3.0-asr-flash", "input": {"messages": [{"role": "user", "content": [{"type": "input_audio", "input_audio": {"data": url_audio}}]}]}, "parameters": {"format": "wav", "sample_rate": "16000"}})
    return "".join(c.get("text", "") for c in _contenido(doc)).strip() or "(sin texto reconocido)"


def generar(modelo, tipo, base_url, clave, texto, progreso=None):
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
