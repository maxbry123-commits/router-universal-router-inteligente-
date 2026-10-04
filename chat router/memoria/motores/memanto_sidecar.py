# Sidecar de memanto: su logica REAL (MemoryWriteService / MemoryReadService, sin cambios) sobre el cliente LOCAL
# (memanto/cliente_local.py: SQLite + busqueda por palabras; respuestas con el mini kernel LLM solo si esta configurado).
# Codigo copiado de Componente open soure.../memanto (original intacto). scope = agent_id de memanto; key = titulo.
# Uso: python memanto_sidecar.py --port 9102 --db /tmp/riu-motores/memanto.sqlite
from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from memanto.app.core import MemoryRecord  # noqa: E402
from memanto.app.services.memory_read_service import MemoryReadService  # noqa: E402
from memanto.app.services.memory_write_service import MemoryWriteService  # noqa: E402
from memanto.cliente_local import LocalClient  # noqa: E402
from sidecar_http import serve  # noqa: E402

FUENTE = os.environ.get('MEMANTO_SOURCE', 'agent')


def _agente(scope: str) -> str:
    return re.sub('[^A-Za-z0-9_-]', '_', scope) or 'default'


def _items(r) -> list:
    if isinstance(r, dict):
        for k in ('memories', 'results', 'items'):
            if isinstance(r.get(k), list):
                return r[k]
    return r if isinstance(r, list) else []


class MemantoEngine:
    def __init__(self, db: str) -> None:
        c = LocalClient(db)
        self.w, self.r = MemoryWriteService(c), MemoryReadService(c)

    @staticmethod
    def _rec(scope: str, m: dict) -> dict:
        data = m.get('content')
        try:
            data = json.loads(data)
        except Exception:  # noqa: BLE001
            pass
        return {'scope': scope, 'key': m.get('title'), 'data': data, 'id': m.get('id'), 'tipo': m.get('type')}

    def health(self) -> dict:
        return {'status': 'ok', 'engine': 'memanto', 'modo': 'servicios reales de memanto con cliente local (sin nube)'}

    def save(self, scope: str, key: str, data) -> dict:
        rec = MemoryRecord(title=key, content=json.dumps(data, ensure_ascii=False, sort_keys=True), agent_id=_agente(scope), actor_id='riu-orquestador', source=FUENTE)
        r = self.w.store_memory(rec)
        return {'id': (r or {}).get('memory_id') or rec.id, 'estado': (r or {}).get('status')}

    def load(self, scope: str, key: str) -> list:
        found = _items(self.r.search_memories(query=key, agent_id=_agente(scope), limit=50))
        return [self._rec(scope, m) for m in found if m.get('title') == key]

    def search(self, scope: str, query: str, k: int = 10) -> list:
        return [self._rec(scope, m) for m in _items(self.r.search_memories(query=query, agent_id=_agente(scope), limit=k))]


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=9102)
    ap.add_argument('--db', default='/tmp/riu-motores/memanto.sqlite')
    a = ap.parse_args()
    serve(MemantoEngine(a.db), a.port)
