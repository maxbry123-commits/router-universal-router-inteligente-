#!/usr/bin/env python3
"""SWE CODE mini-router: ejecuta la cascada de cascada.json contra llama-server(s).
HTTP OpenAI-compatible only. ~90 lineas, cero dependencias extra (solo requests)."""
import json, os, sys, time, uuid, urllib.request

RAIZ = os.path.dirname(os.path.abspath(__file__))
CASCADA = json.load(open(os.path.join(RAIZ, "cascada.json")))
MOTORES = json.load(open(os.path.join(RAIZ, "motores.json")))["motores"]
BASE_URL = os.getenv(CASCADA["base_url_env"], CASCADA["base_url_default"]).rstrip("/")


def llamar(modelo: str, mensajes: list) -> str:
    body = json.dumps({"model": modelo, "messages": mensajes, "temperature": 0.2}).encode()
    req = urllib.request.Request(f"{BASE_URL}/chat/completions", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.load(r)["choices"][0]["message"]["content"]


def recibo(pid, nodo, estado, extra=None):
    r = {"pid": pid, "nodo": nodo, "estado": estado, "ts": int(time.time())}
    if extra: r.update(extra)
    return r


def correr(objetivo: str) -> dict:
    pid = f"swecode-{uuid.uuid4().hex[:8]}"
    recibos = [recibo(pid, "inicio", "OK", {"objetivo": objetivo[:200]})]
    entrada = objetivo
    for paso in CASCADA["pasos"]:
        modelo, nodo, agente = paso["modelo"], paso["nodo"], paso["agente"]
        prompt = (f"AGENTE={agente}. Tarea: {objetivo}\n"
                  f"Entrada del paso anterior ({paso['entrada']}):\n{entrada}\n"
                  f"Entrega SOLO: {paso['salida']}.")
        try:
            salida = llamar(modelo, [{"role": "user", "content": prompt}])
            recibos.append(recibo(pid, nodo, "OK", {"modelo": modelo, "chars": len(salida)}))
            entrada = salida
        except Exception as e:
            recibos.append(recibo(pid, nodo, "FAIL", {"modelo": modelo, "error": str(e)[:300]}))
            return {"pid": pid, "estado": "FAIL", "paso_fallido": nodo, "recibos": recibos}
    return {"pid": pid, "estado": "DONE", "resultado": entrada, "recibos": recibos}


def main():
    objetivo = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read().strip()
    if not objetivo:
        print(json.dumps({"verdict": "INPUT_GAP", "detail": "objetivo requerido"})); sys.exit(1)
    print(json.dumps(correr(objetivo), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
