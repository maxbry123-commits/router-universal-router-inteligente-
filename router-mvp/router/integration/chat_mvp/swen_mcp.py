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
import subprocess
import sys
from pathlib import Path
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

# Estado de los procesos MCP en el almacenamiento YA EXISTENTE, no en GitHub.
# Solo el usuario del servidor puede leer los archivos (modo 0600).
_ESTADO = Path(os.getenv("SWEN_MCP_STATE_DIR") or
    (Path(os.getenv("BRIDGE_STATE_DIR") or "/data/state") / "swen_mcp"))

def _persist_path(pid):
    return (_ESTADO / (pid + ".json")) if re.fullmatch(r"swen_[0-9a-f]{32}",str(pid)) else None

def _persist_read(pid):
    p=_persist_path(pid)
    try:
        if not p or p.is_symlink() or not p.is_file() or p.stat().st_size>380000:
            return None
        obj=json.loads(p.read_text(encoding="utf-8"))
        return obj if isinstance(obj,dict) and obj.get("pid")==pid else None
    except (OSError,ValueError,TypeError):
        return None

def _persist_write(pid, datos):
    p=_persist_path(pid)
    if p is None:
        return False
    tmp=p.with_name("."+pid+"."+uuid.uuid4().hex+".tmp")
    try:
        _ESTADO.mkdir(mode=0o700,parents=True,exist_ok=True)
        if _ESTADO.is_symlink():
            return False
        serial=json.dumps({"pid":pid,**datos},ensure_ascii=False,default=str)
        if len(serial.encode("utf-8"))>350000:
            return False
        descriptor=os.open(tmp,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        with os.fdopen(descriptor,"w",encoding="utf-8") as fh:
            fh.write(serial)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp,p)
        return True
    except (OSError,ValueError,TypeError):
        return False
    finally:
        try: tmp.unlink(missing_ok=True)
        except OSError: pass

def _persist_result(pid):
    obj=_persist_read(pid)
    if not obj:
        return None
    if isinstance(obj.get("resultado"),dict):
        return {"proceso_id":pid,**obj["resultado"],"recuperado_del_disco":True}
    worker=obj.get("worker")
    try:
        if type(worker) is int and worker>1:
            os.kill(worker,0)
            return {"estado":"procesando","proceso_id":pid,
                    "modelo_solicitado":obj.get("modelo"),"recuperado_del_disco":True}
    except OSError:
        pass
    return {"estado":"error","proceso_id":pid,
            "error":"SWEN_PROCESO_INTERRUMPIDO_TRAS_REINICIO",
            "modelo_solicitado":obj.get("modelo"),
            "sesion":obj.get("sesion"),"recuperado_del_disco":True}

def _persist_by_request(digest):
    try:
        files=sorted(_ESTADO.glob("swen_*.json"),
                     key=lambda f:f.stat().st_mtime,reverse=True)[:256]
        for p in files:
            obj=_persist_read(p.stem)
            if obj and obj.get("rid_hash")==digest:
                return obj
    except OSError:
        pass
    return None

def _persist_done(pid,modelo,sesion,firma,digest,created,future):
    try:
        outcome=future.result()
        if not isinstance(outcome,dict):
            outcome={"estado":"error","error":"SWEN_RESPUESTA_INVALIDA"}
    except Exception:
        outcome={"estado":"error","error":"SWEN_INFERENCIA_FALLIDA"}
    _persist_write(pid,{"modelo":modelo,"sesion":sesion,"firma":firma,
        "rid_hash":digest,"creado":created,"worker":os.getpid(),"resultado":outcome})


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


