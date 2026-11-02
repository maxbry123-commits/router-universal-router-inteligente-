"""Harness HTTP: /invoke -> Router MVP por HTTP. Sin modelos, claves HF ni datos GitHub."""
import hashlib
import asyncio
import httpx
import json
import hmac
import os
import re
import time
import urllib.error
import urllib.request
import uuid
from urllib.parse import urlparse

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from plugins.router_api_cliente import llamar

OPCIONES = {"tools", "tool_choice", "temperature", "top_p", "max_tokens",
            "parallel_tool_calls", "response_format", "enable_thinking", "reasoning_effort"}
app = FastAPI()
# Sin tope de vueltas de herramientas. Cada /invoke dura como mucho PAUSA_S: al cumplirse devuelve `continuar` con la
# conversacion y el Router lo vuelve a llamar (hasta RIU_MAX_HORAS, 48 h). Asi un trabajo largo no depende de una sola peticion HTTP.
PAUSA_S = float(os.environ.get("RIU_HARNESS_PAUSA_S", "0"))  # 0 = el Router recibe la conversacion tras CADA ronda de herramientas y la guarda en el almacen
CONTEXTO_MAX = int(os.environ.get("RIU_CONTEXTO_MAX_CHARS", "3600000"))  # el contexto no crece sin fin en trabajos de horas: sirve para cualquier modelo
RECIENTES, STUB = 6, 300
_SECRETO = re.compile(r"(?:sk-(?:sp-)?[A-Za-z0-9_-]{12,}|github_pat_[A-Za-z0-9_]{12,}|gh[pousr]_[A-Za-z0-9]{12,}|hf_[A-Za-z0-9]{20,}|gsk_[A-Za-z0-9]{12,}|nvapi-[A-Za-z0-9_-]{12,})")


def con_efectos(nombre, args):
    """Herramientas que cambian algo fuera del chat (escribir, enviar, delegar): se registran en el diario de la tarea."""
    a = args.get("accion")
    if nombre in ("github_escribir", "agente", "llm", "swe_agente") or str(nombre).startswith("mcp__"):
        # Una tool MCP externa no certifica que sea solo lectura; tratarla como potencialmente mutante.
        return True
    if nombre == "archivos":
        return a not in ("estado", "raiz", "listar_raiz", "buscar", "listar")
    if nombre == "loop":
        # FAIL CLOSED: nuevas operaciones del LOOP se registran hasta clasificarse expresamente.
        return a not in ("status", "health", "estado", "estado_paralelo", "motores", "motor_fases", "motores_registro", "agentes", "fuente_listar")
    return ((nombre == "github_api" and str(args.get("metodo", args.get("method", "GET"))).upper() != "GET") or (nombre == "almacen" and a == "guardar")
            or (nombre == "memoria" and a == "save") or (nombre == "yaiwes_md" and a == "escribir")
            or (nombre == "pendientes" and a in ("agregar", "marcar", "ordenar", "quitar")) or (nombre == "sala" and a not in ("listar", "leer")))


def _llave(nombre, args):
    return hashlib.sha256((nombre + json.dumps(args, sort_keys=True, ensure_ascii=False)).encode("utf-8")).hexdigest()[:24]


def _diario(tarea):
    """Solo la ausencia comprobada del archivo equivale a diario nuevo. Ante red caída o corrupción, detenerse."""
    try:
        valor = leer({"nombre": "tareas/%s/diario.json" % tarea})["valor"]
    except Exception as exc:
        if "no existe" in str(exc).lower() or "HTTP 404" in str(exc):
            return {}
        raise RuntimeError("DIARIO_NO_DISPONIBLE") from None
    try:
        datos = json.loads(valor)
    except (ValueError, TypeError):
        raise RuntimeError("DIARIO_CORRUPTO") from None
    if not isinstance(datos, dict):
        raise RuntimeError("DIARIO_CORRUPTO")
    return datos


def _anotar(tarea, diario):
    """El guardado del diario es obligatorio: nunca silenciar fallos que permitirían repetir efectos."""
    if not isinstance(diario, dict):
        raise ValueError("DIARIO_INVALIDO")
    valor = _SECRETO.sub("[REDACTADO]", json.dumps(diario, ensure_ascii=False))
    try:
        guardar({"nombre": "tareas/%s/diario.json" % tarea, "valor": valor})
    except Exception:
        raise RuntimeError("DIARIO_NO_PERSISTIDO") from None


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


ACCIONES_CONTROL = ("tools_lock",)  # solo lectura cuando no llevan `tool`: estado de los botones del chat (agentes_on, ia)


