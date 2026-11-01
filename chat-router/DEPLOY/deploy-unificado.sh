#!/usr/bin/env bash
# deploy-unificado.sh — comprueba, fusiona origin/main, sube a main + rama de trabajo y verifica el SHA desplegado.
#
#   bash chat-router/DEPLOY/deploy-unificado.sh                 # SIMULACRO (por defecto): corre guardia, suites y escaneo; NO fusiona ni sube
#   bash chat-router/DEPLOY/deploy-unificado.sh --rapido        # idem con suites reducidas
#   bash chat-router/DEPLOY/deploy-unificado.sh --ejecutar      # merge de origin/main + push a main y a la rama actual + hook + verificacion
#
# Opciones: --dry-run (defecto) | --ejecutar | --rapido | --sin-espera (no sondea el Space tras subir) | -h
# Entorno (todo opcional; NUNCA se imprimen valores):
#   VERCEL_DEPLOY_HOOK  URL del Deploy Hook de Vercel (secreto: solo por entorno, jamas en el repo)
#   SPACE_URL           defecto https://comand-center-1-riu-router.hf.space
#   VERCEL_URL_BASE     defecto https://riu-jev-bridge.vercel.app
#   ESPERA_S / INTERVALO_S  espera maxima (600) y pausa entre sondeos (20) de la verificacion
#   RIU_API_KEY         si existe, /web/health se consulta con X-API-Key (detalle completo; solo se imprimen conteos)
# Idempotente: repetirlo no duplica nada (merge sin cambios, push sin novedades, hook = otro despliegue del mismo SHA).
# No hace commit, no usa stash y no guarda secretos en disco.
set -euo pipefail

EJECUTAR=0; RAPIDO=0; ESPERAR=1
for a in "$@"; do
  case "$a" in
    --ejecutar) EJECUTAR=1 ;;
    --dry-run) EJECUTAR=0 ;;
    --rapido) RAPIDO=1 ;;
    --sin-espera) ESPERAR=0 ;;
    -h|--help) sed -n '2,17p' "$0"; exit 0 ;;
    *) echo "opcion desconocida: $a (usa -h)" >&2; exit 64 ;;
  esac
done