def _diagnostico_claves():
    """Solo conteos de claves configuradas (no validez, valores ni huellas).
    Se consulta el MISMO banco del Router y el panel del bridge OpenClaw.
    """
    inventario = {}
    try:
        from mvp import externos
        from mvp import app as mvp_app
        banco = getattr(mvp_app.app.state, "banco", None)
        inventario["yaiwes"] = {
            "groq": len(externos.claves("groq", banco)),
            "nvidia": len(externos.claves("nvidia", banco))}
    except (ImportError, RuntimeError, TypeError, AttributeError) as exc:
        inventario["yaiwes"] = {"error": type(exc).__name__}
    key = _clave()
    try:
        if not key:
            raise ValueError("SIN_CLAVE_ACCESO")
        req = urllib.request.Request("http://127.0.0.1:7870/v1/claves",
                                     headers={"X-API-Key": key})
        with urllib.request.urlopen(req, timeout=10) as response:
            datos = json.loads(response.read(10240))
        if not isinstance(datos, dict) or datos.get("ok") is not True:
            raise ValueError("SIN_CONTEOS")
        inventario["openclaw"] = {p: int(datos[p]) for p in ("groq","nvidia")
                                  if type(datos.get(p)) is int and 0 <= datos[p] <= 1000}
    except (urllib.error.URLError, OSError, ValueError, TypeError, KeyError) as exc:
        inventario["openclaw"] = {"error": type(exc).__name__}
    # Las claves configuradas no certifican permiso, saldo ni que sean
    # cuentas distintas: 429 de organizacion requiere esperar su cuota.
    return {"estado": "terminado", "reply": "Inventario de claves: "
            + json.dumps(inventario, ensure_ascii=False, sort_keys=True),
            "inventario": inventario,
            "aviso": "Cantidad configurada, no claves validadas ante proveedor."}


def _coda_tests():
    """Ejecuta solo los tests versionados y fijos; no ejecuta texto del chat."""
    raiz = Path(__file__).resolve().parents[4]
    backend = raiz / "chat-router" / "chat" / "backend"
    js_test = raiz / "chat-router" / "SWE CODE" / "web-bridge" / "test" / "coda_router.test.mjs"
    if not (backend / "mvp" / "test_loop_codigo.py").is_file() or not js_test.is_file():
        return {"estado":"error", "error":"PRUEBAS_CODA_AUSENTES"}
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join((str(raiz / "chat-router"), str(backend),
                                        env.get("PYTHONPATH","")))
    casos = [
        ("mvp_codacode", [sys.executable, "-m", "unittest",
                           "mvp.test_loop_codigo", "mvp.test_rotacion_groq_coda", "-v"], backend),
        ("mcp_harness", [sys.executable, "-m", "unittest",
                          "deepseek_harness.test_metricas_credenciales", "-v"], backend),
    ]
    node = __import__("shutil").which("node")
    if node:
        casos.append(("bridge_openclaw", [node, "--test", str(js_test)], raiz))
    salidas = {}
    for nombre, argv, cwd in casos:
        try:
            r = subprocess.run(argv, cwd=str(cwd), env=env,
                               capture_output=True, text=True, timeout=55, check=False)
            salidas[nombre] = {"pass":r.returncode==0, "exit":r.returncode,
                               "resumen":(r.stdout+"\n"+r.stderr)[-1200:]}
        except (OSError, subprocess.TimeoutExpired):
            salidas[nombre] = {"pass":False, "error":"EJECUTOR_NO_DISPONIBLE_O_TIMEOUT"}
    ok = all(v.get("pass") for v in salidas.values()) and bool(node)
    return {"estado":"terminado" if ok else "error", "reply": "CODA_TESTS_" + ("PASS" if ok else "GAP"),
            "pruebas":salidas, "node_presente":bool(node),
            "aviso":"Pruebas deterministas. No sustituyen llamadas reales a APIs."}


