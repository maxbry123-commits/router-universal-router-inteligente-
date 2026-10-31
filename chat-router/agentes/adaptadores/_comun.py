"""Utilidades de los adaptadores: subproceso seguro (lista de argumentos, sin shell, timeout, limite de salida, entorno minimo),
validacion de entradas, endpoint del modelo y recibo. Sin estado y sin almacenamiento propio."""
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import tempfile
import time
import urllib.request
from datetime import datetime, timezone

from .modelos import validar_modelo

TIMEOUT_S = float(os.environ.get("RIU_AGENTE_TIMEOUT_S", "1800"))
MAX_SALIDA = int(os.environ.get("RIU_AGENTE_MAX_SALIDA", "400000"))
MAX_OBJETIVO, MAX_CONTEXTO = 20000, 40000
_TASK_ID = re.compile(r"[A-Za-z0-9_-]{1,64}")
_SECRETO = re.compile(r"(?:sk-(?:sp-)?[A-Za-z0-9_-]{12,}|github_pat_[A-Za-z0-9_]{12,}|gh[pousr]_[A-Za-z0-9]{12,}|hf_[A-Za-z0-9]{20,}|gsk_[A-Za-z0-9]{12,}|nvapi-[A-Za-z0-9_-]{12,})")
INSTALAR = {
    "codex": "Instala la CLI de Codex (npm i -g @openai/codex, o compila agentes/agentes-listos/codex/codex-main/codex-rs) y define RIU_CODEX_BIN si no esta en PATH.",
    "opencode": "Instala OpenCode (npm i -g opencode-ai) o define RIU_OPENCODE_BIN con la ruta del binario.",
    "swe-agent": "Instala SWE-agent: pip install -e agentes/agentes-listos/SWE-agent/SWE-agent-main (comando `sweagent`) y define RIU_SWEAGENT_BIN si no esta en PATH; requiere Docker.",
    "openhands": "Instala el SDK: pip install -e agentes/agentes-listos/openhands-software-agent-sdk/code/openhands-sdk y .../openhands-tools; define RIU_OPENHANDS_PYTHON con el Python que lo tiene.",
    "claude-code": "Instala la CLI de Claude Code (`claude`) y define RIU_CLAUDE_BIN si no esta en PATH.",
    "openclaw": "Arranca el Gateway OpenClaw (127.0.0.1:18789, habilita gateway.http.endpoints.chatCompletions) y define OPENCLAW_GATEWAY_TOKEN; URL por RIU_OPENCLAW_URL.",
}


class ErrorPrevio(Exception):
    """Fallo antes de lanzar nada: el resultado ya es el dict de error que devuelve run()."""
    def __init__(self, resultado):
        super().__init__(resultado.get("codigo"))
        self.resultado = resultado


_NOMBRE_SENSIBLE = re.compile(r"(?:KEY|TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIAL)S?(?:_\d+)?$", re.I)


def valores_sensibles():
    """Valores (>= 8 caracteres) de las variables de entorno con nombre de credencial (RIU_API_KEY, *_TOKEN, GROQ_API_KEY_3...), mas largos primero."""
    vals = {v.strip() for n, v in os.environ.items() if _NOMBRE_SENSIBLE.search(n) and isinstance(v, str) and len(v.strip()) >= 8}
    return sorted(vals, key=len, reverse=True)


def redactar(texto):
    """Quita credenciales por FORMA (sk-, gsk_, nvapi-...) y por VALOR de las variables sensibles del entorno."""
    t = _SECRETO.sub("[REDACTADO]", texto if isinstance(texto, str) else str(texto))
    for v in valores_sensibles():
        if v in t:
            t = t.replace(v, "[REDACTADO]")
    return t


