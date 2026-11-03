#!/usr/bin/env bash
# Ejecuta de verdad `--version` / `--help` (y la importacion del SDK) de cada agente y escribe un JSON de estado SIN secretos
# (solo nombre, ruta, ok y la primera linea de la version). Destino: $RIU_ESTADO_JSON o <runtime>/estado-agentes.json; tambien lo imprime.
# Busca igual que los adaptadores: RIU_*_BIN -> <runtime>/bin -> PATH. Salida 0 siempre que se pudo escribir el JSON (lo no instalado figura instalado:false).
set -euo pipefail
export OPENHANDS_SUPPRESS_BANNER=1  # el SDK imprime un cuadro al importarse

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME="$(mkdir -p "${RIU_AGENTES_RUNTIME:-$AQUI}" && cd "${RIU_AGENTES_RUNTIME:-$AQUI}" && pwd)"
# Ejecutar los --version con el MISMO Node24 que usan los adaptadores.
if [ -x "$RUNTIME/node24/bin/node" ]; then export PATH="$RUNTIME/node24/bin:$PATH";
elif [ -x /opt/node24/bin/node ]; then export PATH="/opt/node24/bin:$PATH"; fi
SALIDA="${RIU_ESTADO_JSON:-$RUNTIME/estado-agentes.json}"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

# buscar VARIABLE nombre -> ruta (RIU_*_BIN si esta definida manda; luego runtime/bin; luego PATH)
buscar() {
  local v="${!1:-}"
  if [[ -n "$v" ]]; then [[ -x "$v" && -f "$v" ]] && echo "$v"; return 0; fi
  if [[ -x "$RUNTIME/bin/$2" && -f "$RUNTIME/bin/$2" ]]; then echo "$RUNTIME/bin/$2"; return 0; fi
  command -v "$2" 2>/dev/null || true
}

# registrar agente ruta argumentos...   -> deja $TMP/<agente>.{ruta,exit,out}
registrar() {
  local agente="$1" ruta="$2"; shift 2
  printf '%s' "$ruta" > "$TMP/$agente.ruta"
  [[ -n "$ruta" ]] || { printf '' > "$TMP/$agente.out"; echo -n "" > "$TMP/$agente.exit"; return 0; }
  local rc=0
  timeout 120 "$ruta" "$@" > "$TMP/$agente.out" 2>&1 < /dev/null || rc=$?
  printf '%s' "$rc" > "$TMP/$agente.exit"
}

registrar codex "$(buscar RIU_CODEX_BIN codex)" --version
registrar opencode "$(buscar RIU_OPENCODE_BIN opencode)" --version
registrar claude-code "$(buscar RIU_CLAUDE_BIN claude)" --version
registrar openclaw "$(buscar RIU_OPENCLAW_BIN openclaw)" --version
SWE="$(buscar RIU_SWEAGENT_BIN sweagent)"
registrar swe-agent "$SWE" --help

PY="${RIU_OPENHANDS_PYTHON:-}"
[[ -n "$PY" ]] || PY="$RUNTIME/venv/openhands/bin/python"
if [[ -x "$PY" ]]; then
  registrar openhands "$PY" -I -c 'import importlib.metadata as m, openhands.sdk, openhands.tools; print("openhands-sdk %s openhands-tools %s" % (m.version("openhands-sdk"), m.version("openhands-tools")))'
else
  registrar openhands ""
fi

# version de SWE-agent: del paquete instalado en el venv de su ejecutable (sweagent --version solo imprime la ayuda)
: > "$TMP/swe-agent.version"
if [[ -n "$SWE" ]]; then
  SWEPY="$(dirname "$(readlink -f "$SWE")")/python"
  [[ -x "$SWEPY" ]] && "$SWEPY" -I -c 'import importlib.metadata as m; print("SWE-agent " + m.version("sweagent") + " / swe-rex " + m.version("swe-rex"))' > "$TMP/swe-agent.version" 2>/dev/null || true
fi

# Docker + imagen de SWE-agent (solo lectura; sin daemon el campo queda null, no se inventa)
IMAGEN="${RIU_SWEAGENT_IMAGE:-riu-sweagent:latest}"
DOCKER="$(buscar RIU_DOCKER_BIN docker)"
DOCKER_EST=""
if [[ -n "$DOCKER" ]]; then
  if timeout 20 "$DOCKER" info >/dev/null 2>&1; then
    if timeout 20 "$DOCKER" image inspect "$IMAGEN" >/dev/null 2>&1; then DOCKER_EST="imagen_presente"; else DOCKER_EST="imagen_ausente"; fi
  else DOCKER_EST="daemon_apagado"; fi
else DOCKER_EST="sin_docker"; fi
printf '%s' "$DOCKER_EST" > "$TMP/docker.estado"

python3 -I - "$TMP" "$RUNTIME" "$SALIDA" "$IMAGEN" <<'PY'
import json, os, re, sys, time
tmp, runtime, salida, imagen = sys.argv[1:5]
SECRETO = re.compile(r"(sk-[A-Za-z0-9_-]{12,}|github_pat_\w{12,}|gh[pousr]_\w{12,}|hf_\w{20,}|gsk_[\w-]{12,}|nvapi-[\w-]{12,}|(?i:bearer)\s+\S+)")
def leer(n):
    try:
        return open(os.path.join(tmp, n), encoding="utf-8", errors="replace").read()
    except OSError:
        return ""
def limpia(t):
    return SECRETO.sub("[redactado]", t)
def primera_linea(t):
    for l in t.splitlines():
        if l.strip():
            return limpia(l.strip())[:200]
    return None
COMANDOS = {"swe-agent": "sweagent --help", "openhands": "python -I -c 'import openhands.sdk, openhands.tools'"}
agentes = {}
for a in ("codex", "opencode", "swe-agent", "openhands", "claude-code", "openclaw"):
    ruta, rc = leer(a + ".ruta"), leer(a + ".exit")
    inst = bool(ruta)
    ok = inst and rc == "0"
    version = primera_linea(leer("swe-agent.version" if a == "swe-agent" else a + ".out")) if ok else None  # SWE-agent: su --help no trae version; se lee del paquete
    e = {"instalado": inst, "ok": ok, "version": version, "ruta": ruta or None}
    if inst:
        e["comando"] = COMANDOS.get(a, os.path.basename(ruta) + " --version")
    if inst and not ok:
        e["exit_code"] = int(rc) if rc.lstrip("-").isdigit() else None
    agentes[a] = e
agentes["swe-agent"]["docker"] = {"estado": leer("docker.estado"), "imagen": imagen}
datos = {"generado": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "runtime": runtime, "agentes": agentes}
os.makedirs(os.path.dirname(os.path.abspath(salida)), exist_ok=True)
with open(salida, "w", encoding="utf-8") as f:
    json.dump(datos, f, indent=2, ensure_ascii=False); f.write("\n")
print(json.dumps(datos, indent=2, ensure_ascii=False))
PY