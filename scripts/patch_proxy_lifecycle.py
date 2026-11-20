"""patch_proxy_lifecycle.py — Añade startup/shutdown al proxy para power_daemon,
billing_monitor y storage_wiring; y la ruta /billing/status.
Idempotente y TOLERANTE A FALLOS: si PowerDaemon no tiene start/stop o falla
el __init__, el proxy NO se tumba.
"""
from pathlib import Path

PROXY = Path("ROUTER MVP v1/system_prompt_py/openai_compatible_proxy.py")

LIFECYCLE_IMPORTS = """
# --- MINIMAX 4: lifecycle ---
try:
    from external.core.power_daemon import PowerDaemon
    _power_daemon = PowerDaemon()
except Exception as _e:
    _power_daemon = None
    print(f"[INFRA] PowerDaemon no disponible: {_e}")

from external.core.billing_monitor import BillingMonitor
from external.core.storage_wiring import StorageWiring
_storage_ok = False
# --- FIN MINIMAX 4 ---
"""

LIFECYCLE_EVENTS = """
# --- MINIMAX 4: lifecycle ---
@app.on_event("startup")
async def _infra_startup():
    global _storage_ok
    try:
        _storage_ok = StorageWiring.verify_storage_connection()
    except Exception as _e:
        _storage_ok = False
        print(f"[INFRA] StorageWiring falló: {_e}")
    if _power_daemon is not None:
        try:
            if hasattr(_power_daemon, "start"):
                _power_daemon.start()
            else:
                print("[INFRA] PowerDaemon sin .start() — no se arranca.")
        except Exception as _e:
            print(f"[INFRA] PowerDaemon.start() falló: {_e}")
    print(f"[INFRA] storage_ok={_storage_ok} power_daemon={'ON' if _power_daemon else 'OFF'}")

@app.on_event("shutdown")
async def _infra_shutdown():
    if _power_daemon is not None and hasattr(_power_daemon, "stop"):
        try:
            _power_daemon.stop()
        except Exception as _e:
            print(f"[INFRA] PowerDaemon.stop() falló: {_e}")
    print("[INFRA] shutdown")

@app.get("/billing/status")
def billing_status():
    return BillingMonitor.check_runtime_cost()
# --- FIN MINIMAX 4 ---
"""

def patch():
    if not PROXY.exists():
        raise FileNotFoundError(f"No existe {PROXY} — revisa la ruta real.")
    text = PROXY.read_text(encoding="utf-8")
    if "MINIMAX 4: lifecycle" in text:
        print("Proxy ya parcheado (idempotente).")
        return
    if '@app.on_event("startup")' in text:
        print("[WARN] El proxy ya tiene un @app.on_event('startup'). Se insertará otro; revisa el orden.")
    lines = text.splitlines()
    last_import = max(i for i, l in enumerate(lines) if l.startswith(("import ", "from ")))
    lines.insert(last_import + 1, LIFECYCLE_IMPORTS)
    text = "\n".join(lines)
    if "app = FastAPI()" in text:
        text = text.replace("app = FastAPI()", "app = FastAPI()\n" + LIFECYCLE_EVENTS, 1)
    elif "app = create_app()" in text:
        text = text.replace("app = create_app()", "app = create_app()\n" + LIFECYCLE_EVENTS, 1)
    else:
        raise RuntimeError("No se encontró app = FastAPI() ni app = create_app()")
    PROXY.write_text(text, encoding="utf-8")
    print("Proxy parcheado: lifecycle + /billing/status (tolerante a fallos).")

if __name__ == "__main__":
    patch()
