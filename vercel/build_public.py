#!/usr/bin/env python3
"""vercel/build_public.py — Generador autonomo del output de Vercel.

Funciona igual con Root Directory = raiz del repo o Root Directory = vercel/,
porque Vercel siempre hace checkout del repo COMPLETO y solo cambia el cwd del
build. Por eso aqui la raiz del repo se calcula como dirname(dirname(__file__)).

Que hace:
  1. localiza el frontend canonico (chat-router/chat)
  2. lo copia a los destinos de salida:
       <root>/public      (Root Directory = raiz)
       <root>/vercel/public (Root Directory = vercel/)
  3. copia LIVE_URL.json (URL viva del router) a los destinos
  4. genera chat/ui/config.js con el Space VIVO (nunca el renombrado/muerto)

Sin dependencias externas. Idempotente. Salida verificable.
"""
import json
import os
import shutil
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))          # .../vercel
RAIZ = os.path.dirname(AQUI)                                # raiz del repo

# Cascada de origen del frontend:
#  1. chat-router/chat   (si el Root Directory es la raiz del repo)
#  2. vercel/chat        (si el Root Directory es vercel/ -> Vercel solo sube esa carpeta)
#  3. descarga desde GitHub raw (ultimo recurso, el repo es publico)
ORIGEN_LOCAL = os.path.join(RAIZ, "chat-router", "chat")
ORIGEN_EMBARCADO = os.path.join(AQUI, "chat")
RAW_BASE = ("https://raw.githubusercontent.com/maxbry123-commits/"
            "router-universal-router-inteligente-/ccr-f01c3de9-bmry0s/chat-router/chat")
ORIGEN = ORIGEN_LOCAL

# El Space vivo (el renombrado); el antiguo riu-router daba 404.
SPACE_VIVO = "https://comand-center-1-space-grupo-1-router-mvp-1.hf.space"
ESPEJOS = [
    "https://comand-center-1-space-grupo-1-router-mvp-1.hf.space",
    "https://comand-center-1-space-grupo-1-router-mvp-1-v2.hf.space",
    "https://comand-center-1-space-grupo-1-router-mvp-1-v7.hf.space",
]

CONFIG_JS = """// Generado por vercel/build_public.py - no editar a mano.
// El destino SIEMPRE es el Space vivo del Grupo 1 (nunca el renombrado/muerto).
window.RIU_CONFIG = {
  routerStopped: false,
  apiBase: '',
  liveUrl: '__LIVE__',
  harnessUrl: '',
  proxyDestino: '__ESPACIO__',
  authHeader: 'X-API-Key',
  espacios: __ESPACIOS__,
  apiTrigger: '/api/chat'
};
"""


