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
from pathlib import Path
import re
import shutil
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

MODELOS = {
    "web-qwen38max": "qwen38max",
    "web-claude-sonnet": "anthropic/claude-sonnet-5-5",
    "web-qwen37max": "qwen37max",
    "web-dsv4-flash": "dsv4-flash",
    "swecode-consulta": "qwen38max",
}
_EXEC = cf.ThreadPoolExecutor(max_workers=4, thread_name_prefix="mcp_swen")
_JOBS: dict[str, dict] = {}
_REQUESTS: dict[str, str] = {}
_LOCK = threading.RLock()
_ID = re.compile(r"^[A-Za-z0-9_-]{1,80}$")
# Compartido con el estado persistente del bridge, no usa nuevas infraestructuras.
_JOURNAL = Path(os.getenv("BRIDGE_STATE_DIR") or "/tmp/state") / "swen_mcp"
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


def _guardar(pid, doc):
    """Checkpoint atómico de proceso/resultados; no guarda claves, correos ni prompts."""
    try:
        _JOURNAL.mkdir(mode=0o700, parents=True, exist_ok=True)
        p = _JOURNAL / (pid + ".json")
        tmp = _JOURNAL / (pid + "." + uuid.uuid4().hex + ".tmp")
        with open(tmp, "x", encoding="utf-8") as out:
            os.chmod(tmp, 0o600)
            json.dump(doc, out, ensure_ascii=False)
        os.replace(tmp, p)
    except OSError:
        try:
            tmp.unlink(missing_ok=True)
        except Exception:
            pass


def _leer(pid):
    if not re.fullmatch(r"swen_[0-9a-f]{32}", str(pid)):
        return None
    try:
        doc = json.loads((_JOURNAL / (pid + ".json")).read_text(encoding="utf-8"))
        return doc if isinstance(doc, dict) and doc.get("proceso_id") == pid else None
    except (OSError, ValueError, TypeError):
        return None


def _diagnostico():
    """Salud REAL del bridge; no ejecuta una inferencia ni expone datos de cuentas."""
    try:
        with urllib.request.urlopen("http://127.0.0.1:7870/health", timeout=8) as response:
            datos = json.load(response)
        pool = datos.get("pool") or {}
        return {"estado": "terminado", "diagnostico": "bridge_swen",
                "bridge_ok": bool(datos.get("ok")), "cuentas_configuradas": bool(pool.get("loaded")),
                "cantidad_cuentas": int(pool.get("total") or 0),
                "estado_sesiones": "SIN_VERIFICAR_CON_LOGIN",
                "nota": "Health confirma proceso/cuentas, no respuesta de modelo."}
    except (OSError, ValueError, urllib.error.URLError):
        return {"estado": "error", "error": "SWEN_BRIDGE_HEALTH_NO_DISPONIBLE"}


def _inferencia_y_checkpoint(pid, modelo, mensaje, sesion, timeout, firma):
    try:
        respuesta = _consulta(modelo, mensaje, sesion, timeout)
    except Exception:
        respuesta = {"estado": "error", "error": "SWEN_EXCEPCION_INTERNA"}
    _guardar(pid, {"proceso_id": pid, "firma": firma, "modelo": modelo,
                   "estado": respuesta.get("estado"), "resultado": respuesta})
    return respuesta


