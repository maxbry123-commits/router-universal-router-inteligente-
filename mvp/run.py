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


def _actualizar():
    anterior = _head()
    if not anterior:
        return False
    correcto, _ = _git("pull", "--ff-only")
    if not correcto:
        return False
    nuevo = _head()
    if nuevo and nuevo != anterior:
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
