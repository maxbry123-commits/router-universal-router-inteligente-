#!/usr/bin/env bash
# Compila y arranca FalkorDB (modulo de grafos sobre redis-server) y PostgreSQL desde el codigo ya bajado.
# Para la maquina del Router / job de HF (Debian, root). Uso: bash 'chat router/memoria/motores/compilar_motores.sh'
set -u
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
C="$RAIZ/router inteligente universal/Componente open soure router inteligente universal"
DL="$RAIZ/router inteligente universal/Componentes del Router/router inteligente software/componentes todos/componentes descargados"
LOG=/tmp/compilar_motores.log
apt-get update -qq >/dev/null 2>&1
apt-get install -y -qq build-essential bison flex pkg-config libreadline-dev zlib1g-dev redis-server curl clang cmake >>"$LOG" 2>&1
if [ ! -x /opt/pg/bin/psql ]; then
  (cd "$C/postgres" && ./configure --prefix=/opt/pg --without-icu --without-readline >>"$LOG" 2>&1 && make -j"$(nproc)" >>"$LOG" 2>&1 && make install >>"$LOG" 2>&1) || echo 'FALLO_COMPILAR_POSTGRES'
fi
if [ -x /opt/pg/bin/initdb ]; then
  id pg >/dev/null 2>&1 || useradd -m pg
  [ -d /opt/pgdata ] || { mkdir -p /opt/pgdata && chown pg /opt/pgdata && su pg -c '/opt/pg/bin/initdb -D /opt/pgdata -U memoria --auth=trust' >>"$LOG" 2>&1; }
  su pg -c '/opt/pg/bin/pg_ctl -D /opt/pgdata -o "-p 5433 -k /tmp" -l /tmp/pg.log start' >>"$LOG" 2>&1
  sleep 3; /opt/pg/bin/createdb -h 127.0.0.1 -p 5433 -U memoria memoria >>"$LOG" 2>&1 || true
fi
if [ ! -f /opt/falkordb.so ]; then
  command -v cargo >/dev/null || { curl -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal >>"$LOG" 2>&1; . "$HOME/.cargo/env"; }
  (cd "$DL/FalkorDB" && cargo build --release >>"$LOG" 2>&1) && cp "$(ls "$DL"/FalkorDB/target/release/*.so | head -1)" /opt/falkordb.so || echo 'FALLO_COMPILAR_FALKORDB'
fi
[ -f /opt/falkordb.so ] && redis-server --port 6390 --loadmodule /opt/falkordb.so --daemonize yes >>"$LOG" 2>&1
echo "compilados -> postgres: $([ -x /opt/pg/bin/psql ] && echo si || echo NO) | falkordb: $([ -f /opt/falkordb.so ] && echo si || echo NO)"