def _router(accion, datos):
    # Misma URL local que plugins.router_api_cliente.llamar: sin variable nueva.
    # Antes se exigia RIU_ROUTER_URL aun con el Router montado en el mismo Space,
    # dejando los seis agentes bloqueados en AGENTES_ESTADO_NO_COMPROBADO.
    base = os.environ.get("RIU_ROUTER_URL", "").strip()
    if not base:
        puerto = os.environ.get("PORT", "7860").strip() or "7860"
        if not puerto.isdecimal() or not 1 <= int(puerto) <= 65535:
            raise RuntimeError("PORT local invalido")
        base = "http://127.0.0.1:" + puerto
    parsed = urlparse(base)
    if (parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname == "127.0.0.1")) or not parsed.hostname:
        raise RuntimeError("RIU_ROUTER_URL no permitida")
    plugin = "fichas_qwen" if accion == "chat" else "puente_chat" if accion in ACCIONES_CONTROL else "router_mvp"  # el Router sirve las acciones de control (tools_lock...) por /plugins/puente_chat/call/<accion>; con router_mvp responde 404
    resultado = llamar(plugin, "llm" if accion == "chat" else accion, datos, timeout=None)
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
SWE_IDS = {"hf-liquid-lfm25", "swe-codex-qwen25-15b", "swe-opencode-qwen35-08b", "swe-agent-lfm25", "swe-openhands-lfm25", "hf-qwen25-coder-15b", "hf-qwen3-06b",
           "lfm2.5-350m", "qwen2.5-coder-1.5b", "qwen3.5-0.8b", "qwen3-0.6b"}
SWE_ALIAS = {"hf-liquid-lfm25": "lfm2.5-350m", "swe-agent-lfm25": "lfm2.5-350m", "swe-openhands-lfm25": "lfm2.5-350m",
             "swe-codex-qwen25-15b": "qwen2.5-coder-1.5b", "hf-qwen25-coder-15b": "qwen2.5-coder-1.5b", "swe-opencode-qwen35-08b": "qwen3.5-0.8b", "hf-qwen3-06b": "qwen3-0.6b"}


def es_swe(modelo):
    m = str(modelo or "")
    return m in SWE_IDS or m.startswith(SWE_PREFIJOS)


EXTERNO_PREFIJOS = ("groq/", "nvidia/", "deepseek/", "minimax/", "openai/")


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


ACCESO_BRIDGE = ("RIU_API_KEY", "RIU_PUBLIC_CHAT_KEY", "RIU_MCP_KEY", "RIU_ROUTER_API_KEY")  # las 4 claves de acceso que el bridge acepta en x-api-key


def _cabeceras_bridge():
    """El bridge exige credencial en toda ruta salvo /health: el Harness manda SU clave de acceso (x-api-key) y, si existe, BRIDGE_TOKEN (x-bridge-key). Nunca se registra."""
    h = {"Content-Type": "application/json"}
    clave = next((os.environ[v].strip() for v in ACCESO_BRIDGE if os.environ.get(v, "").strip()), "")
    if clave:
        h["X-API-Key"] = clave
    token = os.environ.get("BRIDGE_TOKEN", "").strip()
    if token:
        h["x-bridge-key"] = token
    return h


