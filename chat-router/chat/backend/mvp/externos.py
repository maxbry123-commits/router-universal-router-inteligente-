"""Modelos de Groq y NVIDIA (APIs compatibles OpenAI) para el chat: id «groq/<modelo>» o «nvidia/<modelo>».
La clave sale del banco (GROQ_API_KEY / NVIDIA_API_KEY) o de las variables del Space (GROQ_API_KEY_2..7, NVIDIA_API_KEY_1..9)."""
import hashlib
import json
import logging
import os
import pathlib
import random
import re
import threading
import time
from email.utils import parsedate_to_datetime
from urllib import error, request
from mvp import compute
try:
    import httpx as _httpx  # conexiones persistentes (keep-alive) y lectura incremental; sin httpx se usa urllib (una conexion por llamada)
except ImportError:  # pragma: no cover - depende del entorno
    _httpx = None

PROVEEDORES = {
    "groq": {"label": "Groq", "base": "https://api.groq.com/openai/v1", "var": "GROQ_API_KEY"},
    "nvidia": {"label": "NVIDIA", "base": "https://integrate.api.nvidia.com/v1", "var": "NVIDIA_API_KEY"},
    "deepseek": {"label": "DeepSeek", "base": "https://api.deepseek.com", "var": "DEEPSEEK_API_KEY"},
    "minimax": {"label": "MiniMax", "base": "https://api.minimax.io/v1", "var": "MINIMAX_API_KEY"},
    "openai": {"label": "OpenAI", "base": "https://api.openai.com/v1", "var": "OPENAI_API_KEY"},
}
NO_CHAT = ("whisper", "tts", "guard", "embed", "rerank", "vision-", "distil-whisper", "playai", "orpheus", "parse", "clip", "nv-embed", "reward")
# Modelos elegidos por el Director para el chat YAIWES. El id completo lleva el proveedor delante («groq/…», «nvidia/…»); `env` es solo el NOMBRE de la variable con la clave.
_P = lambda nombre, prov, **kw: {"nombre": nombre, "proveedor": prov, "base_url": PROVEEDORES[prov]["base"], "env": PROVEEDORES[prov]["var"], **kw}
PROVEEDORES_NUEVOS = {
    "groq/qwen/qwen3.8-27b": _P("Qwen 3.8 27B", "groq", temperature=1.0, top_p=0.95, max_tokens=2048, reasoning_effort="medium", reasoning_format="hidden"),
    "nvidia/minimaxai/minimax-m3.1-flash": _P("MiniMax M3.1 Flash", "nvidia", temperature=1.0, top_p=0.95, max_tokens=4096),
    "nvidia/meta/muse-glimmer-30b": _P("Muse Glimmer 30B", "nvidia", temperature=1.0, top_p=0.95, max_tokens=4096),
    "nvidia/nvidia/nemotron-3-ultra-550b-a55b": _P("Nemotron 3 Ultra 550B", "nvidia", temperature=1.0, top_p=0.95, max_tokens=4096),
    "nvidia/z-ai/glm-5.3": _P("GLM 5.3", "nvidia", temperature=0.5, top_p=1.0, max_tokens=4096),
    "nvidia/z-ai/glm-5.3-flash": _P("GLM 5.3 Flash", "nvidia", temperature=0.5, top_p=1.0, max_tokens=4096),
    "deepseek/deepseek-v4-pro": _P("DeepSeek V4 Pro", "deepseek"),
    "deepseek/deepseek-flash": _P("DeepSeek Flash", "deepseek"),
    "minimax/MiniMax-M3": _P("MiniMax M3", "minimax"),
    "minimax/MiniMax-M2.7": _P("MiniMax M2.7", "minimax"),
    "openai/gpt-5.6": _P("OpenAI GPT-5.6", "openai"),
    "openai/gpt-5.5": _P("OpenAI GPT-5.5", "openai"),
}
PARAMETROS_MODELO = {mid: {k: v for k, v in cfg.items() if k in ("temperature", "top_p", "max_tokens", "reasoning_effort", "reasoning_format")} for mid, cfg in PROVEEDORES_NUEVOS.items()}
_PARAMS = ("temperature", "top_p", "max_tokens", "reasoning_effort", "reasoning_format")
# Limites REALES por proveedor/modelo (se aplican a los valores explicitos del llamador; el recorte se informa, nunca es silencioso).
# Fuente OFICIAL (Firecrawl, 2026-11-01): console.groq.com/docs/models y console.groq.com/docs/model/qwen/qwen3.8-27b -> qwen/qwen3.8-27b: contexto 131,072, MAX COMPLETION/OUTPUT TOKENS 16,384,
# reasoning_effort in {default, none, low, medium, high}, reasoning_format in {hidden, parsed}. NVIDIA (build.nvidia.com/<org>/<modelo>) solo publica max_tokens en ejemplos (8192/16384), no un tope: sin tope local, el 400 del proveedor se trata como peticion invalida.
LIMITES_MODELO = {"groq/qwen/qwen3.8-27b": {"max_tokens": 16384, "reasoning_effort": ("default", "none", "low", "medium", "high"), "reasoning_format": ("hidden", "parsed")}}
_OPCIONES_EXT = compute.OPCIONES | {"reasoning_format"}  # Groq/NVIDIA admiten ademas reasoning_format (el cliente Qwen de compute.py no cambia)
_PASAN = ("tools", "tool_choice", "parallel_tool_calls", "response_format")  # contrato de herramientas: el llamador manda tal cual
CACHE = {}  # proveedor -> (instante, lista de ids)
_SWE = {}  # (ruta, mtime_ns, tamano, clave de acceso) -> banco compartido abierto (o None si no se pudo abrir); evita repetir PBKDF2


