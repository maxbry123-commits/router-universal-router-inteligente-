"""Chat MVP: autenticacion, banco de credenciales y cliente Token Plan."""
import asyncio
import base64
import hmac, logging, re, uuid
import os, subprocess, sys, time
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from mvp import bank, compute, control, externos, memoria, modelos, harness_client, hf_store, mcp_cliente, mcp_route, escalado, multimedia, prompt, sala_turno, trabajos
_MODOS = Path(__file__).resolve().parent / "herramientas" / "modos"
sys.path.append(str(_MODOS))  # motores que envuelven el system prompt (movidos desde fichas/fichas_qwen/modos)
import mode_router  # noqa: E402
REGISTRO = mode_router.load_registry(str(_MODOS / "modes_registry.json"))
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
    try:
        await asyncio.wait_for(CONTROL.cargar(), 15)  # estado de permisos guardado por /almacen; sin HF sigue en memoria
    except asyncio.TimeoutError:
        pass
    yield
app = FastAPI(lifespan=inicio)
app.add_middleware(CORSMiddleware, allow_methods=["*"], allow_headers=["*"],  # el chat (Vercel) llama al Router desde otro origen; la autenticacion es la X-API-Key, no cookies
                   allow_origin_regex=os.environ.get("RIU_CORS_REGEX", r"https://riu-jev-bridge[a-z0-9-]*\.vercel\.app|http://127\.0\.0\.1:\d+"))
CONTROL = control.Control()

def _controles(cuerpo):
    controles = {}
    for nombre in ("tools", "agente_tool", "llm_tool"):
        valor = cuerpo.get(nombre, False)
        if type(valor) is not bool:
            raise HTTPException(status_code=400, detail=nombre + " debe ser booleano")
        controles[nombre] = valor
    return controles

def _verificar_herramienta(nombre, controles):
    permitido, bloqueo = CONTROL.decidir(nombre, controles)  # conexion + herramienta + delegacion IA, decididas en el servidor
    if not permitido:
        logging.getLogger(__name__).warning("Herramienta bloqueada por %s", bloqueo)
        raise HTTPException(status_code=403, detail="Herramienta bloqueada: " + bloqueo)

def _verificar_llamadas(llamadas, controles):
    for llamada in llamadas:
        funcion = llamada.get("function") if isinstance(llamada, dict) else None
        _verificar_herramienta(funcion.get("name") if isinstance(funcion, dict) else None, controles)

def _verificar_opciones(opciones, controles):
    if isinstance(opciones, dict):
        _verificar_llamadas(opciones.get("tools") or [], controles)

def autorizado(authorization=None, x_api_key=None):
    esperadas = [os.environ[n] for n in bank.ACCESO if os.environ.get(n)]  # cualquiera de las variables de acceso configuradas abre la puerta (p. ej. RIU_MCP_KEY para pruebas)
    bearer = authorization[7:] if authorization and authorization.lower().startswith("bearer ") else None
    return any(hmac.compare_digest(v, e) for e in esperadas for v in (bearer, x_api_key) if isinstance(v, str))
def verificar(authorization: str | None = Header(None),
              x_api_key: str | None = Header(None), key: str | None = Query(None)):  # ?key= para clientes MCP que solo aceptan una URL
    if not autorizado(authorization, x_api_key or key):
        recibida = "recibido: X-API-Key %d car., Bearer %d car." % (len(x_api_key or key or ""), len(authorization[7:]) if authorization else 0)  # solo longitudes de lo que envio el cliente: ayuda a ver si el navegador manda la clave completa
        raise HTTPException(status_code=401, detail="clave de acceso invalida (" + recibida + ")")
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
        return {"status": "ok" if app.state.banco else "degraded", "commit": str(getattr(app.state, "commit", "desconocido"))[:10]}  # el commit no es secreto: sirve para comprobar que version corre
    return {"status": "ok" if app.state.banco else "degraded", "cpu": escalado.cpu_local(),
            "commit": app.state.commit, "banco_abierto": bool(app.state.banco),
            "qwen_base_url_presente": bool(modelos.base_url()),
            "plan": modelos.plan(), "modelo_defecto": modelos.cargar()["modelo_defecto"],
            "clave_qwen_presente": bool(modelos.clave_env() or
                                       (app.state.banco and app.state.banco.leer("QWEN_API_KEY")))}
