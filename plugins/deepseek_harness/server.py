"""Harness HTTP: /invoke -> Router MVP por HTTP. Sin modelos, claves HF ni datos GitHub."""
import hmac
import os

from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse
from plugins.router_api_cliente import llamar

OPCIONES = {"tools", "tool_choice", "temperature", "top_p", "max_tokens",
            "parallel_tool_calls", "response_format", "enable_thinking", "reasoning_effort"}
app = FastAPI()


def _ok(result):
    return {"status": "ok", "result": result}


def _err(mensaje, codigo=200):
    return JSONResponse({"status": "error", "error": mensaje}, status_code=codigo)


def _router(accion, datos):
    base = os.environ.get("RIU_ROUTER_URL", "").strip()
    if not (base.startswith("https://") or base.startswith("http://127.0.0.1:")):
        raise RuntimeError("RIU_ROUTER_URL no configurada")
    resultado = llamar("router_mvp", accion, datos)
    if not isinstance(resultado, dict) or resultado.get("error") or resultado.get("status") == "degraded":
        motivo = resultado.get("error", "respuesta invalida") if isinstance(resultado, dict) else "respuesta invalida"
        raise RuntimeError("Router " + str(motivo)[:80])
    if accion == "almacen" and resultado.get("ok") is not True:
        raise RuntimeError("Router no confirmo almacenamiento HF")
    return resultado


def guardar(args):
    nombre = args.get("nombre")
    salida = _router("almacen", {"accion": "guardar", "destino": "hf", "nombre": nombre, "valor": args.get("valor")})
    return {"nombre": nombre, "destino": "hf", "commit": salida.get("commit")}


def leer(args):
    nombre = args.get("nombre")
    salida = _router("almacen", {"accion": "leer", "destino": "hf", "nombre": nombre})
    return {"nombre": nombre, "valor": salida["valor"]}


def computar(args):
    raise ValueError("computar no implementado: contrato de tarea sin definir")


HERRAMIENTAS = {"guardar": guardar, "leer": leer, "computar": computar}


def llm(cuerpo):
    mensajes = cuerpo.get("messages", cuerpo.get("mensajes"))
    if not isinstance(mensajes, list) or not mensajes:
        raise ValueError("se requieren messages")
    opciones = cuerpo.get("opciones") or {}
    if not isinstance(opciones, dict) or any(k not in OPCIONES for k in opciones):
        raise ValueError("opciones no permitidas")
    salida = _router("chat", {"mensajes": mensajes, "modelo": cuerpo.get("modelo"), "opciones": opciones})
    if not isinstance(salida.get("tool_calls"), list) or not isinstance(salida.get("texto"), str):
        raise RuntimeError("Router respuesta de chat invalida")
    return {"texto": salida["texto"], "tool_calls": salida["tool_calls"]}


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
    except Exception as exc:
        return _err(type(exc).__name__)
