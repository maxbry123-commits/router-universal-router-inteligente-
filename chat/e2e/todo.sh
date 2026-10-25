#!/bin/bash
# Batería completa del chat (móvil y escritorio) contra un Router local con modelos simulados. Uso: bash chat/e2e/todo.sh
# Requisitos: python3 con fastapi/uvicorn (pip install -r mvp/requirements.txt httpx), node con `playwright` y `axe-core` (npm i playwright axe-core eslint),
# Chromium (variable CHROMIUM=/ruta/chromium si no es el de playwright). Cada suite imprime PASS/FAIL con su evidencia.
cd "$(dirname "$0")"; RAIZ=$(cd ../.. && pwd); FRONT=$RAIZ/chat/frontend
for f in "$FRONT"/*.js; do cp "$f" /tmp/chk.mjs; node --check /tmp/chk.mjs >/dev/null 2>&1 || echo "SINTAXIS FAIL $f"; done; echo "== sintaxis JS revisada"
echo "== nombres sin definir (eslint no-undef; 1 aviso conocido y protegido: actualizarMIA): $(cd "$FRONT" && npx eslint -c ../e2e/eslint.config.mjs *.js 2>&1 | grep -c no-undef)"
(fuser -k 8765/tcp >/dev/null 2>&1 || true); sleep 1; nohup python3 servidor.py > servidor.log 2>&1 &
for i in $(seq 1 40); do curl -s -m1 localhost:8765/health >/dev/null && break; sleep 0.5; done
run() { local out; out=$(timeout 240 node "$@" 2>&1 | grep -E "^(movil |desk )?(PASS|FAIL)|^ERROR|reglas fallan"); echo "== $* : $(echo "$out" | grep -c PASS) PASS, $(echo "$out" | grep -cE 'FAIL|ERROR') FAIL"; echo "$out" | grep -E "FAIL|ERROR"; echo "$out" | grep "reglas fallan" | grep -v ": 0 reglas"; }
run modelos_e2e.js movil; run modelos_e2e.js desk; run paso2.js; run refuta.js; run dispositivos.js
for v in movil desk; do run rui.js $v; run paso21.js $v; run axe.js $v; done
run teclado.js; run original.js; run tools_ctl.js movil; run tools_ctl.js desk
for v in movil desk; do echo "== botones $v: $(timeout 240 node botones.js $v 2>&1 | grep -E '^(ERR|REV)' | grep -v 'ON/OFF Team\|ON/OFF Ask\|Bajar al final\|Ir al principio\|Copiar texto\|Enviar\]' | wc -l) por revisar"; done
node --test "$FRONT/test/power.test.js" 2>&1 | grep "^# pass\|^# fail"
(cd "$RAIZ" && python3 -m pytest mvp -q 2>&1 | tail -1)
fuser -k 8765/tcp >/dev/null 2>&1; echo FIN
