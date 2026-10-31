#!/usr/bin/env python3
"""SWE CODE mini-router: ejecuta la cascada de cascada.json contra llama-server(s).
HTTP OpenAI-compatible only. ~90 lineas, cero dependencias extra (solo requests)."""
import hashlib, json, os, re, sys, tempfile, time, uuid, urllib.error, urllib.request

RAIZ = os.path.dirname(os.path.abspath(__file__))
CASCADA = json.load(open(os.path.join(RAIZ, "cascada.json")))
MOTORES = json.load(open(os.path.join(RAIZ, "motores.json")))["motores"]
BASE_URL = os.getenv(CASCADA["base_url_env"], CASCADA["base_url_default"]).rstrip("/")
# Cola HF: S1/S2/S3 son slots intercambiables (cualquier Space sirve cualquier
# modelo via model=, 1 vivo por Space, carga bajo demanda, encola al libre).
# El orden del paso = preferencia; el salto a otra URL = slot libre/respaldo.
URLS = {s: os.getenv(f"SWECODE_URL_{s}").rstrip("/") for s in ("S1", "S2", "S3")
        if os.getenv(f"SWECODE_URL_{s}")}
if not URLS:
    URLS = {"S1": BASE_URL}


# Respaldo cuando ningun slot HF responde: Groq y luego NVIDIA, con las mismas claves del chat (variables GROQ_API_KEY / NVIDIA_API_KEY, y _1.._20).
# Modelos objetivo (ids ya investigados; no se inventan mas). Mas ids por env: RIU_SWE_GROQ_MODELOS / RIU_SWE_NVIDIA_MODELOS (coma),
# p.ej. minimaxai/minimax-m3.1-flash, deepseek-ai/deepseek-v4.1-flash (kimi-k3 sin confirmar gratis: solo si el operador lo anade).
MODELOS_DEFECTO = {"groq": "qwen/qwen3.8-27b", "nvidia": "meta/muse-glimmer-30b"}
MODELOS_RESPALDO = {"groq": [], "nvidia": ["nvidia/nemotron-3-super-120b-a12b"]}   # solo con el modelo por defecto
EXTERNOS = {"groq": ("https://api.groq.com/openai/v1", "GROQ_API_KEY", os.getenv("RIU_SWE_GROQ_MODELO", MODELOS_DEFECTO["groq"])),
            "nvidia": ("https://integrate.api.nvidia.com/v1", "NVIDIA_API_KEY", os.getenv("RIU_SWE_NVIDIA_MODELO", MODELOS_DEFECTO["nvidia"]))}
MAX_CONTINUACIONES = 8   # veces que se pide "continua" si finish_reason == 'length' (sumado entre proveedores)
_CONTINUA = "Continua exactamente donde te quedaste, sin repetir lo ya escrito."
_ULTIMO = {}             # via/modelo de la ultima llamada exitosa (para anotarlos en el estado de la etapa)


def _claves(var: str) -> list:
    """VAR, VAR_1 .. VAR_20 (las que existan), sin repetir valores."""
    vistas, out = set(), []
    for nombre in [var] + [f"{var}_{i}" for i in range(1, 21)]:
        v = (os.getenv(nombre) or "").strip()
        if v and v not in vistas:
            vistas.add(v); out.append(v)
    return out


def _modelos(via: str, principal: str) -> list:
    """Modelo principal + lista por env + (si es el modelo por defecto) los de respaldo conocidos. Sin repetir."""
    lista = [principal] + [m.strip() for m in os.getenv(f"RIU_SWE_{via.upper()}_MODELOS", "").split(",") if m.strip()]
    if principal == MODELOS_DEFECTO.get(via):
        lista += MODELOS_RESPALDO.get(via, [])
    return list(dict.fromkeys(lista))


class _Parcial(Exception):
    """Fallo a mitad de una continuacion: conserva lo ya recibido para seguir con otra clave/proveedor."""
    def __init__(self, parcial, causa):
        super().__init__(str(causa)); self.parcial, self.causa = parcial, causa