def _tarea_id_bridge(conv_id, modelo, mensajes):
    """tarea_id explicito para el checkpoint del bridge (modelos locales/Groq/NVIDIA): <tarea>-<sha256([modelo, mensajes]) 12>. El mismo envio reintentado reanuda;
    otra vuelta de la misma tarea (mensajes distintos) es otra tarea del bridge y no choca (CHECKPOINT_OTRA_TAREA). Solo [A-Za-z0-9_-], <= 64."""
    base = re.sub(r"[^A-Za-z0-9_-]", "", str(conv_id))[:51]
    huella = hashlib.sha256(json.dumps([modelo, mensajes], sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")).hexdigest()[:12]
    return (base + "-" + huella) if base else ""


def _plan_bridge(mensajes, tools):
    """{objetivo, operaciones_previstas} para el bridge: solo con herramientas (efectos). objetivo = ultimo mensaje del usuario (<= 500, sin secretos); operaciones = nombres de las tools ofrecidas."""
    nombres = [t["function"]["name"] for t in (tools or []) if isinstance(t, dict) and isinstance(t.get("function"), dict) and isinstance(t["function"].get("name"), str) and t["function"]["name"]]
    if not nombres:
        return {}
    ult = next((str(m.get("content") or "") for m in reversed(mensajes) if isinstance(m, dict) and m.get("role") == "user"), "")
    return {"objetivo": _SECRETO.sub("[REDACTADO]", " ".join(ult.split()))[:500] or "tarea del chat", "operaciones_previstas": nombres[:100]}


def _metricas_bridge(m):
    """Traduce unidades del bridge SWE a las claves del Router MVP; nunca inventa mediciones."""
    if not isinstance(m, dict):
        return {}
    out = {}
    if type(m.get("stream")) is bool:
        out["stream"] = m["stream"]
    for origen, destino, factor in (("ttft_ms", "ttft_s", 0.001),
                                    ("total_ms", "duracion_s", 0.001),
                                    ("tokens_s", "tokens_por_s", 1.0)):
        v = m.get(origen)
        if isinstance(v, (int, float)) and not isinstance(v, bool) and 0 <= v < 1e10:
            out[destino] = round(v * factor, 4)
    v = m.get("tokens")
    if isinstance(v, int) and not isinstance(v, bool) and v >= 0:
        out["tokens"] = v
    if type(m.get("tokens_estimado")) is bool:
        out["tokens_estimados"] = m["tokens_estimado"]
    if m.get("origen_tokens") in ("proveedor", "estimado"):
        out["origen_tokens"] = m["origen_tokens"]
    return out


def _bridge_chat(mensajes, modelo, conv_id="", opciones=None):
    """Una vuelta de chat por el bridge (OpenAI-compatible): mismo formato que _router('chat'). Con tarea (conv_id) y un modelo local/Groq/NVIDIA manda ademas tarea_id explicito."""
    modelo = SWE_ALIAS.get(modelo, modelo)
    tarea_id = _tarea_id_bridge(conv_id, modelo, mensajes) if conv_id and not str(modelo).startswith(SWE_PREFIJOS) else ""
    opc = {k: v for k, v in (opciones or {}).items() if k in ("tools", "tool_choice")}
    # El bridge pide confirmar el objetivo y las operaciones previstas ANTES de dar herramientas a una tarea (141, activa por defecto). Aqui la confirmacion es la del Router: las herramientas
    # disponibles ya las dejo encendidas el usuario (Tools ON) y el bucle solo ejecuta las del catalogo. El plan que se registra en el checkpoint = su ultimo mensaje + esas herramientas.
    plan = _plan_bridge(mensajes, opc.get("tools")) if tarea_id else {}
    req = urllib.request.Request(_bridge_url() + "/v1/chat/completions", method="POST", headers=_cabeceras_bridge(),
                                 data=json.dumps({"model": modelo, "messages": mensajes, **({"conv_id": conv_id} if conv_id else {}), **({"tarea_id": tarea_id} if tarea_id else {}),
                                                **opc, **plan}).encode())
    try:
        from agentes.adaptadores import _comun as _c  # opener sin redireccion (chat-router va en PYTHONPATH)
        with _c.abrir(req, float(os.environ.get("RIU_SWE_TIMEOUT_S", "130"))) as r:
            bruto = json.load(r)
        msg = bruto["choices"][0]["message"]
        msg.get  # message null -> AttributeError controlado abajo
    except (OSError, ValueError, KeyError, IndexError, TypeError, AttributeError) as exc:
        raise RuntimeError("Bridge " + type(exc).__name__ + ": " + str(exc)[:80]) from None
    return {"texto": msg.get("content") or "", "tool_calls": msg.get("tool_calls") or [], "finish_reason": bruto["choices"][0].get("finish_reason") or "stop",
            "mensaje_asistente": msg, "modelo_respuesta": bruto.get("modelo_usado") or modelo,
            **({"metricas": _metricas_bridge(bruto["metricas"])} if isinstance(bruto.get("metricas"), dict) else {})}


def _bridge_sin_router(mensajes, modelo):
    """Router MVP caido: un modelo externo pedido se intenta primero por el bridge con ESE id; solo si eso falla se degrada a local, y se dice (aviso_modelo)."""
    pedido = str(modelo or "")
    if es_externo(pedido):
        # Ningun modelo externo solicitado por nombre se reemplaza silenciosamente por HF local.
        return _bridge_chat(mensajes, pedido)
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


def mechanico_buscar(args):
    """Authenticated read-only search port; never run snippets as code."""
    if not isinstance(args,dict) or set(args)!={"query"}:
        raise ValueError("MECHANIC_RESEARCH_ARGUMENTS_INVALID")
    from nct_loop.repair import research_sources, safe_research_open
    # All ten URLs are fixed in the existing LOOP code/config; the query
    # is URL-encoded and never influences hostnames or imported modules.
    return research_sources(args["query"],safe_research_open)

HERRAMIENTAS = {"guardar": guardar, "leer": leer, "computar": computar,
                "mechanico_buscar": mechanico_buscar}


METRICAS_ESCALARES = ("stream", "ttft_s", "ttft_origen", "duracion_s", "tokens", "tokens_estimados", "origen_tokens", "tokens_por_s", "tools_invalidas", "lineas_invalidas")
METRICAS_OBJETO = ("parametros", "contexto_compactado")  # el recorte de contexto y los parametros ignorados NO son silenciosos: viajan con la respuesta


def _metricas(salida):
    """Metricas del Router/proveedor reenviadas SOLO con claves conocidas y valores simples (sin secretos ni campos arbitrarios). Sin metricas no se inventan."""
    m = salida.get("metricas") if isinstance(salida, dict) else None
    if not isinstance(m, dict):
        return {}
    out = {k: m[k] for k in METRICAS_ESCALARES if k in m and (m[k] is None or isinstance(m[k], (bool, int, float, str)))}
    for k in METRICAS_OBJETO:
        v = m.get(k)
        if isinstance(v, dict) and len(json.dumps(v, default=str)) <= 2000:
            out[k] = json.loads(_SECRETO.sub("[REDACTADO]", json.dumps(v, default=str)))
    return {"metricas": {k: (_SECRETO.sub("[REDACTADO]", v) if isinstance(v, str) else v) for k, v in out.items()}} if out else {}


def _delegacion_permitida(nombre, cuerpo):
    """Tools OFF no desactiva el MCP interno, pero nunca autoriza delegar a otras IA/agentes."""
    if nombre in ("agente", "loop"):
        return cuerpo.get("tools") is True and cuerpo.get("agente_tool") is True
    if nombre == "llm":
        return cuerpo.get("tools") is True and cuerpo.get("llm_tool") is True
    return True


def _normalizar_tool_calls(llamadas):
    """Una tool sin id recibe uno unico; ids duplicados se rechazan ANTES de cualquier efecto."""
    if not isinstance(llamadas, list):
        raise RuntimeError("TOOL_CALLS_INVALIDAS")
    resultado, ids = [], set()
    for llamada in llamadas:
        if not isinstance(llamada, dict) or not isinstance(llamada.get("function"), dict):
            raise RuntimeError("TOOL_CALL_INVALIDA")
        ident = llamada.get("id") or "call_" + uuid.uuid4().hex[:24]
        if not isinstance(ident, str) or not ident or ident in ids:
            raise RuntimeError("TOOL_CALL_ID_INVALIDO_O_DUPLICADO")
        ids.add(ident)
        resultado.append({**llamada, "id": ident})
    return resultado


def _respuesta_mcp_fallida(resultado):
    """Ni un error JSON-RPC ni result.isError certifican una operacion con efectos."""
    if not isinstance(resultado, dict):
        return True
    if resultado.get("error"):
        return True
    sub = resultado.get("result")
    return isinstance(sub, dict) and sub.get("isError") is True


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
                  if (t["name"] in ("github_leer", "github_escribir", "almacen", "pendientes", "sala", "agente", "llm", "yaiwes_md", "loop", "archivos") or t["name"].startswith("mcp__"))
                  and _delegacion_permitida(t["name"], cuerpo)}
    if not permitidas and not sin_router and not (es_swe(cuerpo.get("modelo")) and _bridge_url()):
        raise RuntimeError("Herramientas GitHub no disponibles en MCP")
    opciones["tools"] = [{"type": "function", "function": {"name": n,
        "description": t["description"], "parameters": t["inputSchema"]}} for n, t in permitidas.items()]
    opciones["tool_choice"] = "auto"
    mensajes = list(mensajes)
    acumulado, continuaciones, usadas = str(cuerpo.get("acumulado") or ""), 0, []  # usadas: herramientas realmente ejecutadas (diagnostico)
    tarea = re.sub(r"[^A-Za-z0-9_-]", "", str(cuerpo.get("tarea_id") or ""))[:64]  # con tarea_id, lo que ya se ejecuto no se repite si la tarea se retoma
    # Solo consultar el diario al llegar una operacion con efectos. Un chat sin herramientas
    # no debe fallar si HF esta temporalmente caido; una escritura sigue fallando cerrado.
    diario = None
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
                    "modelo_solicitado": cuerpo.get("modelo"), "modelo_respuesta": salida.get("modelo_respuesta"), **aviso, **_metricas(salida)}
        aviso = {"aviso_modelo": salida["aviso_modelo"]} if salida.get("aviso_modelo") else {}
        if not isinstance(salida.get("tool_calls"), list) or not isinstance(salida.get("texto"), str):
            raise RuntimeError("Router respuesta de chat invalida")
        llamadas = _normalizar_tool_calls(salida["tool_calls"])
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
                    "modelo_solicitado": cuerpo.get("modelo"), "modelo_respuesta": salida.get("modelo_respuesta"), **aviso, **_metricas(salida)}
        asistente = salida.get("mensaje_asistente")
        if isinstance(asistente, dict):
            asistente = {**asistente, "tool_calls": llamadas}  # mantener id normalizado en ambos lados del protocolo
        else:
            asistente = {"role": "assistant", "content": salida["texto"] or None, "tool_calls": llamadas}
        mensajes.append(asistente)
        for llamada in llamadas:
            funcion = llamada.get("function") or {}
            nombre = funcion.get("name")
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
            if llave and diario is None:
                diario = _diario(tarea)  # HF caido o corrupto: error ANTES de cualquier efecto.
            if llave and llave in diario:  # se reusa SOLO una operación confirmada: INICIADA puede haber tenido efectos
                previa = diario[llave]
                if isinstance(previa, dict) and previa.get("estado") == "INICIADA":
                    raise RuntimeError("OPERACION_SIN_CONFIRMAR")
                if isinstance(previa, dict) and previa.get("estado") != "CONFIRMADA":
                    raise RuntimeError("DIARIO_CORRUPTO")
                resultado = {"ya_ejecutada_en_esta_tarea": True,
                             "resultado": previa.get("resultado") if isinstance(previa, dict) else previa}
            else:
                if llave:
                    diario[llave] = {"estado": "INICIADA", "herramienta": nombre}
                    _anotar(tarea, diario)  # persistencia ANTES de tocar sistemas externos
                resultado = llamar("router_mvp", "mcp", {"jsonrpc": "2.0", "id": llamada["id"],
                    "method": "tools/call", "params": {"name": nombre, "arguments": args}})
                if llave and _respuesta_mcp_fallida(resultado):
                    # La operacion pudo ejecutarse antes del error: guardar INICIADA y exigir conciliacion.
                    raise RuntimeError("OPERACION_SIN_CONFIRMAR")
                if llave:
                    texto_resultado = json.dumps(resultado, ensure_ascii=False)
                    # Guardar el resultado estructurado completo. Truncarlo a 2000 caracteres
                    # rompe la reanudacion; si el almacenamiento excede su limite, debe
                    # permanecer INICIADA y exigir reconciliacion, nunca fingir CONFIRMADA.
                    diario[llave] = {"estado": "CONFIRMADA", "resultado": resultado,
                                    "recibo": hashlib.sha256(texto_resultado.encode("utf-8")).hexdigest()[:24]}
                    _anotar(tarea, diario)  # si falla queda INICIADA: reconciliar, NUNCA ejecutar de nuevo
            mensajes.append({"role": "tool", "tool_call_id": llamada["id"],
                             "content": json.dumps(resultado, ensure_ascii=False)})
        if time.monotonic() - t0 > PAUSA_S:  # fin de una ronda de herramientas: el Router recibe la conversacion, la guarda y reanuda
            return {"texto": "", "tool_calls": [], "finish_reason": "pausa_herramientas", "continuar": True, "mensajes": mensajes,
                    "acumulado": acumulado, "herramientas_usadas": usadas, "modelo_solicitado": cuerpo.get("modelo")}


