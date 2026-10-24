"""Cliente Qwen compatible OpenAI. No guarda credenciales ni ejecuta tools."""
import json
import time
from urllib import error, request
from mvp import modelos

REINTENTABLES = {429, 502, 503, 504}
OPCIONES = {"tools", "tool_choice", "temperature", "top_p", "max_tokens",
            "parallel_tool_calls", "response_format", "enable_thinking", "reasoning_effort"}


def _endpoint(base_url):
    if not isinstance(base_url, str) or not base_url.startswith("https://"):
        if not (isinstance(base_url, str) and base_url.startswith("http://127.0.0.1:")):
            raise ValueError("QWEN_BASE_URL debe usar HTTPS o loopback de pruebas")
    return base_url.rstrip("/") + "/chat/completions"


def _solicitar(url, payload, clave):
    headers = {"Content-Type": "application/json", "User-Agent": "qwencloud-skills"}  # obligatorio en Token Plan (SDK oficial)
    if clave:
        headers["Authorization"] = "Bearer " + clave
    req = request.Request(url, data=json.dumps(payload).encode("utf-8"),
                          headers=headers, method="POST")
    with request.urlopen(req, timeout=120) as resp:
        return json.load(resp)


def llamar(mensajes, modelo, base_url, clave, opciones=None):
    """Devuelve texto, tool_calls, uso y respuesta cruda; reintenta solo fallos transitorios."""
    if not isinstance(mensajes, list) or not modelo:
        raise ValueError("Se requieren modelo y mensajes")
    payload = {"model": modelo, "messages": mensajes, "stream": False}
    for nombre, valor in (opciones or {}).items():
        if nombre not in OPCIONES:
            raise ValueError("opcion Qwen no permitida: " + nombre)
        payload[nombre] = valor
    payload.update(modelos.extra_body(modelo, opciones=opciones))
    ultimo = RuntimeError("Qwen error de red")
    for base in modelos.bases(base_url):  # oficial primero, QwenCloud como alterna si la primera no acepta la clave o no responde
        try:
            return _intentar(_endpoint(base), payload, clave, modelo)
        except _Alterna as exc:
            ultimo = RuntimeError(str(exc))
    raise ultimo


class _Alterna(Exception):
    """Fallo de esa URL base (401/403/404 o red): vale la pena probar la otra."""


def _intentar(url, payload, clave, modelo):
    for intento in range(3):
        try:
            bruto = _solicitar(url, payload, clave)
            mensaje = bruto["choices"][0]["message"]
            return {"texto": mensaje.get("content") or "",
                    "tool_calls": mensaje.get("tool_calls") or [],
                    "finish_reason": bruto["choices"][0].get("finish_reason"),
                    "uso": bruto.get("usage") or {}, "bruto": bruto, "mensaje_asistente": mensaje,
                    "modelo_solicitado": modelo, "modelo_respuesta": bruto.get("model")}
        except error.HTTPError as exc:
            if exc.code in (401, 403, 404):
                raise _Alterna("Qwen HTTP " + str(exc.code)) from None
            if exc.code not in REINTENTABLES or intento == 2:
                raise RuntimeError("Qwen HTTP " + str(exc.code)) from None
        except (error.URLError, TimeoutError, OSError):
            if intento == 2:
                raise _Alterna("Qwen error de red") from None
        time.sleep(min(2 ** intento, 2))
