"""Chat MVP: autenticacion, banco de credenciales y cliente Token Plan."""
import asyncio
import hmac, uuid
import os, subprocess, time
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import Depends, FastAPI, Header, HTTPException
from mvp import bank, compute, modelos, harness_client, hf_store, mcp_route
@asynccontextmanager
async def inicio(app):
    app.state.banco = None
    app.state.commit = "desconocido"
    try:
        app.state.banco = bank.abrir_desde_env()
    except Exception:
        pass
    try:
        root = str(Path(__file__).resolve().parent.parent)
        cmd = subprocess.run(["git", "-C", root, "rev-parse", "HEAD"],
                             capture_output=True, text=True, timeout=3)
        if cmd.returncode == 0:
            app.state.commit = cmd.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    yield
app = FastAPI(lifespan=inicio)
def autorizado(authorization=None, x_api_key=None):
    esperado = next((os.environ[n] for n in bank.ACCESO if os.environ.get(n)), None)
    bearer = authorization[7:] if authorization and authorization.lower().startswith("bearer ") else None
    return bool(esperado and any(hmac.compare_digest(v, esperado)
                                 for v in (bearer, x_api_key) if isinstance(v, str)))
def verificar(authorization: str | None = Header(None),
              x_api_key: str | None = Header(None)):
    if not autorizado(authorization, x_api_key):
        raise HTTPException(status_code=401, detail="clave de acceso invalida")
def clave_harness():
    banco = app.state.banco
    clave = banco.leer("RIU_API_KEY") if banco else None
    if not clave:
        raise HTTPException(status_code=503, detail="credencial Harness ausente en banco")
    return clave
@app.get("/health")
def health(authorization: str | None = Header(None),
           x_api_key: str | None = Header(None)):
    if not autorizado(authorization, x_api_key):
        return {"status": "ok" if app.state.banco else "degraded"}
    return {"status": "ok" if app.state.banco else "degraded",
            "commit": app.state.commit, "banco_abierto": bool(app.state.banco),
            "qwen_base_url_presente": bool(modelos.base_url()),
            "plan": modelos.plan(), "modelo_defecto": modelos.cargar()["modelo_defecto"],
            "clave_qwen_presente": bool(modelos.clave_env() or
                                       (app.state.banco and app.state.banco.leer("QWEN_API_KEY")))}
