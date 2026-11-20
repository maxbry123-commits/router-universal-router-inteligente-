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
ORIGEN = os.path.join(RAIZ, "chat-router", "chat")

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
    if os.path.isdir(destino):
        shutil.rmtree(destino)
    shutil.copytree(origen, destino)
    # el index publico es el chat
    idx = os.path.join(origen, "index.html")
    if os.path.isfile(idx):
        shutil.copyfile(idx, os.path.join(destino, "index.html"))
    # config del frontend con el Space vivo
    ui = os.path.join(destino, "ui")
    os.makedirs(ui, exist_ok=True)
    with open(os.path.join(ui, "config.js"), "w", encoding="utf-8") as f:
        f.write(CONFIG_JS.replace("__LIVE__", _live_url())
                         .replace("__ESPACIO__", SPACE_VIVO)
                         .replace("__ESPACIOS__", json.dumps(ESPEJOS)))
    # URL viva del router
    live = os.path.join(RAIZ, "LIVE_URL.json")
    if os.path.isfile(live):
        shutil.copyfile(live, os.path.join(destino, "LIVE_URL.json"))
    return len(os.listdir(destino))


def main():
    if not os.path.isdir(ORIGEN):
        print("FATAL: no existe el frontend canonico:", ORIGEN)
        sys.exit(1)
    destinos = [os.path.join(AQUI, "public"), os.path.join(RAIZ, "public")]
    hechos = []
    for d in destinos:
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