def _consulta(modelo, mensaje, sesion, timeout):
    if mensaje.strip() == "@swen/ocauth":
        # Verificación de disponibilidad de RUTAS YA AUTORIZADAS (sin tokens).
        # No inicia sesión, no copia credenciales ni crea cuentas.
        claude=shutil.which("claude") or ("/opt/node24/bin/claude" if os.path.isfile("/opt/node24/bin/claude") else "")
        api=bool(os.getenv("ANTHROPIC_API_KEY"))
        cli_status="NO_INSTALADO"
        if claude:
            try:
                home="/tmp/openclaw-home-"+str(os.getuid())
                resp=subprocess.run([claude,"auth","status","--json"],
                    timeout=12,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                    text=True,check=False,env={**os.environ,
                      "HOME":home,"PATH":"/opt/node24/bin:"+os.getenv("PATH","")})
                if resp.returncode==0:
                    d=json.loads(resp.stdout[:5000])
                    cli_status="ACTIVO" if d.get("loggedIn") is True else "NO_AUTORIZADO"
                else: cli_status="NO_AUTORIZADO"
            except (OSError,ValueError,subprocess.TimeoutExpired):
                cli_status="NO_VERIFICABLE"
        return {"estado":"terminado","diagnostico":"anthropic_auth",
                "anthropic_api_env":api,"claude_cli":cli_status,
                "nota":"El Gateway puede tener perfiles almacenados aparte; ping HTTP sigue siendo la prueba definitiva."}
    if mensaje.strip() == "@swen/ocping":
        # Prueba REAL mínima de OpenClaw Sonnet, sin override de modelos ni
        # comandos /think: aislar error de contrato HTTP vs autenticación.
        token = os.getenv("OPENCLAW_GATEWAY_TOKEN") or ""
        if not token:
            return {"estado":"error","error":"OPENCLAW_TOKEN_NO_CONFIGURADO"}
        body = json.dumps({"model":"openclaw/swen-council","stream":False,
                           "messages":[{"role":"user","content":"Responde solo PING_SWEN_OK"}]}).encode()
        req = urllib.request.Request("http://127.0.0.1:18789/v1/chat/completions",
                                      data=body,method="POST",headers={
                                      "Authorization":"Bearer "+token,
                                      "Content-Type":"application/json","Accept":"application/json"})
        try:
            with urllib.request.urlopen(req,timeout=100) as response:
                data=json.load(response)
            msg = str(((data.get("choices") or [{}])[0].get("message") or {}).get("content") or "")
            return {"estado":"terminado","diagnostico":"openclaw_sonnet_ping",
                    "http":200,"respuesta_no_vacia":bool(msg.strip()),
                    "ping_ok":"PING_SWEN_OK" in msg}
        except urllib.error.HTTPError as exc:
            raw=exc.read(6000)
            try:
                data=json.loads(raw)
                er=data.get("error") or {}
                if not isinstance(er,dict): er={}
                code=str(er.get("code") or "")
                kind=str(er.get("type") or "")
                msg=str(er.get("message") or "").lower()
            except (ValueError,TypeError,UnicodeError):
                code=kind=msg=""
            if not re.fullmatch(r"[A-Za-z0-9_-]{1,60}",code):code="SIN_CODIGO"
            if not re.fullmatch(r"[A-Za-z0-9_-]{1,60}",kind):kind="SIN_TIPO"
            vocab=("model","agent","auth","provider","credential","profile",
                   "session","schema","invalid","unknown","allow","quota",
                   "gateway","configuration","missing","required","disabled")
            return {"estado":"error","diagnostico":"openclaw_sonnet_ping",
                    "http":exc.code,"codigo":code,"tipo":kind,
                    "categorias":[v for v in vocab if v in msg]}
        except (OSError,ValueError,TimeoutError):
            return {"estado":"error","error":"OPENCLAW_PING_SIN_RESPUESTA"}
    if mensaje.strip() == "@swen/ocproc":
        # Observabilidad estricta: procesa sólo /proc local y entrega contadores,
        # sin argumentos ni token de los procesos.
        procesos=[]
        for proc in Path("/proc").iterdir():
            if not proc.name.isdigit():
                continue
            try:
                argv=(proc/"cmdline").read_bytes().decode("utf-8","replace").split("\\x00")
                args=" ".join(argv)
                if "openclaw" in args.lower() and "gateway" in args.lower():
                    procesos.append({"pid":int(proc.name),
                        "puerto": "--port 18789" in args,
                        "comando_gateway":" gateway " in (" "+args+" ")})
            except (OSError,ValueError):
                continue
        return {"estado":"terminado","diagnostico":"proceso_openclaw",
                "procesos":procesos[:12],
                "total":len(procesos)}
    if mensaje.strip() == "@swen/ocroute":
        # Sonda HTTP localhost con bearer del entorno; imprime SOLO status.
        token = os.getenv("OPENCLAW_GATEWAY_TOKEN") or ""
        estados = {}
        detalles = {}
        for ruta in ("/v1/models","/openclaw/v1/models","/health"):
            req = urllib.request.Request("http://127.0.0.1:18789"+ruta,
                                          headers={"Authorization":"Bearer "+token})
            try:
                with urllib.request.urlopen(req,timeout=6) as resp:
                    estados[ruta] = resp.status
                    tipo = str(resp.headers.get("content-type","")).split(";")[0].strip().lower()
                    muestra = resp.read(4096)
                    try:
                        j = json.loads(muestra)
                        api = (isinstance(j,dict) and j.get("object")=="list"
                               and isinstance(j.get("data"),list))
                    except (ValueError,UnicodeError,TypeError):
                        api = False
                    detalles[ruta] = {"tipo":tipo[:40],"catalogo_api":api}
            except urllib.error.HTTPError as exc:
                estados[ruta] = exc.code
                detalles[ruta] = {"tipo":"HTTP_ERROR","catalogo_api":False}
            except (OSError,TimeoutError):
                estados[ruta] = 0
                detalles[ruta] = {"tipo":"SIN_CONEXION","catalogo_api":False}
        return {"estado":"terminado","diagnostico":"rutas_gateway",
                "http":estados,"detalles":detalles,
                "url_custom_configurado":bool(os.getenv("RIU_OPENCLAW_URL"))}
    if mensaje.strip() == "@swen/oclint":
        # Doctor LINT es sólo lectura; no altera pairing, sesión o configuración.
        binary = "/opt/node24/bin/openclaw" if os.path.isfile("/opt/node24/bin/openclaw") else shutil.which("openclaw")
        if not binary or not os.path.isfile(binary):
            return {"estado":"error","error":"OPENCLAW_BIN_NO_ENCONTRADO"}
        home = "/tmp/openclaw-home-" + str(os.getuid())
        try:
            run = subprocess.run([binary,"doctor","--lint","--only",
                                  "core/doctor/gateway-config","--json"],
                cwd="/tmp",capture_output=True,text=True,timeout=35,check=False,
                env={**os.environ,"HOME":home,
                     "OPENCLAW_STATE_DIR":home+"/.openclaw","OPENCLAW_HOME":home,
                     "PATH":"/opt/node24/bin:"+os.getenv("PATH","")})
            try:
                result=json.loads(run.stdout)
                findings=result.get("findings") or []
                safe=[]
                for issue in findings[:12] if isinstance(findings,list) else []:
                    if not isinstance(issue,dict):continue
                    field=issue.get("path") or ""
                    if not isinstance(field,str) or not re.fullmatch(
                        r"(?:gateway|agents|models|tools)[.\\[\\]a-zA-Z0-9_./-]{0,120}",field):
                        field=""
                    msg=str(issue.get("message") or "")
                    # Mostrar solo nombres de CLAVES DE CONFIG, nunca mensajes completos:
                    # un proveedor podría incluir tokens/emails en sus diagnósticos.
                    refs=sorted(set(re.findall(
                        r"(?:gateway|agents|models|tools)(?:\\.[A-Za-z_][A-Za-z0-9_-]*){1,8}",msg)))
                    clases=[w for w in ("unknown","invalid","missing","unrecognized",
                                        "unsupported","schema","config","workspace",
                                        "provider","authentication","migration") if w in msg.lower()]
                    safe.append({"check":str(issue.get("checkId") or "")[:70],
                        "severity":str(issue.get("severity") or "")[:20],
                        "path":field,"referencias":refs[:8],"categorias":clases})
                return {"estado":"terminado","diagnostico":"openclaw_doctor_lint",
                    "codigo":run.returncode,"comprobaciones":int(result.get("checksRun") or 0),
                    "fallos":safe}
            except (ValueError,TypeError,AttributeError):
                return {"estado":"error","error":"OPENCLAW_LINT_NO_JSON",
                    "codigo":run.returncode}
        except (OSError,subprocess.TimeoutExpired):
            return {"estado":"error","error":"OPENCLAW_LINT_FALLO"}
    if mensaje.strip() == "@swen/ocschema":
        # Validación read-only del JSON local contra el esquema publicado
        # por el ejecutable OpenClaw instalado. No copiar valores secretos.
        binary = "/opt/node24/bin/openclaw" if os.path.isfile("/opt/node24/bin/openclaw") else shutil.which("openclaw")
        try:
            import jsonschema
        except ImportError:
            return {"estado":"error","error":"VALIDADOR_JSONSCHEMA_NO_INSTALADO"}
        if not binary or not os.path.isfile(binary):
            return {"estado":"error","error":"OPENCLAW_BIN_NO_ENCONTRADO"}
        home = "/tmp/openclaw-home-" + str(os.getuid())
        env = {**os.environ,"HOME":home,"OPENCLAW_STATE_DIR":home+"/.openclaw",
               "OPENCLAW_HOME":home,"PATH":"/opt/node24/bin:"+os.getenv("PATH","")}
        try:
            run=subprocess.run([binary,"config","schema"],capture_output=True,
                               text=True,timeout=28,check=False,env=env,cwd="/tmp")
            if run.returncode or len(run.stdout)>6000000:
                return {"estado":"error","error":"OPENCLAW_SCHEMA_NO_DISPONIBLE"}
            spec=json.loads(run.stdout)
            schema=spec.get("schema") if isinstance(spec,dict) and isinstance(spec.get("schema"),dict) else spec
            cfgpath=Path(home)/".openclaw"/"openclaw.json"
            if cfgpath.is_symlink() or not cfgpath.is_file():
                return {"estado":"error","error":"OPENCLAW_CONFIG_NO_ENCONTRADA"}
            config=json.loads(cfgpath.read_text(encoding="utf-8"))
            val=jsonschema.Draft202012Validator(schema)
            issues=[]
            for err in val.iter_errors(config):
                path=".".join(str(x) for x in err.path)
                if not re.fullmatch(r"[A-Za-z0-9_.:/\\[\\]-]{0,130}",path):
                    path="[RUTA_REDACTADA]"
                issues.append({"campo":path[:130],"criterio":str(err.validator)[:36]})
                if len(issues)>=18:break
            return {"estado":"terminado","diagnostico":"jsonschema_openclaw",
                    "config_valida":len(issues)==0,"issues":issues}
        except (OSError,subprocess.TimeoutExpired,ValueError,TypeError):
            return {"estado":"error","error":"OPENCLAW_SCHEMA_VALIDACION_FALLO"}
    if mensaje.strip() == "@swen/ocdoctor":
        binary = "/opt/node24/bin/openclaw" if os.path.isfile("/opt/node24/bin/openclaw") else shutil.which("openclaw")
        if not os.path.isfile(binary):
            return {"estado":"error","error":"OPENCLAW_BIN_NO_ENCONTRADO"}
        home = "/tmp/openclaw-home-" + str(os.getuid())
        try:
            run = subprocess.run([binary,"config","validate","--json"],cwd="/tmp",capture_output=True,
                                 text=True,timeout=22,check=False,env={
                                   **os.environ,"HOME":home,
                                   "OPENCLAW_STATE_DIR":home+"/.openclaw",
                                   "OPENCLAW_HOME":home,
                                   "PATH":"/opt/node24/bin:"+os.getenv("PATH","")})
            salida = (run.stdout+"\\n"+run.stderr).lower()
            # --json: sólo revelar rutas de campos con error de esquema,
            # nunca valores de configuración, perfiles o secretos.
            paths_json=[]
            descripciones=[]
            datos_clase="SIN_JSON"
            raiz_campos=[]
            try:
                obj=json.loads(run.stdout)
                if isinstance(obj,dict):
                    datos_clase="JSON_OBJETO"
                    raiz_campos=sorted(x for x in obj.keys() if x in
                        ("ok","valid","errors","issues","path","details","error","message","warnings"))
                else:
                    datos_clase="JSON_OTRO"
                errores=(obj.get("errors") or obj.get("issues") or []) if isinstance(obj,dict) else []
                if isinstance(errores,list):
                    for item in errores[:20]:
                        if not isinstance(item,dict): continue
                        p=item.get("path") or item.get("field") or ""
                        if isinstance(p,list): p=".".join(str(x) for x in p)
                        if isinstance(p,str) and re.fullmatch(
                           r"(?:gateway|agents|models|tools)(?:[.\\[\\]a-zA-Z0-9_-]*)",p):
                            paths_json.append(p[:110])
                        # Sólo vocabulario técnico, nunca valores contenidos en el mensaje.
                        raw=str(item.get("message") or item.get("reason") or "").lower()
                        vocab=("default","ownership","explicit","legacy","migration",
                               "workspace","required","missing","invalid","unknown",
                               "agent","binding","systemagent","main","schema",
                               "duplicate","conflict","unsupported","id")
                        if "descripciones" not in locals(): descripciones=[]
                        descripciones.append({"codigo":str(item.get("code") or "")[:45]
                               if re.fullmatch(r"[A-Za-z0-9_-]{1,45}",str(item.get("code") or "")) else "",
                               "palabras":[k for k in vocab if k in raw]})
            except (ValueError,TypeError,AttributeError):
                pass
            if run.returncode == 0:
                tipo = "VALIDA"
            elif any(k in salida for k in ("unknown command","unknown option",
                                           "unrecognized command","no such command")):
                tipo = "CLI_SIN_CONFIG_VALIDATE"
            elif any(k in salida for k in ("invalid config","validation failed",
                                           "unrecognized key","unknown key","invalid configuration")):
                tipo = "CONFIG_INVALIDA"
            elif "permission denied" in salida:
                tipo = "PERMISOS"
            else:
                tipo = "ERROR_NO_CLASIFICADO"
            paths = sorted(set(re.findall(
                r"(?:gateway|agents|models|tools)\.[A-Za-z0-9_.\[\]-]{1,80}",salida)))
            # Publicar sólo líneas diagnósticas redactadas, sin valores/config.
            pistas=[]
            for linea in (run.stderr+"\\n"+run.stdout).splitlines():
                if not re.search(r"error|invalid|unknown|unsupported|command|schema|usage|validation|failed",linea,re.I):
                    continue
                linea=re.sub(r"[\\w.+-]+@[\\w.-]+","[EMAIL]",linea)
                linea=re.sub(r"https?://[^\\s]+","[URL]",linea)
                linea=re.sub(r"(?i)(password|token|secret|api.?key).*",r"\\1 [REDACTADO]",linea)
                linea=re.sub(r"\\b[A-Za-z0-9_-]{36,}\\b","[VALOR]",linea)
                pistas.append(linea[:160])
            return {"estado":"terminado","diagnostico":"schema_openclaw",
                    "config_valida":run.returncode==0, "tipo":tipo,
                    "campos":sorted(set(paths+paths_json))[:12],
                    "categorias_issues":descripciones[:8], "pistas":pistas[:6],
                    "json_tipo":datos_clase, "json_campos":raiz_campos,
                    "salidas":{"stdout":bool(run.stdout.strip()),"stderr":bool(run.stderr.strip())},
                    "codigo_salida":run.returncode}
        except (OSError,subprocess.TimeoutExpired):
            return {"estado":"error","error":"OPENCLAW_DOCTOR_NO_DISPONIBLE"}
    if mensaje.strip() == "@swen/occonfig":
        # Diagnóstico seguro del Gateway: sólo booleanos de la configuración,
        # nunca claves, tokens, perfiles ni datos personales.
        p = Path("/tmp/openclaw-home-" + str(os.getuid()) + "/.openclaw/openclaw.json")
        try:
            if p.is_symlink() or not p.is_file():
                return {"estado":"error","error":"OPENCLAW_CONFIG_NO_ENCONTRADA"}
            c = json.loads(p.read_text(encoding="utf-8"))
            gw = c.get("gateway") or {}
            http = (gw.get("http") or {}).get("endpoints") or {}
            registro = c.get("agents") or {}
            agents = registro.get("entries") or {}
            return {"estado":"terminado","diagnostico":"config_openclaw",
                    "agentes_list_presente":isinstance(registro.get("list"),list),
                    "agentes_entries_presente":isinstance(registro.get("entries"),dict),
                    "agentes_default":sum(1 for a in agents.values() if isinstance(a,dict) and a.get("default") is True),
                    "main_default":bool((agents.get("main") or {}).get("default") is True),
                    "ownership_explicit":registro.get("ownership")=="explicit",
                    "gateway_mode_local":gw.get("mode")=="local",
                    "chat_completions_habilitado":bool((http.get("chatCompletions") or {}).get("enabled")),
                    "agente_claude_registrado":"swen-council" in agents,
                    "agente_reparador_registrado":"swen-repair" in agents,
                    "openclaw_enable":os.getenv("OPENCLAW_ENABLE")=="1",
                    "gateway_token_configurado":bool(os.getenv("OPENCLAW_GATEWAY_TOKEN"))}
        except (OSError,ValueError,TypeError):
            return {"estado":"error","error":"OPENCLAW_CONFIG_INACCESIBLE"}
    if mensaje.strip() == "@swen/autotest":
        # Suite fija de nuestro repositorio, nunca comandos externos arbitrarios.
        raiz = Path(__file__).resolve().parents[4]
        test = raiz / "chat-router" / "SWE CODE" / "web-bridge" / "test" / "autoreparacion.test.mjs"
        node = shutil.which("node")
        if not node or not test.is_file():
            return {"estado":"error","error":"SWEN_AUTOTEST_SIN_NODE_O_ARCHIVO"}
        try:
            r = subprocess.run([node,"--test",str(test)], cwd=str(raiz),text=True,
                               capture_output=True,timeout=40,check=False,
                               env={**os.environ,"OPENCLAW_ENABLE":"0"})
            output=(r.stdout+"\n"+r.stderr)[-6000:]
            return {"estado":"terminado" if r.returncode==0 else "error",
                    "diagnostico":"autorreparacion_test",
                    "pass":r.returncode==0,"codigo_salida":r.returncode,
                    "resumen":output}
        except (OSError,subprocess.TimeoutExpired):
            return {"estado":"error","error":"SWEN_AUTOTEST_FALLO_TIMEOUT"}
    if mensaje.strip() == "@swen/gaps":
        req = urllib.request.Request("http://127.0.0.1:7870/v1/swen/gaps",
                                     headers={"X-API-Key": _clave()})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.load(resp)
            return {"estado":"terminado","diagnostico":"autoreparacion",
                    "gaps":(data.get("gaps") or [])[:20]}
        except urllib.error.HTTPError as exc:
            return {"estado":"error","error":"SWEN_GAPS_HTTP_"+str(exc.code)}
        except (OSError, ValueError, TimeoutError):
            return {"estado":"error","error":"SWEN_GAPS_NO_DISPONIBLES"}
    if mensaje.strip().startswith("@swen/reparar "):
        partes = mensaje.strip().split()
        gap = partes[1] if len(partes)==2 else ""
        if not re.fullmatch(r"gap_[0-9a-f]{24}",gap):
            return {"estado":"error","error":"SWEN_GAP_ID_INVALIDO"}
        req = urllib.request.Request("http://127.0.0.1:7870/v1/swen/gaps/"+gap+"/investigar",
                                     data=b"{}",method="POST",
                                     headers={"X-API-Key": _clave(),
                                              "Content-Type":"application/json"})
        try:
            with urllib.request.urlopen(req, timeout=75) as resp:
                return {"estado":"terminado","diagnostico":"openclaw", "respuesta":json.load(resp)}
        except urllib.error.HTTPError as exc:
            try:
                detalle=json.loads(exc.read(8192))
                return {"estado":"error","error":str(detalle.get("code") or "NO_DISPONIBLE")[:90]}
            except (ValueError, TypeError):
                return {"estado":"error","error":"SWEN_REPARAR_HTTP_"+str(exc.code)}
        except (OSError,ValueError,TimeoutError):
            return {"estado":"error","error":"SWEN_REPARAR_SIN_RESPUESTA"}
    if mensaje.strip() == "@swen/diag":
        req = urllib.request.Request("http://127.0.0.1:7870/v1/web/diagnostico",
                                     headers={"X-API-Key": _clave()})
        try:
            with urllib.request.urlopen(req, timeout=14) as response:
                d = json.load(response)
            return {"estado":"terminado","diagnostico":"web_auth_editor",
                    "indicadores":d.get("indicadores",{}),
                    "nota":"Diagnóstico de elementos visibles, no acceso a credenciales."}
        except urllib.error.HTTPError as exc:
            return {"estado":"error","error":"SWEN_DIAG_HTTP_"+str(exc.code)}
        except (OSError,ValueError,TimeoutError):
            return {"estado":"error","error":"SWEN_DIAG_NO_DISPONIBLE"}
    if mensaje.strip() == "@swen/claude":
        req = urllib.request.Request("http://127.0.0.1:7870/v1/claude/estado",
                                     headers={"X-API-Key": _clave()})
        try:
            with urllib.request.urlopen(req, timeout=12) as respuesta:
                data = json.load(respuesta)
            return {"estado":"terminado", "diagnostico":"claude_gateway",
                    "gateway_disponible":bool(data.get("disponible")),
                    "razon":str(data.get("reason") or "SIN_RESULTADO")[:100],
                    "modelo":str(data.get("modelo") or "")[:100],
                    "http":int(data.get("http") or 0)}
        except urllib.error.HTTPError as exc:
            return {"estado":"error","error":"SWEN_CLAUDE_HTTP_" + str(exc.code)}
        except (OSError, ValueError, TimeoutError):
            return {"estado":"error","error":"SWEN_CLAUDE_NO_VERIFICABLE"}
    if mensaje.strip() == "@swen/sesiones":
        # Diagnóstico auténtico de las SESIONES WEB. Emplea el endpoint
        # existente; se respetan las verificaciones oficiales de cada sitio.
        req = urllib.request.Request("http://127.0.0.1:7870/refresh_session",
                                     data=b"{}", method="POST",
                                     headers={"Content-Type": "application/json",
                                              "X-API-Key": _clave()})
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                obj = json.load(resp)
            return {"estado": "terminado", "diagnostico": "sesiones",
                    "sitios": {k: str(v)[:160] for k, v in
                               (obj.get("sitios") or {}).items()
                               if k in ("qwen", "deepseek")},
                    "nota": "Prueba de sesión/login; ninguna inferencia ejecutada."}
        except urllib.error.HTTPError as exc:
            return {"estado": "error", "error": "SWEN_SESIONES_HTTP_" + str(exc.code)}
        except (OSError, ValueError, TimeoutError):
            return {"estado": "error", "error": "SWEN_SESIONES_NO_DISPONIBLES"}
    key = _clave()
    if not key:
        return {"estado": "error", "error": "SWEN_MCP_SIN_CLAVE_BACKEND"}
    cuerpo = {"model": modelo, "messages": [{"role": "user", "content": mensaje}],
              "conv_id": sesion, "tools": False, "stream": False, "origen": "mcp-swen"}
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
            eleccion = (obj.get("choices") or [{}])[0]
            mensaje_respuesta = eleccion.get("message") or {}
            usado = obj.get("modelo_usado") or obj.get("model") or ""
            texto = mensaje_respuesta.get("content") or ""
            if not isinstance(texto, str) or not texto.strip():
                return {"estado": "error", "error": "SWEN_SIN_RESPUESTA", "modelo_usado": usado}
            if usado and str(usado) != MODELOS[modelo]:
                return {"estado": "error", "error": "SWEN_MODELO_CAMBIADO",
                        "modelo_solicitado": modelo, "modelo_usado": str(usado)[:100]}
            if obj.get("via_respaldo"):
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
    if mensaje.strip() == "@swen/health":
        return _diagnostico()
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
        _guardar(pid, {"proceso_id": pid, "firma": firma, "modelo": modelo,
                       "estado": "procesando", "creado": time.time()})
        f = _EXEC.submit(_inferencia_y_checkpoint, pid, modelo, mensaje, sesion,
                         450 if modelo == "swecode-consulta" else 360, firma)
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
        guardado = _leer(pid)
        if guardado:
            if isinstance(guardado.get("resultado"), dict):
                return {"proceso_id": pid, **guardado["resultado"]}
            return {"estado": "interrumpido", "proceso_id": pid,
                    "modelo_solicitado": guardado.get("modelo"),
                    "error": "SWEN_PROCESO_REINICIADO_ANTES_DE_TERMINAR"}
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
