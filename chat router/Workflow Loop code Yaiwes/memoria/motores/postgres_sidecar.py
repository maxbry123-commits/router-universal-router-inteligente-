# Sidecar de PostgreSQL: runtime REAL (servidor compilado desde el codigo bajado: Componente open soure.../postgres).
# Habla con el servidor por psql, el cliente oficial que se compila con el servidor. Valores pasados como variables psql
# con comillas seguras (:'var'), nunca pegados al SQL. Contrato HTTP: sidecar_http.py.
# Uso: python postgres_sidecar.py --port 9106 --psql /opt/pg/bin/psql --dsn 'host=127.0.0.1 port=5433 user=memoria dbname=memoria'
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sidecar_http import serve  # noqa: E402

SEP = chr(31)
TABLA = 'CREATE TABLE IF NOT EXISTS riu_memoria (scope text NOT NULL, key text NOT NULL, data jsonb, ts timestamptz DEFAULT now(), PRIMARY KEY (scope, key));'
GUARDAR = "INSERT INTO riu_memoria (scope, key, data) VALUES (:'scope', :'key', :'data'::jsonb) ON CONFLICT (scope, key) DO UPDATE SET data = EXCLUDED.data, ts = now();"
CARGAR = "SELECT key, data::text FROM riu_memoria WHERE scope = :'scope' AND key = :'key';"
BUSCAR = "SELECT key, data::text FROM riu_memoria WHERE scope = :'scope' AND (key || ' ' || data::text) ILIKE '%' || :'q' || '%' ORDER BY key LIMIT %d;"


class PgEngine:
    def __init__(self, psql: str, dsn: str) -> None:
        self.psql, self.dsn = psql, dsn
        self.sql(TABLA, {})

    def sql(self, texto: str, variables: dict) -> list:
        args = [self.psql, '-X', '-q', '-A', '-t', '-v', 'ON_ERROR_STOP=1', '-F', SEP, '-d', self.dsn]
        for k, v in variables.items():
            args += ['-v', '%s=%s' % (k, v)]
        p = subprocess.run(args, input=texto, capture_output=True, text=True, timeout=30)
        if p.returncode != 0:
            raise RuntimeError(p.stderr.strip()[:200])
        return [ln.split(SEP) for ln in p.stdout.splitlines() if ln]

    def _recs(self, scope: str, filas: list) -> list:
        return [{'scope': scope, 'key': f[0], 'data': json.loads(f[1]) if len(f) > 1 and f[1] else None} for f in filas]

    def health(self) -> dict:
        v = self.sql('SELECT version();', {})
        return {'status': 'ok', 'engine': 'postgresql', 'modo': (v[0][0] if v else '?')[:60]}

    def save(self, scope: str, key: str, data) -> dict:
        self.sql(GUARDAR, {'scope': scope, 'key': key, 'data': json.dumps(data, ensure_ascii=False, sort_keys=True)})
        return {'tabla': 'riu_memoria'}

    def load(self, scope: str, key: str) -> list:
        return self._recs(scope, self.sql(CARGAR, {'scope': scope, 'key': key}))

    def search(self, scope: str, query: str, k: int = 10) -> list:
        return self._recs(scope, self.sql(BUSCAR % int(k), {'scope': scope, 'q': query}))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=9106)
    ap.add_argument('--psql', default='/opt/pg/bin/psql')
    ap.add_argument('--dsn', default='host=127.0.0.1 port=5433 user=memoria dbname=memoria')
    a = ap.parse_args()
    serve(PgEngine(a.psql, a.dsn), a.port)
