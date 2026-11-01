#!/usr/bin/env bash
# Para `source`: pone <runtime>/bin al frente del PATH y exporta RIU_*_BIN / RIU_OPENHANDS_PYTHON de lo que este instalado en el runtime.
# Los adaptadores (agentes/adaptadores/_comun.py) ya buscan en <runtime>/bin por defecto; esto es para shells, boot.sh y herramientas externas.
# No pisa lo que ya este definido (RIU_*_BIN existentes mandan) y nunca toca claves.
_riu_aqui="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export RIU_AGENTES_RUNTIME="${RIU_AGENTES_RUNTIME:-$_riu_aqui}"
case ":$PATH:" in *":$RIU_AGENTES_RUNTIME/bin:"*) ;; *) export PATH="$RIU_AGENTES_RUNTIME/bin:$PATH" ;; esac
_riu_exporta() { # $1 variable, $2 ejecutable
  if [ -z "${!1:-}" ] && [ -x "$RIU_AGENTES_RUNTIME/bin/$2" ]; then export "$1=$RIU_AGENTES_RUNTIME/bin/$2"; fi
}
_riu_exporta RIU_CODEX_BIN codex
_riu_exporta RIU_OPENCODE_BIN opencode
_riu_exporta RIU_SWEAGENT_BIN sweagent
_riu_exporta RIU_CLAUDE_BIN claude
if [ -z "${RIU_OPENHANDS_PYTHON:-}" ] && [ -x "$RIU_AGENTES_RUNTIME/venv/openhands/bin/python" ]; then export RIU_OPENHANDS_PYTHON="$RIU_AGENTES_RUNTIME/venv/openhands/bin/python"; fi
unset -f _riu_exporta; unset _riu_aqui
