#!/usr/bin/env python3
"""T03 — Supervisor de OmniRoute (stdlib only).

- Lock de instancia única (fichero + flock si está disponible).
- Antes de (re)lanzar: espera a que el puerto 20128 quede libre (evita EADDRINUSE).
- Healthcheck HTTP cada 30 s.
- Backoff real: 5s, 15s, 45s, 135s… (x3, tope 300 s).
- Si RSS del proceso > RAM_LIMIT_BYTES (6 GB) → reinicio controlado.
"""
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.request

HOST = os.environ.get("APP_BIND_HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "20128"))
DATA_DIR = os.environ.get("DATA_DIR", "/tmp/omniroute-data")
APP_DIR = os.environ.get("OMNIROUTE_APP_DIR", "/tmp/omniroute-app")
LOCK_FILE = os.path.join(DATA_DIR, "supervisor.lock")
HEALTH_URL = f"http://{HOST}:{PORT}/api/monitoring/health"
HEALTH_INTERVAL = 30
RAM_LIMIT = 6 * 1024**3  # 6 GB
BACKOFF_BASE = 5
BACKOFF_MAX = 300
PORT_WAIT_TIMEOUT = 120

_proc = None


def log(msg):
    print(f"[{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}] {msg}", flush=True)


def acquire_lock(path):
    """Lock de instancia única. Devuelve fd o termina el proceso."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o644)
    try:
        import fcntl
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except ImportError:
        # Sin fcntl (no POSIX): lock por contenido con PID vivo.
        with open(path) as f:
            old = f.read().strip()
        if old and os.path.exists(f"/proc/{old}"):
            log(f"FATAL: ya hay una instancia viva (pid {old})")
            sys.exit(1)
    except OSError:
        log("FATAL: otra instancia del supervisor tiene el lock")
        sys.exit(1)
    os.ftruncate(fd, 0)
    os.write(fd, str(os.getpid()).encode())
    return fd


def port_free(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    try:
        s.bind((host, port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def wait_port_free(host, port, timeout=PORT_WAIT_TIMEOUT):
    """Espera a que el puerto quede libre antes de relanzar."""
    t0 = time.time()
    while not port_free(host, port):
        if time.time() - t0 > timeout:
            log(f"WARN: puerto {port} sigue ocupado tras {timeout}s; NO se relanza")
            return False
        time.sleep(1)
    return True


def healthy():
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=5) as r:
            return 200 <= r.status < 300
    except Exception:
        return False


def rss_bytes(pid):
    try:
        with open(f"/proc/{pid}/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) * 1024
    except OSError:
        return 0
    return 0


def start_process():
    env = dict(os.environ)
    env.setdefault("NODE_OPTIONS", "--max-old-space-size=4096")
    env.setdefault("APP_BIND_HOST", HOST)
    env.setdefault("PORT", str(PORT))
    env.setdefault("REQUIRE_API_KEY", "false")
    env.setdefault("DATA_DIR", DATA_DIR)
    return subprocess.Popen(["npm", "run", "start"], cwd=APP_DIR, env=env)


def stop_process(proc, grace=15):
    if proc is None or proc.poll() is not None:
        return
    proc.send_signal(signal.SIGTERM)
    try:
        proc.wait(timeout=grace)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=10)


def backoff_delay(failures):
    return min(BACKOFF_BASE * (3 ** failures), BACKOFF_MAX)


def main():
    global _proc
    acquire_lock(LOCK_FILE)
    log(f"Supervisor activo. App={APP_DIR} {HOST}:{PORT} DATA_DIR={DATA_DIR}")

    def _sigterm(*_):
        log("SIGTERM: parada controlada")
        stop_process(_proc)
        sys.exit(0)

    signal.signal(signal.SIGTERM, _sigterm)
    signal.signal(signal.SIGINT, _sigterm)

    failures = 0
    while True:
        if not wait_port_free(HOST, PORT):
            delay = backoff_delay(failures)
            failures += 1
            log(f"Puerto ocupado; reintento de supervisor en {delay}s")
            time.sleep(delay)
            continue
        log("Lanzando OmniRoute…")
        _proc = start_process()
        started = time.time()
        last_check = 0.0

        while True:
            rc = _proc.poll()
            if rc is not None:
                log(f"Proceso terminó (rc={rc})")
                break
            now = time.time()
            if now - last_check >= HEALTH_INTERVAL:
                last_check = now
                rss = rss_bytes(_proc.pid)
                if rss > RAM_LIMIT:
                    log(f"RAM {rss // 1024**2} MB > 6 GB → reinicio controlado")
                    stop_process(_proc)
                    break
                if now - started > 60 and not healthy():
                    log("Healthcheck FAIL → reinicio")
                    stop_process(_proc)
                    break
            time.sleep(1)

        uptime = time.time() - started
        failures = 0 if uptime > 300 else failures + 1
        delay = backoff_delay(failures)
        log(f"Reintento en {delay}s (fallos consecutivos={failures})")
        time.sleep(delay)


if __name__ == "__main__":
    main()
