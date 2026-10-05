"""Router de respaldo HF (ficha respaldo-hf). Probado 2026-10-04.

Usa el COMPUTO DEL ROUTER (no una cuenta aparte): POST <puerta>/hf/compute/run con el token de la ficha 0 (permiso computo).

Uso:  RIU_TOKEN=<token ficha 0> python3 respaldo_hf.py start 27b|35b   -> imprime JOB y URL
      RIU_TOKEN=<token ficha 0> python3 respaldo_hf.py status <job>
      RIU_TOKEN=<token ficha 0> python3 respaldo_hf.py stop <job>       -> apagado remoto (boton del chat)

Apagado automatico (dentro del L4): 30 s despues de terminar una respuesta, o 5 min sin ningun pedido.
La URL https://<job>--8080.hf.jobs solo responde con un token de Hugging Face (Authorization: Bearer <HF_TOKEN>).
"""
import json
import os
import sys
import urllib.request

PUERTA = os.environ.get("RIU_ROUTER_URL", "https://comand-center-1-claude-github-mcp-backup.hf.space")
MODELOS = {
    "27b": ("unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL", "qwen3.8-27b"),
    "35b": ("unsloth/Qwen3.6-35B-A3B-MTP-GGUF:UD-Q3_K_XL", "qwen3.6-35b"),
}
ARRANQUE = r"""/app/llama-server --host 0.0.0.0 --port 8080 -hf "$MODELO" --alias "$ALIAS" -ngl 999 -fa on -np 1 -b 128 -c 16384 --temp 0 --top-k 20 --top-p 0.95 --no-mmproj --reasoning-budget 0 --spec-type draft-mtp --spec-draft-n-max 2 --jinja > /tmp/l.log 2>&1 &
P=$!
while kill -0 $P 2>/dev/null; do
  sleep 5
  I=$(( $(date +%s) - $(stat -c %Y /tmp/l.log) ))
  if grep -q print_timing /tmp/l.log && [ $I -ge 30 ]; then echo APAGADO_FIN_DE_SALIDA; kill $P; exit 0; fi
  if [ $I -ge 300 ]; then echo APAGADO_5_MIN_SIN_USO; kill $P; exit 0; fi
done
tail -n 20 /tmp/l.log
"""


def llamar(metodo: str, ruta: str, cuerpo: dict | None = None) -> dict:
    cab = {"Authorization": "Bearer " + os.environ["RIU_TOKEN"], "Content-Type": "application/json"}
    if os.environ.get("DIRECTOR_KEY"):
        cab["X-Director-Key"] = os.environ["DIRECTOR_KEY"]
    req = urllib.request.Request(PUERTA + ruta, data=json.dumps(cuerpo).encode() if cuerpo else None, headers=cab, method=metodo)
    return json.loads(urllib.request.urlopen(req, timeout=60).read().decode())


def encender(cual: str) -> dict:
    repo, alias = MODELOS[cual]
    r = llamar("POST", "/hf/compute/run", {"command": ["bash", "-c", ARRANQUE], "image": "ghcr.io/ggml-org/llama.cpp:server-cuda",
                                            "flavor": "l4x1", "timeout": "2h", "expose": [8080], "env": {"MODELO": repo, "ALIAS": alias}})
    return {"job_id": r["job_id"], "url": "https://" + r["job_id"] + "--8080.hf.jobs", "modelo": alias}


def main() -> None:
    accion = sys.argv[1] if len(sys.argv) > 1 else "status"
    if accion == "start":
        print(json.dumps(encender(sys.argv[2] if len(sys.argv) > 2 else "35b")))
    elif accion == "status":
        print(json.dumps(llamar("GET", "/hf/compute/" + sys.argv[2])))
    elif accion == "stop":
        print(json.dumps(llamar("DELETE", "/hf/compute/" + sys.argv[2])))


if __name__ == "__main__":
    main()