def _ruta_banco_swe():
    """Ruta común con boot.sh: el bridge corre con BRIDGE_STATE_DIR=/tmp/state.
    Esa variable se define solo en el proceso Node, NO en el proceso Python.
    La ruta anterior bajo web-bridge/state no correspondía al banco persistido.
    """
    return os.environ.get("RIU_BANCO_SWE") or os.path.join(
        os.environ.get("BRIDGE_STATE_DIR") or "/tmp/state", "banco-swe.bin")


def _banco_compartido():
    """Solo LECTURA del banco cifrado que usa el Router SWE CODE: sin duplicar secretos."""
    try:
        from mvp import bank
        ruta = _ruta_banco_swe()
        accesos = tuple(dict.fromkeys(os.environ[v] for v in bank.ACCESO if os.environ.get(v)))  # el banco puede estar cifrado con cualquiera de las variables de acceso
        if not accesos or not os.path.isfile(ruta):  # no existe: no se abre (abrir() crearia el archivo)
            return None
        st = os.stat(ruta)
        llave = (ruta, st.st_mtime_ns, st.st_size, accesos)
        if llave not in _SWE:
            _SWE.clear()
            _SWE[llave] = None
            for acceso in accesos:
                try:
                    _SWE[llave] = bank.abrir(ruta, acceso)
                    break
                except Exception:
                    continue
        return _SWE[llave]
    except Exception:
        return None


def proveedor(modelo):
    p = str(modelo or "").split("/", 1)[0]
    return p if p in PROVEEDORES and "/" in str(modelo) and str(modelo).split("/", 1)[1] else None


def claves(prov, banco=None):
    """Todas las claves del proveedor, en orden: banco (GROQ_API_KEY, GROQ_API_KEY_1..n) y luego el entorno; al final el banco compartido del web-bridge; sin repetir."""
    var, out = PROVEEDORES[prov]["var"], []
    nombres = [var] + [var + "_" + str(i) for i in range(1, 21)]
    for n in nombres:
        for v in ((banco.leer(n) if banco else None), os.environ.get(n)):
            if v and v not in out:
                out.append(v)
    swe = _banco_compartido()  # al final: las claves que el usuario pego en el chat del web-bridge
    for n in nombres if swe else ():
        v = swe.leer(n)
        if v and v not in out:
            out.append(v)
    return out


def clave(prov, banco=None):
    c = claves(prov, banco)
    return c[0] if c else None


def _get(url, k):
    req = request.Request(url, headers={"Authorization": "Bearer " + k, "User-Agent": "riu-router"})
    with request.urlopen(req, timeout=20) as r:
        return json.load(r)


def modelos(prov, banco=None):
    """Ids de chat que publica el proveedor (GET /models), con caché de 10 minutos."""
    if prov in CACHE and time.time() - CACHE[prov][0] < 600:
        return CACHE[prov][1]
    pool, datos, ultimo = claves(prov, banco), None, None
    if not pool:
        raise RuntimeError(PROVEEDORES[prov]["label"] + " sin clave (" + PROVEEDORES[prov]["var"] + ")")
    for k in pool:  # la primera clave que el proveedor acepte
        try:
            datos = _get(PROVEEDORES[prov]["base"] + "/models", k); break
        except OSError as exc:
            ultimo = exc
    if datos is None:
        raise RuntimeError(PROVEEDORES[prov]["label"] + ": ninguna de las %d claves fue aceptada (%s)" % (len(pool), str(ultimo)[:80]))
    ids = sorted(m["id"] for m in datos.get("data", []) if not any(x in m["id"].lower() for x in NO_CHAT))
    CACHE[prov] = (time.time(), [prov + "/" + i for i in ids])
    return CACHE[prov][1]


