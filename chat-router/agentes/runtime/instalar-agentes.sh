#!/usr/bin/env bash
# Instala los agentes REALES en <destino>/{bin,venv,node} (fuera de git; destino = $RIU_AGENTES_RUNTIME o este mismo directorio).
# Idempotente: cada componente deja <destino>/.instalado/<nombre> con la huella de su lockfile y se salta si coincide y el binario responde.
# Versiones fijadas en los lockfiles de este directorio. Usa las fuentes ya descargadas en ../agentes-listos cuando el proyecto lo permite
# (SWE-agent: pip install -e sobre una copia en <destino>/src) y la fuente oficial (npm / PyPI) cuando no (codex y opencode se compilan con Rust/Bun: se instalan sus paquetes npm
# fijados; OpenHands: el SDK descargado es otra version que la fijada, ver RIU_OPENHANDS_FUENTE).
# Uso: instalar-agentes.sh [componente ...]   componentes: codex-opencode claude openclaw sweagent openhands (por defecto todos)
# Variables: RIU_AGENTES_RUNTIME (destino), RIU_PYTHON (python3), RIU_INSTALAR_OMITIR="openclaw ..." (omitir), RIU_OPENHANDS_FUENTE=local (pip install -e
# del SDK descargado), RIU_INSTALAR_TOLERANTE=1 (un componente que falla no hace fallar el script; su estado queda en el JSON de verificar-agentes.sh).
# NUNCA imprime ni lee claves del entorno; solo ejecuta npm y pip con las variables de red que el sandbox ya tenga (proxy, CA).
set -euo pipefail
export OPENHANDS_SUPPRESS_BANNER=1  # el SDK imprime un cuadro al importarse

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESTINO="$(mkdir -p "${RIU_AGENTES_RUNTIME:-$AQUI}" && cd "${RIU_AGENTES_RUNTIME:-$AQUI}" && pwd)"
LISTOS="$AQUI/../agentes-listos"
PYTHON="${RIU_PYTHON:-python3}"
OMITIR=" ${RIU_INSTALAR_OMITIR:-} "
TODOS="codex-opencode claude openclaw sweagent openhands"
SELECCION="${*:-$TODOS}"
FALLOS=()

mkdir -p "$DESTINO/bin" "$DESTINO/venv" "$DESTINO/node" "$DESTINO/src" "$DESTINO/.instalado"
exec 9>"$DESTINO/.instalar.lock"
flock 9  # dos instalaciones a la vez (build y arranque) no se pisan

log() { printf '[instalar-agentes] %s\n' "$*"; }
huella() { cat "$@" | sha256sum | cut -d' ' -f1; }
al_dia() { [[ -f "$DESTINO/.instalado/$1" && "$(cat "$DESTINO/.instalado/$1")" == "$2" ]]; }
marcar() { printf '%s' "$2" > "$DESTINO/.instalado/$1"; }
enlazar() { ln -sfn "$(realpath -s --relative-to="$DESTINO/bin" "$2")" "$DESTINO/bin/$1"; }  # enlace relativo: el runtime se puede mover

requiere_node() {
  command -v node >/dev/null && command -v npm >/dev/null || { log "ERROR: falta node/npm (se necesita Node >= 22)"; return 1; }
  local mayor; mayor="$(node -p 'process.versions.node.split(".")[0]')"
  (( mayor >= 22 )) || { log "ERROR: Node $(node -v) es antiguo (se necesita >= 22)"; return 1; }
}

# $1 componente, $2 carpeta de lockfile (package.json + package-lock.json), resto: "nombre-del-bin:ruta/relativa/en/node_modules/.bin"
instalar_npm() {
  local comp="$1" lock="$AQUI/$2"; shift 2
  local dir="$DESTINO/node/$comp" h; h="$(huella "$lock/package.json" "$lock/package-lock.json")"
  if al_dia "$comp" "$h" && "$dir/node_modules/.bin/${1%%:*}" --version >/dev/null 2>&1; then log "$comp ya instalado (lockfile sin cambios)"; return 0; fi
  requiere_node || return 1
  mkdir -p "$dir"; cp "$lock/package.json" "$lock/package-lock.json" "$dir/"
  log "npm ci $comp ($(grep -c '"resolved"' "$dir/package-lock.json") paquetes fijados)"
  (cd "$dir" && npm ci --no-audit --no-fund --loglevel=error) || return 1
  local par
  for par in "$@"; do
    [[ -x "$dir/node_modules/.bin/${par#*:}" ]] || { log "ERROR: npm no dejo ${par#*:}"; return 1; }
    enlazar "${par%%:*}" "$dir/node_modules/.bin/${par#*:}"
  done
  "$DESTINO/bin/${1%%:*}" --version >/dev/null 2>&1 || { log "ERROR: ${1%%:*} no responde a --version"; return 1; }
  marcar "$comp" "$h"
}

