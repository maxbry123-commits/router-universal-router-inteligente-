# -*- coding: utf-8 -*-
"""Puente MCP EXISTENTE -> chat SWE CODE free del mismo Space.

El MCP ya conectado a ChatGPT usa:
 chat(ficha_qwen="swen-code-free", modelo="web-qwen38max", message="...")
 resultado(proceso_id="swen_...")

No instala otro servidor, no usa una ficha Qwen para llamar a un modelo WEB,
no cambia a LLM local, no ejecuta herramientas por su cuenta.
"""
from __future__ import annotations

import concurrent.futures as cf
import hashlib
import json
import os
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

MODELOS = {
    "web-qwen38max": "qwen38max",
    "web-qwen37max": "qwen37max",
    "web-dsv4-flash": "dsv4-flash",
    "web-claude-sonnet": "claude-sonnet",
    "swecode-consulta": "qwen38max",
    # El mismo MCP del chat comprueba el provider OpenClaw sin otro puente.
    "groq/qwen/qwen3.8-27b": "groq/qwen/qwen3.8-27b",
    "nvidia/minimaxai/minimax-m3.1-flash": "nvidia/minimaxai/minimax-m3.1-flash",
    "nvidia/meta/muse-glimmer-30b": "nvidia/meta/muse-glimmer-30b",
    "nvidia/nvidia/nemotron-3-ultra-550b-a55b": "nvidia/nvidia/nemotron-3-ultra-550b-a55b",
    "nvidia/z-ai/glm-5.3": "nvidia/z-ai/glm-5.3",
}
_EXEC = cf.ThreadPoolExecutor(max_workers=4, thread_name_prefix="mcp_swen")
_JOBS: dict[str, dict] = {}
_REQUESTS: dict[str, str] = {}
_LOCK = threading.RLock()
_ID = re.compile(r"^[A-Za-z0-9_-]{1,80}$")
# Sólo servicios LOCALES existentes: no aceptar URL aportada por el modelo.
_RUTA = "/plugins/deepseek_harness/modelos/v1/chat/completions"


def _destinos():
    rutas = []
    base = str(os.getenv("RIU_DEEPSEEK_HARNESS_URL") or "").strip().rstrip("/")
    if base:
        u = urllib.parse.urlsplit(base)
        if u.scheme == "http" and u.hostname in ("localhost", "127.0.0.1", "::1") and not u.username:
            rutas.append(base + ("" if base.endswith("/modelos/v1/chat/completions") else "/modelos/v1/chat/completions"))
    for puerto in ("7861", "7860"):
        url = "http://127.0.0.1:" + puerto + _RUTA
        if url not in rutas:
            rutas.append(url)
    return rutas


def _clave():
    return str(os.getenv("RIU_API_KEY") or os.getenv("RIU_PUBLIC_CHAT_KEY") or "").strip()


def _coda_resultado(pid, modelo, key, solicitado=500, horas=4):
    """Polling sobre resultado del mismo Router; no crea otro proceso ni puente.
    Se usa solo cuando el provider OpenClaw devolvio 202 + PID.
    """
    if not re.fullmatch(r"p-[A-Za-z0-9_-]{1,80}", str(pid)):
        return {"estado": "error", "error": "CODA_PID_INVALIDO"}
    fin = time.monotonic() + max(1, min(horas, 4)) * 3600
    ultimo_error = "CODA_ROUTER_NO_DISPONIBLE"
    while time.monotonic() < fin:
        for puerto in ("7861", "7860"):
            url = "http://127.0.0.1:" + puerto + "/plugins/puente_chat/call/resultado"
            req = urllib.request.Request(
                url, method="POST",
                headers={"Content-Type": "application/json", "X-API-Key": key},
                data=json.dumps({"proceso_id": pid, "espera": 6}).encode("utf-8"))
            try:
                with urllib.request.urlopen(req, timeout=14) as resp:
                    data = json.loads(resp.read(2_000_001))
                item = data.get("result") if data.get("status") == "ok" else None
                if not isinstance(item, dict):
                    ultimo_error = "CODA_RESPUESTA_ROUTER_INVALIDA"
                    continue
                estado = item.get("estado")
                if estado == "completado":
                    texto = str(((item.get("choices") or [{}])[0].get("message") or {}).get("content") or "")
                    metricas = item.get("metricas") or {}
                    if not texto.strip() or len(texto.splitlines()) != solicitado or metricas.get("lineas_verificadas") != solicitado:
                        return {"estado": "error", "error": "CODA_SIN_500_LINEAS_VERIFICADAS",
                                "lineas": len(texto.splitlines()), "proceso_router": pid}
                    return {"estado": "terminado", "reply": texto[:150000],
                            "modelo_solicitado": modelo, "modelo_usado": modelo, "finish_reason": "stop",
                            "lineas_verificadas": solicitado, "proceso_router": pid,
                            "origen": "openclaw_bridge_coda_mvp"}
                if estado == "error" or item.get("error"):
                    return {"estado": "error", "error": str(item.get("error") or "CODA_ERROR")[:180],
                            "proceso_router": pid, "modelo_solicitado": modelo}
                ultimo_error = "CODA_PENDIENTE"
                break
            except (OSError, ValueError, KeyError) as exc:
                ultimo_error = "CODA_SIN_CONEXION_" + type(exc).__name__
        time.sleep(4)
    return {"estado": "error", "error": "CODA_LIMITE_TIEMPO_" + ultimo_error,
            "proceso_router": pid, "modelo_solicitado": modelo}


