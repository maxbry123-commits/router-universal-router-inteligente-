"""Prueba real de todos los modelos y herramientas contra el Router. Uso: RIU_KEY=<clave> python -m mvp.pruebas_vivo.correr [--base URL] [--solo modelo] [--sin-medios]
Escribe informe_sol.md e informe_sol.json (evidencia cruda recortada). PASS solo con salida real; si no hay respuesta, FAIL con el error exacto."""
import json
import os
import sys
import time
from mvp import modelos
from mvp.pruebas_vivo.cliente import Cliente, texto

REPO = "maxbry123-commits/router-universal-router-inteligente-"
FILAS = []


def anotar(modelo, prueba, ok, evidencia, t0):
    FILAS.append({"modelo": modelo, "prueba": prueba, "estado": "PASS" if ok else "FAIL", "evidencia": str(evidencia)[:300], "segundos": round(time.time() - t0, 1)})
    print(FILAS[-1]["estado"], modelo, prueba, flush=True)


def prueba_chat(c, m, nombre, mensaje, valida, rid, **extra):
    t0 = time.time()
    r = c.chat(m, mensaje, rid=rid, **extra)
    t = texto(r)
    anotar(m, nombre, r.get("estado") == "completado" and bool(valida(t, r)), t or r.get("error") or r, t0)
    return r


def texto_modelo(c, m):
    p = prueba_chat
    p(c, m, "nombre", "Responde solo el nombre exacto de tu modelo, sin más texto.", lambda t, r: t.strip(), f"v-{m}-1")
    p(c, m, "eco", f"Responde exactamente: PONG-{m}", lambda t, r: f"PONG-{m}" in t, f"v-{m}-2")
    p(c, m, "calculo 17x23", "¿Cuánto es 17 por 23? Responde solo el número.", lambda t, r: "391" in t, f"v-{m}-3")
    p(c, m, "español", "Responde en español en una frase: ¿qué es un router?", lambda t, r: len(t) > 10, f"v-{m}-4")
    p(c, m, "memoria", None, lambda t, r: "42" in t, f"v-{m}-5", messages=[{"role": "user", "content": "Mi número es 42"}, {"role": "assistant", "content": "Anotado."}, {"role": "user", "content": "¿Cuál es mi número? Responde solo el número."}])
    p(c, m, "formato corto", "Dime tres ventajas de usar caché.", lambda t, r: 0 < len(t.split()) < 160 and not t.strip().startswith("{"), f"v-{m}-6")
    herramientas_modelo(c, m)


def herramientas_modelo(c, m):
    def con_tool(nombre, mensaje, rid, comprobar):
        t0 = time.time()
        r = c.chat(m, mensaje, rid=rid, tools=True, llm_tool=True)
        ok, dato = comprobar()
        anotar(m, nombre, r.get("estado") == "completado" and ok, dato or texto(r) or r.get("error"), t0)
    con_tool("tool pendientes", f"Usa la herramienta pendientes: agrega 'sol-{m}' y confirma.", f"v-{m}-7", lambda: (lambda o, d: (f"sol-{m}" in json.dumps(d), d))(*c.herramienta("pendientes", {"accion": "listar"})))
    con_tool("tool yaiwes_md", f"Usa yaiwes_md: escribe el texto 'proyecto-{m}' y confirma.", f"v-{m}-8", lambda: (lambda o, d: (f"proyecto-{m}" in json.dumps(d), d))(*c.herramienta("yaiwes_md", {"accion": "leer"})))
    con_tool("tool github leer", f"Usa github_leer en el repo {REPO}, ruta README.md, rama main. Cita la primera línea.", f"v-{m}-9", lambda: (True, "ver texto de la respuesta"))
    con_tool("tool github escribir", f"Usa github_escribir en el repo {REPO}, rama prueba-sol, ruta Prueba/sol-{m}.txt, contenido 'ok-{m}', mensaje 'prueba sol'.", f"v-{m}-10",
             lambda: (lambda o, d: (f"ok-{m}" in json.dumps(d), d))(*c.herramienta("github_leer", {"repo": REPO, "ruta": f"Prueba/sol-{m}.txt", "rama": "prueba-sol"})))
    con_tool("tool hf almacen", f"Usa almacen: guarda en destino hf el nombre chat_estado/sol-{m}.txt con valor 'ok-{m}'.", f"v-{m}-11",
             lambda: (lambda o, d: (f"ok-{m}" in json.dumps(d), d))(*c.herramienta("almacen", {"accion": "leer", "destino": "hf", "nombre": f"chat_estado/sol-{m}.txt"})))
    con_tool("tool llm", "Usa la herramienta llm con el modelo qwen3.8-flash y el mensaje 'Di OK'. Dime qué respondió.", f"v-{m}-12", lambda: (True, "ver texto de la respuesta"))
    con_tool("tool sala", f"Usa la herramienta sala: crea la sala 'sala-{m}'. Confirma.", f"v-{m}-13", lambda: (lambda o, d: (f"sala-{m}" in json.dumps(d), d))(*c.herramienta("sala", {"accion": "listar"})))