# --- SWE: agentes reales (chat-router/agentes/adaptadores). Solo se invocan por la accion `invoke` autenticada (clave del backend); NO estan en el catalogo
# MCP, asi que ningun modelo puede llamarlas desde el bucle de herramientas de llm() (en particular, ningun modelo puede aprobar). ---
try:
    from agentes.adaptadores import workflows as _swe  # noqa: E402  (chat-router va en PYTHONPATH, igual que `plugins`)
    from agentes.adaptadores.contrato import TareaSWE  # noqa: E402,F401  (contrato comun YAIWES/OpenClaw)
    from agentes.adaptadores.dispatcher import ejecutar_agente  # noqa: E402
    from agentes.adaptadores import disponibilidad as _disponibilidad  # noqa: E402
    _SWE_OK = True
except ImportError:  # sin agentes.adaptadores solo faltan los swe_*: status, invoke (guardar/leer/computar) y llm siguen vivos
    _swe = _disponibilidad = ejecutar_agente = TareaSWE = None
    _SWE_OK = False


def _swe_status():
    """result.swe del status: disponibilidad REAL (instalado/configurado) de agentes, workflows y modelos; solo lectura, sin claves. Si falla no se inventa nada."""
    if not _SWE_OK:
        return {"error": "ADAPTADORES_NO_DISPONIBLES"}
    try:
        return _disponibilidad.capacidades()
    except Exception:  # noqa: BLE001 - un fallo de la comprobacion no debe tumbar el status del Harness
        return {"error": "DISPONIBILIDAD_NO_COMPROBADA"}