# ---------- politicas por modelo (router-mvp/fichas/fichas_qwen/fichas/politicas_modelo.json -> «politicas_externos») ----------
POLITICA_DEFECTO = {
    "streaming": {"activable": True, "con_tools": True, "stream_options_usage": True},
    "reintentos": {"max": 3, "base_s": 0.5, "tope_s": 30.0, "retry_after_max_s": 60.0, "rotar_clave_en_429": True, "presupuesto_s": compute.PRESUPUESTO_TOTAL_S},
    "timeout_s": compute.TIMEOUT_DEFECTO_S,
    "parametros_compatibles": None,  # None: sin filtro
    "contexto": {"max_caracteres": 400_000, "resultado_tool_max": 4000, "recientes": 6},
}
_POL = {}  # (ruta, mtime_ns) -> politicas_externos del archivo


def _fusion(base, extra):
    out = dict(base)
    for k, v in (extra or {}).items():
        out[k] = _fusion(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def _ruta_politicas():
    if os.environ.get("RIU_POLITICAS_MODELO"):
        return os.environ["RIU_POLITICAS_MODELO"]
    aqui = pathlib.Path(__file__).resolve()
    for cand in ((aqui.parents[4] / "router-mvp/fichas/fichas_qwen/fichas/politicas_modelo.json") if len(aqui.parents) > 4 else None, aqui.parent / "politicas_modelo.json"):
        if cand and cand.is_file():
            return str(cand)
    return None


def politica(modelo):
    """Politica efectiva del modelo: valores por defecto <- «_defecto» del JSON <- entrada del modelo. Sin archivo, los valores por defecto."""
    fuente = {}
    try:
        ruta = _ruta_politicas()
        llave = (ruta, os.stat(ruta).st_mtime_ns)
        if llave not in _POL:
            _POL.clear()
            with open(ruta, encoding="utf-8") as f:
                _POL[llave] = (json.load(f).get("politicas_externos") or {})
        fuente = _POL[llave]
    except (OSError, TypeError, ValueError, AttributeError):
        pass
    return _fusion(_fusion(POLITICA_DEFECTO, fuente.get("_defecto")), fuente.get(modelo))


def disponible(modelo):
    """True/False según el GET /models en caché (10 min); None si aún no se conoce (no se adivina)."""
    c = CACHE.get(proveedor(modelo))
    return None if not c or time.time() - c[0] >= 600 else modelo in c[1]


def _numero(v, bajo, alto, abierto_bajo=False):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and (bajo < v if abierto_bajo else bajo <= v) and v <= alto


def parametros(modelo, opciones, pol=None):
    """Parametros de inferencia: PRIMERO los valores por defecto del modelo y DESPUES los explicitos validos del llamador (R7).
    Un explicito invalido o que el modelo no admite se ignora (queda el del modelo) y se lista en `ignorados`; max_tokens y demas se recortan al limite real y se informa en `recortados`.
    Devuelve (payload_parcial, info)."""
    pol = pol if pol is not None else politica(modelo)
    comp, lim = pol.get("parametros_compatibles"), LIMITES_MODELO.get(modelo, {})
    out, info = dict(PARAMETROS_MODELO.get(modelo, {})), {"ignorados": [], "recortados": {}}
    for n, v in (opciones or {}).items():
        if n not in _OPCIONES_EXT or n == "enable_thinking":
            if n == "enable_thinking": info["ignorados"].append(n)  # solo Qwen/DashScope; Groq y NVIDIA lo usan por otro camino
            continue
        if n in _PASAN:
            out[n] = v; continue
        if comp is not None and n not in comp:
            info["ignorados"].append(n); continue
        if n == "temperature": bien = _numero(v, 0, 2)
        elif n == "top_p": bien = _numero(v, 0, 1, True)
        elif n == "max_tokens": bien = isinstance(v, int) and not isinstance(v, bool) and v > 0
        else: bien = isinstance(v, str) and (n not in lim or v in lim[n])
        if not bien:
            info["ignorados"].append(n); continue
        if n == "max_tokens" and lim.get("max_tokens") and v > lim["max_tokens"]:
            info["recortados"][n] = {"pedido": v, "aplicado": lim["max_tokens"]}; v = lim["max_tokens"]
        out[n] = v
    if comp is not None:  # los defectos del modelo tambien respetan la lista de compatibles
        for n in _PARAMS:
            if n not in comp:
                out.pop(n, None)
    # Qwen 3.8 27B de Groq acepta tools, pero no parallel tool calls.
    # El valor por defecto del API es true: forzar false al ofrecer funciones.
    if modelo == "groq/qwen/qwen3.8-27b" and out.get("tools"):
        if out.get("parallel_tool_calls") is True:
            info["ignorados"].append("parallel_tool_calls=true")
        out["parallel_tool_calls"] = False
    return out, {k: v for k, v in info.items() if v}


def _tam(mensajes):
    return sum(len(str(m.get("content") or "")) for m in mensajes if isinstance(m, dict))


def _compactar_info(mensajes, pol):
    """(mensajes, info): solo sobre el tope recorta los resultados de herramientas MAS VIEJOS (no system, no user, no lo reciente). No muta el original.
    info = None si no se toco nada; si se recorto, {resultados_recortados, caracteres_antes, caracteres_despues}: la respuesta lo AVISA (nunca un recorte silencioso)."""
    c = pol.get("contexto") or {}
    antes = _tam(mensajes)
    if not c.get("max_caracteres") or antes <= c["max_caracteres"]:
        return mensajes, None
    out, maxr, n = list(mensajes), int(c.get("resultado_tool_max") or 4000), 0
    for i in range(max(len(out) - int(c.get("recientes") or 6), 0)):
        m = out[i]
        if isinstance(m, dict) and m.get("role") == "tool" and len(str(m.get("content") or "")) > maxr:
            out[i] = {**m, "content": str(m["content"])[:maxr] + " ...[recortado por tamano; ya se uso]"}; n += 1
            if _tam(out) <= c["max_caracteres"]:
                break
    return out, ({"resultados_recortados": n, "caracteres_antes": antes, "caracteres_despues": _tam(out)} if n else None)


def _compactar(mensajes, pol):
    return _compactar_info(mensajes, pol)[0]


# ---------- transporte: conexion persistente (httpx) o urllib; normaliza los fallos en ErrorHTTP / ErrorRed ----------
TRANSITORIOS = compute.REINTENTABLES | {408, 500, 529}
_dormir, _azar, _reloj = time.sleep, random.random, time.monotonic  # costuras de las pruebas
_ENFRIADAS = {}  # (proveedor, huella de la clave) -> instante (_reloj) hasta el que la clave NO se prueba primero tras un 429. Nunca guarda la clave en claro.


def limpiar_enfriadas():
    _ENFRIADAS.clear()


def _huella_clave(prov, k):
    return (prov, hashlib.sha256(k.encode("utf-8", "surrogatepass")).hexdigest()[:16])


def _enfriar(prov, k, pol, retry_after, codigo=429):
    """429 en una clave: se aparta cooldown_429_s (60 s, o el Retry-After del proveedor hasta 10 min). 402 (sin credito/cuota): cooldown_402_s (10 min): no se vuelve a probar primero."""
    r = pol.get("reintentos") or {}
    base = float(r.get("cooldown_402_s", 600.0)) if codigo == 402 else float(r.get("cooldown_429_s", 60.0))
    _ENFRIADAS[_huella_clave(prov, k)] = _reloj() + max(base, min(float(retry_after or 0), 600.0))


def _ordenar(prov, pool):
    """Claves libres primero (orden original); las enfriadas por 429 al final, la que antes caduca primero. Si todas estan enfriadas se intentan igual (no se inventa un fallo)."""
    ahora = _reloj()
    for h in [h for h, hasta in _ENFRIADAS.items() if hasta <= ahora]:
        del _ENFRIADAS[h]
    libres = [k for k in pool if _huella_clave(prov, k) not in _ENFRIADAS]
    return libres + sorted((k for k in pool if k not in libres), key=lambda k: _ENFRIADAS[_huella_clave(prov, k)])


# ---------- 152: tabla de errores. Una politica DISTINTA por familia (reintentar / rotar de clave / respetar Retry-After / enfriar la clave) ----------
TABLA_ERRORES = {
    "limite_temporal":    {"codigos": (429,), "reintentar": True, "rotar_clave": True, "respeta_retry_after": True, "enfriar_clave": True,
                           "texto": "429: limite de peticiones/tokens; se espera Retry-After o se rota de clave"},
    "credito_cuota":      {"codigos": (402,), "reintentar": False, "rotar_clave": True, "respeta_retry_after": False, "enfriar_clave": True,
                           "texto": "402: sin credito o cuota agotada en esa clave; otra clave puede servir, repetir con la misma no"},
    "credencial_permiso": {"codigos": (401, 403), "reintentar": False, "rotar_clave": True, "respeta_retry_after": False, "enfriar_clave": False,
                           "texto": "401/403: credencial invalida o sin permiso para el modelo; se descarta esa clave"},
    "timeout_red":        {"codigos": (408,), "reintentar": True, "rotar_clave": False, "respeta_retry_after": False, "enfriar_clave": False,
                           "texto": "timeout/red: backoff con jitter; si ya llegaron datos del stream NO se repite (duplicaria texto)"},
    "servidor_temporal":  {"codigos": (500, 502, 503, 504, 529), "reintentar": True, "rotar_clave": False, "respeta_retry_after": True, "enfriar_clave": False,
                           "texto": "5xx: fallo temporal del proveedor; backoff exponencial con jitter y tope de intentos"},
    "peticion_invalida":  {"codigos": (400, 404, 422), "reintentar": False, "rotar_clave": False, "respeta_retry_after": False, "enfriar_clave": False,
                           "texto": "400/404/422: modelo o peticion invalida; no se reintenta ni se cambia de modelo"},
}


def clasificar_error(codigo, red=False):
    """Politica de la familia del error: {tipo, reintentar, rotar_clave, respeta_retry_after, enfriar_clave, texto}. `red=True` = timeout/conexion sin codigo HTTP."""
    if red:
        return {"tipo": "timeout_red", **TABLA_ERRORES["timeout_red"]}
    for tipo, e in TABLA_ERRORES.items():
        if codigo in e["codigos"]:
            return {"tipo": tipo, **e}
    return {"tipo": "peticion_invalida" if codigo is not None and 400 <= codigo < 500 else "servidor_temporal", **TABLA_ERRORES["peticion_invalida" if codigo is not None and 400 <= codigo < 500 else "servidor_temporal"]}


class ErrorProveedor(RuntimeError):
    """Error final de una llamada, con su familia (`tipo`), el codigo HTTP (`codigo`, None si fue de red) y si valia la pena reintentarlo (`reintentable`). Mensaje sin credenciales."""
    def __init__(self, mensaje, codigo=None, red=False):
        super().__init__(mensaje)
        pol = clasificar_error(codigo, red)
        self.codigo, self.tipo, self.reintentable = codigo, pol["tipo"], pol["reintentar"]


class ErrorHTTP(Exception):
    def __init__(self, codigo, retry_after=None):
        super().__init__("HTTP %d" % codigo); self.codigo, self.retry_after = codigo, retry_after


class ErrorRed(Exception):
    def __init__(self, mensaje, con_datos=False):
        super().__init__(mensaje); self.con_datos = con_datos


def _retry_after(valor):
    """Cabecera Retry-After: segundos o fecha HTTP -> segundos (None si no viene o no se entiende)."""
    if not valor:
        return None
    try:
        return max(float(valor), 0.0)
    except ValueError:
        try:
            return max(parsedate_to_datetime(valor).timestamp() - time.time(), 0.0)
        except (TypeError, ValueError, IndexError):
            return None


_CLIENTE, _LOCK = None, threading.Lock()


def _cliente():
    global _CLIENTE
    with _LOCK:
        if _CLIENTE is None:
            _CLIENTE = _httpx.Client(limits=_httpx.Limits(max_keepalive_connections=16, max_connections=64, keepalive_expiry=60.0))
        return _CLIENTE


def _cab(clave, stream=False):
    return {"Content-Type": "application/json", "Authorization": "Bearer " + clave, "User-Agent": "riu-router", **({"Accept": "text/event-stream"} if stream else {})}


def _tiempo(exc, timeout):
    return ErrorRed("tiempo de espera agotado (%g s)" % timeout) if isinstance(exc, (TimeoutError,)) or (_httpx and isinstance(exc, _httpx.TimeoutException)) else ErrorRed(type(exc).__name__)


def _solicitar(url, payload, clave, timeout):
    """POST JSON -> respuesta ya decodificada."""
    try:
        if _httpx is not None:
            r = _cliente().post(url, json=payload, headers=_cab(clave), timeout=_httpx.Timeout(timeout, connect=min(timeout, 20.0)))
            if r.status_code >= 400:
                raise ErrorHTTP(r.status_code, _retry_after(r.headers.get("Retry-After")))
            return r.json()
        with request.urlopen(request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=_cab(clave), method="POST"), timeout=timeout) as r:
            return json.load(r)
    except ErrorHTTP:
        raise
    except error.HTTPError as exc:
        raise ErrorHTTP(exc.code, _retry_after(exc.headers.get("Retry-After"))) from None
    except ValueError:
        raise ErrorRed("respuesta no es JSON") from None
    except error.URLError as exc:
        raise _tiempo(exc.reason if isinstance(exc.reason, BaseException) else exc, timeout) from None
    except (OSError, getattr(_httpx, "HTTPError", OSError)) as exc:
        raise _tiempo(exc, timeout) from None