def _consulta(modelo, mensaje, sesion, timeout):
    # Sondas rápidas de la infraestructura EXISTENTE. No mandan prompts a
    # Qwen, DeepSeek ni Claude y nunca solicitan contraseñas o cookies.
    comando = str(mensaje).strip()
    if comando in ("@swen/health", "@swen/diag"):
        key = _clave()
        if not key:
            return {"estado":"error","error":"SWEN_MCP_SIN_CLAVE_BACKEND"}
        ruta = "/health" if comando == "@swen/health" else "/v1/web/diagnostico"
        req = urllib.request.Request("http://127.0.0.1:7870" + ruta,
                                     headers={"X-API-Key": key})
        try:
            with urllib.request.urlopen(req, timeout=15) as res:
                obj = json.loads(res.read(65536))
            if comando == "@swen/health":
                pool = obj.get("pool") or {}
                return {"estado":"terminado","diagnostico":"bridge_health",
                        "bridge_ok":obj.get("ok") is True,
                        "cuentas_configuradas":int(pool.get("total") or 0),
                        "banco_cargado":pool.get("loaded") is True,
                        "nota":"Cuentas configuradas no equivalen a sesiones iniciadas."}
            data = obj.get("indicadores") or {}
            sites = {}
            for site in ("qwen","deepseek","claude"):
                item = data.get(site) or {}
                sites[site] = {"navegador":str(item.get("navegador") or "NO_VERIFICADO")[:30],
                    "auth_url":item.get("auth_url") is True,
                    "login_visible":item.get("login_visible") is True,
                    "editor_visible":item.get("editor_visible") is True,
                    "modelo_selector_visible":item.get("modelo_selector_visible") is True}
            return {"estado":"terminado","diagnostico":"estado_web_sin_datos_personales",
                    "sitios":sites,
                    "nota":"Indicadores de DOM; no prueban inferencia ni autentican cuentas."}
        except urllib.error.HTTPError as exc:
            return {"estado":"error","error":"SWEN_DIAGNOSTICO_HTTP_"+str(exc.code)}
        except (OSError,ValueError,TypeError,TimeoutError):
            return {"estado":"error","error":"SWEN_DIAGNOSTICO_NO_DISPONIBLE"}
    if str(mensaje).strip() == "@swen/claves":
        return _diagnostico_claves()
    if str(mensaje).strip() == "@swen/selftest-persistencia":
        pid = "swen_" + uuid.uuid4().hex
        ok = _persist_write(pid,{"modelo":"web-qwen38max","worker":os.getpid(),
                "resultado":{"estado":"terminado","reply":"PERSISTENCIA_OK"}})
        resultado = _persist_result(pid)
        try:
            p = _persist_path(pid)
            if p: p.unlink(missing_ok=True)
        except OSError: pass
        return {"estado":"terminado","diagnostico":"persistencia_mcp",
                "pass":bool(ok and resultado and resultado.get("reply")=="PERSISTENCIA_OK"),
                "disco":"DISPONIBLE" if ok else "NO_DISPONIBLE"}
    if str(mensaje).strip() == "@swen/codatest":
        return _coda_tests()
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
        digest=hashlib.sha256((rid+"|"+_clave()).encode()).hexdigest() if rid else ""
        if digest:
            anterior=_persist_by_request(digest)
            if anterior:
                if anterior.get("firma") != firma:
                    return {"error":"SWEN_REQUEST_ID_REUTILIZADO"}
                return _persist_result(anterior["pid"]) or {
                    "estado":"error","error":"SWEN_REGISTRO_NO_DISPONIBLE"}
        if len(_JOBS) >= 128:
            return {"error": "SWEN_COLA_LLENA"}
        pid = "swen_" + uuid.uuid4().hex
        creado=time.time()
        persistido=_persist_write(pid,{"modelo":modelo,"sesion":sesion,
            "firma":firma,"rid_hash":digest,"creado":creado,"worker":os.getpid()})
        f = _EXEC.submit(_consulta, modelo, mensaje, sesion,
                         450 if modelo == "swecode-consulta" else 360)
        _JOBS[pid] = {"futuro": f, "creado": creado, "firma": firma, "modelo": modelo}
        f.add_done_callback(lambda futuro,_pid=pid,_m=modelo,_s=sesion,
            _f=firma,_d=digest,_c=creado:
            _persist_done(_pid,_m,_s,_f,_d,_c,futuro))
        if rid:
            _REQUESTS[rid] = pid
        return {"estado": "procesando", "proceso_id": pid, "modelo_solicitado": modelo,
                "persistencia_mcp":"ACTIVA" if persistido else "NO_DISPONIBLE"}


def resultado(args):
    pid = str(args.get("proceso_id") or "")
    if not re.fullmatch(r"swen_[0-9a-f]{32}", pid):
        return {"error": "SWEN_PROCESO_ID_INVALIDO"}
    with _LOCK:
        job = _JOBS.get(pid)
    if not job:
        return _persist_result(pid) or {
            "estado":"error","error":"SWEN_PROCESO_NO_ENCONTRADO","proceso_id":pid}
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
