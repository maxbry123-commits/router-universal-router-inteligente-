"""Harness HTTP: /invoke -> Router MVP por HTTP. Sin modelos, claves HF ni datos GitHub."""
import hashlib
import json
import hmac
import os
import re
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from plugins.router_api_cliente import llamar

OPCIONES = {"tools", "tool_choice", "temperature", "top_p", "max_tokens",
            "parallel_tool_calls", "response_format", "enable_thinking", "reasoning_effort"}
app = FastAPI()
# Sin tope de vueltas de herramientas. Cada /invoke dura como mucho PAUSA_S: al cumplirse devuelve `continuar` con la
# conversacion y el Router lo vuelve a llamar (hasta RIU_MAX_HORAS, 48 h). Asi un trabajo largo no depende de una sola peticion HTTP.
PAUSA_S = float(os.environ.get("RIU_HARNESS_PAUSA_S", "0"))  # 0 = el Router recibe la conversacion tras CADA ronda de herramientas y la guarda en el almacen
CONTEXTO_MAX = int(os.environ.get("RIU_CONTEXTO_MAX_CHARS", "3600000"))  # el contexto no crece sin fin en trabajos de horas: sirve para cualquier modelo
RECIENTES, STUB = 6, 300
_SECRETO = re.compile(r"(?:sk-(?:sp-)?[A-Za-z0-9_-]{12,}|github_pat_[A-Za-z0-9_]{12,}|gh[pousr]_[A-Za-z0-9]{12,}|hf_[A-Za-z0-9]{20,})")


def con_efectos(nombre, args):
    """Herramientas que cambian algo fuera del chat (escribir, enviar, delegar): se registran en el diario de la tarea."""
    a = args.get("accion")
    if nombre in ("github_escribir", "agente", "llm", "swe_agente"):  # swe_agente: un agente real lanzado por swe_avanzar
        return True
    return ((nombre == "github_api" and str(args.get("metodo", "GET")).upper() != "GET") or (nombre == "almacen" and a == "guardar")
            or (nombre == "memoria" and a == "save") or (nombre == "yaiwes_md" and a == "escribir")
            or (nombre == "pendientes" and a in ("agregar", "marcar", "ordenar", "quitar")) or (nombre == "sala" and a in ("crear", "enviar", "permiso"))
            or (nombre == "loop" and a in ("gobernar", "paralelo", "ejecutar")))


def _llave(nombre, args):
    return hashlib.sha256((nombre + json.dumps(args, sort_keys=True, ensure_ascii=False)).encode("utf-8")).hexdigest()[:24]


def _diario(tarea):
    try:
        return json.loads(leer({"nombre": "tareas/%s/diario.json" % tarea})["valor"])
    except Exception:  # noqa: BLE001 - sin diario todavia (o almacen caido): se sigue sin el
        return {}


def _anotar(tarea, diario):
    try:
        guardar({"nombre": "tareas/%s/diario.json" % tarea, "valor": _SECRETO.sub("[REDACTADO]", json.dumps(diario, ensure_ascii=False))})
    except Exception:  # noqa: BLE001
        pass


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
    resultado = llamar("fichas_qwen" if accion == "chat" else "router_mvp", "llm" if accion == "chat" else accion, datos, timeout=None)
    if isinstance(resultado, dict) and resultado.get("status_code") == 403:
        causa = str(resultado.get("error") or "").split("(HTTP 403)")[-1].lstrip(": ").strip()  # p. ej. «ia=false»: quien llama debe saber qué botón encender
        raise HTTPException(status_code=403, detail="Herramienta bloqueada por Router (HTTP 403)" + (": " + causa if causa else ""))
    if not isinstance(resultado, dict) or resultado.get("error") or resultado.get("status") == "degraded":
        motivo = resultado.get("error", "respuesta invalida") if isinstance(resultado, dict) else "respuesta invalida"
        raise RuntimeError("Router " + str(motivo)[:80])
    if accion == "almacen" and resultado.get("ok") is not True:
        raise RuntimeError("Router no confirmo almacenamiento HF")
    return resultado


