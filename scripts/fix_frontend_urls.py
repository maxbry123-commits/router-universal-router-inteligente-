"""fix_frontend_urls.py — Reemplaza riu-router por space-grupo-1-router-mvp-1 en el frontend.

Alcance (ampliado sobre el borrador del Director, con evidencia):
  - chat-router/chat/**  -> ya estaba limpio (MiniMax 2 migró los hosts a space-grupo-1-router-mvp-1)
  - LIVE_URL.json (raiz) -> era el UNICO puntero vivo a riu-router y la causa del 404
    ("https://comand-center-1-riu-router.hf.space" -> Space inexistente, API 404).
    Reemplazo: "comand-center-1-riu-router.hf.space" -> "comand-center-1-space-grupo-1-router-mvp-1.hf.space"
    (Space verificado, API 200).

El Space riu-router NO existe (404) y space-grupo-1-router-mvp-1 sí (200), por eso la sustitucion
de la cadena "riu-router" por "space-grupo-1-router-mvp-1" conserva el prefijo "comand-center-1-".
"""
import os, logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(ROOT, "chat-router", "chat")
ROOT_FILES = ["LIVE_URL.json"]
OLD, NEW = "riu-router", "space-grupo-1-router-mvp-1"
EXTS = (".html", ".js", ".json", ".css")


def fix_file(path):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    if OLD not in text:
        return False
    with open(path, "w", encoding="utf-8") as f:
        f.write(text.replace(OLD, NEW))
    logger.info(f"Corregido: {os.path.relpath(path, ROOT)}")
    return True


def main():
    changed, scanned = 0, 0
    for root, _, files in os.walk(FRONTEND_DIR):
        for name in files:
            if name.endswith(EXTS):
                scanned += 1
                if fix_file(os.path.join(root, name)):
                    changed += 1
    for name in ROOT_FILES:
        p = os.path.join(ROOT, name)
        if os.path.exists(p):
            scanned += 1
            if fix_file(p):
                changed += 1
    print(f"Archivos escaneados: {scanned} | Archivos corregidos: {changed}")


if __name__ == "__main__":
    main()
