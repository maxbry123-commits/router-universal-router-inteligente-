"""Comprueba el cableado de entrada al chat: MCP (3 formas de clave) y HTTP (chat, plugins, almacen, modelos). Uso: RIU_KEY=<clave> python3 -m mvp.pruebas_vivo.conectividad [--base URL]"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://comand-center-1-riu-router.hf.space"
FILAS = []


def llamar(base, ruta, cuerpo=None, cab=None, metodo=None):
    h = {"Content-Type": "application/json", **(cab or {})}
    sol = urllib.request.Request(base + ruta, data=None if cuerpo is None else json.dumps(cuerpo).encode(), headers=h, method=metodo or ("GET" if cuerpo is None else "POST"))
    try:
        with urllib.request.urlopen(sol, timeout=120) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as exc:
        try:
            return exc.code, json.loads(exc.read() or b"{}")
        except ValueError:
            return exc.code, {}


def nota(nombre, ok, evidencia):
    FILAS.append((nombre, "PASS" if ok else "FAIL", str(evidencia)[:200]))
    print(FILAS[-1][1], nombre, "::", FILAS[-1][2], flush=True)


def esperar(base, plugin, cab, r):
    for _ in range(20):
        if r.get("estado") != "procesando":
            return r
        r = llamar(base, "/plugins/%s/call/resultado" % plugin, {"proceso_id": r["proceso_id"], "espera": 8}, cab)[1].get("result", {})
        time.sleep(0.2)
    return {"estado": "error", "error": "tiempo agotado"}


def main(argv):
    base = (argv[argv.index("--base") + 1] if "--base" in argv else BASE).rstrip("/")
    clave = os.environ.get("RIU_KEY") or sys.exit("Falta RIU_KEY (la clave de acceso del Router).")
    x, b = {"X-API-Key": clave}, {"Authorization": "Bearer " + clave}
    c, h = llamar(base, "/health"); nota("GET /health (sin clave)", c == 200 and h.get("status") == "ok", {k: h.get(k) for k in ("status", "commit")})
    lista = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
    for nombre, ruta, cab in (("MCP clave en X-API-Key", "/mcp", x), ("MCP clave en Authorization Bearer", "/mcp", b), ("MCP clave en ?key=", "/mcp?key=" + urllib.parse.quote(clave, safe=""), {})):
        c, d = llamar(base, ruta, lista, cab); nota(nombre, c == 200 and any(t["name"] == "chat" for t in d.get("result", {}).get("tools", [])), c)
    c, _ = llamar(base, "/mcp", lista, {"X-API-Key": "clave-mala"}); nota("MCP clave mala -> 401", c == 401, c)
    c, _ = llamar(base, "/mcp", lista); nota("MCP sin clave -> 401", c == 401, c)
    c, d = llamar(base, "/chat/providers/qwen/models", cab=x); nota("HTTP GET modelos", c == 200 and len(d.get("models", [])) >= 20, "%s modelos" % len(d.get("models", [])))
    c, d = llamar(base, "/plugins/fichas_qwen/call/fichas", {}, x); nota("HTTP fichas", c == 200 and d.get("result", {}).get("fichas"), c)
    for plugin in ("fichas_qwen", "puente_chat"):
        c, d = llamar(base, "/plugins/%s/call/chat_async" % plugin, {"message": "Responde solo OK", "modelo": "qwen3.8-flash", "request_id": "con-%s-%d" % (plugin, time.time())}, x)
        r = esperar(base, plugin, x, d.get("result", {})); nota("HTTP chat_async + resultado (%s)" % plugin, c == 200 and r.get("estado") == "completado", (r.get("choices") or [{}])[0].get("message", {}).get("content") or r)
    c, d = llamar(base, "/chat/send", {"message": "Responde solo OK", "model": "qwen3.8-flash"}, x); nota("HTTP /chat/send", c == 200 and bool(d.get("reply")), d.get("reply") or d)
    nombre = "chat_estado/conectividad-%d.txt" % time.time()
    c, d = llamar(base, "/almacen", {"accion": "guardar", "destino": "hf", "nombre": nombre, "valor": "ok"}, x); nota("HTTP /almacen guardar HF", c == 200 and d.get("ok"), d)
    c, d = llamar(base, "/almacen", {"accion": "leer", "destino": "hf", "nombre": nombre}, x); nota("HTTP /almacen leer HF", c == 200 and d.get("valor") == "ok", d)
    c, d = llamar(base, "/mcp", {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "chat", "arguments": {"ficha_qwen": "1", "modelo": "qwen3.8-flash", "message": "Responde solo OK", "request_id": "con-mcp-%d" % time.time()}}}, x)
    pid = (d.get("result", {}).get("structuredContent") or {}).get("proceso_id"); r = esperar(base, "fichas_qwen", x, {"estado": "procesando", "proceso_id": pid}) if pid else {}
    nota("MCP chat + resultado (mismo chat)", r.get("estado") == "completado", (r.get("choices") or [{}])[0].get("message", {}).get("content") or r)
    c, d = llamar(base, "/mcp", {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "salud", "arguments": {}}}, x)
    sal = d.get("result", {}).get("structuredContent") or {}
    nota("MCP salud (commit y modelos sin HTTP directo)", sal.get("status") == "ok" and bool(sal.get("commit")), {k: sal.get(k) for k in ("commit", "plan")})
    c, d = llamar(base, "/mcp", {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "chat", "arguments": {"ficha_qwen": "1", "modelo": "ficha-qwen38flash", "message": "Responde solo OK", "request_id": "con-alias-%d" % time.time()}}}, x)
    nota("MCP chat con nombre antiguo (ficha-qwen38flash)", bool((d.get("result", {}).get("structuredContent") or {}).get("proceso_id")), d.get("error") or "proceso creado")
    print("PASS %d / %d" % (sum(f[1] == "PASS" for f in FILAS), len(FILAS)))
    with open("conectividad.md", "w", encoding="utf-8") as f:
        f.write("| prueba | estado | evidencia |\n|---|---|---|\n" + "".join("| %s | %s | %s |\n" % (n, e, v.replace("|", "/")) for n, e, v in FILAS))


if __name__ == "__main__":
    main(sys.argv)