def _pedir(url: str, headers: dict, modelo: str, mensajes: list, timeout: int):
    body = json.dumps({"model": modelo, "messages": mensajes, "temperature": 0.2}).encode()
    req = urllib.request.Request(f"{url}/chat/completions", method="POST", data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        ch = json.load(r)["choices"][0]
    return ch["message"].get("content") or "", ch.get("finish_reason")


def _completar(url, headers, modelo, mensajes, timeout, previo="", presupuesto=None):
    """Una respuesta completa: si finish_reason == 'length' pide continuar (tope MAX_CONTINUACIONES en total)."""
    presupuesto = presupuesto if presupuesto is not None else {"cont": 0}
    acum = previo
    while True:
        msgs = mensajes if not acum else mensajes + [{"role": "assistant", "content": acum}, {"role": "user", "content": _CONTINUA}]
        try:
            texto, fin = _pedir(url, headers, modelo, msgs, timeout)
        except Exception as e:
            raise _Parcial(acum, e) if acum else e
        acum += texto
        if fin != "length" or presupuesto["cont"] >= MAX_CONTINUACIONES:
            return acum
        presupuesto["cont"] += 1


def _clase(e) -> str:
    """'modelo': el modelo no sirve (400/404/422) -> siguiente modelo; resto (429/402/401/5xx/timeout/red) -> siguiente clave."""
    return "modelo" if isinstance(e, urllib.error.HTTPError) and e.code in (400, 404, 422) else "clave"


def _externo(mensajes: list, ultimo, parcial: str = ""):
    """Devuelve (texto, via) con via = 'groq' | 'nvidia' (la primera clave/modelo que responda). Rota claves y modelos; conserva lo parcial."""
    presupuesto = {"cont": 0}
    for via, (base, var, modelo) in EXTERNOS.items():
        claves = _claves(var)
        for m in _modelos(via, modelo):
            for clave in claves:
                try:
                    cab = {"Content-Type": "application/json", "Authorization": "Bearer " + clave, "User-Agent": "riu-swe-code"}
                    texto = _completar(base.rstrip("/"), cab, m, mensajes, 120, parcial, presupuesto)
                    _ULTIMO.update(via=via, modelo=m)
                    return texto, via
                except Exception as e:
                    if isinstance(e, _Parcial):
                        parcial, e = e.parcial, e.causa
                    ultimo = e
                    if _clase(e) == "modelo":
                        break
    raise ultimo or RuntimeError('sin servidores')


def llamar_via(modelo: str, mensajes: list, servidor: str = "S1"):
    """Como llamar() pero devuelve (texto, via): 'hf-slot', 'groq' o 'nvidia'."""
    orden = [servidor] + [s for s in URLS if s != servidor]
    ultimo, parcial, presupuesto = None, "", {"cont": 0}
    for s in orden:
        base_url = URLS.get(s)
        if not base_url:
            continue
        try:
            texto = _completar(base_url, {"Content-Type": "application/json"}, modelo, mensajes, 600, parcial, presupuesto)
            _ULTIMO.update(via="hf-slot", modelo=modelo)
            return texto, "hf-slot"
        except Exception as e:
            if isinstance(e, _Parcial):
                parcial, e = e.parcial, e.causa
            ultimo = e
    return _externo(mensajes, ultimo, parcial)


def llamar(modelo: str, mensajes: list, servidor: str = "S1") -> str:
    return llamar_via(modelo, mensajes, servidor)[0]


def recibo(pid, nodo, estado, extra=None):
    r = {"pid": pid, "nodo": nodo, "estado": estado, "ts": int(time.time())}
    if extra: r.update(extra)
    return r


# --- recuperacion: etapas confirmadas en JSON atomico, reanudables por tarea_id ---
# Directorio: RIU_MINI_STATE, o $BRIDGE_STATE_DIR/mini_router (se respalda en /data), o <repo>/state/mini_router. Siempre absoluto.
_REDACTAR = [re.compile(p, re.I) for p in (
    r"\bBearer\s+[A-Za-z0-9._~+/=-]{8,}",
    r"\b(?:gsk_|nvapi-|sk-|sk_|ghp_|github_pat_|hf_|AIza)[A-Za-z0-9_-]{10,}",
    r"\b(?:api[_-]?key|token|password|secret)\s*[:=]\s*[\"']?[A-Za-z0-9._~+/=-]{8,}")]


def _estado_dir() -> str:
    d = os.getenv("RIU_MINI_STATE") or (os.path.join(os.getenv("BRIDGE_STATE_DIR"), "mini_router") if os.getenv("BRIDGE_STATE_DIR") else os.path.join(RAIZ, "state", "mini_router"))
    return os.path.abspath(d)


def _redactar(txt):
    """Nunca se persisten claves: tacha las claves reales del entorno y los patrones tipicos de credenciales."""
    if not isinstance(txt, str):
        return txt
    for var in [v for _, v, _ in EXTERNOS.values()]:
        for c in _claves(var):
            txt = txt.replace(c, "[REDACTED]")
    for rx in _REDACTAR:
        txt = rx.sub("[REDACTED]", txt)
    return txt


def _ruta_estado(tarea_id) -> str:
    limpio = re.sub(r"\.{2,}", "_", re.sub(r"[^\w.-]", "_", str(tarea_id)))[:100] or "sin-id"
    return os.path.join(_estado_dir(), limpio + ".json")


def _guardar_estado(tarea_id, estado: dict):
    destino = _ruta_estado(tarea_id)
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(destino), prefix=".tmp-", suffix=".part")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(estado, f, ensure_ascii=False, indent=1); f.flush()
            try: os.fsync(f.fileno())
            except OSError: pass
        os.replace(tmp, destino)
    except BaseException:
        try: os.unlink(tmp)
        except OSError: pass
        raise


