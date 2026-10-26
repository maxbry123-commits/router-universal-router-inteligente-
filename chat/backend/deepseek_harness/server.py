"""Harness HTTP: /invoke -> Router MVP por HTTP. Sin modelos, claves HF ni datos GitHub."""
import json
import hmac
import os
import time

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from plugins.router_api_cliente import llamar

OPCIONES = {"tools", "tool_choice", "temperature", "top_p", "max_tokens",
            "parallel_tool_calls", "response_format", "enable_thinking", "reasoning_effort"}
app = FastAPI()
# Sin tope de vueltas de herramientas. Cada /invoke dura como mucho PAUSA_S: al cumplirse devuelve `continuar` con la
# conversacion y el Router lo vuelve a llamar (hasta RIU_MAX_HORAS, 48 h). Asi un trabajo largo no depende de una sola peticion HTTP.
PAUSA_S = float(os.environ.get("RIU_HARNESS_PAUSA_S", "90"))
CONTEXTO_MAX = int(os.environ.get("RIU_CONTEXTO_MAX_CHARS", "3600000"))  # el contexto no crece sin fin en trabajos de horas: sirve para cualquier modelo
RECIENTES, STUB = 6, 300


def _tam(mensajes):
    return sum(len(str(m.get("content") or "")) for m in mensajes if isinstance(m, dict))


def compactar(mensajes, tope=None):
    """Si la conversacion pasa del tope, los resultados de herramientas MAS VIEJOS se recortan (no se tocan system, user ni las ultimas vueltas)."""
    tope = tope or CONTEXTO_MAX
    out = list(mensajes)
    for i in range(max(len(out) - RECIENTES, 0)):
        if _tam(out) <= tope:
            break
        m = out[i]
        if isinstance(m, dict) and m.get("role") == "tool" and len(str(m.get("content") or "")) > STUB:
            out[i] = {**m, "content": str(m["content"])[:STUB] + " ...[recortado por tamano; ya se uso]"}
    return out


def _ok(result):
    return {"status": "ok", "result": result}


def _err(mensaje, codigo=200):
    return JSONResponse({"status": "error", "error": mensaje}, status_code=codigo)


