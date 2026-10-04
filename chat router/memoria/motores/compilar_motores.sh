#!/usr/bin/env bash
# Arranca FalkorDB (modulo de grafos sobre redis-server) y PostgreSQL para la memoria. MVP:
# PostgreSQL: compila el codigo bajado; si falla, usa el paquete oficial de Debian (no bloquea).
# FalkorDB: modulo oficial ya compilado (lo que su repo indica por defecto); si no baja, intenta cargo build del codigo bajado.
set -u
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
C="$RAIZ/router inteligente universal/Componente open soure router inteligente universal"
DL="$RAIZ/router inteligente universal/Componentes del Router/router inteligente software/componentes todos/componentes descargados"
LOG=/tmp/compilar_motores.log
apt-get update -qq >/dev/null 2>&1
apt-get install -y -qq build-essential bison flex pkg-config libreadline-dev zlib1g-dev redis-server curl libgomp1 >>"$LOG" 2>&1
if [ ! -x /opt/pg/bin/psql ]; then
  if (cd "$C/postgres" && ./configure --prefix=/opt/pg --without-icu --without-readline >>"$LOG" 2>&1 && make -j"$(nproc)" >>"$LOG" 2>&1 && make install >>"$LOG" 2>&1); then
    echo 'postgres: compilado del codigo bajado'
  else
    echo 'postgres: fallo al compilar el codigo bajado, causa:'; grep -iE 'error' "$LOG" | tail -3 | cut -c1-200
    apt-get install -y -qq postgresql >>"$LOG" 2>&1 && ln -sfn "$(ls -d /usr/lib/postgresql/*/ | head -1)" /opt/pg && echo 'postgres: paquete oficial instalado'
  fi
fi
if [ -x /opt/pg/bin/initdb ]; then
  id pg >/dev/null 2>&1 || useradd -m pg
  [ -d /opt/pgdata ] || { mkdir -p /opt/pgdata && chown pg /opt/pgdata && su pg -c '/opt/pg/bin/initdb -D /opt/pgdata -U memoria --auth=trust' >>"$LOG" 2>&1; }
  su pg -c '/opt/pg/bin/pg_ctl -D /opt/pgdata -o "-p 5433 -k /tmp" -l /tmp/pg.log start' >>"$LOG" 2>&1
  sleep 3; /opt/pg/bin/createdb -h 127.0.0.1 -p 5433 -U memoria memoria >>"$LOG" 2>&1 || true
fi
if [ ! -f /opt/falkordb.so ]; then
  for a in falkordb-x64.so falkordb.so; do curl -sSfL -o /opt/falkordb.so "https://github.com/FalkorDB/FalkorDB/releases/latest/download/$a" 2>>"$LOG" && break; rm -f /opt/falkordb.so; done
  [ -f /opt/falkordb.so ] && echo 'falkordb: modulo oficial descargado' || {
    command -v cargo >/dev/null || { curl -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal >>"$LOG" 2>&1; . "$HOME/.cargo/env"; }
    (cd "$DL/FalkorDB" && cargo build --release >>"$LOG" 2>&1) && cp "$(ls "$DL"/FalkorDB/target/release/*.so | head -1)" /opt/falkordb.so && echo 'falkordb: compilado del codigo bajado' || echo 'FALLO_FALKORDB'; }
fi
if [ -f /opt/falkordb.so ]; then
  if ! redis-server --version | grep -qE 'v=(7[.][2-9]|[89][.])'; then  # FalkorDB pide Redis 7.2 o mayor; Debian trae 7.0
    curl -fsSL https://packages.redis.io/gpg | gpg --dearmor --yes -o /usr/share/keyrings/redis.gpg 2>>"$LOG"
    echo "deb [signed-by=/usr/share/keyrings/redis.gpg] https://packages.redis.io/deb $(. /etc/os-release; echo $VERSION_CODENAME) main" > /etc/apt/sources.list.d/redis.list
    apt-get update -qq >/dev/null 2>&1
    V=$(apt-cache madison redis-server | awk '{print $3}' | grep -E '^6:7[.]4' | head -1)
    apt-get install -y -qq --allow-downgrades redis-server${V:+=$V} redis-tools${V:+=$V} >>"$LOG" 2>&1
  fi
  redis-server --port 6390 --loadmodule /opt/falkordb.so --daemonize yes --logfile /tmp/redis6390.log >>"$LOG" 2>&1; sleep 2
  redis-cli -p 6390 GRAPH.LIST >/dev/null 2>&1 || { echo "falkordb: no cargo en $(redis-server --version | cut -c1-40), causa:"; tail -3 /tmp/redis6390.log | cut -c1-200; }
fi
echo "listos -> postgres: $([ -x /opt/pg/bin/psql ] && echo si || echo NO) | falkordb: $(redis-cli -p 6390 GRAPH.LIST >/dev/null 2>&1 && echo si || echo NO)"
