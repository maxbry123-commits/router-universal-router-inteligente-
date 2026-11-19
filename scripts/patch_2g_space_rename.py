#!/usr/bin/env python3
"""patch_2g_space_rename.py — MINIMAX 2G · renombra los 6 Spaces en MI cableado.

El 2026-07-18 los 6 Spaces del router se renombraron en Hugging Face (move_repo):
  Grupo 1 (compute): local-llm-router{,-v2,-v7}    -> space-grupo-1-router-mvp-1{,-v2,-v7}
  Grupo 2 (LLM local): swe-code-s{1,2,3}            -> space-grupo-2-router-llm-hf-{1,2,3}
Los nombres viejos quedan RETIRADOS (404) segun external/core/space_inventory.py
(commit dd158a420). Mi cableado (chat, selector, registro de agentes y proxy)
tenia las URLs viejas -> el chat apuntaria a Spaces que ya no existen.

Este script actualiza SOLO mis 4 ficheros, con reemplazo literal y sin tocar
nada mas. Es idempotente: si ya no hay nada que cambiar, no escribe.

Salida: una linea por fichero con el numero de sustituciones. RC 0 siempre
(es un parche de texto, la validacion la hace validate_2f.py).
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# (viejo, nuevo) — se aplican EN ORDEN: los prefijos mas largos primero
# para que "local-llm-router-v2" no se coma "local-llm-router".
REEMPLAZOS = (
    ("comand-center-1-local-llm-router-v7.hf.space", "comand-center-1-space-grupo-1-router-mvp-1-v7.hf.space"),
    ("comand-center-1-local-llm-router-v2.hf.space", "comand-center-1-space-grupo-1-router-mvp-1-v2.hf.space"),
    ("comand-center-1-local-llm-router.hf.space", "comand-center-1-space-grupo-1-router-mvp-1.hf.space"),
    ("comand-center-1-swe-code-s1.hf.space", "comand-center-1-space-grupo-2-router-llm-hf-1.hf.space"),
    ("comand-center-1-swe-code-s2.hf.space", "comand-center-1-space-grupo-2-router-llm-hf-2.hf.space"),
    ("comand-center-1-swe-code-s3.hf.space", "comand-center-1-space-grupo-2-router-llm-hf-3.hf.space"),
)

FICHEROS = (
    "chat-router/chat/index.html",
    "chat-router/chat/ui/model-selector.js",
    "router_llm_hf/AGENTS_REGISTRY.json",
    "ROUTER MVP v1/system_prompt_py/openai_compatible_proxy.py",
)

# El proxy construye la URL con el NOMBRE del Space (no con la URL entera):
#   url = f"https://comand-center-1-{space}.hf.space/v1/chat/completions"
# asi que ahi bastan los nombres sueltos (sin host).
NOMBRES_SUELTOS = (
    ('"swe-code-s1"', '"space-grupo-2-router-llm-hf-1"'),
    ('"swe-code-s2"', '"space-grupo-2-router-llm-hf-2"'),
    ('"swe-code-s3"', '"space-grupo-2-router-llm-hf-3"'),
)

# Prosa del registro que citaba el Space viejo por su nombre.
TEXTO = (
    ("Space local-llm-router tenga saldo", "Space space-grupo-1-router-mvp-1 tenga saldo"),
    ("Space local-llm-router-v2 tenga saldo", "Space space-grupo-1-router-mvp-1-v2 tenga saldo"),
    ("Space local-llm-router-v7 tenga saldo", "Space space-grupo-1-router-mvp-1-v7 tenga saldo"),
)


def main() -> int:
    total = 0
    for rel in FICHEROS:
        ruta = REPO / rel
        if not ruta.exists():
            print(f"FALTA  {rel} (no existe)")
            continue
        src = ruta.read_text(encoding="utf-8")
        dst = src
        n = 0
        for viejo, nuevo in REEMPLAZOS:
            n += dst.count(viejo)
            dst = dst.replace(viejo, nuevo)
        if ruta.name == "openai_compatible_proxy.py":
            for viejo, nuevo in NOMBRES_SUELTOS:
                n += dst.count(viejo)
                dst = dst.replace(viejo, nuevo)
        if ruta.name == "AGENTS_REGISTRY.json":
            for viejo, nuevo in TEXTO:
                n += dst.count(viejo)
                dst = dst.replace(viejo, nuevo)
        if dst != src:
            ruta.write_text(dst, encoding="utf-8")
        total += n
        print(f"{'OK   ' if n else 'SIN  '} {rel}: {n} sustitucion(es)")
    print(f"TOTAL: {total} sustitucion(es)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
