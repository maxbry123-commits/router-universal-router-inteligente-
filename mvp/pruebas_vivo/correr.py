"""Prueba real de todos los modelos y herramientas contra el Router. Uso: RIU_KEY=<clave> python3 -m mvp.pruebas_vivo.correr [--base URL] [--solo modelo] [--sin-medios] [--medios] [--video]
Escribe informe_sol.md e informe_sol.json (evidencia cruda recortada, se actualiza tras cada prueba). PASS solo con salida real; sin respuesta, FAIL con el error exacto."""
import os
import sys
import time
from mvp import modelos
from mvp.pruebas_vivo import pruebas
from mvp.pruebas_vivo.cliente import Cliente
from mvp.pruebas_vivo.limpiar import limpiar


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
    pruebas.anotar("router", "health", h.get("status") == "ok", {k: h.get(k) for k in ("status", "commit", "error")}, time.time())
    codigo, doc = c.mcp("tools/list")
    nombres = [t["name"] for t in doc.get("result", {}).get("tools", [])]
    pruebas.anotar("router", "tools/list", codigo == 200 and "chat" in nombres, nombres, time.time())
    c.post("/plugins/puente_chat/call/agent_access_lock", {"quien": "ia", "locked": False})  # IA ON para la prueba de llm
    lista = [argv[argv.index("--solo") + 1]] if "--solo" in argv else [] if "--medios" in argv else [m["id"] for m in modelos.cargar()["texto"] if m["p"]]
    try:
        for m in lista:
            pruebas.texto_modelo(c, m)
        if ("--solo" not in argv and "--sin-medios" not in argv) or "--medios" in argv:
            pruebas.medios(c)
    finally:
        print("Limpieza de datos de prueba:", limpiar(c)[1] or "nada")  # los pendientes sol-* y el yaiwes.md de prueba no deben quedar en el chat real
    print("PASS %d / %d. Informe: informe_sol.md" % (sum(x["estado"] == "PASS" for x in pruebas.FILAS), len(pruebas.FILAS)))


if __name__ == "__main__":
    main(sys.argv)