def _defaults_entorno():
    """Defaults SIN variables nuevas en Hugging Face (solo si la variable NO esta definida; vacia = desactivada a proposito):
    RIU_SWE_WORKSPACE_RAIZ = <BRIDGE_STATE_DIR o tmp>/swe-workspace, creado con permisos 0700 (nuestro y no un enlace simbolico; si no se puede, queda sin configurar).
    SWECODE_URL_S1..S3 los resuelve agentes.adaptadores._comun.url_swecode (URLs publicas); aprobadores y operadores nunca se inventan."""
    if _SWE_OK and "RIU_SWE_WORKSPACE_RAIZ" not in os.environ:
        from agentes.adaptadores import _comun as _c
        raiz = _c.raiz_workspace_defecto()
        if _c.crear_dir_privado(raiz):
            os.environ["RIU_SWE_WORKSPACE_RAIZ"] = raiz


def _ctx_swe():
    """Las funciones del Harness se pasan en cada llamada (no se copian): guardar/leer/_router/llm/con_efectos/_diario/_anotar/_llave."""
    _defaults_entorno()
    return _swe.Contexto(guardar=guardar, leer=leer, llm=llm, router=_router, con_efectos=con_efectos, diario=_diario, anotar=_anotar, llave=_llave, secreto=_SECRETO,
                         ejecutar_agente=lambda *a, **k: ejecutar_agente(*a, **k))


def _exigir_agentes_on():
    """Agentes ON/OFF lo decide el SERVIDOR (estado del Router, `tools_lock` sin cambios = solo lectura), tambien para quien llega por el bridge de OpenClaw y no por mvp/app.py.
    Si no se puede comprobar, la operacion con efectos NO se ejecuta."""
    try:
        r = _router("tools_lock", {})
    except HTTPException:
        raise
    except Exception:  # noqa: BLE001 - Router caido o sin URL: no se asume permiso
        raise ValueError("AGENTES_ESTADO_NO_COMPROBADO") from None
    if not isinstance(r, dict) or r.get("agentes_on") is not True:  # _router devuelve el `result` de tools_lock
        raise ValueError("AGENTES_APAGADOS")


def swe_iniciar(args):
    if args.get("modo_agentico") is True:  # modo agentico OFF = solo el modelo que responde: no pide permiso de agentes
        _exigir_agentes_on()
    return _swe.swe_iniciar(args, _ctx_swe())


def swe_avanzar(args):
    _exigir_agentes_on()  # avanzar/reanudar/aprobar son las que lanzan los agentes: se exige siempre (el Harness no sabe el modo hasta cargar la tarea)
    return _swe.swe_avanzar(args, _ctx_swe())


def swe_estado(args):
    return _swe.swe_estado(args, _ctx_swe())


def swe_aprobar(args):
    _exigir_agentes_on()
    return _swe.swe_aprobar(args, _ctx_swe())


def swe_reanudar(args):
    _exigir_agentes_on()
    return _swe.swe_reanudar(args, _ctx_swe())


if _SWE_OK:
    HERRAMIENTAS.update({"swe_iniciar": swe_iniciar, "swe_avanzar": swe_avanzar, "swe_estado": swe_estado, "swe_aprobar": swe_aprobar, "swe_reanudar": swe_reanudar})