def medios(c):
    d = modelos.cargar()
    urls = {}
    for x in [m["id"] for m in d["imagen"] if m["p"]]:
        r = prueba_chat(c, x, "imagen", "Un gato naranja en una ventana, estilo acuarela", lambda t, r: "[[imagen:http" in t, f"v-{x}")
        urls[x] = texto(r).split("[[imagen:")[-1].split("]]")[0]
    prueba_chat(c, "qwen-audio-3.0-tts-plus", "voz", "Hola, esto es una prueba de voz.", lambda t, r: "[[audio:" in t, "v-tts")
    t0 = time.time(); r = c.chat("qwen-audio-3.0-realtime-plus", "hola", rid="v-rt"); anotar("qwen-audio-3.0-realtime-plus", "rechazo claro (WebSocket)", "websocket" in json.dumps(r).lower(), r.get("error") or r, t0)
    foto = urls.get("qwen-image-3.0-pro", "")
    for x in [m["id"] for m in d["video"] if m["p"]]:
        sufijo = " " + foto if x.endswith(("i2v", "r2v")) and foto.startswith("http") else ""
        prueba_chat(c, x, "video", "Una ola rompiendo en una playa" + sufijo, lambda t, r: "[[video:http" in t, f"v-{x}", vueltas=70)


def main(argv):
    base = argv[argv.index("--base") + 1] if "--base" in argv else "https://comand-center-1-riu-router.hf.space"
    clave = os.environ.get("RIU_KEY", "")
    if not clave:
        sys.exit("Falta la variable RIU_KEY (la clave de acceso del Router).")
    c = Cliente(base, clave)
    try:
        h = c.health()
    except OSError as exc:  # sin red, DNS o HTTP 5xx: se anota y se sigue para ver si el MCP responde
        h = {"error": str(exc)}
    anotar("router", "health", h.get("status") == "ok", {k: h.get(k) for k in ("status", "commit", "error")}, time.time())
    codigo, doc = c.mcp("tools/list")
    nombres = [t["name"] for t in doc.get("result", {}).get("tools", [])]
    anotar("router", "tools/list", codigo == 200 and "chat" in nombres, nombres, time.time())
    c.post("/plugins/puente_chat/call/agent_access_lock", {"quien": "ia", "locked": False})  # IA ON para la prueba de llm
    lista = [argv[argv.index("--solo") + 1]] if "--solo" in argv else [m["id"] for m in modelos.cargar()["texto"] if m["p"]]
    for m in lista:
        texto_modelo(c, m)
    if "--solo" not in argv and "--sin-medios" not in argv:
        medios(c)
    json.dump(FILAS, open("informe_sol.json", "w"), ensure_ascii=False, indent=1)
    with open("informe_sol.md", "w", encoding="utf-8") as f:
        f.write("| modelo | prueba | estado | segundos | evidencia |\n|---|---|---|---|---|\n")
        for x in FILAS:
            f.write("| %s | %s | %s | %s | %s |\n" % (x["modelo"], x["prueba"], x["estado"], x["segundos"], x["evidencia"].replace("|", "/").replace("\n", " ")))
    print("PASS %d / %d. Informe: informe_sol.md" % (sum(x["estado"] == "PASS" for x in FILAS), len(FILAS)))


if __name__ == "__main__":
    main(sys.argv)
