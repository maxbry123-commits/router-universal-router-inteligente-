"""Arranque del MVP con autopull exclusivo de la rama desplegada."""
import os
import subprocess
import sys
import threading
import shutil
import atexit
import time
from pathlib import Path

def _raiz():
    """Raiz del clon: mvp/ puede ser un enlace a chat/backend/mvp (el Space arranca mvp.run desde la raiz)."""
    aqui = Path(__file__).resolve().parent
    try:
        r = subprocess.run(["git", "-C", str(aqui), "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=20, check=False)
        if r.returncode == 0 and r.stdout.strip():
            return Path(r.stdout.strip())
    except (OSError, subprocess.TimeoutExpired):
        pass
    return aqui.parent


REPO = _raiz()
BRIDGE_DIR = REPO / "chat-router" / "SWE CODE" / "web-bridge"
_BRIDGE = None


def _bridge_externo():
    """El Space existente ejecuta /proxy.py y su propio boot.sh lanza :7870.

    No iniciar un segundo bridge desde el Runner (EADDRINUSE / respuestas intermitentes).
    En contenedores que arrancan solo con el Dockerfile del repo, /proxy.py no existe.
    """
    return Path("/proxy.py").is_file()


def _parar_bridge():
    global _BRIDGE
    proc, _BRIDGE = _BRIDGE, None
    if not proc or proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=3)


def _iniciar_bridge():
    """Bridge EXISTENTE en el MISMO Space, no otro servicio externo ni nueva raiz."""
    global _BRIDGE
    if _bridge_externo():
        return True  # HF boot.sh administra el Node y el proxy; no duplicar el puerto 7870.
    if _BRIDGE and _BRIDGE.poll() is None:
        return True
    node = shutil.which("node")
    if not node or not (BRIDGE_DIR / "node_modules" / "express").is_dir():
        print("BRIDGE_SIN_NODE_O_DEPENDENCIAS: no se anuncia conexion, verifique imagen y npm", flush=True)
        return False
    env = _entorno()
    env["BRIDGE_PORT"] = str(os.getenv("BRIDGE_PORT") or "7870")
    try:
        _BRIDGE = subprocess.Popen([node, "src/server.js"], cwd=str(BRIDGE_DIR), env=env)
        print("BRIDGE_INICIADO: puerto " + env["BRIDGE_PORT"], flush=True)
        return True
    except OSError:
        print("BRIDGE_NO_INICIADO", flush=True)
        return False


atexit.register(_parar_bridge)


def _rutas():
    """Las 2 raices del repo: router-mvp (mvp, router, fichas) y chat-router (plugins, chat)."""
    return [str(REPO / "router-mvp"), str(REPO / "chat-router")]


def _entorno():
    return {**os.environ, "PYTHONPATH": os.pathsep.join(_rutas() + [os.environ.get("PYTHONPATH", "")])}


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


SIN_REINICIO = ("chat-router/chat/frontend/", "router-mvp/componentes/", "chat-router/chat/docs/", "chat-router/chat/e2e/", "chat-router/chat/auditoria/", "router-mvp/raiz_router/", "router-mvp/raiz_fichas_prompt/", "chat-router/chat/backend/mvp/pruebas_vivo/")  # los sirve Vercel o son documentos


def _toca_servidor(anterior, nuevo):
    """Un commit solo de frontend o documentos no reinicia el Router (evita 'Error de Router' al subir cambios de pantalla)."""
    ok, lista = _git("diff", "--name-only", anterior, nuevo)
    return not ok or any(not r.startswith(SIN_REINICIO) for r in lista.splitlines())


def _carga_bien():
    """El codigo nuevo debe poder importirse antes de reiniciar; si no, un commit roto dejaria el servidor caido y el autopull muerto."""
    if not (REPO / "router-mvp" / "mvp" / "app.py").exists():
        return True
    try:
        r = subprocess.run([sys.executable, "-c", "import mvp.app"], cwd=str(REPO / "router-mvp"), env=_entorno(), capture_output=True, text=True, timeout=120, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return False
    if r.returncode:
        print("AUTOPULL: el codigo nuevo no carga: " + r.stderr.strip()[-300:], flush=True)
    return r.returncode == 0


ARRANQUE, _DIFERIDO = None, None  # commit que corre este proceso; desde cuando se difiere un reinicio
DIFERIR_MAX_S = (float(os.environ["RIU_MAX_HORAS"]) + 1) * 3600 if float(os.environ.get("RIU_MAX_HORAS", "0")) > 0 else float(os.environ.get("RIU_DEFER_MAX_S", "3600"))  # sin RIU_MAX_HORAS: espera maxima de 1 h (RIU_DEFER_MAX_S); un trabajo procesando atascado no difiere el reinicio para siempre


def _tareas_en_curso():
    app = sys.modules.get("mvp.app")
    try:
        return int(app._en_curso()) if app is not None and hasattr(app, "_en_curso") else 0
    except Exception:  # noqa: BLE001 - un fallo al contar nunca debe tumbar el autopull
        return 0


def _actualizar():
    global _DIFERIDO
    anterior = _head()
    if not anterior:
        return False
    correcto, _ = _git("pull", "--ff-only")
    if not correcto:
        print("AUTOPULL: git pull fallo; sigo con " + anterior[:10], flush=True)
        return False
    nuevo = _head()
    base = ARRANQUE or anterior  # lo que corre hoy: un reinicio diferido se sigue comparando contra el
    if nuevo and nuevo != base and _toca_servidor(base, nuevo):
        en_curso = _tareas_en_curso()
        if en_curso and (_DIFERIDO is None or time.time() - _DIFERIDO < DIFERIR_MAX_S):
            if _DIFERIDO is None:
                _DIFERIDO = time.time()
                print("AUTOPULL: hay tareas en curso; el reinicio con %s espera a que terminen" % nuevo[:10], flush=True)
            return False
        if en_curso:  # tope de espera vencido con tareas sin terminar: se reinicia igual y se reanudan al arrancar
            print("AUTOPULL: tareas en curso tras el tope de espera; reinicio con %s (se reanudan al arrancar)" % nuevo[:10], flush=True)
        if not _carga_bien():
            _git("reset", "--hard", base)  # vuelve a la version que funcionaba
            print("AUTOPULL: deshice %s y sigo con %s" % (nuevo[:10], base[:10]), flush=True)
            return False
        print("AUTOPULL: reinicio con %s" % nuevo[:10], flush=True)
        _parar_bridge()  # liberar 7870 antes de ejecutar el nuevo codigo
        os.execv(sys.executable, [sys.executable, *sys.argv])
        return True
    return False


def _vigilar():
    while True:
        time.sleep(60)
        _actualizar()
        if not _bridge_externo() and (_BRIDGE is None or _BRIDGE.poll() is not None):
            _iniciar_bridge()  # solo si el Runner es dueno del bridge; HF boot ya lo vigila


def _iniciar_hilo():
    if os.environ.get("MVP_AUTOPULL", "1") == "0":
        return False
    threading.Thread(target=_vigilar, name="mvp-autopull", daemon=True).start()
    return True


def _instalar_agentes_fondo():
    """Instala y comprueba los agentes del Harness YA existente; nunca bloquea el arranque.
    
    La fuente es chat-router/agentes/runtime, sin nueva raiz de codigo, Space ni
    duplicar el Harness. Los adaptadores reportan NO INSTALADO mientras no
    termine la instalacion y NO CONFIGURADO si falta Gateway, Docker o claves.
    """
    if os.environ.get("RIU_AGENTES_AUTO_INSTALAR", "1") == "0":
        return
    runtime = REPO / "chat-router" / "agentes" / "runtime"
    instalar = runtime / "instalar-agentes.sh"
    verificar = runtime / "verificar-agentes.sh"
    if not instalar.is_file() or not verificar.is_file():
        print("AGENTES: scripts existentes ausentes; no se simula disponibilidad", flush=True)
        return

    def tarea():
        env = _entorno()
        env.setdefault("RIU_AGENTES_RUNTIME", str(runtime))
        env["RIU_INSTALAR_TOLERANTE"] = "1"
        # Los instaladores solo requieren PATH/proxy; no necesitan claves de APIs.
        env = {k: v for k, v in env.items()
               if not any(t in k.upper() for t in ("TOKEN", "PASSWORD", "API_KEY", "SECRET", "PASSPHRASE"))}
        try:
            with open("/tmp/riu-agentes-instalacion.log", "a", encoding="utf-8") as registro:
                inst = subprocess.run(["bash", str(instalar)], cwd=str(REPO), env=env,
                                      stdout=registro, stderr=subprocess.STDOUT, check=False)
                estado = subprocess.run(["bash", str(verificar)], cwd=str(REPO), env=env,
                                         stdout=registro, stderr=subprocess.STDOUT, check=False)
            print("AGENTES: instalacion=%s verificacion=%s (disponibilidad real: Harness status.swe)"
                  % (inst.returncode, estado.returncode), flush=True)
        except (OSError, subprocess.SubprocessError) as error:
            print("AGENTES: no se pudo comprobar runtime (%s)" % type(error).__name__, flush=True)

    threading.Thread(target=tarea, name="riu-agentes-runtime", daemon=True).start()


def main():
    for ruta in reversed(_rutas()):
        sys.path.insert(0, ruta)
    global ARRANQUE
    ARRANQUE = _head()
    print("MVP commit: " + (ARRANQUE or "desconocido"), flush=True)
    _iniciar_bridge()
    _instalar_agentes_fondo()
    _iniciar_hilo()
    import uvicorn
    uvicorn.run("mvp.app:app", host="0.0.0.0", port=int(os.environ.get("PORT") or 7860))  # el Space lo lanza con PORT=7861 (detras de su proxy); boot.sh detecta esta linea


if __name__ == "__main__":
    main()
