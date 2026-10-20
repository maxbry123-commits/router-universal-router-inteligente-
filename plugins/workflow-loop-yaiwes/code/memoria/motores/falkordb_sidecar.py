# Sidecar de FalkorDB: runtime REAL del motor (modulo de grafos cargado en redis-server), compilado desde el codigo bajado
# (Componentes del Router/.../componentes descargados/FalkorDB). Cada memoria = nodo (:Memoria {scope, key, data}).
# Cliente: redis-py instalado desde el codigo bajado. Contrato HTTP: sidecar_http.py.
# Uso: python falkordb_sidecar.py --port 9105 --redis redis://127.0.0.1:6390 --grafo memoria
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import redis  # noqa: E402

from sidecar_http import serve  # noqa: E402


def lit(v) -> str:
    return json.dumps(v if isinstance(v, str) else json.dumps(v, ensure_ascii=False, sort_keys=True), ensure_ascii=False)


class FalkorEngine:
    def __init__(self, url: str, grafo: str) -> None:
        self.r = redis.Redis.from_url(url, decode_responses=True)
        self.g = grafo
        self.r.ping()

    def q(self, params: dict, query: str) -> list:
        cab = ' '.join('%s=%s' % (k, lit(v)) for k, v in params.items())
        res = self.r.execute_command('GRAPH.QUERY', self.g, ('CYPHER ' + cab + ' ' if cab else '') + query)
        return res[1] if isinstance(res, list) and len(res) > 1 and isinstance(res[1], list) else []

    @staticmethod
    def _rec(scope: str, row) -> dict:
        data = row[1]
        try:
            data = json.loads(data)
        except Exception:  # noqa: BLE001
            pass
        return {'scope': scope, 'key': row[0], 'data': data}

    def health(self) -> dict:
        return {'status': 'ok', 'engine': 'falkordb', 'modo': 'grafo FalkorDB sobre redis-server', 'grafo': self.g}

    def save(self, scope: str, key: str, data) -> dict:
        self.q({'scope': scope, 'key': key, 'data': data}, 'MERGE (m:Memoria {scope: $scope, key: $key}) SET m.data = $data RETURN m.key')
        return {'grafo': self.g}

    def load(self, scope: str, key: str) -> list:
        return [self._rec(scope, r) for r in self.q({'scope': scope, 'key': key}, 'MATCH (m:Memoria {scope: $scope, key: $key}) RETURN m.key, m.data')]

    def search(self, scope: str, query: str, k: int = 10) -> list:
        rows = self.q({'scope': scope, 'q': query.lower()}, 'MATCH (m:Memoria {scope: $scope}) WHERE toLower(m.key) CONTAINS $q OR toLower(m.data) CONTAINS $q RETURN m.key, m.data ORDER BY m.key LIMIT %d' % int(k))
        return [self._rec(scope, r) for r in rows]


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=9105)
    ap.add_argument('--redis', default='redis://127.0.0.1:6390')
    ap.add_argument('--grafo', default='memoria')
    a = ap.parse_args()
    serve(FalkorEngine(a.redis, a.grafo), a.port)