RAIZ=$(git rev-parse --show-toplevel)
cd "$RAIZ"
RAMA=$(git branch --show-current || true)
SPACE_URL=${SPACE_URL:-https://comand-center-1-riu-router.hf.space}
VERCEL_URL_BASE=${VERCEL_URL_BASE:-https://riu-jev-bridge.vercel.app}
ESPERA_S=${ESPERA_S:-600}; INTERVALO_S=${INTERVALO_S:-20}
FALLOS=0
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

titulo() { printf '\n== %s\n' "$*"; }
ok() { printf '  OK    %s\n' "$*"; }
aviso() { printf '  AVISO %s\n' "$*"; }
falla() {
  printf '  FALLA %s\n' "$*"; FALLOS=$((FALLOS + 1))
  if [ "$EJECUTAR" = 1 ]; then echo "ABORTO: con --ejecutar no se sigue tras un fallo (nada se subio)." >&2; exit 1; fi
}
resumen_log() {
  local r; r=$(grep -hE '^# (tests|pass|fail) |[0-9]+ (passed|failed)' "$1" | tr '\n' ' ' | sed 's/ \+/ /g')
  printf '%s' "${r:-$(tail -n 1 "$1" | cut -c1-160)}"
}

# suite <nombre> <comando...>: corre el comando; solo imprime conteos (pass/fail), nunca la salida completa
suite() {
  local nombre=$1; shift; local log="$TMP/suite.$RANDOM.log"
  if "$@" >"$log" 2>&1; then ok "$nombre: $(resumen_log "$log")"
  else falla "$nombre: $(resumen_log "$log") (ultimas lineas: $(tail -n 2 "$log" | tr '\n' ' ' | cut -c1-160))"; fi
}

printf 'deploy-unificado: modo=%s rapido=%s rama=%s raiz=%s\n' "$([ "$EJECUTAR" = 1 ] && echo EJECUTAR || echo SIMULACRO)" "$RAPIDO" "${RAMA:-?}" "$RAIZ"
[ -n "$RAMA" ] || { echo "HEAD desacoplado: cambia a una rama antes de desplegar" >&2; exit 1; }

# ---------------------------------------------------------------- 1. guardia de cableado
titulo "1. Guardia de cableado"
suite "guardia_cableado" python3 chat-router/chat/auditoria/guardia_cableado.py

# ---------------------------------------------------------------- 2. suites
titulo "2. Suites ($([ "$RAPIDO" = 1 ] && echo rapido || echo completo))"
export PYTHONPATH="$RAIZ/router-mvp:$RAIZ/chat-router${PYTHONPATH:+:$PYTHONPATH}"
BRIDGE="chat-router/SWE CODE/web-bridge"
if [ "$RAPIDO" = 1 ]; then
  suite "bridge node --test (subconjunto)" bash -c 'cd "$1" && node --test test/swe_rutas.test.mjs test/autoactualizar.test.mjs test/seguridad.test.mjs test/despliegue.test.mjs test/openclaw.test.mjs' _ "$BRIDGE"
else
  suite "bridge node --test" bash -c 'cd "$1" && node --test test/*.test.mjs' _ "$BRIDGE"
  if [ -f "chat-router/SWE CODE free/puente-movil/test/server.test.mjs" ]; then
    suite "puente-movil node --test" bash -c 'cd "chat-router/SWE CODE free/puente-movil" && node --test test/*.test.mjs'
  fi
fi
suite "frontend node --test" bash -c 'cd chat-router/chat/frontend && node --test test/*.test.mjs test/*.test.js'
if python3 -m pytest --version >/dev/null 2>&1; then
  M=router-mvp/mvp
  if [ "$RAPIDO" = 1 ]; then
    suite "python pytest (subconjunto)" python3 -m pytest -q -p no:cacheprovider "$M/test_app.py" "$M/test_run.py" "$M/test_harness.py" "$M/test_harness_swe.py" "$M/test_auth_clave.py" "$M/test_swe_yaiwes.py" chat-router/chat/backend/deepseek_harness
  else
    suite "python pytest (router-mvp/mvp + harness + banco del bridge)" python3 -m pytest -q -p no:cacheprovider "$M" chat-router/chat/backend/deepseek_harness "chat-router/SWE CODE/web-bridge/test_claves_banco.py" "chat-router/SWE CODE/web-bridge/test_memoria_hf.py"
  fi
else
  falla "python3 -m pytest no disponible (pip install pytest httpx)"
fi

# ---------------------------------------------------------------- 3. secretos
titulo "3. Escaneo de secretos (gsk_ nvapi- ghp_ github_pat_ hf_) en lo staged, el arbol de trabajo y lo que se subiria"
PATRON='gsk_[A-Za-z0-9]{20,}|nvapi-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|hf_[A-Za-z0-9]{30,}'
git fetch --quiet origin main 2>/dev/null || aviso "git fetch origin main fallo (sin red?): se usa el origin/main local"
escanear() { git "$@" 2>/dev/null | grep -E '^\+' | grep -vE '^\+\+\+' | grep -cE "$PATRON" || true; }
N_STAGED=$(escanear diff --cached -U0)
N_TRABAJO=$(escanear diff -U0)
N_SALIDA=0; if git rev-parse --verify -q origin/main >/dev/null; then N_SALIDA=$(escanear diff -U0 origin/main..HEAD); fi
N_NUEVOS=0
while IFS= read -r f; do
  case "$f" in */node_modules/*|*.png|*.jpg|*.gz|*.bin|*.apk) continue ;; esac
  if [ -f "$f" ]; then n=$(grep -cE "$PATRON" "$f" 2>/dev/null || true); N_NUEVOS=$((N_NUEVOS + ${n:-0})); fi
done < <(git ls-files -o --exclude-standard)
printf '  lineas con patron de secreto: staged=%s trabajo=%s a_subir=%s sin_seguimiento=%s\n' "$N_STAGED" "$N_TRABAJO" "$N_SALIDA" "$N_NUEVOS"
if [ $((N_STAGED + N_TRABAJO + N_SALIDA + N_NUEVOS)) -gt 0 ]; then
  falla "posible secreto en el codigo a subir (revisalo a mano con git diff; aqui no se imprimen coincidencias)"
else ok "sin patrones de secretos"; fi

# ---------------------------------------------------------------- 4. merge de origin/main
titulo "4. Merge de origin/main en $RAMA"
if git rev-parse --verify -q origin/main >/dev/null; then
  read -r DETRAS ADELANTE < <(git rev-list --left-right --count origin/main...HEAD)
  printf '  %s: detras de origin/main=%s adelante=%s\n' "$RAMA" "$DETRAS" "$ADELANTE"
  SIN_COMMIT=$(git status --porcelain --untracked-files=no | wc -l | tr -d ' ')
  [ "$SIN_COMMIT" = 0 ] || aviso "$SIN_COMMIT archivos con cambios sin commit: NO se suben (este script no hace commit)"
  if [ "$DETRAS" = 0 ]; then ok "ya contiene origin/main: no hay nada que fusionar"
  elif [ "$EJECUTAR" = 1 ]; then
    if git merge --no-edit origin/main >"$TMP/merge.log" 2>&1; then ok "merge hecho"
    else git merge --abort 2>/dev/null || true; falla "conflicto al fusionar origin/main (merge abortado; resuelve a mano)"; fi
  else
    if git merge-tree --write-tree HEAD origin/main >/dev/null 2>&1; then ok "SIMULACRO: el merge seria limpio (sin conflictos)"
    else falla "SIMULACRO: el merge tendria conflictos con origin/main"; fi
  fi
  if [ "$EJECUTAR" = 1 ]; then suite "guardia_cableado tras el merge" python3 chat-router/chat/auditoria/guardia_cableado.py; fi
else aviso "no existe origin/main local"; fi

SHA=$(git rev-parse HEAD)

# ---------------------------------------------------------------- 5. push
titulo "5. Push"
if [ "$EJECUTAR" = 1 ]; then
  git push origin "HEAD:refs/heads/main" && ok "push a main"
  if [ "$RAMA" != main ]; then git push origin "HEAD:refs/heads/$RAMA" && ok "push a $RAMA"; fi
else
  echo "  SIMULACRO: git push origin HEAD:refs/heads/main y HEAD:refs/heads/$RAMA (sin --ejecutar no se sube)"
fi

# ---------------------------------------------------------------- 6. Vercel
titulo "6. Vercel (riu-jev-bridge)"
if [ -n "${VERCEL_DEPLOY_HOOK:-}" ]; then
  if [ "$EJECUTAR" = 1 ]; then
    if curl -fsS --max-time 30 -X POST -o /dev/null "$VERCEL_DEPLOY_HOOK"; then ok "Deploy Hook disparado"; else falla "el Deploy Hook de Vercel respondio con error"; fi
  else echo "  SIMULACRO: dispararia el Deploy Hook (variable VERCEL_DEPLOY_HOOK definida)"; fi
else
  cat <<'TXT'
  VERCEL_DEPLOY_HOOK no esta definida. Si el proyecto tiene la integracion Git, el push a main ya despliega solo.
  Para crear el hook (manual, una vez): Vercel -> proyecto riu-jev-bridge -> Settings -> Git -> Deploy Hooks
    -> nombre "deploy-unificado", rama "main" -> Create -> copia la URL y exportala SOLO en tu terminal:
       export VERCEL_DEPLOY_HOOK='<url del hook>'      # secreto: no la guardes en archivos del repo
TXT
fi

# ---------------------------------------------------------------- 7. Harness / agentes (solo aviso)
titulo "7. Harness y agentes (no se actualizan solos)"
echo "  Space del Harness: SIN autopull -> reinicialo a mano (panel HF: Restart / Factory reboot) para que clone el nuevo main."
if [ -f chat-router/agentes/runtime/instalar-agentes.sh ]; then echo "  instalar-agentes.sh existe: ejecutalo DENTRO del entorno del Harness (bash chat-router/agentes/runtime/instalar-agentes.sh)."
else echo "  chat-router/agentes/runtime/instalar-agentes.sh aun no existe en este arbol."; fi

# ---------------------------------------------------------------- 8. verificacion
titulo "8. Verificacion del SHA desplegado (solo conteos)"
ESPERADO=$SHA
[ "$EJECUTAR" = 1 ] || ESPERADO=$(git rev-parse -q --verify origin/main || echo "$SHA")
E10=${ESPERADO:0:10}
printf '  SHA esperado=%s (%s)\n' "$E10" "$([ "$EJECUTAR" = 1 ] && echo "el que se subio" || echo "origin/main; en simulacro solo se mira el estado actual")"

sonda() {  # sonda <url> [cabecera]: JSON por stdout, vacio si falla
  if [ -n "${2:-}" ]; then curl -fsS --max-time 15 -H "$2" "$1" 2>/dev/null || true; else curl -fsS --max-time 15 "$1" 2>/dev/null || true; fi
}
campo() {  # campo <json> <ruta.punteada>: valor (o conteo si es objeto/lista) o vacio
  printf '%s' "$1" | python3 -I -c 'import sys,json
try:
    d=json.load(sys.stdin)
    for k in sys.argv[1].split("."):
        d=d[k]
    print(d if not isinstance(d,(dict,list)) else len(d))
except Exception:
    pass' "$2"
}
ronda() {  # una pasada; devuelve 0 si Space /health y Vercel version.json coinciden con el SHA esperado
  local h w v c cs cv pend=0
  h=$(sonda "$SPACE_URL/health"); cs=$(campo "$h" commit)
  if [ -z "$h" ]; then echo "  Space /health: sin respuesta"; pend=1
  elif [ "${cs:0:10}" = "$E10" ]; then echo "  Space /health: status=$(campo "$h" status) commit=${cs:0:10} COINCIDE"
  else echo "  Space /health: status=$(campo "$h" status) commit=${cs:0:10} NO coincide"; pend=1; fi
  if [ -n "${RIU_API_KEY:-}" ]; then w=$(sonda "$SPACE_URL/web/health" "X-API-Key: $RIU_API_KEY"); else w=$(sonda "$SPACE_URL/web/health"); fi
  if [ -z "$w" ]; then echo "  Space /web/health: sin respuesta"; pend=1
  else
    c=$(campo "$w" commit)
    echo "  Space /web/health: ok=$(campo "$w" ok) pool.total=$(campo "$w" pool.total) groq=$(campo "$w" respaldo.groq) nvidia=$(campo "$w" respaldo.nvidia) hf_local=$(campo "$w" respaldo.hf_local) commit=${c:0:10}${c:+ }$([ -n "$c" ] || echo "(el bridge no lo devuelve; vale el /health del Space: mismo clon)")"
    if [ -n "$c" ] && [ "${c:0:10}" != "$E10" ]; then pend=1; fi
  fi
  v=$(sonda "$VERCEL_URL_BASE/version.json"); cv=$(campo "$v" commit)
  if [ -z "$v" ]; then echo "  Vercel /version.json: sin respuesta"; pend=1
  elif [ "${cv:0:10}" = "$E10" ]; then echo "  Vercel /version.json: commit=${cv:0:10} COINCIDE"
  else echo "  Vercel /version.json: commit=${cv:0:10} NO coincide"; pend=1; fi
  return $pend
}
if [ "$EJECUTAR" = 1 ] && [ "$ESPERAR" = 1 ]; then
  T0=$(date +%s); OKV=0
  while :; do
    if ronda; then OKV=1; break; fi
    [ $(( $(date +%s) - T0 )) -lt "$ESPERA_S" ] || break
    echo "  ... reintento en ${INTERVALO_S}s (autopull del Router: <= 60 s; Vercel: build ~1-2 min)"; sleep "$INTERVALO_S"
  done
  if [ "$OKV" = 1 ]; then ok "Space y Vercel sirven el SHA $E10"
  else aviso "tras ${ESPERA_S}s no coinciden todos los destinos (el Harness, S1-S3, APK y OpenClaw se actualizan aparte: ver DEPLOY.md)"; FALLOS=$((FALLOS + 1)); fi
else
  ronda || true
fi

# ---------------------------------------------------------------- resumen
titulo "Resumen"
if [ "$EJECUTAR" = 1 ]; then echo "  EJECUTADO. SHA subido: $E10. Fallos/avisos de verificacion: $FALLOS"
else echo "  SIMULACRO terminado: nada se fusiono ni se subio. Fallos: $FALLOS. Para subir: bash chat-router/DEPLOY/deploy-unificado.sh --ejecutar"; fi
[ "$FALLOS" = 0 ]