def _live_url():
    p = os.path.join(RAIZ, "LIVE_URL.json")
    if os.path.isfile(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                d = json.load(f)
            for k in ("url", "live_url", "base_url", "proxy"):
                if isinstance(d, dict) and d.get(k):
                    return str(d[k]).rstrip("/")
        except Exception:
            pass
    return SPACE_VIVO


def _copiar_arbol(origen, destino):
    """Copia el frontend al destino con DOS layouts:
      L1  <dest>/index.html + <dest>/ui/*        (index en la raiz)
      L2  <dest>/chat/index.html + <dest>/chat/ui/*  (index dentro de chat/)
    El deployment vivo de Vercel usa L2 (su / sirve YAIWES - Organizacion y sus
    assets estan en /chat/ui/), asi que se generan los dos: asi el build vale
    con el output directory que tenga configurado el proyecto.
    """
    if os.path.isdir(destino):
        shutil.rmtree(destino)
    os.makedirs(destino, exist_ok=True)

    def _ui_de(dest_ui):
        os.makedirs(dest_ui, exist_ok=True)
        src_ui = os.path.join(origen, "ui")
        if os.path.isdir(src_ui):
            for n in os.listdir(src_ui):
                s = os.path.join(src_ui, n)
                if os.path.isfile(s):
                    shutil.copyfile(s, os.path.join(dest_ui, n))
        with open(os.path.join(dest_ui, "config.js"), "w", encoding="utf-8") as f:
            f.write(CONFIG_JS.replace("__LIVE__", _live_url())
                             .replace("__ESPACIO__", SPACE_VIVO)
                             .replace("__ESPACIOS__", json.dumps(ESPEJOS)))

    idx = os.path.join(origen, "index.html")
    # L1
    if os.path.isfile(idx):
        shutil.copyfile(idx, os.path.join(destino, "index.html"))
    _ui_de(os.path.join(destino, "ui"))
    # L2
    chat = os.path.join(destino, "chat")
    os.makedirs(chat, exist_ok=True)
    if os.path.isfile(idx):
        shutil.copyfile(idx, os.path.join(chat, "index.html"))
    _ui_de(os.path.join(chat, "ui"))
    # URL viva del router
    live = os.path.join(RAIZ, "LIVE_URL.json")
    if os.path.isfile(live):
        shutil.copyfile(live, os.path.join(destino, "LIVE_URL.json"))
    return len(os.listdir(destino))


def _descargar_origen(destino):
    """Ultimo recurso: baja el frontend canonico desde GitHub raw (repo publico)."""
    import urllib.request
    ficheros = ["index.html", "sdk.html", "http-mcp.html", "propuestas.html"]
    os.makedirs(os.path.join(destino, "ui"), exist_ok=True)
    ui = ["app.css", "theme.css", "ui-controller.js", "model-selector.js", "loop.js",
          "cola-panel.html", "hermes-panel.html", "hitl-panel.html", "loop-panel.html",
          "mindmap-panel.html", "motion-panel.html", "openclaw-panel.html",
          "watchdog-panel.html"]
    for n in ficheros:
        with urllib.request.urlopen(RAW_BASE + "/" + n, timeout=45) as r:
            open(os.path.join(destino, n), "wb").write(r.read())
    for n in ui:
        try:
            with urllib.request.urlopen(RAW_BASE + "/ui/" + n, timeout=45) as r:
                open(os.path.join(destino, "ui", n), "wb").write(r.read())
        except Exception as e:
            print("  aviso: no se pudo bajar ui/%s (%s)" % (n, e))
    return destino


def main():
    global ORIGEN
    if os.path.isdir(ORIGEN_LOCAL):
        ORIGEN = ORIGEN_LOCAL
        print("origen: chat-router/chat (repo completo)")
    elif os.path.isdir(ORIGEN_EMBARCADO):
        ORIGEN = ORIGEN_EMBARCADO
        print("origen: vercel/chat (embarcado en el Root Directory)")
    else:
        ORIGEN = os.path.join(AQUI, "_chat_descargado")
        print("origen: descarga desde GitHub raw")
        try:
            _descargar_origen(ORIGEN)
        except Exception as e:
            print("FATAL: no se pudo obtener el frontend:", e)
            sys.exit(1)
    if not os.path.isdir(ORIGEN):
        print("FATAL: no existe el frontend canonico:", ORIGEN)
        sys.exit(1)
    # Se escribe en TODOS los destinos plausibles: asi el build de Vercel
    # funciona con cualquier Root Directory (raiz, vercel/, chat-router/) y con
    # cualquier Output Directory (public, dist, build, out).
    candidatos = [
        os.path.join(AQUI, "public"), os.path.join(AQUI, "dist"),
        os.path.join(AQUI, "build"), os.path.join(AQUI, "out"),
        os.path.join(RAIZ, "public"), os.path.join(RAIZ, "dist"),
        os.path.join(RAIZ, "build"), os.path.join(RAIZ, "out"),
        os.path.join(RAIZ, "chat-router", "public"),
    ]
    hechos = []
    for d in candidatos:
        try:
            n = _copiar_arbol(ORIGEN, d)
            hechos.append((d, n))
        except Exception as e:
            print("  aviso: no se pudo escribir", d, "->", type(e).__name__, e)
    if not hechos:
        print("FATAL: ningun destino se pudo escribir")
        sys.exit(1)
    for d, n in hechos:
        print("OK  %s  (%d entradas)" % (d, n))
    print("space vivo:", SPACE_VIVO)
    print("live url  :", _live_url())


if __name__ == "__main__":
    main()