# --- SWE CODE free / SWEN CODE: su router propio es el web-bridge (RIU_SWE_BRIDGE_URL). El Harness le manda sus ids y, si el Router MVP cae, sigue con modelos locales ---
SWE_PREFIJOS = ("web-", "swecode-")
SWE_IDS = {"hf-liquid-lfm25", "swe-codex-qwen25-15b", "swe-opencode-qwen35-08b", "swe-agent-lfm25", "swe-openhands-lfm25", "hf-qwen25-coder-15b",
           "lfm2.5-350m", "qwen2.5-coder-1.5b", "qwen3.5-0.8b", "qwen3-0.6b"}
SWE_ALIAS = {"hf-liquid-lfm25": "lfm2.5-350m", "swe-agent-lfm25": "lfm2.5-350m", "swe-openhands-lfm25": "lfm2.5-350m",
             "swe-codex-qwen25-15b": "qwen2.5-coder-1.5b", "hf-qwen25-coder-15b": "qwen2.5-coder-1.5b", "swe-opencode-qwen35-08b": "qwen3.5-0.8b"}


def es_swe(modelo):
    m = str(modelo or "")
    return m in SWE_IDS or m.startswith(SWE_PREFIJOS)


EXTERNO_PREFIJOS = ("groq/", "nvidia/")


def es_externo(modelo):
    """Modelo servido por un proveedor externo (Groq/NVIDIA) que el bridge sabe pedir por su id completo."""
    return isinstance(modelo, str) and modelo.startswith(EXTERNO_PREFIJOS)


def _bridge_url():
    u = os.environ.get("RIU_SWE_BRIDGE_URL", "http://127.0.0.1:7870").strip().rstrip("/")  # el Space arranca el bridge en :7870; RIU_SWE_BRIDGE_URL="" lo desactiva
    try:
        p = urlparse(u)
        ok = (p.scheme == "https" and p.hostname) or (p.scheme == "http" and p.hostname in ("127.0.0.1", "localhost") and not p.username)
    except ValueError:
        ok = False
    return u if ok else ""


def _router_caido(exc):
    """Caida real del Router MVP (red, timeout, 502/503/504); una cuota (429), un 4xx o un error del modelo NO cuentan."""
    m = str(exc)
    return bool(re.match(r"Router (?!HTTP )\w+", m) or re.match(r"Router HTTP 50[234]", m))


def _bridge_chat(mensajes, modelo, conv_id="", opciones=None):
    """Una vuelta de chat por el bridge (OpenAI-compatible): mismo formato que _router('chat')."""
    modelo = SWE_ALIAS.get(modelo, modelo)
    req = urllib.request.Request(_bridge_url() + "/v1/chat/completions", method="POST", headers={"Content-Type": "application/json"},
                                 data=json.dumps({"model": modelo, "messages": mensajes, **({"conv_id": conv_id} if conv_id else {}),
                                                **{k: v for k, v in (opciones or {}).items() if k in ("tools", "tool_choice")}}).encode())
    try:
        with urllib.request.urlopen(req, timeout=float(os.environ.get("RIU_SWE_TIMEOUT_S", "130"))) as r:
            bruto = json.load(r)
        msg = bruto["choices"][0]["message"]
        msg.get  # message null -> AttributeError controlado abajo
    except (OSError, ValueError, KeyError, IndexError, TypeError, AttributeError) as exc:
        raise RuntimeError("Bridge " + type(exc).__name__ + ": " + str(exc)[:80]) from None
    return {"texto": msg.get("content") or "", "tool_calls": msg.get("tool_calls") or [], "finish_reason": bruto["choices"][0].get("finish_reason") or "stop",
            "mensaje_asistente": msg, "modelo_respuesta": bruto.get("modelo_usado") or modelo}


