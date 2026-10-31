"""Disponibilidad REAL de agentes, workflows y modelos para `result.swe` del `status` del Harness (contrato en `SWE CODE free/ARQUITECTURA.md`).

Solo lee: busca binarios, comprueba variables y, a lo sumo, importa un modulo (`importlib.find_spec`) o abre un socket / un GET /models. Nunca lanza un agente,
nunca escribe y nunca devuelve el valor de una clave: los motivos nombran la VARIABLE que falta, no su contenido. Formato por entrada:
{"disponible": bool, "motivo": str} y, en agentes que solo admiten ciertos modelos, "modelos": [ids del catalogo]."""
import json
import os
import socket
import sys
import tempfile
import time
import urllib.request
from urllib.parse import urlparse

from . import _comun
from . import openclaw as _openclaw
from .modelos import AGENTES, MODELOS, WORKFLOWS

TTL_MODELOS_S, TTL_OPENHANDS_S, TTL_FALLO_S = 600.0, 60.0, 60.0
_CACHE = {}  # ("modelos", proveedor) | ("openhands", python) -> (instante, valor | None)
_BASES = {"groq": "https://api.groq.com/openai/v1", "nvidia": "https://integrate.api.nvidia.com/v1"}
_COMPROBACION_OPENHANDS = "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('openhands.sdk') and importlib.util.find_spec('openhands.tools') else 3)"


def _ok(**extra):
    return {"disponible": True, "motivo": "", **extra}


def _no(motivo):
    return {"disponible": False, "motivo": str(motivo)[:200]}


def _url_local_o_https(u):
    try:
        x = urlparse(u)
        return bool(x.hostname and not x.username and (x.scheme == "https" or (x.scheme == "http" and x.hostname in ("127.0.0.1", "localhost", "::1"))))
    except ValueError:
        return False


# ---------------- sondas (solo lectura; sustituibles en pruebas) ----------------
def _sonda_openhands(python):
    """True si ese Python importa openhands.sdk y openhands.tools (mismo chequeo del adaptador). Con cache: lanza un `python -c` de solo importacion."""
    if not (isinstance(python, str) and os.path.isfile(python) and os.access(python, os.X_OK)):
        return False
    c = _CACHE.get(("openhands", python))
    if c and time.time() - c[0] < TTL_OPENHANDS_S:
        return c[1]
    try:
        r = _comun.ejecutar_proceso([python, "-c", _COMPROBACION_OPENHANDS], tempfile.gettempdir(), _comun.entorno_base(), timeout=20)
        valor = r["exit_code"] == 0 and not r["timeout"]
    except (OSError, TypeError):
        valor = False
    _CACHE[("openhands", python)] = (time.time(), valor)
    return valor


def _sonda_gateway(url):
    """True si hay algo escuchando en el host:puerto del Gateway OpenClaw (conexion TCP, sin enviar nada)."""
    x = urlparse(url)
    try:
        with socket.create_connection((x.hostname, x.port or (443 if x.scheme == "https" else 80)), timeout=1.0):
            return True
    except OSError:
        return False


