#!/usr/bin/env python3
"""revivir_url_riu.py — Revive la URL que usa el owner:
   https://comand-center-1-riu-router.hf.space/
   ese hostname quedo huerfano cuando el Space "riu-router" fue renombrado a
   "space-grupo-1-router-mvp-1" (reorganizacion de los 6 Spaces).

Dos vias, en este orden:
  A) ALIAS en HF:  alias "riu-router" sobre el Space vivo.
     -> el hostname vuelve a existir y apunta al Space VIVO (sin tocar nada mas).
  B) SPACE PUENTE: si el alias no genera hostname, se crea un Space diminuto
     llamado "riu-router" que responde 307 hacia el Space vivo.
     -> mismo resultado para el usuario, un Space mas (coste ~0 si duerme).

REQUIERE: HF_TOKEN (variable de entorno). Sin token: sale sin tocar nada.
"""
import os
import sys

SPACE_VIVO = "COMAND-CENTER-1/space-grupo-1-router-mvp-1"
ALIAS = "riu-router"
HOSTNAME_VIEJO = "https://comand-center-1-riu-router.hf.space/chat/"


def main():
    token = os.environ.get("HF_TOKEN") or os.environ.get("HF_TOKEN_1_NEW") or ""
    if not token:
        print("FATAL: falta HF_TOKEN en el entorno (no se hace nada).")
        sys.exit(2)
    try:
        from huggingface_hub import HfApi
    except Exception as e:
        print("FATAL: huggingface_hub no disponible:", e)
        sys.exit(2)
    api = HfApi(token=token)

    # ---- A) ALIAS ----
    try:
        api.create_alias(repo_id=SPACE_VIVO, alias=ALIAS, repo_type="space")
        print("A) alias '%s' creado sobre %s" % (ALIAS, SPACE_VIVO))
        print("   comprueba: https://huggingface.co/spaces/%s/%s" % ("COMAND-CENTER-1", ALIAS))
        print("   y el hostname: %s" % HOSTNAME_VIEJO)
        return 0
    except Exception as e:
        print("A) alias NO disponible: %s: %s" % (type(e).__name__, str(e)[:160]))
        print("   -> se pasa a la via B (Space puente)")

    # ---- B) SPACE PUENTE ----
    try:
        api.create_repo(repo_id="COMAND-CENTER-1/%s" % ALIAS, repo_type="space",
                        space_sdk="docker", private=True)
        print("B) Space puente creado: COMAND-CENTER-1/%s" % ALIAS)
    except Exception as e:
        if "already exists" in str(e).lower() or "409" in str(e):
            print("B) el Space puente ya existe")
        else:
            print("B) no se pudo crear el puente: %s: %s" % (type(e).__name__, str(e)[:160]))
            return 1

    # contenido minimo: responde 307 al Space vivo
    dockerfile = """FROM python:3.11-slim
WORKDIR /app
COPY puente.py /app/puente.py
EXPOSE 7860
CMD ["python3","/app/puente.py"]
"""
    puente = '''"""puente.py — Space puente: devuelve 307 hacia el Space vivo del router.
Su unico trabajo es que el hostname historique (comand-center-1-riu-router.hf.space)
vuelva a existir y lleve al chat real."""
import http.server, socketserver, urllib.parse

VIVO = "https://comand-center-1-space-grupo-1-router-mvp-1.hf.space"


class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        destino = VIVO + self.path
        self.send_response(307)
        self.send_header("Location", destino)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n:
            self.rfile.read(n)
        destino = VIVO + self.path
        self.send_response(307)
        self.send_header("Location", destino)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, *a):
        pass


socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("0.0.0.0", 7860), H) as httpd:
    httpd.serve_forever()
'''
    readme = """---
title: Puente RIU (compatibilidad de hostname)
emoji: 🔗
colorFrom: gray
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# Puente RIU

Este Space existe solo para que el hostname historico
`https://comand-center-1-riu-router.hf.space/` siga existiendo: responde 307
hacia el Space vivo del router (`space-grupo-1-router-mvp-1`).
"""
    for nombre, contenido in (("Dockerfile", dockerfile), ("puente.py", puente), ("README.md", readme)):
        try:
            api.upload_file(path_or_fileobj=contenido.encode(), path_in_repo=nombre,
                            repo_id="COMAND-CENTER-1/%s" % ALIAS, repo_type="space",
                            commit_message="puente de hostname hacia el Space vivo")
            print("   subido:", nombre)
        except Exception as e:
            print("   NO se pudo subir %s: %s" % (nombre, str(e)[:120]))

    try:
        api.set_space_sleep_time(repo_id="COMAND-CENTER-1/%s" % ALIAS, seconds=172800)
        print("   sleep: 172800 s (48 h, el valor por defecto de inactividad de HF)")
    except Exception as e:
        print("   aviso con sleep:", str(e)[:120])

    print("B) listo. Comprueba: %s" % HOSTNAME_VIEJO)
    return 0


if __name__ == "__main__":
    sys.exit(main())
