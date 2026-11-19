#!/usr/bin/env python3
"""Copia el frontend del chat (chat-router/chat) a public/ para Vercel.

El chat se sirve como estatico desde Vercel (sin CPU) y llama a /api/chat
(la funcion serverless), que es la que despierta los Spaces del router.
"""
import os, shutil, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGEN = os.path.join(RAIZ, "chat-router", "chat")
DESTINO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")

if not os.path.isdir(ORIGEN):
    print("no existe", ORIGEN); sys.exit(1)
if os.path.isdir(DESTINO):
    shutil.rmtree(DESTINO)
shutil.copytree(ORIGEN, DESTINO)
# el index publico es el chat
shutil.copyfile(os.path.join(ORIGEN, "index.html"), os.path.join(DESTINO, "index.html"))
print("public/ listo:", len(os.listdir(DESTINO)), "entradas")