def _cargar_estado(tarea_id, huella):
    try:
        with open(_ruta_estado(tarea_id), encoding="utf-8") as f:
            e = json.load(f)
        return e if e.get("huella") == huella and isinstance(e.get("pasos"), dict) else None
    except (OSError, ValueError):
        return None


def correr(objetivo: str, pasos=None, tarea_id=None) -> dict:
    """Con tarea_id cada etapa confirmada se guarda; repetir la llamada reanuda desde la primera sin confirmar."""
    pasos = pasos or CASCADA["pasos"]
    huella = hashlib.sha256((objetivo + "\0" + json.dumps([p["nodo"] for p in pasos])).encode()).hexdigest()[:16]
    est = _cargar_estado(tarea_id, huella) if tarea_id else None
    pid = est["pid"] if est else f"swecode-{uuid.uuid4().hex[:8]}"
    est = est or {"schema": "swe-code.mini_router.estado.v1", "tarea_id": tarea_id, "pid": pid, "huella": huella,
                  "objetivo": _redactar(objetivo[:200]), "estado": "CONTINUAR", "ultimo_paso_confirmado": None, "pasos": {}}

    def guardar(**cambios):
        if tarea_id:
            est.update(cambios, ts=int(time.time())); _guardar_estado(tarea_id, est)

    recibos = [recibo(pid, "inicio", "OK", {"objetivo": objetivo[:200]})]
    entrada = objetivo
    for i, paso in enumerate(pasos):
        if paso.get("condicional") and "[GAP]" not in entrada:
            continue
        modelo, nodo, agente = paso["modelo"], paso["nodo"], paso["agente"]
        clave_paso = f"{i}:{nodo}"
        previo = est["pasos"].get(clave_paso)
        if previo and previo.get("estado") == "DONE":   # ya confirmado: no se repite
            entrada = previo["salida"]
            recibos.append(recibo(pid, nodo, "OK", {"modelo": modelo, "chars": len(entrada), "via": previo.get("proveedor"), "reanudado": True}))
            continue
        prompt = (f"AGENTE={agente}. Tarea: {objetivo}\n"
                  f"Entrada del paso anterior ({paso['entrada']}):\n{entrada}\n"
                  f"Entrega SOLO: {paso['salida']}.")
        try:
            _ULTIMO.clear()
            salida, via = llamar_via(modelo, [{"role": "user", "content": prompt}],
                                     paso.get("servidor", "S1"))
            recibos.append(recibo(pid, nodo, "OK", {"modelo": modelo, "chars": len(salida),
                                                  "servidor": paso.get("servidor"), "via": via}))
            entrada = salida
            est["pasos"][clave_paso] = {"nodo": nodo, "estado": "DONE", "salida": _redactar(salida), "proveedor": via,
                                        "modelo": _ULTIMO.get("modelo", modelo), "ts": int(time.time())}
            guardar(ultimo_paso_confirmado=clave_paso, estado="CONTINUAR", error=None)
        except Exception as e:
            recibos.append(recibo(pid, nodo, "FAIL", {"modelo": modelo, "error": str(e)[:300]}))
            guardar(estado="ERROR", error=_redactar(str(e)[:300]), paso_fallido=nodo)
            return {"pid": pid, "estado": "FAIL", "paso_fallido": nodo, "recibos": recibos}
    guardar(estado="DONE", error=None)
    return {"pid": pid, "estado": "DONE", "resultado": entrada, "recibos": recibos}


def main():
    args = sys.argv[1:]
    pasos, tarea_id = None, None
    if args[:1] == ["--tarea-id"] and len(args) > 1:   # reanuda desde la ultima etapa confirmada
        tarea_id, args = args[1], args[2:]
    if args[:1] == ["--pipeline"]:
        nombre = args[1] if len(args) > 1 else "code"
        pasos = CASCADA.get("pipelines", {}).get(nombre)
        if not pasos:
            print(json.dumps({"verdict": "INPUT_GAP", "detail": f"pipeline desconocido: {nombre}",
                              "pipelines": list(CASCADA.get("pipelines", {}))})); sys.exit(1)
        args = args[2:]
    docs = []
    while args[:1] == ["--doc"]:
        args = args[1:]
        if not args: break
        try:
            with open(args[0], encoding="utf-8") as f:
                docs.append((os.path.basename(args[0]), f.read()[:100000]))
        except OSError as e:
            print(json.dumps({"verdict": "INPUT_GAP", "detail": f"doc ilegible: {args[0]} ({e})"})); sys.exit(1)
        args = args[1:]
    objetivo = args[0] if args else sys.stdin.read().strip()
    if not objetivo:
        print(json.dumps({"verdict": "INPUT_GAP", "detail": "objetivo requerido"})); sys.exit(1)
    if docs:
        objetivo += "\n\n" + "\n\n".join(f"[DOCUMENTO: {n}]\n{c}" for n, c in docs)
    print(json.dumps(correr(objetivo, pasos, tarea_id=tarea_id), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
