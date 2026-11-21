"""api/control.py — Panel de control de los 2 grupos de servidores del Router YAIWES.

Una sola funcion serverless que:
  1) CATALOGO  -> GET  /api/catalogo   (modelos reales y su estado en vivo)
  2) CONTROL   -> GET  /api/control    (estado de los 2 grupos)
  3) ACCIONES  -> POST /api/control    {"accion":"on|off|restart|trigger","grupo":1|2}

Por que vive en Vercel y no en el Space: el token de escritura de Hugging Face
(para cambiar el sleep_time o reiniciar un Space) NO debe estar en el navegador.
Aqui se usa la variable de entorno HF_TOKEN_1 (sensitive) y el navegador solo
habla con esta funcion.

Grupos:
  1 -> Grupo 1 · compute/proxy  (space-grupo-1-router-mvp-1, -v2, -v7)
  2 -> Grupo 2 · LLM local     (space-grupo-2-router-llm-hf-1, -2, -3)

Politica de apagado (pedido del owner): 30 minutos sin llamada -> el Space se
duerme y NO se factura. "Encender" deja el grupo siempre despierto (sleep=-1).
"""
import json
import os
import time
import urllib.error
import urllib.request

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

OWNER = "COMAND-CENTER-1"
HF = "https://huggingface.co"
ROUTER_HOST = "comand-center-1-space-grupo-1-router-mvp-1.hf.space"
TIMEOUT = float(os.environ.get("CONTROL_TIMEOUT_S", "12"))

# ------------------------------------------------------------------ grupos
GRUPOS = {
    1: {
        "nombre": "Grupo 1 · Router (compute/proxy)",
        "spaces": ["space-grupo-1-router-mvp-1",
                   "space-grupo-1-router-mvp-1-v2",
                   "space-grupo-1-router-mvp-1-v7"],
        "host": "comand-center-1-space-grupo-1-router-mvp-1.hf.space",
    },
    2: {
        "nombre": "Grupo 2 · LLM local (GGUF)",
        "spaces": ["space-grupo-2-router-llm-hf-1",
                   "space-grupo-2-router-llm-hf-2",
                   "space-grupo-2-router-llm-hf-3"],
        "host": "comand-center-1-space-grupo-2-router-llm-hf-1.hf.space",
    },
}

# Modelos VERIFICADOS en vivo contra cada API (el owner, 2026-11-19; medido hoy):
#   NVIDIA (integrate.api.nvidia.com): 2 de 15 probados responden 200.
#   Groq   (api.groq.com/openai/v1):   2 de 12 probados responden 200 (gpt-oss).
MODELOS_NVIDIA = [
    ("nvidia/nemotron-3.5-lightning-30b-a3b", "Nemotron 3.5 Lightning 30B"),
    ("nvidia/nemotron-3.5-bolt-e4b", "Nemotron 3.5 Bolt 4B"),
]
MODELOS_GROQ = [
    ("openai/gpt-oss-20b", "GPT OSS 20B"),
    ("openai/gpt-oss-120b", "GPT OSS 120B"),
]
# SWE CODE local: los 3 GGUF REALES del Grupo 2 (space_inventory.py:GROUP_2_MODELOS)
MODELOS_LOCALES = [
    ("hf/qwen2.5-coder-0.5b", "Qwen2.5 Coder 0.5B"),
    ("hf/lfm2.5-350m", "LFM2.5 350M"),
    ("hf/qwen3.5-0.8b", "Qwen3.5 0.8B"),
]
SLEEP_30MIN = 1800
SLEEP_JAMAS = -1

app = FastAPI(title="YAIWES · control de servidores")


# ------------------------------------------------------------------ helpers
def _token():
    return (os.environ.get("HF_TOKEN_1") or os.environ.get("HF_TOKEN")
            or os.environ.get("HUGGING_FACE_HUB_TOKEN") or "")


def _req(url, method="GET", body=None, token=False, timeout=None):
    headers = {"User-Agent": "YAIWES-Control/1.0"}
    if token and _token():
        headers["Authorization"] = "Bearer " + _token()
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout or TIMEOUT) as r:
            crudo = r.read().decode("utf-8", "replace")
            try:
                return r.status, json.loads(crudo)
            except Exception:
                return r.status, {"raw": crudo[:2000]}
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8", "replace"))
        except Exception:
            return e.code, {}
    except Exception as e:
        return 0, {"error": repr(e)[:200]}


def _estado_space(repo):
    st, d = _req(f"{HF}/api/spaces/{OWNER}/{repo}")
    if st != 200 or not isinstance(d, dict):
        return {"space": repo, "ok": False, "stage": "DESCONOCIDO", "http": st}
    rt = d.get("runtime") or {}
    return {
        "space": repo,
        "ok": True,
        "stage": rt.get("stage"),
        "sleeping": bool(rt.get("sleeping")),
        "gcTimeout": rt.get("gcTimeout"),
        "hardware": ((rt.get("hardware") or {}).get("current")),
        "host": "https://%s-%s.hf.space" % (OWNER.lower(), repo),
    }


def _despierta(host):
    """Despierta un Space dormido con un GET a su /health (no hace falta token)."""
    t0 = time.time()
    st, d = _req(f"https://{host}/health", timeout=45)
    return {"http": st, "segundos": round(time.time() - t0, 1),
            "ok": st == 200, "despertado": st == 200}