def _bridge_sin_router(mensajes, modelo):
    """Router MVP caido: un modelo externo pedido se intenta primero por el bridge con ESE id; solo si eso falla se degrada a local, y se dice (aviso_modelo)."""
    pedido = str(modelo or "")
    if es_externo(pedido):
        try:
            return _bridge_chat(mensajes, pedido)
        except RuntimeError:
            pass
    local = os.environ.get("RIU_SWE_LOCAL_MODELO", "lfm2.5-350m")
    salida = _bridge_chat(mensajes, local)
    salida["aviso_modelo"] = "Se pidio %s y no respondio (Router MVP caido); respondio el modelo local %s." % (pedido or "(sin modelo)", salida.get("modelo_respuesta") or local)
    return salida


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
    sin_router = bool(catalogo.get("error")) and bool(_bridge_url())  # Router MVP caido: el Harness sigue solo con el bridge, sin herramientas
    if catalogo.get("error") and not sin_router:
        raise RuntimeError("No se pudo obtener el catalogo MCP")
    permitidas = {t["name"]: t for t in ({} if sin_router else catalogo).get("result", {}).get("tools", [])
                  if t["name"] in ("github_leer", "github_escribir", "almacen", "pendientes", "sala", "agente", "llm", "yaiwes_md", "loop", "archivos") or t["name"].startswith("mcp__")}
    if not permitidas and not sin_router and not (es_swe(cuerpo.get("modelo")) and _bridge_url()):
        raise RuntimeError("Herramientas GitHub no disponibles en MCP")
    opciones["tools"] = [{"type": "function", "function": {"name": n,
        "description": t["description"], "parameters": t["inputSchema"]}} for n, t in permitidas.items()]
    opciones["tool_choice"] = "auto"
    mensajes = list(mensajes)
    acumulado, continuaciones, usadas = str(cuerpo.get("acumulado") or ""), 0, []  # usadas: herramientas realmente ejecutadas (diagnostico)
    tarea = re.sub(r"[^A-Za-z0-9_-]", "", str(cuerpo.get("tarea_id") or ""))[:64]  # con tarea_id, lo que ya se ejecuto no se repite si la tarea se retoma
    diario = _diario(tarea) if tarea else {}
    t0, paso, salida, aviso = time.monotonic(), -1, {}, {}
    while True:
        paso += 1
        try:
            mensajes = compactar(mensajes, int(cuerpo.get("contexto_max") or 0) or None)
            if _bridge_url() and es_swe(cuerpo.get("modelo")):
                salida = _bridge_chat(mensajes, cuerpo.get("modelo"), tarea, opciones)
            else:
                try:
                    salida = _router("chat", {"mensajes": mensajes, "modelo": cuerpo.get("modelo"), "opciones": opciones, "tarea_id": tarea,  # el Router entrega el texto parcial a esa tarea
                                 **{k: cuerpo.get(k, False) for k in ("tools", "agente_tool", "llm_tool")}})
                except RuntimeError as exc:
                    if not _bridge_url() or not (sin_router or _router_caido(exc)):
                        raise
                    salida = _bridge_sin_router(mensajes, cuerpo.get("modelo"))  # Router MVP caido: el modelo pedido por el bridge si es externo; si no, modelos locales (con aviso)
        except RuntimeError:
            if not acumulado:
                raise
            return {"texto": acumulado, "tool_calls": [], "finish_reason": "length", "herramientas_usadas": usadas,
                    "modelo_solicitado": cuerpo.get("modelo"), "modelo_respuesta": salida.get("modelo_respuesta"), **aviso}
        aviso = {"aviso_modelo": salida["aviso_modelo"]} if salida.get("aviso_modelo") else {}
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
                    "modelo_solicitado": cuerpo.get("modelo"), "modelo_respuesta": salida.get("modelo_respuesta"), **aviso}
        mensajes.append(salida.get("mensaje_asistente") or {"role": "assistant", "content": salida["texto"] or None, "tool_calls": llamadas})
        for llamada in llamadas:
            funcion = llamada.get("function") or {}
            nombre = funcion.get("name")
            if not llamada.get("id"):
                continue  # sin id no se puede responder; el modelo vuelve a pedirla en la ronda siguiente
            if nombre not in permitidas:  # no corta la tarea: el modelo recibe el error y elige otra herramienta
                mensajes.append({"role": "tool", "tool_call_id": llamada["id"], "content": json.dumps({"error": "Herramienta no autorizada: " + str(nombre)}, ensure_ascii=False)})
                continue
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
                mensajes.append({"role": "tool", "tool_call_id": llamada["id"], "content": json.dumps({"error": "Escritura GitHub permitida solo en main"}, ensure_ascii=False)})
                continue
            llave = _llave(nombre, args) if tarea and con_efectos(nombre, args) else None
            if llave and llave in diario:  # ya se hizo en esta tarea (antes de un reinicio o corte): se devuelve lo que paso, no se repite
                resultado = {"ya_ejecutada_en_esta_tarea": True, "resultado": diario[llave]}
            else:
                resultado = llamar("router_mvp", "mcp", {"jsonrpc": "2.0", "id": llamada["id"],
                    "method": "tools/call", "params": {"name": nombre, "arguments": args}})
                if llave:
                    diario[llave] = json.dumps(resultado, ensure_ascii=False)[:2000]
                    _anotar(tarea, diario)
            mensajes.append({"role": "tool", "tool_call_id": llamada["id"],
                             "content": json.dumps(resultado, ensure_ascii=False)})
        if time.monotonic() - t0 > PAUSA_S:  # fin de una ronda de herramientas: el Router recibe la conversacion, la guarda y reanuda
            return {"texto": "", "tool_calls": [], "finish_reason": "pausa_herramientas", "continuar": True, "mensajes": mensajes,
                    "acumulado": acumulado, "herramientas_usadas": usadas, "modelo_solicitado": cuerpo.get("modelo")}