def _sonda_modelos(proveedor, clave):
    """Ids que el proveedor lista en GET {base}/models (cache 10 min; un fallo se recuerda 60 s para no frenar cada status). Lanza OSError/ValueError si no responde."""
    c = _CACHE.get(("modelos", proveedor))
    if c and time.time() - c[0] < (TTL_MODELOS_S if c[1] is not None else TTL_FALLO_S):
        if c[1] is None:
            raise OSError("proveedor sin respuesta (cache)")
        return c[1]
    req = urllib.request.Request(_BASES[proveedor] + "/models", method="GET", headers={"Authorization": "Bearer " + clave, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:  # noqa: S310 (base fija https del proveedor)
            datos = json.loads(r.read(2_000_000).decode("utf-8", "replace"))
        ids = {m["id"] for m in datos["data"] if isinstance(m, dict) and isinstance(m.get("id"), str)}
    except (OSError, ValueError, KeyError, TypeError):
        _CACHE[("modelos", proveedor)] = (time.time(), None)
        raise OSError("GET /models fallo") from None
    _CACHE[("modelos", proveedor)] = (time.time(), ids)
    return ids


# ---------------- agentes ----------------
def _faltan(agente, binario, variable):
    return _no("%s no esta instalado (CLI `%s` ausente del PATH; define %s)" % (agente, binario, variable))


def _agente_codex(sondas):
    if not _comun.binario("codex", "RIU_CODEX_BIN"):
        return _faltan("codex", "codex", "RIU_CODEX_BIN")
    if not os.environ.get("RIU_CODEX_BASE_URL", "").strip():
        return _no("codex instalado pero falta RIU_CODEX_BASE_URL: Codex solo habla la API Responses y necesita un endpoint /responses")
    return _ok()


def _agente_opencode(sondas):
    return _ok() if _comun.binario("opencode", "RIU_OPENCODE_BIN") else _faltan("opencode", "opencode", "RIU_OPENCODE_BIN")


def _agente_swe_agent(sondas):
    if not _comun.binario("sweagent", "RIU_SWEAGENT_BIN"):
        return _faltan("swe-agent", "sweagent", "RIU_SWEAGENT_BIN")
    if not _comun.binario("docker", "RIU_DOCKER_BIN"):
        return _no("swe-agent instalado pero corre en un contenedor y falta Docker (docker en PATH o RIU_DOCKER_BIN)")
    return _ok()


def _python_openhands():
    return os.environ.get("RIU_OPENHANDS_PYTHON", "").strip() or sys.executable


def _agente_openhands(sondas):
    py = _python_openhands()
    if not (os.path.isfile(py) and os.access(py, os.X_OK)):
        return _no("openhands no esta instalado: RIU_OPENHANDS_PYTHON no es un ejecutable")
    if not sondas["openhands"](py):
        return _no("openhands no esta instalado: el Python configurado no importa openhands.sdk/openhands.tools (RIU_OPENHANDS_PYTHON)")
    return _ok()


def _agente_claude(sondas):
    if not _comun.binario("claude", "RIU_CLAUDE_BIN"):
        return _faltan("claude-code", "claude", "RIU_CLAUDE_BIN")
    url, modelo = os.environ.get("RIU_CLAUDE_PASARELA_URL", "").strip(), os.environ.get("RIU_CLAUDE_PASARELA_MODELO", "").strip()
    if not url or not modelo:
        return _no("claude-code instalado pero sin configurar: faltan RIU_CLAUDE_PASARELA_URL y/o RIU_CLAUDE_PASARELA_MODELO (pasarela Anthropic->NVIDIA)")
    if "nvidia/" + modelo not in MODELOS:
        return _no("claude-code: el modelo de la pasarela no esta en el catalogo NVIDIA de modelos.py (RIU_CLAUDE_PASARELA_MODELO)")
    return _ok(modelos=["nvidia/" + modelo])  # Claude Code solo usa el modelo NVIDIA que sirve la pasarela


def _agente_openclaw(sondas):
    if not os.environ.get("OPENCLAW_GATEWAY_TOKEN", "").strip():
        return _no("openclaw sin configurar: falta OPENCLAW_GATEWAY_TOKEN en el entorno del Harness")
    url = _openclaw._url()
    if not url:
        return _no("RIU_OPENCLAW_URL invalida: debe ser https o http en loopback")
    if not sondas["gateway"](url):
        return _no("el Gateway OpenClaw no responde en la URL configurada (RIU_OPENCLAW_URL, por defecto 127.0.0.1:18789)")
    return _ok()


_AGENTES = {"codex": _agente_codex, "opencode": _agente_opencode, "swe-agent": _agente_swe_agent, "openhands": _agente_openhands,
            "claude-code": _agente_claude, "openclaw": _agente_openclaw}


# ---------------- modelos ----------------
def _hf_configurado():
    return any(os.environ.get("SWECODE_URL_S%d" % n, "").strip() for n in (1, 2, 3))


def _modelos(sonda):
    out, listas = {}, {}
    for mid, cfg in MODELOS.items():
        prov = cfg["provider"]
        if prov == "hf":
            out[mid] = _ok() if _hf_configurado() else _no("falta SWECODE_URL_S1..S3: ningun servidor HF configurado en el entorno del Harness")
            continue
        clave = _comun._clave(prov.upper() + "_API_KEY")
        if not clave:
            out[mid] = _no("falta %s_API_KEY (o *_1..20) en el entorno del Harness" % prov.upper())
            continue
        if sonda is None:
            out[mid] = _ok()
            continue
        if prov not in listas:
            try:
                listas[prov] = set(sonda(prov, clave))
            except Exception as exc:  # noqa: BLE001 - proveedor caido o clave rechazada: no se inventa ni se descarta
                listas[prov] = type(exc).__name__
        if isinstance(listas[prov], str):
            out[mid] = _ok(motivo="sin verificar GET /models (%s)" % listas[prov])
        else:
            out[mid] = _ok() if cfg["model"] in listas[prov] else _no("%s no figura en GET /models de %s" % (cfg["model"], prov))
    return out


# ---------------- workflows ----------------
def _workflow_swe_code(agentes):
    faltan = [a for a in ("codex", "opencode", "openhands") if not agentes[a]["disponible"]]
    motivos = (["faltan agentes conectados: " + ", ".join(faltan)] if faltan else []) + ([] if _hf_configurado() else ["falta SWECODE_URL_S1..S3 para los modelos HF de los pasos"])
    return _no("; ".join(motivos)) if motivos else _ok()


def _workflow_liquid_mirror(agentes):
    urls = {s: os.environ.get("SWECODE_URL_" + s, "").strip().rstrip("/") for s in ("S2", "S3")}
    if not urls["S2"] or not urls["S3"]:
        return _no("falta SWECODE_URL_S2 y/o SWECODE_URL_S3: Liquid Mirror usa un servidor distinto para cada participante")
    if not all(_url_local_o_https(u) for u in urls.values()):
        return _no("SWECODE_URL_S2/S3 invalidas: https o http en loopback")
    if urls["S2"] == urls["S3"]:
        return _no("S2 y S3 no son independientes: SWECODE_URL_S2 y SWECODE_URL_S3 apuntan al mismo servidor")
    if not agentes["openhands"]["disponible"]:
        return _no("falta el agente verificador openhands (Liquid Mirror lo usa para verificar)")
    return _ok()


def capacidades(sonda_openhands=None, sonda_gateway=None, sonda_modelos=None):
    """{"agentes": {...}, "workflows": {...}, "modelos": {...}} con la disponibilidad real en este entorno. Solo lectura."""
    sondas = {"openhands": sonda_openhands or _sonda_openhands, "gateway": sonda_gateway or _sonda_gateway}
    if sonda_modelos is None and os.environ.get("RIU_SWE_SONDA_MODELOS", "1").strip() != "0":
        sonda_modelos = _sonda_modelos
    agentes = {}
    for a in AGENTES:
        try:
            agentes[a] = _AGENTES[a](sondas)
        except Exception as exc:  # noqa: BLE001 - una comprobacion rota no tumba el status del Harness
            agentes[a] = _no("no se pudo comprobar (%s)" % type(exc).__name__)
    comprobar = {"individual": lambda: _ok(), "swe_code": lambda: _workflow_swe_code(agentes), "liquid_mirror": lambda: _workflow_liquid_mirror(agentes)}
    workflows = {}
    for w in WORKFLOWS:
        try:
            workflows[w] = comprobar[w]()
        except Exception as exc:  # noqa: BLE001
            workflows[w] = _no("no se pudo comprobar (%s)" % type(exc).__name__)
    return {"agentes": agentes, "workflows": workflows, "modelos": _modelos(sonda_modelos)}
