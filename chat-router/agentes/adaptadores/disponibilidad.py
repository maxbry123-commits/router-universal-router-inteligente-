"""Disponibilidad REAL de agentes, workflows y modelos para `result.swe` del `status` del Harness (contrato en `SWE CODE free/ARQUITECTURA.md`).

R6: cada entrada declara UNO de seis estados (DISPONIBLE, NO INSTALADO, NO CONFIGURADO, NO COMPATIBLE, NO DISPONIBLE EN PROVEEDOR, SIN VERIFICAR) y su veredicto de tres valores
(DISPONIBLE / NO DISPONIBLE / SIN VERIFICAR). Un fallo de la comprobacion (proveedor caido, sonda rota, timeout) es SIN VERIFICAR, nunca DISPONIBLE ni NO INSTALADO.
Solo lee: busca binarios, comprueba variables y, a lo sumo, importa un modulo (`importlib.find_spec`) o abre un socket / un GET /models. Nunca lanza un agente,
nunca escribe y nunca devuelve el valor de una clave: los motivos nombran la VARIABLE que falta, no su contenido. Formato por entrada:
{"disponible": bool, "motivo": str} (contrato antiguo, intacto) mas los campos nuevos: "estado" (los seis), "veredicto" (los tres), "verificado" (bool), "causa" (codigo estable),
"intentable" (bool: se puede intentar y mostrar el estado real; los modelos SIN VERIFICAR si, los agentes no) y, en agentes que solo admiten ciertos modelos, "modelos": [ids del catalogo];
en modelos ademas "nombre", "proveedor" y, si hay, "nota" (todos del catalogo unico modelos.py)."""
import hashlib
import json
import os
import socket
import sys
import tempfile
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse

from . import _comun
from . import openclaw as _openclaw
from .modelos import AGENTES, MODELOS, NOMBRES, NOTAS, WORKFLOWS

ESTADOS = ("DISPONIBLE", "NO INSTALADO", "NO CONFIGURADO", "NO COMPATIBLE", "NO DISPONIBLE EN PROVEEDOR", "SIN VERIFICAR")
_GRAVEDAD = ("NO INSTALADO", "NO CONFIGURADO", "NO COMPATIBLE", "NO DISPONIBLE EN PROVEEDOR", "SIN VERIFICAR")  # un workflow hereda el bloqueo definitivo antes que el no comprobado


class ProveedorRechazo(OSError):
    """El proveedor contesto 401/403 a GET /models: la clave no sirvio (no se sabe nada del modelo)."""
    def __init__(self, codigo):
        super().__init__("HTTP %s" % codigo); self.codigo = codigo

TTL_MODELOS_S, TTL_OPENHANDS_S, TTL_FALLO_S = 600.0, 60.0, 60.0
_CACHE = {}  # ("modelos", proveedor) | ("openhands", python) -> (instante, valor | None)
_BASES = {"groq": "https://api.groq.com/openai/v1", "nvidia": "https://integrate.api.nvidia.com/v1"}
_COMPROBACION_OPENHANDS = ("import importlib.util, sys\n"
                           "try:\n    ok = importlib.util.find_spec('openhands.sdk') and importlib.util.find_spec('openhands.tools')\n"
                           "except ImportError:\n    ok = None  # sin el paquete 'openhands' find_spec lanza ModuleNotFoundError: es ausencia, no fallo\n"
                           "sys.exit(0 if ok else 3)")


def _entrada(estado, motivo="", causa="", intentable=None, **extra):
    """Forma unica de toda entrada. `disponible` (bool) solo es True si el estado es DISPONIBLE: desconocido jamas se presenta como verificado."""
    return {"disponible": estado == "DISPONIBLE", "motivo": str(motivo)[:200], "estado": estado,
            "veredicto": "DISPONIBLE" if estado == "DISPONIBLE" else "SIN VERIFICAR" if estado == "SIN VERIFICAR" else "NO DISPONIBLE",
            "verificado": estado != "SIN VERIFICAR", "causa": causa, "intentable": estado == "DISPONIBLE" if intentable is None else intentable, **extra}


def _ok(**extra):
    return _entrada("DISPONIBLE", **extra)