# --- SWE: agentes reales (chat-router/agentes/adaptadores). Solo se invocan por la accion `invoke` autenticada (clave del backend); NO estan en el catalogo
# MCP, asi que ningun modelo puede llamarlas desde el bucle de herramientas de llm() (en particular, ningun modelo puede aprobar). ---
from agentes.adaptadores import workflows as _swe  # noqa: E402  (chat-router va en PYTHONPATH, igual que `plugins`)
from agentes.adaptadores.contrato import TareaSWE  # noqa: E402,F401  (contrato comun YAIWES/OpenClaw)
from agentes.adaptadores.dispatcher import ejecutar_agente  # noqa: E402
from agentes.adaptadores import disponibilidad as _disponibilidad  # noqa: E402


def _swe_status():
    """result.swe del status: disponibilidad REAL (instalado/configurado) de agentes, workflows y modelos; solo lectura, sin claves. Si falla no se inventa nada."""
    try:
        return _disponibilidad.capacidades()
    except Exception:  # noqa: BLE001 - un fallo de la comprobacion no debe tumbar el status del Harness
        return {"error": "DISPONIBILIDAD_NO_COMPROBADA"}


def _ctx_swe():
    """Las funciones del Harness se pasan en cada llamada (no se copian): guardar/leer/_router/llm/con_efectos/_diario/_anotar/_llave."""
    return _swe.Contexto(guardar=guardar, leer=leer, llm=llm, router=_router, con_efectos=con_efectos, diario=_diario, anotar=_anotar, llave=_llave, secreto=_SECRETO,
                         ejecutar_agente=lambda *a, **k: ejecutar_agente(*a, **k))


def swe_iniciar(args):
    return _swe.swe_iniciar(args, _ctx_swe())


def swe_avanzar(args):
    return _swe.swe_avanzar(args, _ctx_swe())


def swe_estado(args):
    return _swe.swe_estado(args, _ctx_swe())


def swe_aprobar(args):
    return _swe.swe_aprobar(args, _ctx_swe())


def swe_reanudar(args):
    return _swe.swe_reanudar(args, _ctx_swe())


HERRAMIENTAS.update({"swe_iniciar": swe_iniciar, "swe_avanzar": swe_avanzar, "swe_estado": swe_estado, "swe_aprobar": swe_aprobar, "swe_reanudar": swe_reanudar})


@app.post("/invoke")
def invoke(cuerpo: dict, x_api_key: str | None = Header(None)):
    esperado = os.environ.get("RIU_API_KEY")
    if not esperado or not isinstance(x_api_key, str) or not hmac.compare_digest(x_api_key, esperado):
        return _err("clave de acceso invalida", 401)
    accion = cuerpo.get("action")
    try:
        if accion == "status":
            return _ok({"servicio": "deepseek_harness", "acciones": ["status", "invoke", "llm"], "swe": _swe_status()})
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
