import os, sys, tempfile, shutil, re, uvicorn
RAIZ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, RAIZ)
os.environ.update(RIU_API_KEY="api-e2e", MVP_MCP_LOCAL="1", RIU_DEEPSEEK_HARNESS_URL="http://127.0.0.1:8765/plugins/deepseek_harness", RIU_ROUTER_URL="http://127.0.0.1:8765")
SRC = os.environ.get("FRONT_SRC", os.path.join(RAIZ, "plugins", "chat-router", "frontend"))
DST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chat_ui")
shutil.rmtree(DST, ignore_errors=True); shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns("yaiwes"))
import subprocess
subprocess.run(["sh","build.sh"],cwd=DST,env={**os.environ,"VERCEL_GIT_COMMIT_SHA":"54c8815ea0d2"},check=True)  # igual que Vercel
a = open(DST + "/api.js", encoding="utf-8").read()
a = a.replace("const VALIDA = (u) => /^https:\\/\\/[a-z0-9-]+\\.hf\\.space$/.test(u || '');", "const VALIDA = (u) => /^http:\\/\\/127\\.0\\.0\\.1:8765$/.test(u || '');")
open(DST + "/api.js", "w", encoding="utf-8").write(a)
c = open(DST + "/config.js", encoding="utf-8").read().replace("https://comand-center-1-riu-router.hf.space", "http://127.0.0.1:8765")
open(DST + "/config.js", "w", encoding="utf-8").write(c)
from mvp import bank, app as servicio
from fastapi.staticfiles import StaticFiles
nube = {}
def guardar(k, n, v): nube[n] = v; return {"ok": True}
def leer(k, n):
    if n not in nube: raise servicio.hf_store.NoExiste("fallo de lectura HF")
    return {"ok": True, "valor": nube[n]}
servicio.hf_store.guardar, servicio.hf_store.leer = guardar, leer
d = tempfile.mkdtemp()
b = bank.abrir(d + "/b.bin", "api-e2e"); b.guardar("HF_TOKEN", "hf-x"); b.guardar("GITHUB_TOKEN", "gh-x"); b.guardar("RIU_API_KEY", "api-e2e")
servicio.app.state.banco = b
b.guardar("QWEN_API_KEY", "q-x")
LARGO = ("## Respuesta de prueba\n\n" + "Este es un párrafo largo para comprobar que la salida no se corta ni se estrecha. " * 12 + "\n\n```python\ndef saludar(nombre):\n    return 'hola ' + nombre + ' ' * 3 + 'esta línea de código es bastante larga para forzar el scroll horizontal del bloque'\n```\n\n" + "- punto uno\n- punto dos\n- punto tres\n\n" + "Fin de la respuesta.")
def falso(mensajes, modelo, base, clave, opciones=None):
    if "modelo eres" in str(mensajes[-1].get("content")):  # identidad: lo que diga el system que va JUSTO antes del mensaje
        ident = str(mensajes[-2].get("content")) if len(mensajes) > 1 and mensajes[-2].get("role") == "system" else "sin identidad"
        import re as _re; m = _re.search(r"Modelo activo: ([^ ,]+)", ident)
        return {"texto": "Soy " + (m.group(1) if m else "DESCONOCIDO"), "tool_calls": [], "finish_reason": "stop", "modelo_respuesta": modelo, "modelo_solicitado": modelo}
    if any(m.get("role") == "system" and "AGENTE_OK" in str(m.get("content")) for m in mensajes if isinstance(m, dict)):
        return {"texto": "agente respondio con " + modelo, "tool_calls": [], "finish_reason": "stop", "modelo_respuesta": modelo, "modelo_solicitado": modelo}
    if any("mediotest" in str(m.get("content")) for m in mensajes if isinstance(m, dict)):
        return {"texto": "Aqui esta [[imagen:https://example.com/x.png]] y [[video:https://example.com/v.mp4]] listo", "tool_calls": [], "finish_reason": "stop", "modelo_respuesta": modelo, "modelo_solicitado": modelo}
    corto = any("corta" in str(m.get("content")) for m in mensajes if isinstance(m, dict))
    return {"texto": LARGO[:600] if corto else LARGO, "tool_calls": [], "finish_reason": "length" if corto else "stop", "modelo_respuesta": modelo, "modelo_solicitado": modelo}
servicio.compute.llamar = falso
os.environ["GROQ_API_KEY"] = "gsk-e2e"
servicio.externos._get = lambda url, k: {"data": [{"id": "llama-3.3-70b-versatile"}, {"id": "openai/gpt-oss-120b"}, {"id": "whisper-large-v3"}]}
_sol = servicio.compute._solicitar
def _sol_falso(url, payload, clave):
    if "groq.com" in url:
        r = falso(payload["messages"], payload["model"], None, None)
        texto = ("Soy " + payload["model"] + " en Groq") if "modelo eres" in str(payload["messages"][-1].get("content")) else r["texto"]
        return {"model": payload["model"], "choices": [{"message": {"content": texto, "tool_calls": r["tool_calls"] or None}, "finish_reason": r["finish_reason"]}]}
    return _sol(url, payload, clave)
servicio.compute._solicitar = _sol_falso
@servicio.asynccontextmanager
async def vida(app): yield
servicio.app.router.lifespan_context = vida
from fastapi.responses import FileResponse
@servicio.app.get("/chat/ui/{ruta:path}")
def ui(ruta: str):
    p = os.path.join(DST, ruta or "shell.html")
    if not os.path.isfile(p): p = os.path.join(DST, "shell.html")
    return FileResponse(p)
POWER = {"stage": "RUNNING"}  # mismo contrato que api/power.js (la función real se prueba con node --test)
from fastapi import Request
from fastapi.responses import JSONResponse
@servicio.app.api_route("/api/power", methods=["GET", "POST"])
async def power(req: Request):
    if req.headers.get("x-api-key") != "api-e2e": return JSONResponse({"detail": "clave de acceso invalida"}, 401)
    if req.method == "POST":
        a = (await req.json()).get("accion")
        if a not in ("encender", "apagar", "reiniciar"): return JSONResponse({"detail": "accion"}, 400)
        POWER["stage"] = "PAUSED" if a == "apagar" else "RUNNING"
        return {"accion": a, "stage": "BUILDING" if a != "apagar" else "PAUSED", "hardware": "cpu-basic"}
    return {"accion": "estado", "stage": POWER["stage"], "hardware": "cpu-basic"}
uvicorn.run(servicio.app, host="127.0.0.1", port=8765, log_level="warning")