def _consulta(modelo, mensaje, sesion, timeout):
    key = _clave()
    if not key:
        return {"estado": "error", "error": "SWEN_MCP_SIN_CLAVE_BACKEND"}
    es_api = modelo.startswith(("groq/", "nvidia/"))
    cuerpo = {"model": modelo, "messages": [{"role": "user", "content": mensaje}],
              "conv_id": sesion, "tools": False, "stream": False,
              "origen": "openclaw" if es_api else "mcp-swen"}
    datos = json.dumps(cuerpo, ensure_ascii=False).encode("utf-8")
    ultimo = "SWEN_BACKEND_NO_ACCESIBLE"
    for destino in _destinos():
        req = urllib.request.Request(destino, data=datos, method="POST",
                                     headers={"Content-Type": "application/json",
                                              "X-API-Key": key, "Authorization": "Bearer " + key})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as respuesta:
                crudo = respuesta.read(2_000_001)
            if len(crudo) > 2_000_000:
                return {"estado": "error", "error": "SWEN_RESPUESTA_EXCESIVA"}
            obj = json.loads(crudo)
            if es_api and obj.get("estado") == "procesando" and obj.get("proceso_id"):
                return _coda_resultado(obj["proceso_id"], modelo, key)
            eleccion = (obj.get("choices") or [{}])[0]
            mensaje_respuesta = eleccion.get("message") or {}
            usado = obj.get("modelo_usado") or obj.get("model") or ""
            texto = mensaje_respuesta.get("content") or ""
            if not isinstance(texto, str) or not texto.strip():
                return {"estado": "error", "error": "SWEN_SIN_RESPUESTA", "modelo_usado": usado}
            # Los proveedores pueden informar el ID con o sin prefijo.
            if es_api and usado and str(usado) == modelo.split("/", 1)[1]:
                usado = modelo
            if usado and str(usado) != MODELOS[modelo]:
                return {"estado": "error", "error": "SWEN_MODELO_CAMBIADO",
                        "modelo_solicitado": modelo, "modelo_usado": str(usado)[:100]}
            if obj.get("via_respaldo") and not es_api:
                return {"estado": "error", "error": "SWEN_FALLBACK_NO_AUTORIZADO"}
            if modelo == "swecode-consulta" and (obj.get("consenso_detalle") or {}).get("arbitro") != "qwen38max":
                return {"estado": "error", "error": "SWEN_CONSIL_SIN_ARBITRO"}
            return {"estado": "terminado", "reply": texto[:150000], "modelo_solicitado": modelo,
                    "modelo_usado": usado, "finish_reason": eleccion.get("finish_reason"),
                    "consenso_detalle": obj.get("consenso_detalle") if modelo == "swecode-consulta" else None,
                    "tool_calls": mensaje_respuesta.get("tool_calls") or []}
        except urllib.error.HTTPError as exc:
            # Un error HTTP indica que llegamos al backend: NUNCA cambiar de servidor/modelo por el error.
            try:
                detalle = json.loads(exc.read(8192).decode("utf-8", "replace"))
                err = (detalle.get("error") or detalle.get("detail") or {})
                codigo = err.get("code") if isinstance(err, dict) else str(err)
            except (ValueError, TypeError, UnicodeError):
                codigo = "HTTP_" + str(exc.code)
            return {"estado": "error", "error": str(codigo or ("HTTP_" + str(exc.code)))[:140],
                    "http": exc.code, "modelo_solicitado": modelo}
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            ultimo = "SWEN_SIN_CONEXION_" + type(exc).__name__
        except (ValueError, KeyError, TypeError, IndexError):
            return {"estado": "error", "error": "SWEN_RESPUESTA_INVALIDA"}
    return {"estado": "error", "error": ultimo, "modelo_solicitado": modelo}


