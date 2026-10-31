"""Modelos de Groq y NVIDIA (APIs compatibles OpenAI) para el chat: id «groq/<modelo>» o «nvidia/<modelo>».
La clave sale del banco (GROQ_API_KEY / NVIDIA_API_KEY) o de las variables del Space (GROQ_API_KEY_2..7, NVIDIA_API_KEY_1..9)."""
import json
import logging
import os
import pathlib
import random
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
}
PARAMETROS_MODELO = {mid: {k: v for k, v in cfg.items() if k in ("temperature", "top_p", "max_tokens", "reasoning_effort", "reasoning_format")} for mid, cfg in PROVEEDORES_NUEVOS.items()}
_PARAMS = ("temperature", "top_p", "max_tokens", "reasoning_effort", "reasoning_format")
CACHE = {}  # proveedor -> (instante, lista de ids)
_SWE = {}  # (ruta, mtime_ns, tamano, clave de acceso) -> banco compartido abierto (o None si no se pudo abrir); evita repetir PBKDF2


def _banco_compartido():
    """Banco cifrado del web-bridge (solo lectura): RIU_BANCO_SWE o <BRIDGE_STATE_DIR|/tmp/state>/banco-swe.bin. Nunca lanza; None si no aporta."""
    try:
        from mvp import bank
        ruta = os.environ.get("RIU_BANCO_SWE") or os.path.join(os.environ.get("BRIDGE_STATE_DIR") or "/tmp/state", "banco-swe.bin")
        acceso = next((os.environ[v] for v in bank.ACCESO if os.environ.get(v)), None)
        if not acceso or not os.path.isfile(ruta):  # no existe: no se abre (abrir() crearia el archivo)
            return None
        st = os.stat(ruta)
        llave = (ruta, st.st_mtime_ns, st.st_size, acceso)
        if llave not in _SWE:
            _SWE.clear()
            try:
                _SWE[llave] = bank.abrir(ruta, acceso)
            except Exception:
                _SWE[llave] = None
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
        raise RuntimeError(PROVEEDORES[prov]["label"] + " sin clave (GROQ_API_KEY / NVIDIA_API_KEY)")
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
    "reintentos": {"max": 3, "base_s": 0.5, "tope_s": 30.0, "retry_after_max_s": 60.0, "rotar_clave_en_429": True},
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


def _tam(mensajes):
    return sum(len(str(m.get("content") or "")) for m in mensajes if isinstance(m, dict))


def _compactar(mensajes, pol):
    """Solo sobre el tope: recorta los resultados de herramientas MAS VIEJOS (no system, no user, no lo reciente). No muta el original."""
    c = pol.get("contexto") or {}
    if not c.get("max_caracteres") or _tam(mensajes) <= c["max_caracteres"]:
        return mensajes
    out, maxr = list(mensajes), int(c.get("resultado_tool_max") or 4000)
    for i in range(max(len(out) - int(c.get("recientes") or 6), 0)):
        m = out[i]
        if isinstance(m, dict) and m.get("role") == "tool" and len(str(m.get("content") or "")) > maxr:
            out[i] = {**m, "content": str(m["content"])[:maxr] + " ...[recortado por tamano; ya se uso]"}
            if _tam(out) <= c["max_caracteres"]:
                break
    return out


# ---------- transporte: conexion persistente (httpx) o urllib; normaliza los fallos en ErrorHTTP / ErrorRed ----------
TRANSITORIOS = compute.REINTENTABLES | {408, 500, 529}
_dormir, _azar = time.sleep, random.random  # costuras de las pruebas


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


def _parsear(bruto, modelo):
    mensaje = bruto["choices"][0]["message"]
    return {"texto": mensaje.get("content") or "", "tool_calls": mensaje.get("tool_calls") or [], "finish_reason": bruto["choices"][0].get("finish_reason"),
            "uso": bruto.get("usage") or {}, "bruto": bruto, "mensaje_asistente": mensaje, "modelo_solicitado": modelo, "modelo_respuesta": bruto.get("model")}


def _sin_imagenes(mensajes):
    return [({**m, "content": "\n".join(p.get("text", "") for p in m["content"] if p.get("type") == "text") + "\n[imagenes adjuntas omitidas: este modelo no admite imagen]"}
             if isinstance(m.get("content"), list) else m) for m in mensajes]


