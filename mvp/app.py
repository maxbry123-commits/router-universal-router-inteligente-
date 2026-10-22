"""Chat MVP: autenticacion, banco de credenciales y cliente Token Plan."""
import asyncio
import hmac
import os, subprocess
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
mcp_route.montar(app, verificar, chat, almacen)