@app.post("/chat", dependencies=[Depends(verificar)])
async def chat(cuerpo: dict):
    try:
        modelo = modelos.validar(cuerpo.get("modelo"))
    except (ValueError, TypeError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from None
    mensajes = cuerpo.get("mensajes")
    if not isinstance(mensajes, list) or not mensajes:
        raise HTTPException(status_code=400, detail="mensajes debe ser lista no vacia")
    if cuerpo.get("via") == "harness":
        try:
            salida = await asyncio.to_thread(harness_client.llm, clave_harness(), mensajes, modelo, cuerpo.get("opciones"))
        except (ValueError, RuntimeError) as error:
            raise HTTPException(status_code=502, detail=str(error)) from None
        if salida.get("status") == "error":
            raise HTTPException(status_code=502, detail=str(salida.get("error") or "harness error"))
        salida = salida.get("result", salida) if isinstance(salida.get("result"), dict) else salida
        return {"texto": salida.get("texto") or "", "tool_calls": salida.get("tool_calls") or []}
    banco = app.state.banco
    clave = banco.leer("QWEN_API_KEY") if banco else None
    if not clave:
        raise HTTPException(status_code=503, detail="QWEN_API_KEY no disponible en banco")
    try:
        salida = await asyncio.to_thread(compute.llamar, mensajes, modelo,
                                         modelos.base_url(), clave, cuerpo.get("opciones"))
    except (ValueError, RuntimeError) as error:
        raise HTTPException(status_code=502, detail=str(error)) from None
    return {"texto": salida["texto"], "tool_calls": salida["tool_calls"]}
@app.post("/almacen", dependencies=[Depends(verificar)])
async def almacen(cuerpo: dict):
    accion = cuerpo.get("accion")
    campos = {"guardar": ("nombre", "valor"), "leer": ("nombre",),
              "computar": ("tarea",), "status": ()}
    if accion not in campos or any(campo not in cuerpo for campo in campos.get(accion, ())):
        raise HTTPException(status_code=400, detail="accion o campos invalidos")
    destino = cuerpo.get("destino", "harness")
    if destino not in ("harness", "hf"): raise HTTPException(status_code=400, detail="destino no permitido")
    if destino == "hf":
        if accion not in ("guardar", "leer"): raise HTTPException(status_code=400, detail="accion HF no permitida")
        banco = app.state.banco; clave = banco.leer("HF_TOKEN") if banco else None
        if not clave: raise HTTPException(status_code=503, detail="HF_TOKEN no disponible en banco")
        try:
            return await asyncio.to_thread(getattr(hf_store, accion), clave, *(cuerpo[campo] for campo in campos[accion]))
        except ValueError as error: raise HTTPException(status_code=400, detail=str(error)) from None
        except RuntimeError as error: raise HTTPException(status_code=502, detail=str(error)) from None
    try:
        return await asyncio.to_thread(getattr(harness_client, accion), clave_harness(),
                                       *(cuerpo[campo] for campo in campos[accion]))
    except (ValueError, RuntimeError) as error:
        raise HTTPException(status_code=502, detail=str(error)) from None
# --- G14: panel-chat.js lee {providers:[{id,label}]} y {models:[{model_id,label}]}; datos solo de mvp/modelos.json ---
@app.get("/chat/providers", dependencies=[Depends(verificar)])
def chat_providers():
    return {"providers": [{"id": "qwen", "label": modelos.cargar()["proveedor"]}]}
@app.get("/chat/providers/{proveedor}/models", dependencies=[Depends(verificar)])
def chat_provider_models(proveedor: str):
    if proveedor != "qwen":
        raise HTTPException(status_code=404, detail="proveedor no disponible en mvp")
    return {"models": [{"model_id": m, "label": m} for m in modelos.permitidos()]}
# --- G16: panel-chat.js:542 lee {agents:[{id,name}]} y :543-544 {accounts:[{account}]}; mvp no tiene fuente de agentes ni de cuentas GitHub -> listas vacias (sin inventar) ---
@app.get("/chat/agents", dependencies=[Depends(verificar)])
def chat_agents():
    return {"agents": []}
@app.get("/chat/github/accounts", dependencies=[Depends(verificar)])
def chat_github_accounts():
    return {"accounts": []}
# --- G1/G2/G3/G4: contrato del frontend (api.js puenteRouter) sobre la logica existente de /chat ---
BLOQUEOS = {}  # sesion -> bool (agent_access_lock, en memoria)
TRABAJOS, _TAREAS = {}, set()  # proceso_id -> {estado, proceso_id, choices|error}; en memoria (se pierde al reiniciar)
FICHAS_QWEN = {"1": "ficha1-modelos", "2": "ficha2-dag-codigo", "3": "ficha3-frontend", "5": "ficha5-mvp"}
async def _chat_ficha(cuerpo):
    q = {**cuerpo, **(cuerpo.get("qwen") or {})}  # api.js harness() anida {plugin, ficha_qwen, modelo} en "qwen"
    mensajes = q.get("mensajes") or q.get("messages") or [{"role": "user", "content": str(q.get("message") or "")}]
    if q.get("instrucciones_fijas"):
        mensajes = [{"role": "system", "content": str(q["instrucciones_fijas"])}] + list(mensajes)
    try:
        modelo = modelos.validar(q.get("modelo") or None)
    except (ValueError, TypeError):
        modelo = modelos.cargar()["modelo_defecto"]  # el frontend manda etiquetas/fichas (nv-*, ficha*) fuera del catalogo
    # Ruta Antonio: Qwen -> Harness DeepSeek (HTTP) -> router. Sin camino alterno; sin URL Harness falla (G5 abierto)
    if not os.environ.get("RIU_DEEPSEEK_HARNESS_URL"):
        raise HTTPException(status_code=503, detail="HARNESS_NO_CONFIGURADO")
    salida = await chat({"modelo": modelo, "mensajes": mensajes, "via": "harness", "opciones": q.get("opciones")})
    return {"estado": "listo", "via": "harness", "choices": [{"message": {
        "role": "assistant", "content": salida["texto"], "tool_calls": salida["tool_calls"]}}]}
async def _correr(pid, cuerpo):
    try:
        TRABAJOS[pid].update(await _chat_ficha(cuerpo))
    except HTTPException as error:
        TRABAJOS[pid].update(estado="error", error=str(error.detail))
    except Exception as error:  # noqa: BLE001 - el proceso debe terminar siempre
        TRABAJOS[pid].update(estado="error", error=type(error).__name__)
@app.post("/plugins/{plugin}/call/{accion}", dependencies=[Depends(verificar)])
async def plugin_call(plugin: str, accion: str, cuerpo: dict):
    if plugin not in ("fichas_qwen", "puente_chat"):
        raise HTTPException(status_code=404, detail="plugin no disponible en mvp")
    if accion in ("fichas", "listar_fichas"):
        return {"status": "ok", "result": {"fichas": [{"n": n, "id": i, "nombre": i} for n, i in FICHAS_QWEN.items()]}}
    if accion in ("chat_async", "chat"):
        pid = "p-" + (str(cuerpo.get("request_id") or "")[:64] or uuid.uuid4().hex)  # request_id fijo => mismo proceso_id
        if pid not in TRABAJOS:
            TRABAJOS[pid] = {"estado": "procesando", "proceso_id": pid}
            tarea = asyncio.create_task(_correr(pid, cuerpo)); _TAREAS.add(tarea); tarea.add_done_callback(_TAREAS.discard)
        return {"status": "ok", "result": dict(TRABAJOS[pid])}
    if accion == "resultado":
        pid = str(cuerpo.get("proceso_id") or "")
        if pid not in TRABAJOS:
            raise HTTPException(status_code=404, detail="proceso_id desconocido")
        try:
            espera = min(max(float(cuerpo.get("espera") or 0), 0), 8)
        except (TypeError, ValueError):
            espera = 0
        for _ in range(int(espera * 4)):  # long-poll: responde apenas termina (max 8 s)
            if TRABAJOS[pid]["estado"] != "procesando":
                break
            await asyncio.sleep(0.25)
        return {"status": "ok", "result": dict(TRABAJOS[pid])}
    if accion == "llm" and plugin == "fichas_qwen":  # G21: Ficha 4 -> modelo DIRECTO (contrato puente_chat llm_call); nunca via=harness
        try:
            modelo = modelos.validar(cuerpo.get("modelo") or None)
        except (ValueError, TypeError):
            modelo = modelos.cargar()["modelo_defecto"]
        opciones = dict(cuerpo.get("opciones") or {})
        if cuerpo.get("max_tokens"):
            opciones["max_tokens"] = cuerpo["max_tokens"]
        try:
            salida = await chat({"modelo": modelo, "mensajes": cuerpo.get("messages") or cuerpo.get("mensajes"), "opciones": opciones})
        except HTTPException as error:
            return {"status": "ok", "result": {"error": "GAP_FICHA4", "detalle": str(error.detail)[:200]}}
        return {"status": "ok", "result": {"reply": salida["texto"], "modelo": modelo,
                                           "ficha": str(cuerpo.get("ficha_qwen") or "ficha4-workflow-yaiwes")}}
    if accion == "agent_access_lock":  # G15: panel-chat.js exige result {ok:true, locked:bool}; en memoria, bloqueado por defecto
        sesion = str(cuerpo.get("sesion") or "web-general")[:60]
        if "locked" in cuerpo:
            if type(cuerpo["locked"]) is not bool:
                raise HTTPException(status_code=400, detail="locked debe ser booleano")
            BLOQUEOS[sesion] = cuerpo["locked"]
        return {"status": "ok", "result": {"ok": True, "sesion": sesion, "locked": BLOQUEOS.get(sesion, True)}}
    raise HTTPException(status_code=400, detail="accion no soportada en mvp")
# --- G19: POST /chat/send (panel-chat.js sin harnessUrl) sobre la misma ruta Harness que chat_async; sin fallback ---
@app.post("/chat/send", dependencies=[Depends(verificar)])
async def chat_send(cuerpo: dict):
    t0 = time.monotonic()
    salida = await _chat_ficha(cuerpo)  # 503 HARNESS_NO_CONFIGURADO si falta RIU_DEEPSEEK_HARNESS_URL
    msg = salida["choices"][0]["message"]
    tools = [((t.get("function") or {}).get("name") or "tool") for t in (msg.get("tool_calls") or []) if isinstance(t, dict)]
    return {"reply": msg["content"], "execution_path": "HARNESS", "ms": int((time.monotonic() - t0) * 1000),
            "tools": tools, "via": "harness"}
mcp_route.montar(app, verificar, chat, almacen)
# --- G5b: Harness /invoke montado en este mismo Space (HF pide PRO para un Space nuevo). Ruta: chat -> Harness -> HTTP -> router ---
from plugins.deepseek_harness.server import app as harness_app  # noqa: E402 - el Harness no importa mvp/; llm sigue por HTTP a fichas_qwen/call/llm
app.mount("/plugins/deepseek_harness", harness_app)  # RIU_DEEPSEEK_HARNESS_URL = https://<space>/plugins/deepseek_harness