def _solicitar_stream(url, payload, clave, timeout, acumulador):
    """POST con stream=true: cada linea SSE va al acumulador apenas llega. ErrorRed.con_datos distingue un corte a mitad (no se reintenta)."""
    terminado = False
    try:
        if _httpx is not None:
            with _cliente().stream("POST", url, json=payload, headers=_cab(clave, True), timeout=_httpx.Timeout(timeout, connect=min(timeout, 20.0))) as r:
                if r.status_code >= 400:
                    r.read()  # se consume el cuerpo del error: la conexion queda libre para reutilizarse
                    raise ErrorHTTP(r.status_code, _retry_after(r.headers.get("Retry-After")))
                for linea in r.iter_lines():
                    if acumulador.linea(linea):
                        terminado = True; break
        else:
            with request.urlopen(request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=_cab(clave, True), method="POST"), timeout=timeout) as r:
                for linea in r:
                    if acumulador.linea(linea):
                        terminado = True; break
    except ErrorHTTP:
        raise
    except error.HTTPError as exc:
        raise ErrorHTTP(exc.code, _retry_after(exc.headers.get("Retry-After"))) from None
    except RuntimeError:
        raise  # error del proveedor dentro del stream: no se reintenta
    except error.URLError as exc:
        e = _tiempo(exc.reason if isinstance(exc.reason, BaseException) else exc, timeout); e.con_datos = acumulador.fragmentos > 0; raise e from None
    except (OSError, getattr(_httpx, "HTTPError", OSError)) as exc:
        e = _tiempo(exc, timeout); e.con_datos = acumulador.fragmentos > 0; raise e from None
    if not terminado and acumulador.finish_reason is None:  # el servidor cerro sin [DONE] ni finish_reason: respuesta truncada
        raise ErrorRed("stream interrumpido", con_datos=acumulador.fragmentos > 0)
    if not acumulador.texto and not acumulador._tools:  # [DONE] no convierte una respuesta vacia en exito
        raise ErrorRed("stream sin contenido ni herramientas", con_datos=acumulador.fragmentos > 0)