MAX_CARACTERES = 1_000_000  # tope de texto por peticion: error claro en vez de un 502 opaco del proveedor
async def _llamar_modelo(mensajes, modelo, opciones):
    """Una llamada directa al modelo: Qwen (QWEN_API_KEY) o Groq/NVIDIA (groq/<id>, nvidia/<id>, mvp/externos.py)."""
    banco = app.state.banco
    try:
        if externos.proveedor(modelo):
            return await asyncio.to_thread(externos.llamar, mensajes, modelo, banco, opciones)
        clave = banco.leer("QWEN_API_KEY") if banco else None
        if not clave:
            raise HTTPException(status_code=503, detail="QWEN_API_KEY no disponible en banco")
        return await asyncio.to_thread(compute.llamar, mensajes, modelo, modelos.base_url(), clave, opciones)
    except PermissionError as error:
        raise HTTPException(status_code=503, detail=str(error)) from None
    except (ValueError, TypeError, RuntimeError) as error:
        raise HTTPException(status_code=502, detail=str(error)) from None
@app.post("/chat", dependencies=[Depends(verificar)])
async def chat(cuerpo: dict):
    controles = _controles(cuerpo)
    try:
        modelo = modelos.validar(cuerpo.get("modelo"))
    except (ValueError, TypeError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from None
    mensajes = cuerpo.get("mensajes")
    if not isinstance(mensajes, list) or not mensajes:
        raise HTTPException(status_code=400, detail="mensajes debe ser lista no vacia")
    if sum(len(str(m.get("content") or "")) for m in mensajes if isinstance(m, dict)) > MAX_CARACTERES:
        raise HTTPException(status_code=413, detail="el contexto supera %d caracteres; acorta el mensaje o abre un chat nuevo" % MAX_CARACTERES)
    if cuerpo.get("via") == "harness":
        try:
            salida = await asyncio.to_thread(harness_client.llm, clave_harness(), mensajes, modelo, cuerpo.get("opciones"), controles)
        except (ValueError, RuntimeError) as error:
            raise HTTPException(status_code=502, detail=str(error)) from None
        if salida.get("status") == "error":
            raise HTTPException(status_code=403 if salida.get("status_code") == 403 else 502, detail=str(salida.get("error") or "harness error"))
        salida = salida.get("result", salida) if isinstance(salida.get("result"), dict) else salida
        llamadas = salida.get("tool_calls") or []
        _verificar_llamadas(llamadas, controles)
        return {"texto": salida.get("texto") or "", "tool_calls": llamadas, "herramientas_usadas": salida.get("herramientas_usadas") or [],
                "finish_reason": salida.get("finish_reason"),
                **{k: salida[k] for k in ("mensaje_asistente", "modelo_solicitado", "modelo_respuesta") if k in salida}}
    salida = await _llamar_modelo(mensajes, modelo, cuerpo.get("opciones"))
    _verificar_llamadas(salida["tool_calls"], controles)
    return {"texto": salida["texto"], "tool_calls": salida["tool_calls"],
            "finish_reason": salida.get("finish_reason"),
                **{k: salida[k] for k in ("mensaje_asistente", "modelo_solicitado", "modelo_respuesta") if k in salida}}
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
        banco = app.state.banco
        try: clave = CONTROL.credencial("hf", banco, estricto=False)  # primera conexion HF ON del banco; sin ninguna, la principal
        except RuntimeError as error: raise HTTPException(status_code=503, detail=str(error)) from None
        try:
            return await asyncio.to_thread(getattr(hf_store, accion), clave, *(cuerpo[campo] for campo in campos[accion]))
        except ValueError as error: raise HTTPException(status_code=400, detail=str(error)) from None
        except hf_store.NoExiste as error: raise HTTPException(status_code=404, detail=str(error)) from None
        except RuntimeError as error: raise HTTPException(status_code=502, detail=str(error)) from None
    try:
        return await asyncio.to_thread(getattr(harness_client, accion), clave_harness(),
                                       *(cuerpo[campo] for campo in campos[accion]))
    except (ValueError, RuntimeError) as error:
        raise HTTPException(status_code=502, detail=str(error)) from None
# --- G14: panel-chat.js lee {providers:[{id,label}]} y {models:[{model_id,label}]}; datos solo de mvp/modelos.json ---
@app.get("/chat/providers", dependencies=[Depends(verificar)])
def chat_providers():  # Groq y NVIDIA solo si hay clave: el selector no ofrece lo que no puede responder
    return {"providers": [{"id": "qwen", "label": modelos.cargar()["proveedor"]}] + [{"id": p, "label": d["label"]} for p, d in externos.PROVEEDORES.items() if externos.clave(p, app.state.banco)]}
@app.get("/chat/providers/{proveedor}/models", dependencies=[Depends(verificar)])
def chat_provider_models(proveedor: str):
    if proveedor in externos.PROVEEDORES:
        try: return {"models": [{"model_id": m, "label": m.split("/", 1)[1], "tipo": "texto"} for m in externos.modelos(proveedor, app.state.banco)]}
        except (RuntimeError, OSError, ValueError) as error: raise HTTPException(status_code=503, detail=str(error)[:200]) from None
    if proveedor != "qwen":
        raise HTTPException(status_code=404, detail="proveedor no disponible en mvp")
    return {"models": [{"model_id": m, "label": m, "tipo": t} for m, t in modelos.catalogo()]}
# --- G16: panel-chat.js:542 lee {agents:[{id,name}]} y :543-544 {accounts:[{account}]}; mvp no tiene fuente de agentes ni de cuentas GitHub -> listas vacias (sin inventar) ---
@app.get("/chat/agents", dependencies=[Depends(verificar)])
def chat_agents():
    return {"agents": []}
@app.get("/chat/github/accounts", dependencies=[Depends(verificar)])
def chat_github_accounts():
    return {"accounts": []}
# --- G1/G2/G3/G4: contrato del frontend (api.js puenteRouter) sobre la logica existente de /chat ---
async def _leer_estado():
    return (await almacen({"accion": "leer", "destino": "hf", "nombre": control.NOMBRE}))["valor"]
async def _guardar_estado(texto):
    await almacen({"accion": "guardar", "destino": "hf", "nombre": control.NOMBRE, "valor": texto})
CONTROL.conectar(_leer_estado, _guardar_estado)  # el estado del chat se persiste por /almacen (sin secretos)
def _clave_hf():
    try: return CONTROL.credencial("hf", app.state.banco, estricto=False)
    except RuntimeError as error: raise HTTPException(status_code=503, detail=str(error)) from None
memoria.rutas(app, verificar, _clave_hf)  # historial y pestañas del chat (chat-ancla.js) en el bucket HF
async def _contexto_anclado(anclados, sesion):
    """Anclas del chat -> un mensaje de sistema: archivos subidos (texto), textos y enlaces; los secretos nunca viajan al modelo."""
    partes, total, vistos = [], 0, set()
    for a in (anclados if isinstance(anclados, list) else [])[:20]:
        a = str(a)[:300]
        if a.startswith("secreto:"):
            continue
        a = a.split(":", 1)[1] if a.split(":", 1)[0] in ("constitucion", "archivo") else a.rsplit(":", 1)[1] if a.startswith("proyecto:") and a.count(":") >= 2 else a
        if a in vistos:  # la misma ancla puede llegar por dos caminos (constitucion y anclados)
            continue
        vistos.add(a)
        if a.split(":", 1)[0] in ("enlace", "raiz", "texto", "handoff"):
            partes.append("- " + a)
            continue
        ruta = CONTROL.ruta_de(a, sesion)
        if not ruta or total > 200_000:
            continue
        try:
            crudo = (await almacen({"accion": "leer", "destino": "hf", "nombre": ruta}))["valor"]
            texto = base64.b64decode(crudo).decode("utf-8")[:60_000]
        except Exception:  # noqa: BLE001 - binario o almacén caído: se omite, el chat sigue
            partes.append("- " + a + " (no se pudo leer su contenido)")
            continue
        total += len(texto)
        partes.append("--- " + a + " ---\n" + texto)
    return {"role": "system", "content": "[ANCLADOS POR EL DIRECTOR]\n" + "\n".join(partes)} if partes else None
ORGANIZADOR = "qwen3.7-plus"
async def _organizar(cuerpo):
    """Pendientes: un modelo (qwen3.7 por defecto) los ordena por prioridad; solo se reordena, nunca se crea ni se borra nada."""
    lista = CONTROL.d["pendientes"]
    clave = app.state.banco.leer("QWEN_API_KEY") if app.state.banco else None
    if not clave: raise HTTPException(status_code=503, detail="QWEN_API_KEY no disponible en banco")
    try: modelo = modelos.validar(cuerpo.get("modelo") or ORGANIZADOR)
    except (ValueError, TypeError) as error: raise ValueError(str(error)) from None
    texto = "\n".join(x["id"] + " | " + x["texto"] for x in lista)
    pedido = [{"role": "user", "content": "Ordena estos pendientes por prioridad. Responde SOLO una lista JSON con todos los ids, sin texto extra.\n" + texto}]
    try: salida = await asyncio.to_thread(compute.llamar, pedido, modelo, modelos.base_url(), clave, None)
    except (ValueError, TypeError, RuntimeError) as error: raise HTTPException(status_code=502, detail=str(error)) from None
    hallados = re.findall(r"[0-9a-f]{8}", salida["texto"])
    ids = [i for n, i in enumerate(hallados) if i in {x["id"] for x in lista} and i not in hallados[:n]]
    ids += [x["id"] for x in lista if x["id"] not in ids]
    return await CONTROL.aplicar("checklist", {"accion": "ordenar", "ids": ids}, app.state.banco)

async def _control(accion, cuerpo, actor="director"):
    try:
        if accion == "checklist" and cuerpo.get("accion") == "organizar": return await _organizar(cuerpo)
        if accion == "salas" and cuerpo.get("accion") == "turno": return await sala_turno.turno(CONTROL, _delegar, app.state.banco, cuerpo)
        if accion == "subir":  # el contenido se guarda por /almacen ANTES de registrarlo: sin fantasmas en el índice
            if not CONTROL.sincronizado: await CONTROL.cargar()
            ruta, _ = CONTROL.validar_subida(cuerpo)
            try: await almacen({"accion": "guardar", "destino": "hf", "nombre": ruta, "valor": cuerpo["datos_b64"]})
            except HTTPException as error:
                if error.status_code == 400: raise ValueError("tipo de archivo no permitido en el almacén (el código va en GitHub)") from None
                raise
        salida = await CONTROL.aplicar(accion, cuerpo, app.state.banco, actor)
        if accion == "status": salida = {**salida, "commit": getattr(app.state, "commit", "desconocido"), "banco": bool(getattr(app.state, "banco", None))}
        if accion == "conexiones" and (cuerpo.get("accion") == "descubrir" or (cuerpo.get("accion") == "agregar" and cuerpo.get("servicio") == "mcp")):
            ident = cuerpo.get("id") or CONTROL.d["conexiones"]["mcp"][-1]["id"]
            con = next((c for c in CONTROL.d["conexiones"]["mcp"] if c["id"] == ident), None)
            if not con: raise ValueError("conexion desconocida")
            try:
                lista = await asyncio.to_thread(mcp_cliente.listar, con["url"], app.state.banco.leer(control._clave_banco("mcp", ident)) if app.state.banco else None)
                salida = await CONTROL.aplicar("conexiones", {"accion": "herramientas", "id": ident, "lista": lista}, app.state.banco)
            except (ValueError, RuntimeError) as error:
                salida = {**await CONTROL.aplicar("conexiones", {}, None), "aviso": str(error)}
        return salida
    except PermissionError as error: raise HTTPException(status_code=403, detail=str(error)) from None
    except ValueError as error: raise HTTPException(status_code=400, detail=str(error)) from None
    except RuntimeError as error: raise HTTPException(status_code=502, detail=str(error)) from None
TRABAJO_VENCE, MAX_COLA, _PROPIOS = 900, 200, set()
TRABAJOS, _TAREAS = {}, set()  # proceso_id -> {estado, proceso_id, choices|error}; en memoria (se pierde al reiniciar)
FICHAS_QWEN = {"1": "ficha1-modelos", "2": "ficha2-dag-codigo", "3": "ficha3-frontend", "5": "ficha5-mvp"}
FICHAS_HEREDADAS = ("nv-", "hf-", "ask-consil")  # ids de ficha del chat anterior; no son modelos del MVP
async def _generar_medio(modelo, tipo, mensajes, progreso):
    banco = app.state.banco
    clave = banco.leer("QWEN_API_KEY") if banco else None
    if not clave: raise HTTPException(status_code=503, detail="QWEN_API_KEY no disponible en banco")
    texto = next((str(m.get("content") or "") for m in reversed(mensajes) if isinstance(m, dict) and m.get("role") == "user"), "")
    try: salida = await asyncio.to_thread(multimedia.generar, modelo, tipo, modelos.base_url(), clave, texto, progreso)
    except ValueError as error: raise HTTPException(status_code=400, detail=str(error)) from None
    except RuntimeError as error: raise HTTPException(status_code=502, detail=str(error)) from None
    return {"estado": "completado", "via": "directo", "finish_reason": "stop", "modelo_solicitado": modelo, "modelo_respuesta": modelo,
            "choices": [{"message": {"role": "assistant", "content": salida, "tool_calls": []}, "finish_reason": "stop"}]}
async def _chat_ficha(cuerpo, progreso=None):
    q = {**cuerpo, **(cuerpo.get("qwen") or {})}  # api.js harness() anida {plugin, ficha_qwen, modelo} en "qwen"
    mensajes = q.get("mensajes") or q.get("messages") or [{"role": "user", "content": str(q.get("message") or "")}]
    if q.get("contexto_previo"):
        if not isinstance(q["contexto_previo"], list):
            raise HTTPException(status_code=400, detail="contexto_previo debe ser una lista")
        mensajes = list(q["contexto_previo"]) + list(mensajes)
    con = q.get("constitucion") if isinstance(q.get("constitucion"), dict) else {}
    ses = str(q.get("sesion") or "web-general")[:60]
    anclado = await _contexto_anclado(q.get("anclados"), ses)
    arch_con = await _contexto_anclado(con.get("anclados"), ses)
    pend = "\n".join("- [%s] %s" % ("x" if p["hecho"] else " ", p["texto"][:300]) for p in CONTROL.d["pendientes"][:30])
    propios = [("CONSTITUCION: es ley para este trabajo; respétala al programar y en lo que respondes", (str(con.get("texto") or "").strip() + ("\n" + arch_con["content"] if arch_con else "")).strip()),
               ("yaiwes.md (información del proyecto; la herramienta yaiwes_md la lee y la escribe)", CONTROL.d["handoff"].get("yaiwes")),
               ("SANDBOX (system prompt de code)", CONTROL.d["sandbox"].get(ses)),
               ("PENDIENTES (lista compartida; la herramienta pendientes la consulta y la actualiza)", pend)]  # encendidos = con texto
    propios = "\n\n".join("[" + n + "]\n" + t for n, t in propios if t)
    if propios:
        mensajes = [{"role": "system", "content": propios}] + list(mensajes)
    if anclado:
        mensajes = [anclado] + list(mensajes)
    if q.get("instrucciones_fijas"):
        mensajes = [{"role": "system", "content": str(q["instrucciones_fijas"])}] + list(mensajes)
    ultimo = mensajes[-1] if isinstance(mensajes[-1], dict) and mensajes[-1].get("role") == "user" else None  # capa de motores: Router -> ficha -> modo -> system prompt
    try:
        ruteo = mode_router.route_request(REGISTRO, {"message": str((ultimo or {}).get("content") or ""), "mode_request": q.get("mode_request")})
    except mode_router.ModeError as error:
        raise HTTPException(status_code=400, detail=str(error)) from None
    aviso_modo = ("modo %s: el bucle autónomo no está en el MVP; se respondió un turno con las reglas del modo" % ruteo["mode_id"]) if ruteo["ficha"]["autonomous_loop"] else None
    if ultimo is not None and ruteo["message"].strip():  # /modo y /auto se quitan del texto
        mensajes = [*mensajes[:-1], {**ultimo, "content": ruteo["message"]}]
    if ruteo["source"] != "default_mode":  # el modo por defecto (m05: "sin herramientas") contradiría las tools autorizadas por el Router: sin regla ni modo elegido no se envuelve
        mensajes = [{"role": "system", "content": ruteo["ficha"]["system_block"]}] + list(mensajes)
    capa = prompt.formato() + ("\n\n" + prompt.sistema() if CONTROL.d["prompt_on"] else "")  # capa externa: formato de salida siempre; system prompt completo con su boton
    mensajes = [{"role": "system", "content": capa}] + list(mensajes)
    seleccionado = str(q.get("modelo") or q.get("model") or "")
    seleccionado = next((m for m, _ in modelos.catalogo() if "".join(c for c in m.lower() if c.isalnum()) == "".join(c for c in seleccionado.lower() if c.isalnum())), seleccionado)
    heredada = seleccionado.startswith(FICHAS_HEREDADAS)
    if heredada:  # sin selector Qwen activo el chat manda su ficha (nv-muse-glimmer): se usa el modelo por defecto y el chat muestra «Modelo solicitado · API»
        seleccionado = ""
    medio = dict(modelos.catalogo()).get(seleccionado)
    if medio and medio != "texto":  # imagen, voz, ASR y video: llamada directa a la ficha (no pasan por herramientas)
        return await _generar_medio(seleccionado, medio, mensajes, progreso)
    try:
        modelo = modelos.validar(seleccionado or None)
    except (ValueError, TypeError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from None
    identidad = {"role": "system", "content": "Modelo activo: %s%s, ejecutado en QwenCloud Token Plan. Las respuestas anteriores de esta conversación pudieron venir de otros modelos: no copies su identidad. Si te preguntan quién o qué modelo eres, responde en una línea con ese nombre y su familia." % (modelo, " — " + modelos.marca(modelo) if modelos.marca(modelo) else "")}
    fin = len(mensajes) - 1 if isinstance(mensajes[-1], dict) and mensajes[-1].get("role") == "user" else len(mensajes)
    mensajes = [*mensajes[:fin], identidad, *mensajes[fin:]]  # justo antes del mensaje actual: el historial de otro modelo no la tapa
    # Ruta Antonio: Qwen -> Harness DeepSeek (HTTP) -> router. Sin camino alterno; sin URL Harness falla (G5 abierto)
    if not os.environ.get("RIU_DEEPSEEK_HARNESS_URL"):
        raise HTTPException(status_code=503, detail="HARNESS_NO_CONFIGURADO")
    opciones = dict(q.get("opciones") or {})
    if q.get("thinking_mode") in ("on", "off") and modelo == "qwen3.8-max":  # selector Pensar del chat; solo este modelo admite el interruptor (modelos.extra_body)
        opciones.setdefault("enable_thinking", q["thinking_mode"] == "on")
    salida = await chat({"modelo": modelo, "mensajes": mensajes, "via": "harness",
                         "opciones": opciones or None, **_controles(q)})
    return {"estado": "completado", "via": "harness", "finish_reason": salida["finish_reason"],
            "modelo_solicitado": modelo, "modelo_respuesta": salida.get("modelo_respuesta"), "herramientas_usadas": salida.get("herramientas_usadas") or [],
            **({"aviso_modelo": "sin selector de modelo encendido: respondió el modelo por defecto " + modelo} if heredada else {}),
            **({"aviso_modo": aviso_modo} if aviso_modo else {}),
            "choices": [{"message": {"role": "assistant", "content": salida["texto"],
                                    "tool_calls": salida["tool_calls"]},
                         "finish_reason": salida["finish_reason"]}]}
async def _local(pid, cuerpo):
    try:
        TRABAJOS[pid].update(await _chat_ficha(cuerpo, lambda t: TRABAJOS[pid].update(progreso=t)))
    except HTTPException as error:
        TRABAJOS[pid].update(estado="error", error=str(error.detail), status_code=error.status_code)
    except Exception as error:  # noqa: BLE001 - el proceso debe terminar siempre
        TRABAJOS[pid].update(estado="error", error=type(error).__name__)
def _clave_acceso(): return next((os.environ[n] for n in bank.ACCESO if os.environ.get(n)), "")
async def _persistir(pid): await asyncio.to_thread(trabajos.guardar, app.state.banco, pid, TRABAJOS[pid])
async def _esperar_destino(pid):
    while not (destino := await escalado.elegir(_clave_acceso())):  # los 3 servidores ocupados: el trabajo espera en cola
        TRABAJOS[pid]["subestado"] = "en_cola"; await asyncio.sleep(2)
    return destino
async def _seguir_remoto(pid, url, remoto):
    r = {"estado": "procesando", "proceso_id": remoto}
    while r.get("estado") == "procesando":
        TRABAJOS[pid]["subestado"] = "ejecutando"
        r = await escalado.enviar(url, _clave_acceso(), "resultado", {"proceso_id": remoto, "espera": 8})
    TRABAJOS[pid].update({k: v for k, v in r.items() if k != "proceso_id"})
async def _remoto(pid, cuerpo, url):
    TRABAJOS[pid].update(destino=url, subestado="enviado" if escalado.despierto(url) else "despertando")
    r = await escalado.enviar(url, _clave_acceso(), "chat_async", {**cuerpo, "request_id": pid[2:]})  # mismo request_id: un reintento no ejecuta dos veces
    TRABAJOS[pid]["proceso_remoto"] = r["proceso_id"]; await _persistir(pid)
    if r.get("estado") == "procesando": await _seguir_remoto(pid, url, r["proceso_id"])
    else: TRABAJOS[pid].update({k: v for k, v in r.items() if k != "proceso_id"})
async def _correr(pid, cuerpo):
    destino = "local"
    try:
        if escalado.remotos(): destino = await _esperar_destino(pid)
        escalado.entrar(destino)
        try: await (_local(pid, cuerpo) if destino == "local" else _remoto(pid, cuerpo, destino))
        finally: escalado.salir(destino)
    except escalado.DestinoError as error: TRABAJOS[pid].update(estado="error", error=str(error))
    TRABAJOS[pid].pop("subestado", None); await _persistir(pid)
async def _recuperar(pid):
    """Trabajo iniciado o terminado por otro proceso: se lee del almacen; un trabajo local 'procesando' sin latido de 15 min se da por interrumpido."""
    doc = await asyncio.to_thread(trabajos.leer, app.state.banco, pid)
    if not doc or (doc.get("estado") == "procesando" and time.time() - doc.get("creado", 0) > TRABAJO_VENCE): return False
    TRABAJOS[pid] = doc
    if doc.get("estado") == "procesando" and doc.get("proceso_remoto"):
        _lanzar(_seguir_adoptado(pid, doc["destino"], doc["proceso_remoto"]))
    return True
async def _seguir_adoptado(pid, url, remoto):
    try: await _seguir_remoto(pid, url, remoto)
    except escalado.DestinoError as error: TRABAJOS[pid].update(estado="error", error=str(error))
    TRABAJOS[pid].pop("subestado", None); await _persistir(pid)
def _lanzar(coro):
    tarea = asyncio.create_task(coro); _TAREAS.add(tarea); tarea.add_done_callback(_TAREAS.discard)
@app.post("/plugins/{plugin}/call/{accion}", dependencies=[Depends(verificar)])
async def plugin_call(plugin: str, accion: str, cuerpo: dict):
    if plugin not in ("fichas_qwen", "puente_chat"):
        raise HTTPException(status_code=404, detail="plugin no disponible en mvp")
    if accion in ("fichas", "listar_fichas"):
        return {"status": "ok", "result": {"fichas": [{"n": n, "id": i, "nombre": i} for n, i in FICHAS_QWEN.items()]}}
    if accion in ("chat_async", "chat"):
        pid = trabajos.identificador(cuerpo.get("request_id"), uuid.uuid4().hex)  # request_id fijo => mismo proceso_id
        if pid not in TRABAJOS and not await _recuperar(pid):
            if sum(1 for t in TRABAJOS.values() if t.get("subestado") == "en_cola") >= MAX_COLA:
                raise HTTPException(status_code=429, detail="cola llena; reintenta en unos segundos")
            TRABAJOS[pid] = {"estado": "procesando", "proceso_id": pid, "finish_reason": "", "creado": time.time()}
            _PROPIOS.add(pid); _lanzar(_correr(pid, cuerpo))
        if TRABAJOS[pid].get("status_code") == 403:
            raise HTTPException(status_code=403, detail=TRABAJOS[pid]["error"])
        return {"status": "ok", "result": dict(TRABAJOS[pid])}
    if accion == "resultado":
        pid = str(cuerpo.get("proceso_id") or "")
        if pid not in TRABAJOS and not await _recuperar(pid):
            raise HTTPException(status_code=404, detail="proceso_id desconocido")
        try:
            espera = min(max(float(cuerpo.get("espera") or 0), 0), 8)
        except (TypeError, ValueError):
            espera = 0
        for i in range(int(espera * 4)):  # long-poll: responde apenas termina (max 8 s)
            if TRABAJOS[pid]["estado"] != "procesando":
                break
            await asyncio.sleep(0.25)
            if pid not in _PROPIOS and i % 8 == 7: await _recuperar(pid)  # lo ejecuta otro proceso: se relee del almacen
        if TRABAJOS[pid].get("status_code") == 403:
            raise HTTPException(status_code=403, detail=TRABAJOS[pid]["error"])
        return {"status": "ok", "result": dict(TRABAJOS[pid])}
    if accion == "llm" and plugin == "fichas_qwen":  # G21: Ficha 4 -> modelo DIRECTO (contrato puente_chat llm_call); nunca via=harness
        try:
            modelo = modelos.validar(cuerpo.get("modelo") or None)
        except (ValueError, TypeError) as error:
            raise HTTPException(status_code=400, detail=str(error)) from None
        opciones = dict(cuerpo.get("opciones") or {})
        if cuerpo.get("max_tokens"):
            opciones["max_tokens"] = cuerpo["max_tokens"]
        try:
            salida = await chat({"modelo": modelo, "mensajes": cuerpo.get("messages") or cuerpo.get("mensajes"), "opciones": opciones, **_controles(cuerpo)})
        except HTTPException:
            raise
        return {"status": "ok", "result": {"reply": salida["texto"], "texto": salida["texto"], "tool_calls": salida["tool_calls"], "finish_reason": salida.get("finish_reason"), "modelo": modelo,
                                           "ficha": str(cuerpo.get("ficha_qwen") or "ficha4-workflow-yaiwes"),
                                           **{k: salida[k] for k in ("mensaje_asistente", "modelo_solicitado", "modelo_respuesta") if k in salida}}}
    if accion == "recurso_probar":  # probar un modelo o un agente del panel: una llamada real, con el tiempo que tarda
        t0 = time.monotonic()
        try:
            r = await _delegar("agente" if cuerpo.get("agente") else "llm", {"nombre": cuerpo.get("agente"), "modelo": cuerpo.get("recurso"), "mensaje": cuerpo.get("mensaje") or "Responde en una linea: que modelo eres?"})
            return {"status": "ok", "result": {"ok": True, "ms": int((time.monotonic() - t0) * 1000), "respuesta": r["texto"]}}
        except HTTPException as error:
            return {"status": "ok", "result": {"ok": False, "ms": int((time.monotonic() - t0) * 1000), "respuesta": str(error.detail)}}
    if accion in control.ACCIONES:  # IA/agentes ON/OFF (agent_access_lock, G15), herramientas, conexiones, pendientes y salas: estado del servidor, bloqueado por defecto
        return {"status": "ok", "result": await _control(accion, cuerpo)}
    raise HTTPException(status_code=400, detail="accion no soportada en mvp")
# --- G19: POST /chat/send (panel-chat.js sin harnessUrl) sobre la misma ruta Harness que chat_async; sin fallback ---
async def _chat_escalado(cuerpo, tope=440):
    """Con escalado configurado, /chat/send usa el mismo circuito (cola, destinos, registro) y espera el resultado."""
    pid = (await plugin_call("puente_chat", "chat_async", {**cuerpo, "request_id": cuerpo.get("request_id") or uuid.uuid4().hex}))["result"]["proceso_id"]
    for _ in range(tope * 2):
        if TRABAJOS[pid]["estado"] != "procesando": break
        await asyncio.sleep(0.5)
        if pid not in _PROPIOS and TRABAJOS[pid].get("destino") is None: await _recuperar(pid)
    r = TRABAJOS[pid]
    if r["estado"] == "procesando": raise HTTPException(status_code=504, detail="el trabajo sigue en curso: consulta resultado con proceso_id " + pid)
    if r["estado"] == "error": raise HTTPException(status_code=r.get("status_code") or 502, detail=r.get("error") or "error")
    return r
@app.post("/chat/send", dependencies=[Depends(verificar)])
async def chat_send(cuerpo: dict):
    t0 = time.monotonic()
    salida = await (_chat_escalado(cuerpo) if escalado.remotos() else _chat_ficha(cuerpo))  # 503 HARNESS_NO_CONFIGURADO si falta RIU_DEEPSEEK_HARNESS_URL
    msg = salida["choices"][0]["message"]
    tools = [((t.get("function") or {}).get("name") or "tool") for t in (msg.get("tool_calls") or []) if isinstance(t, dict)]
    return {"reply": msg["content"], "execution_path": "HARNESS", "ms": int((time.monotonic() - t0) * 1000),
            "tools": tools, "via": "harness", "finish_reason": salida["finish_reason"],
            "modelo_solicitado": salida.get("modelo_solicitado"), "modelo_respuesta": salida.get("modelo_respuesta"),
            **{k: salida[k] for k in ("aviso_modo", "aviso_modelo") if salida.get(k)}}
async def _delegar(nombre, args):
    """Herramientas agente/llm del modelo: una llamada nueva (sin herramientas, sin historial) al modelo del agente o al elegido."""
    if nombre == "agente":
        a = CONTROL.d["agentes"].get(str(args.get("nombre")))
        if not a: raise HTTPException(status_code=400, detail="agente desconocido: " + str(args.get("nombre"))[:40])
        modelo, sistema = a["recurso"], a.get("sistema")
    else:
        try: modelo, sistema = modelos.validar(args.get("modelo")), None
        except (ValueError, TypeError) as error: raise HTTPException(status_code=400, detail=str(error)) from None
    msgs = ([{"role": "system", "content": sistema}] if sistema else []) + [{"role": "user", "content": str(args.get("mensaje"))[:20000]}]
    salida = await _llamar_modelo(msgs, modelo, None)
    return {"agente": args.get("nombre"), "modelo": modelo, "texto": salida["texto"]}
mcp_route.montar(app, verificar, chat, almacen, CONTROL, _delegar)
# --- G5b: Harness /invoke montado en este mismo Space (HF pide PRO para un Space nuevo). Ruta: chat -> Harness -> HTTP -> router ---
from plugins.deepseek_harness.server import app as harness_app  # noqa: E402 - el Harness no importa mvp/; llm sigue por HTTP a fichas_qwen/call/llm
app.mount("/plugins/deepseek_harness", harness_app)  # RIU_DEEPSEEK_HARNESS_URL = https://<space>/plugins/deepseek_harness