class _SinRedireccion(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # un 3xx llega como HTTPError: ni la clave ni el cuerpo viajan a otro destino


_ABRIDOR = urllib.request.build_opener(_SinRedireccion)


def abrir(req, timeout):
    """urlopen que NO sigue redirecciones (la cabecera Authorization y el cuerpo solo van al host validado)."""
    return _ABRIDOR.open(req, timeout=timeout)


def ahora():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def error(agente, task_id, codigo, mensaje, efectos_posibles=False, exit_code=None, **extra):
    """Resultado de fallo. efectos_posibles=False solo si se sabe que nada se ejecuto (el Harness puede reintentar sin riesgo)."""
    return {"ok": False, "agente": agente, "task_id": task_id, "codigo": codigo, "error": redactar(mensaje)[:2000], "resultado": "",
            "herramientas": [], "evidencias": [], "recibo": None, "exit_code": exit_code, "efectos_posibles": bool(efectos_posibles), **extra}


def no_instalado(agente, task_id, detalle=""):
    return error(agente, task_id, "AGENTE_NO_INSTALADO", ("%s no esta instalado en este entorno. %s %s" % (agente, detalle, INSTALAR.get(agente, ""))).strip(), False)


def entorno_base(extra=None):
    """Entorno minimo: no hereda claves del Harness (RIU_API_KEY, tokens). Cada adaptador anade solo lo que su agente necesita."""
    e = {k: os.environ[k] for k in ("PATH", "HOME", "LANG", "LC_ALL", "TMPDIR", "USER") if os.environ.get(k)}
    e.setdefault("PATH", "/usr/local/bin:/usr/bin:/bin")
    e.update(extra or {})
    return e


def binario(nombre, variable):
    ruta = os.environ.get(variable, "").strip()
    if ruta:
        return ruta if os.path.isfile(ruta) and os.access(ruta, os.X_OK) else None
    return shutil.which(nombre)


def ejecutar_proceso(argv, cwd, env, timeout=None, max_salida=None, entrada=None):
    """Lanza argv (lista, shell=False). Mata el grupo de procesos al vencer el timeout o al pasar el limite de salida."""
    timeout = TIMEOUT_S if timeout is None else timeout
    max_salida = MAX_SALIDA if max_salida is None else max_salida
    if not isinstance(argv, (list, tuple)) or not all(isinstance(a, str) for a in argv):
        raise TypeError("argv debe ser una lista de str")
    t0 = time.monotonic()
    with tempfile.TemporaryFile() as fo, tempfile.TemporaryFile() as fe, tempfile.TemporaryFile() as fi:
        if entrada:
            fi.write(entrada.encode("utf-8")); fi.flush()
        fi.seek(0)
        p = subprocess.Popen(list(argv), cwd=cwd, env=env, stdin=fi, stdout=fo, stderr=fe, shell=False, start_new_session=True)
        vencio = truncado = False
        while p.poll() is None:
            if time.monotonic() - t0 > timeout:
                vencio = True
            elif os.fstat(fo.fileno()).st_size > max_salida or os.fstat(fe.fileno()).st_size > max_salida:
                truncado = True
            else:
                time.sleep(0.02)
                continue
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            p.wait()
        codigo = p.returncode
        def leer(f):
            f.seek(0); datos = f.read(max_salida + 1)
            return datos[:max_salida].decode("utf-8", "replace"), len(datos) > max_salida
        so, t1 = leer(fo); se, t2 = leer(fe)
    return {"exit_code": codigo, "stdout": so, "stderr": se, "timeout": vencio, "truncado": truncado or t1 or t2,
            "duracion_s": round(time.monotonic() - t0, 3), "pid": p.pid}


def preparar(agente, tarea_id, modelo, objetivo, contexto, permisos, checkpoint):
    """Valida las entradas de run() y arma el prompt. El texto del modelo es DATO: va como un solo argumento o por stdin, nunca a un shell."""
    def fallo(codigo, msg):
        return ErrorPrevio(error(agente, tarea_id if isinstance(tarea_id, str) else "", codigo, msg))
    if not isinstance(tarea_id, str) or not _TASK_ID.fullmatch(tarea_id):
        raise fallo("TASK_ID_INVALIDO", "task_id invalido")
    try:
        validar_modelo(modelo)
    except ValueError:
        raise fallo("MODELO_NO_REGISTRADO", "modelo fuera del catalogo") from None
    if not isinstance(objetivo, str) or not objetivo.strip():
        raise fallo("OBJETIVO_VACIO", "objetivo vacio")
    if len(objetivo) > MAX_OBJETIVO:
        raise fallo("OBJETIVO_DEMASIADO_LARGO", "objetivo supera %d caracteres" % MAX_OBJETIVO)
    if not isinstance(permisos, dict):
        raise fallo("PERMISOS_INVALIDOS", "permisos debe ser dict")
    directorio = permisos.get("directorio")
    if not isinstance(directorio, str) or not directorio or not os.path.isdir(directorio):
        raise fallo("DIRECTORIO_INVALIDO", "permisos.directorio no existe")
    ctx = contexto if isinstance(contexto, str) else json.dumps(contexto, ensure_ascii=False, default=str)
    prompt = "Tarea %s:\n%s" % (tarea_id, objetivo.strip())
    if ctx.strip():
        prompt += "\n\nContexto confirmado de pasos anteriores:\n" + ctx.strip()[:MAX_CONTEXTO]
    return {"prompt": prompt, "directorio": os.path.realpath(directorio), "escritura": bool(permisos.get("escritura")),
            "ejecucion": bool(permisos.get("ejecucion")), "modelo": modelo, "tarea_id": tarea_id,
            "checkpoint": checkpoint if isinstance(checkpoint, dict) else {}}


def _clave(var):
    for nombre in [var] + ["%s_%d" % (var, i) for i in range(1, 21)]:
        v = os.environ.get(nombre, "").strip()
        if v:
            return v
    return ""


def _credencial_bridge():
    """Los agentes (clientes OpenAI-compatibles) mandan esto como Bearer al bridge, que exige credencial: RIU_AGENTES_LLM_API_KEY o, si no, BRIDGE_TOKEN.
    Sin ninguna queda el marcador «no-requerida» y el bridge respondera 401 (se ve en el error del agente)."""
    return os.environ.get("RIU_AGENTES_LLM_API_KEY", "").strip() or os.environ.get("BRIDGE_TOKEN", "").strip() or "no-requerida"


def endpoint_modelo(modelo_id, agente="", tarea_id=""):
    """Endpoint OpenAI-compatible del modelo. hf -> bridge (RIU_SWE_BRIDGE_URL); groq/nvidia -> proveedor, con la clave del entorno."""
    cfg = validar_modelo(modelo_id)
    prov = cfg["provider"]
    if prov == "hf":
        base = (os.environ.get("RIU_AGENTES_LLM_BASE_URL") or os.environ.get("RIU_SWE_BRIDGE_URL") or "http://127.0.0.1:7870").strip().rstrip("/")
        if not base.endswith("/v1"):
            base += "/v1"
        return {"proveedor": prov, "base_url": base, "modelo": cfg["model"], "api_key": _credencial_bridge()}
    base = {"groq": "https://api.groq.com/openai/v1", "nvidia": "https://integrate.api.nvidia.com/v1"}[prov]
    clave = _clave(prov.upper() + "_API_KEY")
    if not clave:
        raise ErrorPrevio(error(agente, tarea_id, "AGENTE_NO_CONFIGURADO", "falta %s_API_KEY en el entorno del Harness" % prov.upper()))
    return {"proveedor": prov, "base_url": base, "modelo": cfg["model"], "api_key": clave}


def recibo(agente, tarea_id, exit_code, salida, inicio):
    """Huella de una ejecucion REAL (agente, tarea, codigo de salida, hash de la salida, instante de inicio). Sin ejecucion no hay recibo."""
    h = hashlib.sha256(json.dumps([agente, tarea_id, exit_code, hashlib.sha256((salida or "").encode("utf-8", "replace")).hexdigest(), inicio]).encode()).hexdigest()[:20]
    return "%s:%s:%s" % (agente, tarea_id, h)


def resultado_ok(agente, tarea_id, proc, texto, herramientas, evidencias, inicio):
    texto = redactar(texto or "")
    return {"ok": True, "agente": agente, "task_id": tarea_id, "resultado": texto[:100000], "herramientas": herramientas, "evidencias": evidencias,
            "recibo": recibo(agente, tarea_id, proc["exit_code"], proc["stdout"] + "\n" + proc["stderr"], inicio), "exit_code": proc["exit_code"],
            "inicio": inicio, "duracion_s": proc["duracion_s"], "truncado": proc["truncado"]}


def fallo_de_proceso(agente, tarea_id, proc):
    """Proceso lanzado que no termino bien: pudo haber efectos, asi que el Harness debe reconciliar antes de reintentar."""
    if proc["timeout"]:
        return error(agente, tarea_id, "AGENTE_TIMEOUT", "el agente supero el timeout y fue terminado", True, proc["exit_code"])
    cola = redactar((proc["stderr"] or proc["stdout"])[-1500:])
    return error(agente, tarea_id, "AGENTE_SALIO_CON_ERROR", "codigo de salida %s: %s" % (proc["exit_code"], cola), True, proc["exit_code"])


def jsonl(texto):
    out = []
    for linea in (texto or "").splitlines():
        linea = linea.strip()
        if linea.startswith("{"):
            try:
                out.append(json.loads(linea))
            except ValueError:
                pass
    return out


def tipos_de_evento(eventos, clave="type"):
    """Nombres de herramientas/eventos vistos en un JSONL real (lista corta sin repetir, para el diario de la tarea)."""
    vistos = []
    for e in eventos:
        item = e.get("item") if isinstance(e.get("item"), dict) else e
        for k in ("tool", "tool_name", clave):
            v = item.get(k)
            if isinstance(v, str) and v not in vistos and v not in ("message", "text", "step_start", "step_finish", "agent_message", "reasoning"):
                vistos.append(v)
                break
    return vistos[:50]