def _no(motivo, estado="NO CONFIGURADO", causa="", intentable=None):
    return _entrada(estado, motivo, causa, intentable)


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
        # True: importa el SDK; False: el Python corrio y NO lo tiene (salida 3); None: la comprobacion fallo (timeout, crash, no se pudo lanzar) = SIN VERIFICAR
        valor = None if r["timeout"] else True if r["exit_code"] == 0 else False if r["exit_code"] == 3 else None
    except (OSError, TypeError):
        valor = None
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


def _sonda_hf(url):
    """True si el servidor HF configurado acepta una conexion TCP (sin enviar nada; un Space dormido tarda en arrancar y NO se declara ausente). Cache 60 s."""
    c = _CACHE.get(("hf", url))
    if c and time.time() - c[0] < TTL_FALLO_S:
        return c[1]
    valor = _sonda_gateway(url)
    _CACHE[("hf", url)] = (time.time(), valor)
    return valor


def _sonda_modelos(proveedor, clave):
    """Ids que el proveedor lista en GET {base}/models (cache 10 min; un fallo se recuerda 60 s para no frenar cada status). Lanza OSError/ValueError si no responde."""
    # No compartir resultados de una clave con otra: pueden tener permisos/modelos distintos.
    # Solo se almacena la huella irreversible, nunca el token.
    cache_key = ("modelos", proveedor, hashlib.sha256(clave.encode("utf-8")).hexdigest())
    c = _CACHE.get(cache_key)
    if c and time.time() - c[0] < (TTL_MODELOS_S if isinstance(c[1], set) else TTL_FALLO_S):
        if isinstance(c[1], tuple) and c[1][0] == "rechazo":
            raise ProveedorRechazo(c[1][1])
        if c[1] is None:
            raise OSError("proveedor sin respuesta (cache)")
        return c[1]
    req = urllib.request.Request(_BASES[proveedor] + "/models", method="GET", headers={"Authorization": "Bearer " + clave, "Accept": "application/json"})
    try:
        with _comun.abrir(req, timeout=5) as r:  # URL fija https y redirecciones prohibidas: la clave NO se reenvia a otro host
            datos = json.loads(r.read(2_000_000).decode("utf-8", "replace"))
        ids = {m["id"] for m in datos["data"] if isinstance(m, dict) and isinstance(m.get("id"), str)}
    except urllib.error.HTTPError as exc:
        _CACHE[cache_key] = (time.time(), ("rechazo", exc.code) if exc.code in (401, 403) else None)
        if exc.code in (401, 403):
            raise ProveedorRechazo(exc.code) from None
        raise OSError("GET /models fallo") from None
    except (OSError, ValueError, KeyError, TypeError):
        _CACHE[cache_key] = (time.time(), None)
        raise OSError("GET /models fallo") from None
    _CACHE[cache_key] = (time.time(), ids)
    return ids


# ---------------- agentes ----------------
def _faltan(agente, binario, variable):
    return _no("%s no esta instalado (CLI `%s` ausente del PATH; define %s)" % (agente, binario, variable), "NO INSTALADO", "binario_ausente")


def _agente_codex(sondas):
    if not _comun.binario("codex", "RIU_CODEX_BIN"):
        return _faltan("codex", "codex", "RIU_CODEX_BIN")
    if not os.environ.get("RIU_CODEX_BASE_URL", "").strip():
        # El bridge existente ya implementa POST /v1/responses. Codex lo usa
        # por _comun.endpoint_modelo, sin un servidor ni variables nuevos.
        if not (os.environ.get("RIU_API_KEY", "").strip() or os.environ.get("BRIDGE_TOKEN", "").strip()
                or os.environ.get("RIU_AGENTES_LLM_API_KEY", "").strip()):
            return _no("codex instalado pero falta RIU_CODEX_BASE_URL o credencial del bridge SWE CODE (RIU_API_KEY)", "NO CONFIGURADO", "falta_RIU_CODEX_BASE_URL")
        url = (os.environ.get("RIU_SWE_BRIDGE_URL") or "http://127.0.0.1:7870").strip()
        if not sondas["gateway"](url):
            return _no("codex instalado: bridge /v1/responses sin respuesta; no se certifica ejecucion", "SIN VERIFICAR", "bridge_sin_respuesta")
    return _ok()


def _agente_opencode(sondas):
    return _ok() if _comun.binario("opencode", "RIU_OPENCODE_BIN") else _faltan("opencode", "opencode", "RIU_OPENCODE_BIN")