def _parsear(bruto, modelo):
    mensaje = bruto["choices"][0]["message"]
    return {"texto": mensaje.get("content") or "", "tool_calls": mensaje.get("tool_calls") or [], "finish_reason": bruto["choices"][0].get("finish_reason"),
            "uso": bruto.get("usage") or {}, "bruto": bruto, "mensaje_asistente": mensaje, "modelo_solicitado": modelo, "modelo_respuesta": bruto.get("model")}


def _sin_imagenes(mensajes):
    return [({**m, "content": "\n".join(p.get("text", "") for p in m["content"] if p.get("type") == "text") + "\n[imagenes adjuntas omitidas: este modelo no admite imagen]"}
             if isinstance(m.get("content"), list) else m) for m in mensajes]


def _con_reintentos(accion, pol, payload, ultima_clave, al_429=None):
    """Una clave: backoff exponencial con jitter, Retry-After del proveedor, tope de intentos y PRESUPUESTO total de tiempo (R8) de la politica.
    Cada familia de error (TABLA_ERRORES) tiene su politica: 401/402/403/404 -> _Alterna (siguiente clave); 429 con otra clave disponible -> _Alterna sin esperar (el limite es por clave).
    al_429(retry_after): aviso para enfriar esa clave entre llamadas. Siempre devuelve la respuesta o LANZA (nunca None); el error final es ErrorProveedor (con `tipo`)."""
    r = pol["reintentos"]
    maximo = max(int(r.get("max") or 1), 1)
    presupuesto, plazo, t0 = float(r.get("presupuesto_s") or compute.PRESUPUESTO_TOTAL_S), compute.timeout_s(pol.get("timeout_s")), _reloj()
    ultimo = [None]  # codigo HTTP del ultimo fallo transitorio (None = red)
    for n in range(maximo):
        espera = min(float(r.get("tope_s", 30.0)), float(r.get("base_s", 0.5)) * 2 ** n) * (0.5 + _azar() / 2)  # jitter: entre la mitad y el valor completo
        try:
            return accion()
        except ErrorHTTP as exc:
            if exc.codigo in (429, 402) and al_429:
                al_429(exc.retry_after, exc.codigo)
            if exc.codigo in (401, 402, 403, 404):  # clave invalida, sin credito o sin acceso al modelo: otra clave puede servir
                raise compute._Alterna("HTTP %d" % exc.codigo) from None
            if exc.codigo == 429 and not ultima_clave and r.get("rotar_clave_en_429", True):
                raise compute._Alterna("HTTP 429") from None
            if exc.codigo == 400 and any(isinstance(m.get("content"), list) for m in payload["messages"] if isinstance(m, dict)):
                raise ErrorProveedor("MODELO_SIN_VISION: proveedor rechazó las fotos; cambia a un modelo con visión", 400) from None
            if exc.codigo not in TRANSITORIOS or n == maximo - 1:
                raise ErrorProveedor("HTTP %d" % exc.codigo, exc.codigo) from None
            ultimo[0] = exc.codigo
            if exc.retry_after is not None:
                espera = min(exc.retry_after, float(r.get("retry_after_max_s", 60.0)))
        except ErrorRed as exc:
            if exc.con_datos or n == maximo - 1:
                raise ErrorProveedor("error de red: " + str(exc), None, True) from None
            ultimo[0] = None
        if (_reloj() - t0) + espera + plazo > presupuesto:  # R8: otro intento ya no cabe en el plazo del Harness -> se informa el ultimo fallo en vez de colgar
            raise ErrorProveedor("%s (reintentos detenidos: no caben en el presupuesto de %g s)" % (("HTTP %d" % ultimo[0]) if ultimo[0] else "error de red", presupuesto), ultimo[0], ultimo[0] is None) from None
        _dormir(espera)
    raise ErrorProveedor("sin respuesta del proveedor tras %d intentos" % maximo)  # p. ej. el ultimo intento fue el reintento sin imagenes: nunca se devuelve None


