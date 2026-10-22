"""Servidor Harness DeepSeek (edificio 2): POST /invoke para mvp/harness_client.py.

Servicio separado: sin imports de mvp/ ni del router. llm va por HTTP al router (Ficha 4).
Env: RIU_API_KEY (X-API-Key esperada y enviada al router), RIU_ROUTER_URL (https, llm),
GITHUB_TOKEN (guardar/leer via GitHub contents API, repo/rama fijos, prefijo riu-chat/).
"""
import base64
import hmac
import json
import os
import urllib.error
import urllib.parse
import urllib.request

from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse

PREFIJO = "riu-chat/"  # mvp/config.json "prefijo"
REPO, RAMA = "maxbry123-commits/router-universal-router-inteligente-", "main"
OPCIONES = {"tools", "tool_choice", "temperature", "top_p", "max_tokens",
            "parallel_tool_calls", "response_format", "enable_thinking", "reasoning_effort"}

app = FastAPI()


def _ok(result):
    return {"status": "ok", "result": result}


def _err(mensaje, codigo=200):
    return JSONResponse({"status": "error", "error": mensaje}, status_code=codigo)


def _ruta(nombre):
    partes = nombre.split("/") if isinstance(nombre, str) else [""]
    if not (1 <= len(nombre or "") <= 128) or "\\" in nombre or ":" in nombre \
            or any(p in ("", ".", "..") or p.startswith(".") for p in partes):
        raise ValueError("nombre invalido")
    return PREFIJO + nombre


def _github(metodo, ruta, cuerpo=None):
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN ausente")
    url = "https://api.github.com/repos/" + REPO + "/contents/" + urllib.parse.quote(ruta)
    if metodo == "GET":
        url += "?ref=" + RAMA
    req = urllib.request.Request(url, method=metodo,
                                 data=json.dumps(cuerpo).encode("utf-8") if cuerpo else None,
                                 headers={"Authorization": "Bearer " + token,
                                          "Accept": "application/vnd.github+json",
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:  # noqa: S310 URL fija
            return json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as exc:
        if exc.code == 404 and metodo == "GET":
            return None
        raise RuntimeError("GitHub HTTP " + str(exc.code)) from None


def guardar(args):
    valor = args.get("valor")
    if not isinstance(valor, str) or len(valor.encode("utf-8")) > 1_000_000:
        raise ValueError("valor invalido")
    ruta = _ruta(args.get("nombre"))
    actual = _github("GET", ruta)
    cuerpo = {"message": "riu-chat: guardar " + args["nombre"], "branch": RAMA,
              "content": base64.b64encode(valor.encode("utf-8")).decode("ascii")}
    if isinstance(actual, dict) and actual.get("sha"):
        cuerpo["sha"] = actual["sha"]
    _github("PUT", ruta, cuerpo)
    return {"nombre": args["nombre"]}


def leer(args):
    ruta = _ruta(args.get("nombre"))
    datos = _github("GET", ruta)
    if not isinstance(datos, dict) or datos.get("type") != "file" or "content" not in datos:
        raise ValueError("no encontrado")
    return {"nombre": args["nombre"], "valor": base64.b64decode(datos["content"]).decode("utf-8")}


def computar(args):
    # Semantica de "tarea" no definida en el repo (pregunta abierta G5).
    raise ValueError("computar no implementado: contrato de tarea sin definir")


HERRAMIENTAS = {"guardar": guardar, "leer": leer, "computar": computar}


def llm(cuerpo):
    # G21: Harness -> HTTP -> router (Ficha 4 /plugins/fichas_qwen/call/llm); el Harness no llama modelos directo
    base, clave = os.environ.get("RIU_ROUTER_URL", "").rstrip("/"), os.environ.get("RIU_API_KEY")
    if not base.startswith("https://") or not clave:
        raise RuntimeError("RIU_ROUTER_URL (https) o RIU_API_KEY ausente")
    mensajes = cuerpo.get("messages", cuerpo.get("mensajes"))
    if not isinstance(mensajes, list) or not mensajes:
        raise ValueError("se requieren messages")
    opciones = cuerpo.get("opciones") or {}
    for k in opciones:
        if k not in OPCIONES:
            raise ValueError("opcion no permitida: " + k)
    payload = {"messages": mensajes, "modelo": cuerpo.get("modelo"), "ficha_qwen": "ficha4-workflow-yaiwes",
               "opciones": opciones, "max_tokens": opciones.get("max_tokens"), "caller_id": "deepseek_harness"}
    req = urllib.request.Request(base + "/plugins/fichas_qwen/call/llm", data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json", "X-API-Key": clave}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=110) as resp:  # noqa: S310 URL https fijada por env
            bruto = json.load(resp)
    except urllib.error.HTTPError as exc:
        raise RuntimeError("router HTTP " + str(exc.code)) from None
    res = bruto.get("result") if isinstance(bruto, dict) else None
    if not isinstance(res, dict) or bruto.get("status") != "ok":
        raise RuntimeError("router respuesta invalida")
    if res.get("error"):
        raise RuntimeError(str(res["error"]) + (": " + str(res.get("detalle"))[:200] if res.get("detalle") else ""))
    return {"texto": str(res.get("reply") or ""), "tool_calls": []}


@app.post("/invoke")
def invoke(cuerpo: dict, x_api_key: str | None = Header(None)):
    esperado = os.environ.get("RIU_API_KEY")
    if not esperado or not isinstance(x_api_key, str) or not hmac.compare_digest(x_api_key, esperado):
        return _err("clave de acceso invalida", 401)
    accion = cuerpo.get("action")
    try:
        if accion == "status":
            return _ok({"servicio": "deepseek_harness", "acciones": ["status", "invoke", "llm"]})
        if accion == "invoke":
            herramienta = HERRAMIENTAS.get(cuerpo.get("tool"))
            if herramienta is None:
                return _err("tool no permitida")
            args = cuerpo.get("args")
            return _ok(herramienta(args if isinstance(args, dict) else {}))
        if accion == "llm":
            return _ok(llm(cuerpo))
        return _err("accion no permitida")
    except (ValueError, RuntimeError) as exc:
        return _err(str(exc))
    except Exception as exc:  # noqa: BLE001 - nunca filtrar detalles/secretos
        return _err(type(exc).__name__)
