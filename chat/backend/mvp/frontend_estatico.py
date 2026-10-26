"""El Router sirve el chat (chat/frontend) por si Vercel no puede desplegar (cupo diario): `/` y `/chat/ui/<archivo>`.
Los archivos salen del clon del repo; el autopull los actualiza sin reiniciar el servidor (chat/frontend/ esta en SIN_REINICIO)."""
from pathlib import Path
from fastapi.responses import FileResponse

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

    @app.get("/chat/ui/{ruta:path}", include_in_schema=False)
    def ui(ruta: str):
        return FileResponse(_archivo(ruta, raiz), headers=SIN_CACHE)