def _seguro(cb):
    def f(total, frag):
        try:
            cb(total, frag)
        except Exception:  # noqa: BLE001 - un fallo al pintar el parcial no debe cortar la respuesta del modelo
            logging.getLogger(__name__).warning("callback de parcial fallo", exc_info=True)
    return f


def _ordenar_system_groq(mensajes, modelo):
    """Qwen3.8/Groq: system al comienzo. Su plantilla no acepta system
    intercalado tras turnos user/assistant/tool de un agente.
    Mantiene el orden de todos los turnos y sus tool_call_id sin alterarlos.
    """
    if modelo != "groq/qwen/qwen3.8-27b":
        return mensajes
    sistemas = [m for m in mensajes if isinstance(m, dict) and m.get("role") == "system"]
    conversacion = [m for m in mensajes if not (isinstance(m, dict) and m.get("role") == "system")]
    return sistemas + conversacion


def llamar(mensajes, modelo, banco=None, opciones=None, al_parcial=None):
    """Una llamada a Groq/NVIDIA con el modelo ELEGIDO (nunca se sustituye). Con `al_parcial(texto_acumulado, fragmento)` y si la politica lo permite, usa SSE."""
    prov = proveedor(modelo)
    pool = claves(prov, banco)
    if not pool:
        raise PermissionError(PROVEEDORES[prov]["label"] + " sin clave (GROQ_API_KEY / NVIDIA_API_KEY en el banco o en el Space)")
    if modelo in PROVEEDORES_NUEVOS and disponible(modelo) is False and len(pool) == 1:
        # El catalogo es de la primera clave aceptada. Con varias claves, otra puede tener
        # permisos diferentes: se consulta el proveedor con el modelo ELEGIDO, sin sustituirlo.
        raise RuntimeError("%s: NO DISPONIBLE: %s no aparece en GET /models del proveedor; no se cambió de modelo" % (PROVEEDORES[prov]["label"], modelo))
    pol = politica(modelo)
    pool = _ordenar(prov, pool)  # las claves enfriadas por un 429 reciente van al final
    mensajes_ok, info_ctx = _compactar_info(_ordenar_system_groq(mensajes, modelo), pol)
    payload = {"model": modelo.split("/", 1)[1], "messages": mensajes_ok}
    extra, info_param = parametros(modelo, opciones, pol)
    payload.update(extra)
    st, tm = pol.get("streaming") or {}, compute.timeout_s(pol.get("timeout_s"))
    stream = (al_parcial is not None and st.get("activable", True) and os.environ.get("RIU_STREAM_EXTERNOS", "") != "0"
              and (st.get("con_tools", True) or not payload.get("tools")))
    nombres_tools = [t.get("function", {}).get("name") for t in (payload.get("tools") or []) if isinstance(t, dict)]
    url, estado, ultimo, codigos = compute._endpoint(PROVEEDORES[prov]["base"]), {"stream": stream}, None, []
    for i, k in enumerate(pool):  # una clave inválida o agotada (401/403/404) pasa a la siguiente del pool
        def accion():
            t0 = time.monotonic()
            if estado["stream"]:
                acumulador = compute.AcumuladorSSE(al_texto=_seguro(al_parcial), herramientas=nombres_tools)
                try:
                    _solicitar_stream(url, {**payload, "stream": True, **({"stream_options": {"include_usage": True}} if st.get("stream_options_usage", True) else {})}, k, tm, acumulador)
                    return acumulador.resultado(modelo)
                except ErrorHTTP as exc:
                    if exc.codigo not in (400, 422):
                        raise
                    estado["stream"] = False  # el proveedor no admite stream con esta peticion: misma peticion sin stream, mismo modelo
            r = _parsear(_solicitar(url, payload, k, tm), modelo)
            dur, tok = time.monotonic() - t0, (r["uso"] or {}).get("completion_tokens")
            r["metricas"] = {"stream": False, "ttft_s": None, "ttft_origen": "no_aplica_sin_stream", "duracion_s": round(dur, 4), "tokens": tok, "tokens_estimados": False,
                             "origen_tokens": "proveedor" if tok is not None else None, "tokens_por_s": round(tok / dur, 2) if tok and dur > 0 else None}  # sin usage no se inventan tokens
            return r
        try:
            try:
                r = _con_reintentos(accion, pol, payload, i == len(pool) - 1, lambda ra, cod, k=k: _enfriar(prov, k, pol, ra, cod))
            except ErrorProveedor as exc:
                # 413 no mejora esperando ni cambiando de clave. Reducir SOLO
                # documentacion del catalogo, nunca mensajes ni contratos de tools.
                reducidas = _tools_compactas(payload.get("tools"))
                if exc.codigo != 413 or prov != "groq" or not reducidas or reducidas == payload.get("tools"):
                    raise
                payload["tools"] = reducidas
                r = _con_reintentos(accion, pol, payload, i == len(pool) - 1, lambda ra, cod, k=k: _enfriar(prov, k, pol, ra, cod))
                r["metricas"]["catalogo_compactado"] = True
            if info_param:
                r["metricas"]["parametros"] = info_param
            if info_ctx:
                r["metricas"]["contexto_compactado"] = info_ctx  # el recorte NO es silencioso: va en la respuesta
            logging.getLogger(__name__).info("%s ttft=%s tokens/s=%s dur=%s", modelo, r["metricas"].get("ttft_s"), r["metricas"].get("tokens_por_s"), r["metricas"].get("duracion_s"))
            return {**r, "modelo_solicitado": modelo}
        except compute._Alterna as exc:
            ultimo = exc; codigos.append(str(exc))
    if codigos and all(c.endswith("HTTP 404") for c in codigos):
        raise ErrorProveedor("%s: HTTP 404 para el modelo %s (no existe o la clave no lo tiene habilitado); no se cambió de modelo" % (PROVEEDORES[prov]["label"], payload["model"]), 404)
    cod = re.search(r"HTTP (\d{3})", str(ultimo))
    raise ErrorProveedor(PROVEEDORES[prov]["label"] + ": ninguna de las %d claves fue aceptada (%s)" % (len(pool), str(ultimo).replace("Qwen ", "")), int(cod.group(1)) if cod else None, not cod)