def _router(accion, datos):
    base = os.environ.get("RIU_ROUTER_URL", "").strip()
    if not (base.startswith("https://") or base.startswith("http://127.0.0.1:")):
        raise RuntimeError("RIU_ROUTER_URL no configurada")
    resultado = llamar("fichas_qwen" if accion == "chat" else "router_mvp", "llm" if accion == "chat" else accion, datos, timeout=900)
    if isinstance(resultado, dict) and resultado.get("status_code") == 403:
        causa = str(resultado.get("error") or "").split("(HTTP 403)")[-1].lstrip(": ").strip()  # p. ej. «ia=false»: quien llama debe saber qué botón encender
        raise HTTPException(status_code=403, detail="Herramienta bloqueada por Router (HTTP 403)" + (": " + causa if causa else ""))
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
    opciones = dict(opciones)
    permitidas = {}
    # GitHub/HF no dependen del permiso de delegacion a otras IA.
    catalogo = llamar("router_mvp", "mcp", {"jsonrpc": "2.0", "id": "catalogo", "method": "tools/list"})
    if catalogo.get("error"):
        raise RuntimeError("No se pudo obtener el catalogo MCP")
    permitidas = {t["name"]: t for t in catalogo.get("result", {}).get("tools", [])
                  if t["name"] in ("github_leer", "github_escribir", "almacen", "pendientes", "sala", "agente", "llm", "yaiwes_md", "loop") or t["name"].startswith("mcp__")}
    if not permitidas:
        raise RuntimeError("Herramientas GitHub no disponibles en MCP")
    opciones["tools"] = [{"type": "function", "function": {"name": n,
        "description": t["description"], "parameters": t["inputSchema"]}} for n, t in permitidas.items()]
    opciones["tool_choice"] = "auto"
    mensajes = list(mensajes)
    acumulado, continuaciones, usadas = str(cuerpo.get("acumulado") or ""), 0, []  # usadas: herramientas realmente ejecutadas (diagnostico)
    t0, paso = time.monotonic(), -1
    while True:
        paso += 1
        if paso > 0 and time.monotonic() - t0 > PAUSA_S:  # pausa entre vueltas: el Router reanuda con esta misma conversacion
            return {"texto": "", "tool_calls": [], "finish_reason": "pausa_herramientas", "continuar": True, "mensajes": mensajes,
                    "acumulado": acumulado, "herramientas_usadas": usadas, "modelo_solicitado": cuerpo.get("modelo")}
        try:
            mensajes = compactar(mensajes)
            salida = _router("chat", {"mensajes": mensajes, "modelo": cuerpo.get("modelo"), "opciones": opciones,
                         **{k: cuerpo.get(k, False) for k in ("tools", "agente_tool", "llm_tool")}})
        except RuntimeError:
            if not acumulado:
                raise
            return {"texto": acumulado, "tool_calls": [], "finish_reason": "length", "herramientas_usadas": usadas,
                    "modelo_solicitado": cuerpo.get("modelo"), "modelo_respuesta": salida.get("modelo_respuesta")}
        if not isinstance(salida.get("tool_calls"), list) or not isinstance(salida.get("texto"), str):
            raise RuntimeError("Router respuesta de chat invalida")
        llamadas = salida["tool_calls"]
        if not llamadas and salida.get("finish_reason") == "length" and salida["texto"] and continuaciones < 2:
            acumulado += salida["texto"]
            continuaciones += 1
            mensajes.extend([salida.get("mensaje_asistente") or {"role": "assistant", "content": salida["texto"]},
                             {"role": "user", "content": "Continua exactamente donde se corto la respuesta anterior, sin repetir texto ni ejecutar herramientas."}])
            opciones.pop("tools", None)
            opciones.pop("tool_choice", None)
            permitidas = {}
            continue
        if not llamadas or not permitidas:
            return {"texto": acumulado + salida["texto"], "tool_calls": llamadas, "finish_reason": salida.get("finish_reason"), "herramientas_usadas": usadas,
                    "modelo_solicitado": cuerpo.get("modelo"), "modelo_respuesta": salida.get("modelo_respuesta")}
        mensajes.append(salida.get("mensaje_asistente") or {"role": "assistant", "content": salida["texto"] or None, "tool_calls": llamadas})
        for llamada in llamadas:
            funcion = llamada.get("function") or {}
            nombre = funcion.get("name")
            if nombre not in permitidas:
                raise HTTPException(status_code=403, detail="Herramienta no autorizada en Harness")
            if not llamada.get("id"):
                raise RuntimeError("tool_call sin id; no se ejecuto")
            usadas.append(nombre)
            try:
                args = json.loads(funcion.get("arguments") or "{}")
            except ValueError:
                args = None
            aviso = ("Argumentos de herramienta invalidos (JSON)" if not isinstance(args, dict) else
                     "Almacen HF permite solo leer y guardar (accion leer o guardar)" if nombre == "almacen" and args.get("accion") not in ("leer", "guardar") else None)
            if aviso:  # error de argumentos: vuelve al modelo como resultado de la herramienta para que corrija; no corta el chat
                mensajes.append({"role": "tool", "tool_call_id": llamada["id"], "content": json.dumps({"error": aviso}, ensure_ascii=False)})
                continue
            if nombre == "almacen":
                args["destino"] = "hf"
            elif nombre.startswith("github_"):
                args.setdefault("rama", "main")
            if nombre == "github_escribir" and args["rama"] != "main":
                raise HTTPException(status_code=403, detail="Escritura GitHub permitida solo en main")
            resultado = llamar("router_mvp", "mcp", {"jsonrpc": "2.0", "id": llamada["id"],
                "method": "tools/call", "params": {"name": nombre, "arguments": args}})
            mensajes.append({"role": "tool", "tool_call_id": llamada["id"],
                             "content": json.dumps(resultado, ensure_ascii=False)})



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
    except HTTPException:
        raise
    except (ValueError, RuntimeError) as exc:
        return _err(str(exc))
    except Exception as exc:
        return _err(type(exc).__name__)
