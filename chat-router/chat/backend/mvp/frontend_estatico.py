"""El Router sirve el chat (chat/frontend) por si Vercel no puede desplegar (cupo diario): `/` y `/chat/ui/<archivo>`.
Los archivos salen del clon del repo; el autopull los actualiza sin reiniciar el servidor (chat/frontend/ esta en SIN_REINICIO)."""
import re
import subprocess
from pathlib import Path
from fastapi.responses import FileResponse, JSONResponse

CARPETA = Path(__file__).resolve().parents[3] / "chat" / "frontend"
SIN_CACHE = {"Cache-Control": "no-cache"}


def _archivo(ruta, raiz=CARPETA):
    raiz = raiz.resolve()
    p = (raiz / (ruta or "shell.html")).resolve()
    return p if p.is_file() and raiz in p.parents else raiz / "shell.html"  # fuera de la carpeta o inexistente: el chat


def montar(app, raiz=CARPETA):
    @app.get("/", include_in_schema=False)
    def inicio():
        return FileResponse(_archivo("", raiz), headers=SIN_CACHE)

    @app.get("/chat/ui/version.json", include_in_schema=False)
    def version():
        # HF sirve los JS del clon GitHub, pero no ejecuta build.sh (Vercel si).
        # Antes se devolvia shell.html HTTP 200 como supuesto version.json:
        # version.js no podia detectar un frontend cambiado ni recargarlo.
        archivo = (raiz / "version.json").resolve()
        if archivo.is_file() and raiz.resolve() in archivo.parents:
            return FileResponse(archivo, headers=SIN_CACHE)
        try:
            sha = subprocess.check_output(
                ["git", "-C", str(raiz), "rev-parse", "HEAD"],
                timeout=3, text=True, stderr=subprocess.DEVNULL).strip()
        except (OSError, subprocess.SubprocessError):
            sha = ""
        if not re.fullmatch(r"[0-9a-fA-F]{40}", sha):
            return JSONResponse({"commit": None}, headers=SIN_CACHE, status_code=503)
        return JSONResponse({"commit": sha}, headers=SIN_CACHE)

    @app.get("/chat/ui/{ruta:path}", include_in_schema=False)
    def ui(ruta: str):
        return FileResponse(_archivo(ruta, raiz), headers=SIN_CACHE)