# Copia una fuente descargada a <destino>/src/<nombre> para instalarla EDITABLE desde ahi: agentes-listos/ no recibe egg-info ni build, y el runtime
# no depende de que el repo siga en disco (en el Space el repo del build se borra). SWE-agent necesita editable: lee config/ y tools/ junto al paquete.
copiar_fuente() { # $1 origen, $2 nombre, $3 huella esperada
  local dst="$DESTINO/src/$2"
  if [[ -d "$dst" && "$(cat "$dst/.huella-fuente" 2>/dev/null)" == "$3" ]]; then return 0; fi
  log "copiando fuente $2 a $dst"
  rm -rf "$dst.tmp" "$dst"; mkdir -p "$DESTINO/src" || return 1
  cp -a "$1" "$dst.tmp" || return 1
  printf '%s' "$3" > "$dst.tmp/.huella-fuente"; mv "$dst.tmp" "$dst"
}

# Crea el venv $1 si falta. (Las funciones corren dentro de `if !`, donde set -e no actua: cada paso que puede fallar lleva `|| return 1`.)
crear_venv() {
  local v="$DESTINO/venv/$1"
  [[ -x "$v/bin/python" ]] || { log "creando venv $1"; "$PYTHON" -m venv "$v" || return 1; }
}

instalar_sweagent() {
  local fuente="$LISTOS/SWE-agent/SWE-agent-main" v="$DESTINO/venv/sweagent" h modo
  if [[ -f "$fuente/pyproject.toml" ]]; then modo="fuente"; else modo="oficial"; fi
  h="$(huella "$AQUI/requirements-sweagent.txt" <(echo "$modo") <(grep -s '^__version__' "$fuente/sweagent/__init__.py"))"
  if al_dia sweagent "$h" && "$v/bin/sweagent" --help >/dev/null 2>&1; then log "sweagent ya instalado"; enlazar sweagent "$v/bin/sweagent"; return 0; fi
  crear_venv sweagent || return 1
  if [[ "$modo" == fuente ]]; then
    log "pip install -e SWE-agent (fuente descargada)"
    copiar_fuente "$fuente" SWE-agent-main "$h" || return 1
    "$v/bin/python" -m pip install --quiet --disable-pip-version-check -r "$AQUI/requirements-sweagent.txt" -e "$DESTINO/src/SWE-agent-main" || return 1
  else
    log "fuente local ausente: pip install desde GitHub (tag v1.1.0)"
    "$v/bin/python" -m pip install --quiet --disable-pip-version-check -r "$AQUI/requirements-sweagent.txt" "git+https://github.com/SWE-agent/SWE-agent.git@v1.1.0" || return 1
  fi
  "$v/bin/sweagent" --help >/dev/null || return 1
  enlazar sweagent "$v/bin/sweagent"; marcar sweagent "$h"
}

instalar_openhands() {
  local v="$DESTINO/venv/openhands" fuente="$LISTOS/openhands-software-agent-sdk/code" modo="${RIU_OPENHANDS_FUENTE:-pypi}" h
  h="$(huella "$AQUI/requirements-openhands.txt" <(echo "$modo"))"
  if al_dia openhands "$h" && "$v/bin/python" -I -c 'import openhands.sdk, openhands.tools' >/dev/null 2>&1; then log "openhands ya instalado"; return 0; fi
  crear_venv openhands || return 1
  if [[ "$modo" == local ]]; then
    log "pip install -e OpenHands SDK (fuente descargada)"
    copiar_fuente "$fuente" openhands-sdk-code "$h" || return 1
    "$v/bin/python" -m pip install --quiet --disable-pip-version-check -e "$DESTINO/src/openhands-sdk-code/openhands-sdk" -e "$DESTINO/src/openhands-sdk-code/openhands-tools" || return 1
  else
    log "pip install openhands-sdk/tools fijados (PyPI)"
    "$v/bin/python" -m pip install --quiet --disable-pip-version-check -r "$AQUI/requirements-openhands.txt" || return 1
  fi
  "$v/bin/python" -I -c 'import openhands.sdk, openhands.tools' || return 1
  marcar openhands "$h"
}

for comp in $SELECCION; do
  if [[ "$OMITIR" == *" $comp "* ]]; then log "$comp omitido (RIU_INSTALAR_OMITIR)"; continue; fi
  case "$comp" in
    codex-opencode) paso=(instalar_npm agentes node-agentes codex:codex opencode:opencode) ;;
    claude)         paso=(instalar_npm claude node-claude claude:claude) ;;
    openclaw)       paso=(instalar_npm openclaw node-openclaw openclaw:openclaw) ;;
    sweagent)       paso=(instalar_sweagent) ;;
    openhands)      paso=(instalar_openhands) ;;
    *) log "componente desconocido: $comp"; FALLOS+=("$comp"); continue ;;
  esac
  if ! "${paso[@]}"; then log "FALLO: $comp"; FALLOS+=("$comp"); fi
done

if ((${#FALLOS[@]})); then
  log "no se pudo instalar: ${FALLOS[*]}"
  [[ "${RIU_INSTALAR_TOLERANTE:-0}" == 1 ]] || exit 1
fi
log "listo. Verificar: $AQUI/verificar-agentes.sh"
