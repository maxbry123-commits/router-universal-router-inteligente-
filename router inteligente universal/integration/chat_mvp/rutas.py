"""Una sola raiz en el almacenamiento HF para todo el Router Inteligente Universal (Director 2026-10-03).

Bucket: HF_BUCKET_ID (COMAND-CENTER-1/yaiwes-memoria-storage). Todo lo del Router vive bajo RIU_ROOT:

  router-inteligente-universal/
    memoria/        SQLite del Router + documentos (copia automatica cada 60 s, se recupera al arrancar)
    banco/          banco de secretos cifrado, providers.json, tokens.json (solo huellas), copias .bak
    laboratorio/    latest.json + reports/<run_id>.json
    control/        registro del Router vigente, procesador pedido, bitacora del kernel
    codigo/         paquete del Router (router-bundle.tar.gz + .json)
    fichas/         una ficha = un archivo .json = una seccion nueva del Router (_plantilla.json no se monta)
    espacios/       almacenamiento propio de cada token/agente
    Ventana status router inteligente universal/   estado vivo (se escribe solo)
  router-respaldo/  mini router T4/L4 (solo HF, lo usa el Space)
"""
from __future__ import annotations

import os

ROOT = os.getenv("RIU_ROOT", "router-inteligente-universal").strip("/")
RESPALDO = os.getenv("RIU_RESPALDO_ROOT", "router-respaldo").strip("/")
VENTANA_NOMBRE = "Ventana status router inteligente universal"


def p(*parts: str) -> str:
    return "/".join([ROOT, *(x.strip("/") for x in parts if x)])


MEMORIA = p("memoria")
BANCO = p("banco")
LABORATORIO = p("laboratorio")
CONTROL = p("control")
CODIGO = p("codigo")
FICHAS = p("fichas")
ESPACIOS = p("espacios")
VENTANA = p(VENTANA_NOMBRE)
TOKENS = p("banco", "tokens.json")
REGISTRY = p("control", "router-current.json")
DESIRED = p("control", "router-desired.json")
KERNEL_LOG = p("control", "kernel-log.jsonl")


def bucket() -> str:
    return os.getenv("HF_BUCKET_ID", "COMAND-CENTER-1/yaiwes-memoria-storage")


def full(rel: str) -> str:
    """Bucket-relative path -> HfFileSystem path."""
    return f"buckets/{bucket()}/{rel}"