def _agente_swe_agent(sondas):
    if not _comun.binario("sweagent", "RIU_SWEAGENT_BIN"):
        return _faltan("swe-agent", "sweagent", "RIU_SWEAGENT_BIN")
    if not _comun.binario("docker", "RIU_DOCKER_BIN"):
        return _no("swe-agent instalado pero corre en un contenedor y falta Docker (docker en PATH o RIU_DOCKER_BIN)", "NO CONFIGURADO", "falta_docker")
    return _ok()


def _python_openhands():
    return _comun.python_openhands()


def _agente_openhands(sondas):
    py = _python_openhands()
    if not (os.path.isfile(py) and os.access(py, os.X_OK)):
        return _no("openhands no esta instalado: RIU_OPENHANDS_PYTHON no es un ejecutable", "NO INSTALADO", "python_no_ejecutable")
    visto = sondas["openhands"](py)
    if visto is None:  # la comprobacion fallo: no se afirma que falte
        return _no("openhands sin verificar: no se pudo ejecutar la comprobacion de importacion (RIU_OPENHANDS_PYTHON)", "SIN VERIFICAR", "comprobacion_fallida")
    if not visto:
        return _no("openhands no esta instalado: el Python configurado no importa openhands.sdk/openhands.tools (RIU_OPENHANDS_PYTHON)", "NO INSTALADO", "sdk_ausente")
    return _ok()


def _agente_claude(sondas):
    if not _comun.binario("claude", "RIU_CLAUDE_BIN"):
        return _faltan("claude-code", "claude", "RIU_CLAUDE_BIN")
    url, modelo = os.environ.get("RIU_CLAUDE_PASARELA_URL", "").strip(), os.environ.get("RIU_CLAUDE_PASARELA_MODELO", "").strip()
    if not url or not modelo:
        return _no("claude-code instalado pero sin configurar: faltan RIU_CLAUDE_PASARELA_URL y/o RIU_CLAUDE_PASARELA_MODELO (pasarela Anthropic->NVIDIA)", "NO CONFIGURADO", "falta_pasarela")
    if "nvidia/" + modelo not in MODELOS:
        return _no("claude-code: el modelo de la pasarela no esta en el catalogo NVIDIA de modelos.py (RIU_CLAUDE_PASARELA_MODELO)", "NO COMPATIBLE", "modelo_fuera_del_catalogo")
    return _ok(modelos=["nvidia/" + modelo])  # Claude Code solo usa el modelo NVIDIA que sirve la pasarela


def _agente_openclaw(sondas):
    if not os.environ.get("OPENCLAW_GATEWAY_TOKEN", "").strip():
        return _no("openclaw sin configurar: falta OPENCLAW_GATEWAY_TOKEN en el entorno del Harness", "NO CONFIGURADO", "falta_token_gateway")
    url = _openclaw._url()
    if not url:
        return _no("RIU_OPENCLAW_URL invalida: debe ser https o http en loopback", "NO CONFIGURADO", "url_invalida")
    if not sondas["gateway"](url):
        return _no("el Gateway OpenClaw no responde en la URL configurada (RIU_OPENCLAW_URL, por defecto 127.0.0.1:18789); sin verificar", "SIN VERIFICAR", "gateway_sin_respuesta")
    return _ok()


_AGENTES = {"codex": _agente_codex, "opencode": _agente_opencode, "swe-agent": _agente_swe_agent, "openhands": _agente_openhands,
            "claude-code": _agente_claude, "openclaw": _agente_openclaw}


# ---------------- modelos ----------------
def _hf_urls():
    return [u for u in (_comun.url_swecode("S%d" % n) for n in (1, 2, 3)) if u]  # sin variable: URLs publicas por defecto (_comun.SWECODE_URLS_PUBLICAS)


def _hf_configurado():
    return bool(_hf_urls())


def _modelo_hf(sonda_hf, activa):
    urls = _hf_urls()
    if not urls:
        return _no("falta SWECODE_URL_S1..S3: ningun servidor HF configurado en el entorno del Harness", "NO CONFIGURADO", "falta_SWECODE_URL")
    if not activa or sonda_hf is None:
        return _no("servidor HF configurado pero sin verificar (comprobacion desactivada)", "SIN VERIFICAR", "verificacion_desactivada", intentable=True)
    if any(sonda_hf(u) for u in urls):
        # TCP abierto no demuestra que ninguno de los cuatro modelos esté cargado o que pueda inferir.
        return _no("servidor HF alcanzable, pero el modelo especifico no tiene inferencia comprobada", "SIN VERIFICAR",
                   "modelo_hf_no_verificado", intentable=True)
    return _no("ningun servidor HF (SWECODE_URL_S1..S3) responde ahora; un Space dormido tarda en arrancar: sin verificar", "SIN VERIFICAR", "servidor_hf_sin_respuesta", intentable=True)