def _con_reintentos(accion, pol, payload, ultima_clave):
    """Una clave: backoff exponencial con jitter, Retry-After del proveedor y tope de intentos de la politica.
    401/403/404 -> _Alterna (siguiente clave); 429 con otra clave disponible -> _Alterna sin esperar (el limite es por clave)."""
    r = pol["reintentos"]
    maximo = max(int(r.get("max") or 1), 1)
    for n in range(maximo):
        espera = min(float(r.get("tope_s", 30.0)), float(r.get("base_s", 0.5)) * 2 ** n) * (0.5 + _azar() / 2)  # jitter: entre la mitad y el valor completo
        try:
            return accion()
        except ErrorHTTP as exc:
            if exc.codigo in (401, 403, 404):
                raise compute._Alterna("HTTP %d" % exc.codigo) from None
            if exc.codigo == 429 and not ultima_clave and r.get("rotar_clave_en_429", True):
                raise compute._Alterna("HTTP 429") from None
            if exc.codigo == 400 and any(isinstance(m.get("content"), list) for m in payload["messages"] if isinstance(m, dict)):
                payload["messages"] = _sin_imagenes(payload["messages"]); continue  # el modelo no admite imagen: se repite con solo el texto
            if exc.codigo not in TRANSITORIOS or n == maximo - 1:
                raise RuntimeError("HTTP %d" % exc.codigo) from None
            if exc.retry_after is not None:
                espera = min(exc.retry_after, float(r.get("retry_after_max_s", 60.0)))
        except ErrorRed as exc:
            if exc.con_datos or n == maximo - 1:
                raise RuntimeError("error de red: " + str(exc)) from None
        _dormir(espera)


def _seguro(cb):
    def f(total, frag):
        try:
            cb(total, frag)
        except Exception:  # noqa: BLE001 - un fallo al pintar el parcial no debe cortar la respuesta del modelo
            logging.getLogger(__name__).warning("callback de parcial fallo", exc_info=True)
    return f


def llamar(mensajes, modelo, banco=None, opciones=None, al_parcial=None):
    """Una llamada a Groq/NVIDIA con el modelo ELEGIDO (nunca se sustituye). Con `al_parcial(texto_acumulado, fragmento)` y si la politica lo permite, usa SSE."""
    prov = proveedor(modelo)
    pool = claves(prov, banco)
    if not pool:
        raise PermissionError(PROVEEDORES[prov]["label"] + " sin clave (GROQ_API_KEY / NVIDIA_API_KEY en el banco o en el Space)")
    if modelo in PROVEEDORES_NUEVOS and disponible(modelo) is False:
        raise RuntimeError("%s: NO DISPONIBLE: %s no aparece en GET /models del proveedor; no se cambió de modelo" % (PROVEEDORES[prov]["label"], modelo))
    pol = politica(modelo)
    payload = {"model": modelo.split("/", 1)[1], "messages": _compactar(mensajes, pol)}
    for n, v in (opciones or {}).items():
        if n in compute.OPCIONES and n not in ("enable_thinking", "reasoning_effort"):
            payload[n] = v
    payload.update(PARAMETROS_MODELO.get(modelo, {}))
    if pol.get("parametros_compatibles") is not None:
        for n in _PARAMS:
            if n not in pol["parametros_compatibles"]:
                payload.pop(n, None)
    st, tm = pol.get("streaming") or {}, compute.timeout_s(pol.get("timeout_s"))
    stream = (al_parcial is not None and st.get("activable", True) and os.environ.get("RIU_STREAM_EXTERNOS", "") != "0"
              and (st.get("con_tools", True) or not payload.get("tools")))
    url, estado, ultimo, codigos = compute._endpoint(PROVEEDORES[prov]["base"]), {"stream": stream}, None, []
    for i, k in enumerate(pool):  # una clave inválida o agotada (401/403/404) pasa a la siguiente del pool
        def accion():
            t0 = time.monotonic()
            if estado["stream"]:
                acumulador = compute.AcumuladorSSE(al_texto=_seguro(al_parcial))
                try:
                    _solicitar_stream(url, {**payload, "stream": True, **({"stream_options": {"include_usage": True}} if st.get("stream_options_usage", True) else {})}, k, tm, acumulador)
                    return acumulador.resultado(modelo)
                except ErrorHTTP as exc:
                    if exc.codigo not in (400, 422):
                        raise
                    estado["stream"] = False  # el proveedor no admite stream con esta peticion: misma peticion sin stream, mismo modelo
            r = _parsear(_solicitar(url, payload, k, tm), modelo)
            dur, tok = time.monotonic() - t0, (r["uso"] or {}).get("completion_tokens")
            r["metricas"] = {"stream": False, "ttft_s": None, "duracion_s": round(dur, 4), "tokens": tok, "tokens_estimados": False, "tokens_por_s": round(tok / dur, 2) if tok and dur > 0 else None}
            return r
        try:
            r = _con_reintentos(accion, pol, payload, i == len(pool) - 1)
            logging.getLogger(__name__).info("%s ttft=%s tokens/s=%s dur=%s", modelo, r["metricas"].get("ttft_s"), r["metricas"].get("tokens_por_s"), r["metricas"].get("duracion_s"))
            return {**r, "modelo_solicitado": modelo}
        except compute._Alterna as exc:
            ultimo = exc; codigos.append(str(exc))
    if codigos and all(c.endswith("HTTP 404") for c in codigos):
        raise RuntimeError("%s: HTTP 404 para el modelo %s (no existe o la clave no lo tiene habilitado); no se cambió de modelo" % (PROVEEDORES[prov]["label"], payload["model"]))
    raise RuntimeError(PROVEEDORES[prov]["label"] + ": ninguna de las %d claves fue aceptada (%s)" % (len(pool), str(ultimo).replace("Qwen ", "")))