def _estado_grupos():
    out = {}
    for g, info in GRUPOS.items():
        spaces = [_estado_space(s) for s in info["spaces"]]
        vivos = sum(1 for s in spaces if s.get("ok") and not s.get("sleeping"))
        out[str(g)] = {
            "nombre": info["nombre"],
            "host": "https://" + info["host"],
            "spaces": spaces,
            "vivos": vivos,
            "total": len(spaces),
            "todos_dormidos": vivos == 0,
            "gcTimeout": (spaces[0] or {}).get("gcTimeout"),
            "hardware": (spaces[0] or {}).get("hardware"),
        }
    return out


def _catalogo():
    """Catalogo real, verificado en vivo, en el formato que espera el frontend."""
    # 1) el router vivo dice si tiene claves de NVIDIA/Groq
    st, prov = _req(f"https://{ROUTER_HOST}/v1/providers/health", timeout=20)
    configurados = {"nvidia": False, "groq": False}
    if st == 200 and isinstance(prov, dict):
        for it in prov.get("items", []) or []:
            if it.get("id") in ("nvidia", "groq") and it.get("configured"):
                configurados[it["id"]] = True

    # 2) los 3 GGUF del Grupo 2: vivos si su Space responde /health
    locales = []
    g2 = GRUPOS[2]
    # los 3 Spaces del Grupo 2 se sondean EN PARALELO (si uno duerme, no bloquea)
    from concurrent.futures import ThreadPoolExecutor

    def _sonda(repo):
        s, _ = _req(f"https://{OWNER.lower()}-{repo}.hf.space/health", timeout=12)
        return s == 200

    with ThreadPoolExecutor(max_workers=3) as ex:
        vivos = list(ex.map(_sonda, g2["spaces"]))
    for (cid, nombre), disponible in zip(MODELOS_LOCALES, vivos):
        locales.append({
            "id": cid,
            "estado": "DISPONIBLE" if disponible else "SIN VERIFICAR",
            "disponible": True if disponible else None,
            "etiqueta": nombre + ("" if disponible else " — SIN VERIFICAR"),
        })

    modelos = []
    for (mid, nombre) in MODELOS_NVIDIA:
        ok = configurados["nvidia"]
        modelos.append({"id": mid, "proveedor": "nvidia", "disponible": True if ok else False,
                        "etiqueta": "NVIDIA · " + nombre})
    for (mid, nombre) in MODELOS_GROQ:
        ok = configurados["groq"]
        modelos.append({"id": mid, "proveedor": "groq", "disponible": True if ok else False,
                        "etiqueta": "Groq · " + nombre})

    return {
        "ok": True,
        "modelos": modelos,
        "locales": locales,
        "configurados": configurados,
        "avisoGroq": "" if configurados["groq"] else "sin claves Groq en el Router",
        "avisoNvidia": "" if configurados["nvidia"] else "sin claves NVIDIA en el Router",
    }


# ------------------------------------------------------------------ rutas
@app.get("/api/catalogo")
def catalogo():
    """Catalogo de modelos en vivo (NVIDIA, Groq, SWE CODE local, SWE CODE free)."""
    d = _catalogo()
    return JSONResponse(status_code=200, content=d)


@app.get("/api/control")
def control_estado():
    """Estado de los 2 grupos + catalogo."""
    return JSONResponse(status_code=200, content={
        "ok": True,
        "grupos": _estado_grupos(),
        "catalogo": _catalogo(),
        "token_hf": bool(_token()),
    })


@app.post("/api/control")
async def control_accion(request: Request):
    """Acciones sobre un grupo: on | off | restart | trigger."""
    try:
        body = json.loads((await request.body()) or b"{}")
    except Exception:
        body = {}
    accion = str(body.get("accion") or "").lower()
    grupo = body.get("grupo")
    try:
        grupo = int(grupo)
    except Exception:
        grupo = 0
    if grupo not in GRUPOS:
        return JSONResponse(status_code=400,
                            content={"ok": False, "error": "grupo debe ser 1 o 2"})
    if accion not in ("on", "off", "restart", "trigger"):
        return JSONResponse(status_code=400,
                            content={"ok": False, "error": "accion: on|off|restart|trigger"})
    info = GRUPOS[grupo]
    detalle = []

    if accion == "trigger":
        # Despierta el grupo: un GET a su /health lo levanta (HF lo arranca solo).
        r = _despierta(info["host"])
        detalle.append({"accion": "trigger", "host": info["host"], **r})

    elif accion in ("on", "off"):
        # on  -> no se duerme nunca (sleep=-1); off -> vuelve a 30 min sin llamada.
        segundos = SLEEP_JAMAS if accion == "on" else SLEEP_30MIN
        for repo in info["spaces"]:
            st, d = _req(f"{HF}/api/spaces/{OWNER}/{repo}/sleeptime", method="POST",
                         body={"seconds": segundos}, token=True, timeout=20)
            detalle.append({"accion": accion, "space": repo, "http": st,
                            "sleep_time": segundos,
                            "respuesta": d if st != 200 else "ok"})
        if accion == "off":
            # Ademas el grupo 1 se duerme ya; el 2 tambien (sleep=1800).
            for repo in info["spaces"]:
                _req(f"https://{OWNER.lower()}-{repo}.hf.space/health", timeout=8)

    elif accion == "restart":
        for repo in info["spaces"]:
            st, d = _req(f"{HF}/api/spaces/{OWNER}/{repo}/restart", method="POST",
                         body={"restart": True}, token=True, timeout=25)
            detalle.append({"accion": "restart", "space": repo, "http": st})

    return JSONResponse(status_code=200, content={
        "ok": all(x.get("http", 200) in (200, 201, 202, 204) for x in detalle) or accion == "trigger",
        "accion": accion,
        "grupo": grupo,
        "nombre": info["nombre"],
        "detalle": detalle,
        "grupos": _estado_grupos(),
    })