@app.post("/credenciales/{accion}")
def credenciales(accion: str, cuerpo: dict, x_api_key: str | None = Header(None)):
    """Relay ADMINISTRATIVO: Chat -> Harness -> plugin HTTP Router MVP -> SWE CODE -> banco.
    Los secretos no entran en prompts, historial del modelo, tools ni logs.
    """
    # Aceptar las MISMAS credenciales de acceso que el Router MVP; NO confundir
    # API_KEY de DeepSeek/MiniMax/OpenAI con una clave autorizada para administrar el banco.
    esperadas = [os.environ[v] for v in ("RIU_API_KEY", "RIU_PUBLIC_CHAT_KEY", "RIU_MCP_KEY", "RIU_ROUTER_API_KEY") if os.environ.get(v)]
    if not isinstance(x_api_key, str) or not any(hmac.compare_digest(
        x_api_key.encode("utf-8", "surrogatepass"), e.encode("utf-8", "surrogatepass")) for e in esperadas):
        return _err("clave de acceso invalida", 401)
    if accion not in ("anadir", "catalogo"):
        return _err("accion no permitida", 404)
    if not isinstance(cuerpo, dict):
        return _err("cuerpo invalido", 400)
    if accion == "anadir":
        secreto = cuerpo.get("secret")
        provider = cuerpo.get("proveedor", "auto")
        tipo = cuerpo.get("tipo", "api_key")
        if (not isinstance(secreto, str) or not 8 <= len(secreto) <= 300
                or any(ch.isspace() for ch in secreto)
                or not isinstance(provider, str) or not re.fullmatch(r"auto|[a-z][a-z0-9_-]{1,31}", provider)
                or tipo not in ("api_key", "sdk")):
            return _err("registro invalido", 400)
    respuesta = llamar("banco_proveedores", accion, cuerpo, timeout=30)
    if not isinstance(respuesta, dict) or respuesta.get("error") or respuesta.get("ok") is not True:
        return _err("banco no disponible", 503)  # no reflejar detalle del banco ni el secreto
    return _ok(respuesta)




async def _mvp_modelo_compat(req, headers, modelo):
    """Una petición modelo al Router MVP ya autorizado, sin volver a Harness."""
    async with httpx.AsyncClient(timeout=httpx.Timeout(450, connect=6), trust_env=False) as client:
        try:
            up = await client.post(_mvp_modelos_url() + "/chat", headers=headers, json=req)
        except httpx.HTTPError:
            raise HTTPException(status_code=503, detail="ROUTER_MVP_SIN_CONEXION") from None
    if up.status_code != 200:
        # El 410 de NVIDIA GLM y el 503 HF son diagnósticos, no fallback.
        try:
            motivo = str(up.json().get("detail") or "")
            origin = re.search(r"\bHTTP\s+(410|429|503)\b", motivo)
        except (ValueError, AttributeError):
            origin = None
        raise HTTPException(status_code=502 if up.status_code >= 500 else up.status_code,
                            detail="ROUTER_MVP_HTTP_" + str(up.status_code) +
                                   (" · PROVEEDOR_HTTP_" + origin.group(1) if origin else ""))
    try:
        obj = up.json()
    except ValueError:
        raise HTTPException(status_code=502, detail="ROUTER_MVP_RESPUESTA_INVALIDA") from None
    return _mensaje_openai(modelo, req["mensajes"], obj, via="mvp")


async def _sse_mvp_con_latidos(req, headers, modelo, latido_s=12):
    """Solo comentarios hasta respuesta final: evita timeout del proxy HF/Vercel.
    Nunca relanza la petición ni reenvía texto duplicado.
    """
    task = asyncio.create_task(_mvp_modelo_compat(req, headers, modelo))
    try:
        yield ": inicio\n\n"
        while not task.done():
            try:
                await asyncio.wait_for(asyncio.shield(task), timeout=latido_s)
            except asyncio.TimeoutError:
                yield ": keepalive\n\n"
        try:
            resultado = await task
        except HTTPException as error:
            # Después de abrir SSE, el HTTP status ya es 200. Informar un
            # único error tipado dentro del stream; no fingir respuesta modelo.
            codigos = re.findall(r"(?:ROUTER_MVP_[A-Z0-9_]+|PROVEEDOR_HTTP_[0-9]{3})", str(error.detail))[:3]
            codigo = codigos[-1] if codigos else "ROUTER_MVP_FALLO"
            yield "data: " + json.dumps({"error": {"code": codigo, "message": codigo},
                "choices": [{"index": 0, "delta": {}, "finish_reason": "error"}]}) + "\n\n"
            yield "data: [DONE]\n\n"
        else:
            for evento in _openai_sse(resultado):
                yield evento
    finally:
        if not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)


# --- Unica entrada OpenAI-compatible para ambos chats: Chat -> Harness ->
# Router MVP (APIs externas) o Router SWE CODE (locales/web) -> proveedor/HF.
# No crear un tercer router ni pasar por /web desde el navegador.
def _mvp_modelos_url():
    """Reentrada al Router MVP del MISMO Space y puerto real (PORT=7860/7861)."""
    puerto = (os.environ.get("PORT") or "7860").strip()
    if not puerto.isdecimal() or not 1 <= int(puerto) <= 65535:
        raise HTTPException(status_code=503, detail="ROUTER_MVP_PUERTO_INVALIDO")
    return "http://127.0.0.1:" + puerto
_SWE_MODELOS_LOCALES = {"lfm2.5-350m", "qwen2.5-coder-1.5b", "qwen3.5-0.8b", "qwen3-0.6b"}
_MODELOS_PRE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.:/-]{0,99}$")