def _limpiar():
    expirados = [pid for pid, job in _JOBS.items()
                 if time.time() - job["creado"] > 3600 and job["futuro"].done()]
    for pid in expirados:
        _JOBS.pop(pid, None)
    for rid, pid in list(_REQUESTS.items()):
        if pid not in _JOBS:
            _REQUESTS.pop(rid, None)


def iniciar(args):
    """Retorna proceso_id inmediatamente; la inferencia nunca bloquea al MCP."""
    modelo = str(args.get("modelo") or "")
    if modelo not in MODELOS:
        return {"error": "SWEN_MODELO_NO_PERMITIDO",
                "permitidos": list(MODELOS)}
    mensaje = args.get("message")
    if not isinstance(mensaje, str) or not mensaje.strip() or len(mensaje) > 100000:
        return {"error": "SWEN_MENSAJE_INVALIDO"}
    sesion = str(args.get("sesion") or ("mcp_" + uuid.uuid4().hex[:16]))
    if not _ID.fullmatch(sesion):
        return {"error": "SWEN_SESION_INVALIDA"}
    rid = str(args.get("request_id") or "")
    if rid and not _ID.fullmatch(rid):
        return {"error": "SWEN_REQUEST_ID_INVALIDO"}
    firma = hashlib.sha256(json.dumps([modelo, mensaje, sesion], ensure_ascii=False).encode()).hexdigest()
    with _LOCK:
        _limpiar()
        if rid and rid in _REQUESTS:
            previo = _JOBS.get(_REQUESTS[rid])
            if previo and previo["firma"] != firma:
                return {"error": "SWEN_REQUEST_ID_REUTILIZADO"}
            if previo:
                return {"estado": "procesando", "proceso_id": _REQUESTS[rid],
                        "modelo_solicitado": modelo}
        if len(_JOBS) >= 128:
            return {"error": "SWEN_COLA_LLENA"}
        pid = "swen_" + uuid.uuid4().hex
        f = _EXEC.submit(_consulta, modelo, mensaje, sesion,
                         450 if modelo == "swecode-consulta" else 360)
        _JOBS[pid] = {"futuro": f, "creado": time.time(), "firma": firma, "modelo": modelo}
        if rid:
            _REQUESTS[rid] = pid
        return {"estado": "procesando", "proceso_id": pid, "modelo_solicitado": modelo}


def resultado(args):
    pid = str(args.get("proceso_id") or "")
    if not re.fullmatch(r"swen_[0-9a-f]{32}", pid):
        return {"error": "SWEN_PROCESO_ID_INVALIDO"}
    with _LOCK:
        job = _JOBS.get(pid)
    if not job:
        return {"estado": "error", "error": "SWEN_PROCESO_NO_ENCONTRADO", "proceso_id": pid}
    futuro = job["futuro"]
    espera = max(0, min(float(args.get("espera") or 0), 12))
    try:
        datos = futuro.result(timeout=espera)
        return {"proceso_id": pid, **datos}
    except cf.TimeoutError:
        return {"estado": "procesando", "proceso_id": pid,
                "modelo_solicitado": job["modelo"]}
    except Exception:
        return {"estado": "error", "proceso_id": pid, "error": "SWEN_INFERENCIA_FALLIDA"}