def _modelos_bridge():
    """Lee una vez el GET /models del bridge existente (banco cifrado compartido).
    Nunca pide tokens, no copia claves y nunca certifica inferencia por un catalogo.
    """
    key = _comun._credencial_bridge()
    if key == "no-requerida":
        return None
    cache_key = ("modelos_bridge",)
    cached = _CACHE.get(cache_key)
    if cached and time.time() - cached[0] < 45:
        return cached[1]
    from urllib.parse import urlparse
    base = (os.environ.get("RIU_SWE_BRIDGE_URL") or "http://127.0.0.1:7870").strip().rstrip("/")
    if base.endswith("/v1"):
        base = base[:-3]
    try:
        x = urlparse(base)
        if not (x.scheme == "https" or x.scheme == "http" and x.hostname in ("127.0.0.1", "localhost")) or x.username or x.password:
            return None
        req = urllib.request.Request(base + "/v1/modelos/disponibilidad",
                                     headers={"X-API-Key": key, "Accept": "application/json"})
        with _comun.abrir(req, 5) as resp:
            doc = json.load(resp)
        modelos = doc.get("modelos")
        listado = {m["id"]: m for m in modelos if isinstance(m, dict) and isinstance(m.get("id"), str)} if doc.get("ok") is True and isinstance(modelos, list) else None
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        listado = None
    _CACHE[cache_key] = (time.time(), listado)
    return listado


def _modelos(sonda, sonda_hf=None):
    out, listas, hf = {}, {}, None
    for mid, cfg in MODELOS.items():
        prov = cfg["provider"]
        if prov == "hf":
            hf = hf or _modelo_hf(sonda_hf, sonda is not None)  # una sola comprobacion para los cuatro modelos locales
            e = dict(hf)
        elif prov == "web":
            # Una cuenta WEB no tiene GET /models tipo API. La sesion se valida
            # al enviar la tarea; nunca fingir disponibilidad por catalogo estatico.
            e = _no("Modelo web registrado; sesión de suscripción sin verificar. Se comprueba al ejecutar.",
                    "SIN VERIFICAR", "web_sesion_pendiente", intentable=True)
        else:
            clave = _comun._clave(prov.upper() + "_API_KEY")
            if not clave:
                # El bridge ya dispone de las claves del banco cifrado.
                # Consultarlo en loopback evita declarar NO CONFIGURADO algo
                # que el proveedor SI publica a traves del mismo Router.
                if _comun._credencial_bridge() != "no-requerida":
                    if "_bridge" not in listas:
                        listas["_bridge"] = _modelos_bridge()
                    b = (listas["_bridge"] or {}).get(mid)
                    if b and b.get("disponible") is True:
                        e = _ok()
                    elif b and b.get("disponible") is False:
                        e = _no("el bridge no encuentra este modelo en GET /models del proveedor", "NO DISPONIBLE EN PROVEEDOR", "ausente_en_get_models")
                    else:
                        e = _no("banco de claves accesible por bridge; proveedor sin verificar para este modelo", "SIN VERIFICAR", "bridge_sin_verificar", intentable=True)
                else:
                    e = _no("falta %s_API_KEY (o *_1..20) en el entorno del Harness y acceso al bridge" % prov.upper(), "NO CONFIGURADO", "sin_clave")
            elif sonda is None:  # una clave existente NO prueba que el modelo exista (38)
                e = _no("clave presente pero sin verificar GET /models (comprobacion desactivada)", "SIN VERIFICAR", "verificacion_desactivada", intentable=True)
            else:
                if prov not in listas:
                    try:
                        listas[prov] = set(sonda(prov, clave))
                    except ProveedorRechazo as exc:  # 401/403: la clave no sirvio; del modelo no se sabe nada
                        listas[prov] = ("clave_rechazada", "sin verificar GET /models: el proveedor rechazo la clave (HTTP %s)" % exc.codigo)
                    except Exception as exc:  # noqa: BLE001 - proveedor caido o respuesta ilegible: ni se inventa ni se descarta
                        listas[prov] = ("get_models_fallo", "sin verificar GET /models (%s)" % type(exc).__name__)
                if isinstance(listas[prov], tuple):
                    e = _no(listas[prov][1], "SIN VERIFICAR", listas[prov][0], intentable=True)
                elif cfg["model"] in listas[prov]:
                    e = _ok()
                else:
                    e = _no("%s no figura en GET /models de %s" % (cfg["model"], prov), "NO DISPONIBLE EN PROVEEDOR", "ausente_en_get_models")
        e["nombre"], e["proveedor"] = NOMBRES.get(mid, mid), prov
        if NOTAS.get(mid):
            e["nota"] = NOTAS[mid]
        out[mid] = e
    return out


