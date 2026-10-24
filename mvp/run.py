"""Arranque del MVP con autopull exclusivo de la rama desplegada."""
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def _git(*args):
    try:
        r = subprocess.run(["git", "-C", str(REPO), *args],
                           capture_output=True, text=True, timeout=20, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return False, ""
    return r.returncode == 0, r.stdout.strip()


def _head():
    ok, sha = _git("rev-parse", "HEAD")
    return sha if ok else None


SIN_REINICIO = ("plugins/chat-router/frontend/", "docs/", "raiz_router/", "raiz_fichas_prompt/", "Prueba/")  # los sirve Vercel o son documentos


def _toca_servidor(anterior, nuevo):
    """Un commit solo de frontend o documentos no reinicia el Router (evita 'Error de Router' al subir cambios de pantalla)."""
    ok, lista = _git("diff", "--name-only", anterior, nuevo)
    return not ok or any(not r.startswith(SIN_REINICIO) for r in lista.splitlines())


def _carga_bien():
    """El codigo nuevo debe poder importarse antes de reiniciar; si no, un commit roto dejaria el servidor caido y el autopull muerto."""
    if not (REPO / "mvp" / "app.py").exists():
        return True
    try:
        r = subprocess.run([sys.executable, "-c", "import mvp.app"], cwd=str(REPO), capture_output=True, text=True, timeout=120, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return False
    if r.returncode:
        print("AUTOPULL: el codigo nuevo no carga: " + r.stderr.strip()[-300:], flush=True)
    return r.returncode == 0


def _actualizar():
    anterior = _head()
    if not anterior:
        return False
    correcto, _ = _git("pull", "--ff-only")
    if not correcto:
        print("AUTOPULL: git pull fallo; sigo con " + anterior[:10], flush=True)
        return False
    nuevo = _head()
    if nuevo and nuevo != anterior and _toca_servidor(anterior, nuevo):
        if not _carga_bien():
            _git("reset", "--hard", anterior)  # vuelve a la version que funcionaba
            print("AUTOPULL: deshice %s y sigo con %s" % (nuevo[:10], anterior[:10]), flush=True)
            return False
        print("AUTOPULL: reinicio con %s" % nuevo[:10], flush=True)
        os.execv(sys.executable, [sys.executable, *sys.argv])
        return True
    return False


def _vigilar():
    while True:
        time.sleep(60)
        _actualizar()


def _iniciar_hilo():
    if os.environ.get("MVP_AUTOPULL", "1") == "0":
        return False
    threading.Thread(target=_vigilar, name="mvp-autopull", daemon=True).start()
    return True


def main():
    sys.path.insert(0, str(REPO))
    print("MVP commit: " + (_head() or "desconocido"), flush=True)
    _iniciar_hilo()
    import uvicorn
    uvicorn.run("mvp.app:app", host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