def _autorizar_chat_modelos(x_api_key, authorization):
    """Misma clave de acceso del chat; una API KEY de modelos no abre este endpoint."""
    token = authorization[7:].strip() if isinstance(authorization, str) and authorization.lower().startswith("bearer ") else ""
    entradas = [v for v in (x_api_key, token) if isinstance(v, str) and v]
    esperadas = [os.environ[n] for n in ACCESO_BRIDGE if os.environ.get(n)]
    if not any(hmac.compare_digest(v.encode("utf-8", "surrogatepass"),
                                k.encode("utf-8", "surrogatepass")) for v in entradas for k in esperadas):
        raise HTTPException(status_code=401, detail="acceso Harness no autorizado")


def _modelo_destino(id_modelo):
    """Seleccion determinista, nunca salta de un modelo externo a uno HF."""
    if not isinstance(id_modelo, str) or not _MODELOS_PRE.fullmatch(id_modelo):
        raise HTTPException(status_code=400, detail="MODELO_INVALIDO")
    # OpenClaw presenta 'swecode/<modelo>' en su catálogo. Algunos clientes
    # mandan el ID interno y otros el nombre completo del provider: aceptar
    # ambos, sin permitir prefijos arbitrarios ni saltar de router.
    solicitado = id_modelo.removeprefix("swecode/")
    model = SWE_ALIAS.get(solicitado, solicitado)
    if model.startswith("hf/") and model[3:] in _SWE_MODELOS_LOCALES:
        model = model[3:]
    if es_externo(model):
        return "mvp", model
    if es_swe(model):
        return "swe", model
    raise HTTPException(status_code=400, detail="MODELO_FUERA_DE_CATALOGO")


def _mensaje_openai(modelo, mensajes, salida, *, via):
    """Un unico mensaje OpenAI; identidad completa y finish_reason preservados."""
    if via == "mvp":
        m = salida.get("mensaje_asistente") if isinstance(salida.get("mensaje_asistente"), dict) else {}
        texto = salida.get("texto") or ""
        tools = salida.get("tool_calls") or []
        usado = salida.get("modelo_respuesta") or modelo
        fin = salida.get("finish_reason") or ("tool_calls" if tools else "stop")
    else:
        c = (salida.get("choices") or [{}])[0]
        m = c.get("message") or {}
        texto = m.get("content") or ""
        tools = m.get("tool_calls") or []
        usado = salida.get("modelo_usado") or modelo
        fin = c.get("finish_reason") or ("tool_calls" if tools else "stop")
    return {"id": "harness-" + uuid.uuid4().hex[:20], "object": "chat.completion",
            "model": usado, "modelo_usado": usado, "via_router": via,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": texto,
                **({"tool_calls": tools} if tools else {})}, "finish_reason": fin}]}


def _openai_sse(respuesta):
    """El MVP entrega el mensaje al terminar. El bridge ya entrega SSE real."""
    c = respuesta["choices"][0]
    o = {"id": respuesta["id"], "object": "chat.completion.chunk", "model": respuesta["model"],
         "choices": [{"index": 0, "delta": {"role": "assistant", "content": c["message"]["content"]},
                      "finish_reason": None}]}
    yield "data: " + json.dumps(o, ensure_ascii=False) + "\n\n"
    if c["message"].get("tool_calls"):
        o["choices"][0]["delta"] = {"tool_calls": c["message"]["tool_calls"]}
        yield "data: " + json.dumps(o, ensure_ascii=False) + "\n\n"
    o["choices"][0]["delta"] = {}
    o["choices"][0]["finish_reason"] = c["finish_reason"]
    yield "data: " + json.dumps(o, ensure_ascii=False) + "\n\n"
    yield "data: [DONE]\n\n"


@app.get("/modelos/v1/models")
async def catalogo_modelos(x_api_key: str | None = Header(None), authorization: str | None = Header(None)):
    _autorizar_chat_modelos(x_api_key, authorization)
    # Misma lista del Router SWE CODE, que conoce Groq/NVIDIA/HF/web. No divulgar claves.
    headers = _cabeceras_bridge()
    async with httpx.AsyncClient(timeout=12, trust_env=False) as client:
        try:
            r = await client.get(_bridge_url() + "/v1/models", headers=headers)
            r.raise_for_status()
            datos = r.json()
            return {"object": "list", "data": datos.get("data", [])}
        except (httpx.HTTPError, ValueError):
            raise HTTPException(status_code=503, detail="SWE_CODE_CATALOGO_NO_DISPONIBLE") from None


@app.get("/modelos/v1/disponibilidad")
async def modelos_disponibilidad(x_api_key: str | None = Header(None),
                                authorization: str | None = Header(None)):
    """Catálogo y estados del router SWE CODE, consultados SIEMPRE por Harness."""
    _autorizar_chat_modelos(x_api_key, authorization)
    base = _bridge_url()
    if not base:
        raise HTTPException(status_code=503, detail="SWE_CODE_ROUTER_NO_CONFIGURADO")
    async with httpx.AsyncClient(timeout=18, trust_env=False) as client:
        try:
            r = await client.get(base + "/v1/modelos/disponibilidad", headers=_cabeceras_bridge())
            r.raise_for_status()
            datos = r.json()
            if not isinstance(datos, dict) or not isinstance(datos.get("modelos"), list):
                raise ValueError("catalogo invalido")
            return datos
        except (httpx.HTTPError, ValueError):
            raise HTTPException(status_code=503, detail="SWE_CODE_CATALOGO_NO_DISPONIBLE") from None