def _tools_compactas(tools):
    """Copia el schema intacto salvo anotaciones; no altera propiedades/enum/required.
    Se usa una sola vez tras 413. Conserva una descripcion breve por funcion.
    """
    if not isinstance(tools, list):
        return None
    def schema(valor):
        if not isinstance(valor, dict):
            return valor
        out = {}
        for k, v in valor.items():
            if k in ("description", "title", "examples", "$comment"):
                continue
            if k in ("properties", "$defs", "definitions", "patternProperties", "dependentSchemas") and isinstance(v, dict):
                out[k] = {nombre: schema(sub) for nombre, sub in v.items()}
            elif k in ("items", "additionalProperties", "contains", "not", "if", "then", "else", "propertyNames"):
                out[k] = schema(v)
            elif k in ("allOf", "anyOf", "oneOf", "prefixItems") and isinstance(v, list):
                out[k] = [schema(sub) for sub in v]
            else:
                out[k] = v
        return out
    out = []
    for tool in tools:
        if not isinstance(tool, dict) or not isinstance(tool.get("function"), dict):
            out.append(tool)
            continue
        fn = dict(tool["function"])
        if isinstance(fn.get("description"), str):
            fn["description"] = fn["description"][:240]
        if "parameters" in fn:
            fn["parameters"] = schema(fn["parameters"])
        out.append({**tool, "function": fn})
    return out

