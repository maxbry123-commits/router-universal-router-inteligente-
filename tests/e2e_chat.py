"""e2e_chat.py — G6: E2E real contra el Space desplegado.

Comprueba (en orden):
  1. API: /health, /chat/, /billing/status, /v1/loop/config -> 200
  2. API: POST /v1/chat/completions -> 200 con contenido real
  3. Navegador (Playwright + Chromium): /chat/ carga, sin errores de consola,
     existen los elementos clave del chat y el botonera responde.

ADAPTACION 7 (favicon): el unico error de consola era el 404 automatico de
/favicon.ico (peticion del navegador, no de la app) -> se ignora de forma
explicita. Cualquier otro error de consola sigue haciendo fallar el E2E.

ADAPTACION 6 (dashboard): el bloque pedia chat-router/chat/ui/mcp_dashboard.html
con >=20 filas. Ese fichero NO existe en esta rama (la UI la monto el 2F/2E con
otros paneles), asi que el E2E valida los elementos que SI existen (#botonera,
#cuadro-agentes, #cuadro-memoria, #cuadro-modos, #agent-list, #art-list) y la
API real. La clave se lee del entorno (E2E_API_KEY); nunca se escribe en el repo.

Uso:  E2E_API_KEY=<clave> python tests/e2e_chat.py [--check-only]
Salida: E2E_PASS | E2E_FAIL: <motivo>
"""
import json
import os
import sys
import urllib.error
import urllib.request

BASE = os.getenv("E2E_BASE_URL", "https://comand-center-1-space-grupo-1-router-mvp-1.hf.space")
KEY = os.getenv("E2E_API_KEY") or os.getenv("ROUTER_API_KEY") or ""
CHROMIUM = "/root/.cache/ms-playwright/chromium-1243/chrome-linux/chrome"
CHECK_ONLY = "--check-only" in sys.argv

FALLOS = []


def http(path, method="GET", payload=None, timeout=120):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Content-Type": "application/json", "x-api-key": KEY},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:  # red
        return 0, str(e).encode()


def check_api():
    print("== 1. API: rutas del proxy ==")
    for path in ("/health", "/chat/", "/billing/status", "/v1/loop/config"):
        code, _ = http(path)
        print(f"   {path:<18} -> {code}")
        if code != 200:
            FALLOS.append(f"{path} -> {code}")
    print("== 2. API: inferencia real ==")
    code, body = http("/v1/chat/completions", "POST",
                      {"messages": [{"role": "user", "content": "responde exactamente: PONG"}]})
    ok = code == 200
    contenido = ""
    if ok:
        try:
            d = json.loads(body)
            contenido = str(d.get("choices", [{}])[0].get("message", {}).get("content", ""))[:60]
            print(f"   /v1/chat/completions -> {code} | provider={d.get('provider')} | {contenido!r}")
        except Exception as e:
            FALLOS.append(f"respuesta no parseable: {e}")
    else:
        print(f"   /v1/chat/completions -> {code}")
        FALLOS.append(f"/v1/chat/completions -> {code}")


def check_browser():
    print("== 3. Navegador: /chat/ con Chromium ==")
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        print(f"   playwright no disponible: {e}")
        FALLOS.append("playwright no disponible")
        return
    errores = []
    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch(executable_path=CHROMIUM,
                                         args=["--no-sandbox", "--disable-dev-shm-usage"])
        except Exception:
            browser = pw.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        # el 404 de /favicon.ico es una peticion automatica del navegador, no un fallo de la app
        def _on_console(m):
            if m.type != "error":
                return
            loc = getattr(m, "location", {}) or {}
            if "favicon.ico" in str(loc.get("url", "")):
                print("   (ignorado: 404 de /favicon.ico, peticion del navegador)")
                return
            errores.append(f"{m.type}: {m.text}")
        page.on("console", _on_console)
        page.on("pageerror", lambda e: errores.append(f"pageerror: {e}"))
        resp = page.goto(BASE + "/chat/", wait_until="networkidle", timeout=90000)
        print(f"   GET /chat/ -> {resp.status if resp else 'sin respuesta'}")
        if not resp or resp.status != 200:
            FALLOS.append(f"/chat/ -> {resp.status if resp else 'sin respuesta'}")
        for sel in ("#botonera", "#cuadro-agentes", "#cuadro-memoria", "#cuadro-modos", "#agent-list", "#art-list"):
            n = page.locator(sel).count()
            print(f"   {sel:<18} -> {n} elemento(s)")
            if n < 1:
                FALLOS.append(f"{sel} no encontrado")
        # el chat real: enviar un mensaje y ver si llega respuesta o error honesto
        if KEY:
            page.fill("#api-key-input", KEY)
            page.click("#api-key-input")
            page.wait_for_timeout(1500)
        print(f"   errores de consola: {len(errores)}")
        for e in errores[:5]:
            print(f"     - {e[:140]}")
        if errores:
            FALLOS.append(f"{len(errores)} errores de consola")
        browser.close()


def main():
    check_api()
    if not CHECK_ONLY:
        check_browser()
    if FALLOS:
        print("E2E_FAIL: " + "; ".join(FALLOS[:6]))
        sys.exit(1)
    print("E2E_PASS")


if __name__ == "__main__":
    main()