@app.post("/modelos/v1/chat/completions")
async def chat_modelos(cuerpo: dict, x_api_key: str | None = Header(None),
                       authorization: str | None = Header(None)):
    _autorizar_chat_modelos(x_api_key, authorization)
    if not isinstance(cuerpo, dict) or not isinstance(cuerpo.get("messages"), list) or not cuerpo["messages"]:
        raise HTTPException(status_code=400, detail="MENSAJES_INVALIDOS")
    # Chat de un modelo: tools de agentes van por /invoke y /chat/swe existentes,
    # nunca por un atajo sin los permisos del Router MVP.
    if cuerpo.get("tool_choice") not in (None, "none", "auto"):
        raise HTTPException(status_code=403, detail="TOOLS_REQUIEREN_HARNESS_INVOKE")
    # OpenClaw suele incluir su inventario de tools en cada petición incluso en
    # conversación normal. No reenviarlo al modelo ni activarlo: los efectos
    # exigen el flujo /invoke y permisos de la constitución.
    destino, modelo = _modelo_destino(cuerpo.get("model"))
    stream = cuerpo.get("stream") is True
    h = _cabeceras_bridge()
    # Los datos que sí atraviesan el Harness son solo el contrato de conversación,
    # no las API keys, tokens del navegador ni rutas arbitrarias.
    req = {"model": modelo, "messages": cuerpo["messages"],
           **{k: cuerpo[k] for k in ("conv_id", "modo", "proyecto") if isinstance(cuerpo.get(k), str)}}
    if destino == "swe":
        if not _bridge_url():
            raise HTTPException(status_code=503, detail="SWE_CODE_ROUTER_NO_CONFIGURADO")
        req["stream"] = stream
        req["origen"] = "openclaw" if cuerpo.get("origen") == "openclaw" else "yaiwes"
        client = httpx.AsyncClient(timeout=httpx.Timeout(450, connect=6), trust_env=False)
        try:
            upstream = await client.send(client.build_request("POST", _bridge_url() + "/v1/chat/completions",
                                                               headers=h, json=req), stream=True)
        except httpx.HTTPError:
            await client.aclose()
            raise HTTPException(status_code=503, detail="SWE_CODE_ROUTER_SIN_CONEXION") from None
        if upstream.status_code != 200:
            try:
                payload_error = json.loads((await upstream.aread()).decode("utf-8"))
                code = str((payload_error.get("error") or {}).get("code") or "HTTP_ERROR")
                if not re.fullmatch(r"[A-Z][A-Z0-9_]{2,60}", code):
                    code = "HTTP_ERROR"
                evidencia = str((payload_error.get("error") or {}).get("message") or "")
                estados = re.findall(r"(?:S[123](?: \(wake\))?:\s*HTTP\s*[45][0-9]{2}|HTTP\s*410|GGUF_[A-Z_]+|LLAMA_SERVER_FALLO|fetch failed|sin SWECODE_URL_S1\.\.S3|vacio)", evidencia)[:6]
            except (ValueError, UnicodeError, AttributeError):
                code, estados = "HTTP_ERROR", []
            await upstream.aclose()
            await client.aclose()
            raise HTTPException(status_code=502 if upstream.status_code >= 500 else upstream.status_code,
                                detail="SWE_CODE_" + code + (" · " + " | ".join(estados) if estados else ""))
        if stream and "text/event-stream" in upstream.headers.get("content-type", "").lower():
            async def trozos():
                try:
                    async for bloque in upstream.aiter_bytes():
                        if bloque:
                            yield bloque
                finally:
                    await upstream.aclose()
                    await client.aclose()
            return StreamingResponse(trozos(), media_type="text/event-stream",
                                     headers={"Cache-Control": "no-cache"})
        try:
            obj = json.loads((await upstream.aread()).decode("utf-8"))
        except (ValueError, UnicodeError):
            raise HTTPException(status_code=502, detail="SWE_CODE_RESPUESTA_INVALIDA") from None
        finally:
            await upstream.aclose()
            await client.aclose()
        resultado = _mensaje_openai(modelo, req["messages"], obj, via="swe")
    else:
        # Externos pasan por Router MVP en el MISMO Space (sin reentrada Harness).
        # /chat sin 'via=harness' llama mvp.externos una sola vez, exacto modelo.
        req["modelo"] = req.pop("model")
        req["mensajes"] = req.pop("messages")
        req["tools"] = False
        req["agente_tool"] = False
        req["llm_tool"] = False
        if stream:
            return StreamingResponse(_sse_mvp_con_latidos(req, h, modelo), media_type="text/event-stream",
                                     headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
        return await _mvp_modelo_compat(req, h, modelo)
    if stream:
        return StreamingResponse(_openai_sse(resultado), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache"})
    return resultado


@app.post("/invoke")
def invoke(cuerpo: dict, x_api_key: str | None = Header(None)):
    esperado = os.environ.get("RIU_API_KEY")
    if not esperado or not isinstance(x_api_key, str) or not hmac.compare_digest(x_api_key.encode("utf-8", "surrogatepass"), esperado.encode("utf-8", "surrogatepass")):  # bytes: con str no ASCII compare_digest lanza TypeError (500)
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
