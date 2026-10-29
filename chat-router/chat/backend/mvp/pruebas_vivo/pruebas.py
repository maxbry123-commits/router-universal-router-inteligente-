"""Las pruebas (texto, herramientas y medios). Cada una anota PASS/FAIL con la evidencia cruda recortada."""
import json
import sys
import time
from mvp import modelos
from mvp.pruebas_vivo.cliente import texto

REPO = "maxbry123-commits/router-universal-router-inteligente-"
FILAS = []
CORRIDA = time.strftime("%d%H%M%S")  # cada corrida usa request_id propios: con el mismo request_id el Router devuelve el resultado guardado y no vuelve a ejecutar (idempotencia)


def escribir_informe():
    json.dump(FILAS, open("informe_sol.json", "w"), ensure_ascii=False, indent=1)
    with open("informe_sol.md", "w", encoding="utf-8") as f:
        f.write("| modelo | prueba | estado | segundos | evidencia |\n|---|---|---|---|---|\n")
        for x in FILAS:
            f.write("| %s | %s | %s | %s | %s |\n" % (x["modelo"], x["prueba"], x["estado"], x["segundos"], x["evidencia"].replace("|", "/").replace("\n", " ")))


def anotar(modelo, prueba, ok, evidencia, t0):
    FILAS.append({"modelo": modelo, "prueba": prueba, "estado": "PASS" if ok else "FAIL", "evidencia": str(evidencia)[:300], "segundos": round(time.time() - t0, 1)})
    print(FILAS[-1]["estado"], modelo, prueba, flush=True)
    escribir_informe()  # el informe parcial siempre esta al dia: si se corta a mitad no se pierde evidencia


def prueba_chat(c, m, nombre, mensaje, valida, rid, **extra):
    t0 = time.time()
    r = c.chat(m, mensaje, rid=CORRIDA + rid, **extra)
    t = texto(r)
    anotar(m, nombre, r.get("estado") == "completado" and bool(valida(t, r)), t or r.get("error") or r, t0)
    return r


def con_tool(c, m, nombre, mensaje, rid, comprobar):
    t0 = time.time()
    r = c.chat(m, mensaje, rid=CORRIDA + rid, tools=True, llm_tool=True)
    try:
        ok, dato = comprobar()
    except Exception as exc:  # un fallo al comprobar es FAIL de esa prueba, nunca corta la corrida
        ok, dato = False, "la comprobacion fallo: %r" % exc
    anotar(m, nombre, r.get("estado") == "completado" and ok, "chat=%s %s | usadas=%s | respuesta=%s | comprobacion=%s" % (r.get("estado"), r.get("error") or "", r.get("herramientas_usadas"), texto(r)[:120], dato), t0)  # evidencia completa: estado del chat, lo que dijo el modelo y lo que quedo guardado


def contiene(c, herramienta, args, esperado):
    return lambda: (lambda o, d: (esperado in json.dumps(d), d))(*c.herramienta(herramienta, args))


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
    con_tool(c, m, "tool pendientes", f"Usa la herramienta pendientes: agrega 'sol-{m}' y confirma.", f"v-{m}-7", contiene(c, "pendientes", {"accion": "listar"}, f"sol-{m}"))
    con_tool(c, m, "tool yaiwes_md", f"Usa yaiwes_md: escribe el texto 'proyecto-{m}' y confirma.", f"v-{m}-8", contiene(c, "yaiwes_md", {"accion": "leer"}, f"proyecto-{m}"))
    con_tool(c, m, "tool github leer", f"Usa github_leer en el repo {REPO}, ruta docs/README.md, rama main. Cita la primera línea.", f"v-{m}-9", lambda: (True, "ver texto de la respuesta"))
    if not any(f["prueba"] == "tool github escribir" for f in FILAS):  # una sola vez, y en main (el Harness no permite otra rama): Prueba/sol-escritura.txt
        con_tool(c, m, "tool github escribir", f"Usa github_escribir en el repo {REPO}, rama main, ruta Prueba/sol-escritura.txt, contenido 'ok-{m}', mensaje 'prueba sol'.", f"v-{m}-10",
                 contiene(c, "github_leer", {"repo": REPO, "ruta": "Prueba/sol-escritura.txt", "rama": "main"}, f"ok-{m}"))
    con_tool(c, m, "tool hf almacen", f"Usa almacen: guarda en destino hf el nombre chat_estado/sol-{m}.txt con valor 'ok-{m}'.", f"v-{m}-11",
             contiene(c, "almacen", {"accion": "leer", "destino": "hf", "nombre": f"chat_estado/sol-{m}.txt"}, f"ok-{m}"))
    con_tool(c, m, "tool llm", "Usa la herramienta llm con el modelo qwen3.8-flash y el mensaje 'Di OK'. Dime qué respondió.", f"v-{m}-12", lambda: (True, "ver texto de la respuesta"))
    con_tool(c, m, "tool sala", f"Usa la herramienta sala: crea la sala 'sala-{m}'. Confirma.", f"v-{m}-13", contiene(c, "sala", {"accion": "listar"}, f"sala-{m}"))


def medios(c):
    d, urls = modelos.cargar(), {}
    for x in [m["id"] for m in d["imagen"] if m["p"]]:
        r = prueba_chat(c, x, "imagen", "Un gato naranja en una ventana, estilo acuarela", lambda t, r: "[[imagen:http" in t, f"v-{x}")
        urls[x] = texto(r).split("[[imagen:")[-1].split("]]")[0]
    prueba_chat(c, "qwen-audio-3.0-tts-plus", "voz", "Hola, esto es una prueba de voz.", lambda t, r: "[[audio:" in t, "v-tts")
    t0 = time.time()
    r = c.chat("qwen-audio-3.0-realtime-plus", "hola", rid=CORRIDA + "v-rt")
    anotar("qwen-audio-3.0-realtime-plus", "rechazo claro (WebSocket)", "websocket" in json.dumps(r).lower(), r.get("error") or r, t0)
    if "--video" not in sys.argv:
        return  # el video es lento y caro (hasta 9 min por modelo): solo con --video
    foto = urls.get("qwen-image-3.0-pro", "")
    for x in [m["id"] for m in d["video"] if m["p"]]:
        sufijo = " " + foto if x.endswith(("i2v", "r2v")) and foto.startswith("http") else ""
        prueba_chat(c, x, "video", "Una ola rompiendo en una playa" + sufijo, lambda t, r: "[[video:http" in t, f"v-{x}", vueltas=70)
