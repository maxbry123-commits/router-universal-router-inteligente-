#!/usr/bin/env python3
"""SWE CODE mini-router: ejecuta la cascada de cascada.json contra llama-server(s).
HTTP OpenAI-compatible only. ~90 lineas, cero dependencias extra (solo requests)."""
import json, os, sys, time, uuid, urllib.request

RAIZ = os.path.dirname(os.path.abspath(__file__))
CASCADA = json.load(open(os.path.join(RAIZ, "cascada.json")))
MOTORES = json.load(open(os.path.join(RAIZ, "motores.json")))["motores"]
BASE_URL = os.getenv(CASCADA["base_url_env"], CASCADA["base_url_default"]).rstrip("/")
# Cola HF: S1/S2/S3 son slots intercambiables (cualquier Space sirve cualquier
# modelo via model=, 1 vivo por Space, carga bajo demanda, encola al libre).
# El orden del paso = preferencia; el salto a otra URL = slot libre/respaldo.
URLS = {s: os.getenv(f"SWECODE_URL_{s}").rstrip("/") for s in ("S1", "S2", "S3")
        if os.getenv(f"SWECODE_URL_{s}")}
if not URLS:
    URLS = {"S1": BASE_URL}


def llamar(modelo: str, mensajes: list, servidor: str = "S1") -> str:
    body = json.dumps({"model": modelo, "messages": mensajes, "temperature": 0.2}).encode()
    orden = [servidor] + [s for s in URLS if s != servidor]
    ultimo = None
    for s in orden:
        base_url = URLS.get(s)
        if not base_url:
            continue
        try:
            req = urllib.request.Request(f"{base_url}/chat/completions", data=body,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=600) as r:
                return json.load(r)["choices"][0]["message"]["content"]
        except Exception as e:
            ultimo = e
    raise ultimo


def recibo(pid, nodo, estado, extra=None):
    r = {"pid": pid, "nodo": nodo, "estado": estado, "ts": int(time.time())}
    if extra: r.update(extra)
    return r


def correr(objetivo: str, pasos=None) -> dict:
    pasos = pasos or CASCADA["pasos"]
    pid = f"swecode-{uuid.uuid4().hex[:8]}"
    recibos = [recibo(pid, "inicio", "OK", {"objetivo": objetivo[:200]})]
    entrada = objetivo
    for paso in pasos:
        modelo, nodo, agente = paso["modelo"], paso["nodo"], paso["agente"]
        prompt = (f"AGENTE={agente}. Tarea: {objetivo}\n"
                  f"Entrada del paso anterior ({paso['entrada']}):\n{entrada}\n"
                  f"Entrega SOLO: {paso['salida']}.")
        try:
            salida = llamar(modelo, [{"role": "user", "content": prompt}],
                            paso.get("servidor", "S1"))
            recibos.append(recibo(pid, nodo, "OK", {"modelo": modelo, "chars": len(salida),
                                                  "servidor": paso.get("servidor")}))
            entrada = salida
        except Exception as e:
            recibos.append(recibo(pid, nodo, "FAIL", {"modelo": modelo, "error": str(e)[:300]}))
            return {"pid": pid, "estado": "FAIL", "paso_fallido": nodo, "recibos": recibos}
    return {"pid": pid, "estado": "DONE", "resultado": entrada, "recibos": recibos}


def main():
    args = sys.argv[1:]
    pasos = None
    if args[:1] == ["--pipeline"]:
        nombre = args[1] if len(args) > 1 else "code"
        pasos = CASCADA.get("pipelines", {}).get(nombre)
        if not pasos:
            print(json.dumps({"verdict": "INPUT_GAP", "detail": f"pipeline desconocido: {nombre}",
                              "pipelines": list(CASCADA.get("pipelines", {}))})); sys.exit(1)
        args = args[2:]
    objetivo = args[0] if args else sys.stdin.read().strip()
    if not objetivo:
        print(json.dumps({"verdict": "INPUT_GAP", "detail": "objetivo requerido"})); sys.exit(1)
    print(json.dumps(correr(objetivo, pasos), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
