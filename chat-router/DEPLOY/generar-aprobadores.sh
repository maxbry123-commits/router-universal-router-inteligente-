#!/usr/bin/env bash
# generar-aprobadores.sh <operador> [<operador> ...]
# Genera un token aleatorio por operador, lo imprime UNA vez y emite la linea con sha256 para RIU_SWE_APROBADORES / BRIDGE_APROBADORES.
# Formato exacto (swe_rutas.js::aprobadores y mvp/app.py::_aprobadores): "operador:sha256hex64" separados por coma; operador = [A-Za-z0-9_.@-]{2,64}.
# No guarda nada en disco.
set -euo pipefail
[ "$#" -ge 1 ] || { echo "uso: $0 <operador> [<operador> ...]" >&2; exit 64; }
LINEA=""
echo "TOKENS (se muestran UNA sola vez; entregalos a cada persona por un canal seguro):"
for op in "$@"; do
  [[ "$op" =~ ^[A-Za-z0-9_.@-]{2,64}$ ]] || { echo "operador invalido: '$op' (usa [A-Za-z0-9_.@-], 2-64)" >&2; exit 65; }
  tok=$(head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n')
  hash=$(printf %s "$tok" | sha256sum | cut -d' ' -f1)
  printf '  %-24s %s\n' "$op" "$tok"
  LINEA="${LINEA:+$LINEA,}$op:$hash"
done
echo
echo "Secretos del servicio (solo hashes):"
echo "  RIU_SWE_APROBADORES=$LINEA    # Space del Router"
echo "  BRIDGE_APROBADORES=$LINEA     # bridge"
echo "  RIU_SWE_OPERADORES=$(IFS=,; echo "$*")   # Harness"