# ---------------- workflows ----------------
def _peor(*entradas):
    """Estado del bloqueo mas grave entre las dependencias no disponibles (definitivo antes que no comprobado)."""
    ests = {e["estado"] for e in entradas}
    return next((g for g in _GRAVEDAD if g in ests), "SIN VERIFICAR")


def _workflow_swe_code(agentes):
    faltan = [a for a in ("codex", "opencode", "openhands") if not agentes[a]["disponible"]]
    motivos = (["faltan agentes conectados: " + ", ".join(faltan)] if faltan else []) + ([] if _hf_configurado() else ["falta SWECODE_URL_S1..S3 para los modelos HF de los pasos"])
    if not motivos:
        return _ok()
    bloqueos = [agentes[a] for a in faltan] + ([] if _hf_configurado() else [_no("", "NO CONFIGURADO")])
    return _no("; ".join(motivos), _peor(*bloqueos), "dependencias")


def _workflow_liquid_mirror(agentes):
    urls = {s: _comun.url_swecode(s).rstrip("/") for s in ("S2", "S3")}
    if not urls["S2"] or not urls["S3"]:
        return _no("falta SWECODE_URL_S2 y/o SWECODE_URL_S3: Liquid Mirror usa un servidor distinto para cada participante", "NO CONFIGURADO", "falta_S2_S3")
    if not all(_url_local_o_https(u) for u in urls.values()):
        return _no("SWECODE_URL_S2/S3 invalidas: https o http en loopback", "NO CONFIGURADO", "url_invalida")
    if urls["S2"] == urls["S3"]:
        return _no("S2 y S3 no son independientes: SWECODE_URL_S2 y SWECODE_URL_S3 apuntan al mismo servidor", "NO CONFIGURADO", "s2_igual_s3")
    if not agentes["openhands"]["disponible"]:
        return _no("falta el agente verificador openhands (Liquid Mirror lo usa para verificar)", _peor(agentes["openhands"]), "dependencias")
    return _ok()


def capacidades(sonda_openhands=None, sonda_gateway=None, sonda_modelos=None, sonda_hf=None):
    """{"agentes": {...}, "workflows": {...}, "modelos": {...}} con la disponibilidad real en este entorno. Solo lectura."""
    sondas = {"openhands": sonda_openhands or _sonda_openhands, "gateway": sonda_gateway or _sonda_gateway}
    if sonda_modelos is None and os.environ.get("RIU_SWE_SONDA_MODELOS", "1").strip() != "0":
        sonda_modelos = _sonda_modelos
        sonda_hf = sonda_hf or _sonda_hf
    agentes = {}
    for a in AGENTES:
        try:
            agentes[a] = _AGENTES[a](sondas)
        except Exception as exc:  # noqa: BLE001 - una comprobacion rota no tumba el status del Harness ni se confunde con "no instalado"
            agentes[a] = _no("sin verificar: no se pudo comprobar (%s)" % type(exc).__name__, "SIN VERIFICAR", "comprobacion_fallida")
    comprobar = {"individual": lambda: _ok(), "swe_code": lambda: _workflow_swe_code(agentes), "liquid_mirror": lambda: _workflow_liquid_mirror(agentes)}
    workflows = {}
    for w in WORKFLOWS:
        try:
            workflows[w] = comprobar[w]()
        except Exception as exc:  # noqa: BLE001
            workflows[w] = _no("sin verificar: no se pudo comprobar (%s)" % type(exc).__name__, "SIN VERIFICAR", "comprobacion_fallida")
    return {"agentes": agentes, "workflows": workflows, "modelos": _modelos(sonda_modelos, sonda_hf)}
