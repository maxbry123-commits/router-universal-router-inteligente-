# Sidecar de graphiti: runtime real (graphiti_core + base de grafos embebida Kuzu), sin servidor externo.
# Sin LLM: guarda y lee episodios (EpisodicNode). NO extrae entidades ni calcula embeddings (GAP: requiere LLM/embedder).
import argparse
import asyncio
import datetime
import json
import os
import re
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sidecar_http import serve  # noqa: E402
from graphiti_core.driver.kuzu_driver import KuzuDriver  # noqa: E402
from graphiti_core.nodes import EpisodeType, EpisodicNode  # noqa: E402


class GraphitiEngine:
    name = 'graphiti'

    def __init__(self, db):
        os.makedirs(os.path.dirname(db), exist_ok=True)
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.loop.run_forever, daemon=True).start()
        self.driver = KuzuDriver(db=db)

    def _run(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self.loop).result(timeout=30)

    @staticmethod
    def _gid(scope):
        return re.sub('[^A-Za-z0-9_-]', '_', scope) or 'default'

    def health(self):
        return {'status': 'ok', 'engine': 'graphiti', 'driver': 'kuzu', 'modo': 'episodios sin LLM; sin extraccion de entidades ni embeddings'}

    def save(self, scope, key, data):
        node = EpisodicNode(name=key, group_id=self._gid(scope), source=EpisodeType.json, source_description='riu-memoria:' + scope, content=json.dumps(data, ensure_ascii=False), valid_at=datetime.datetime.now(datetime.timezone.utc), entity_edges=[])
        self._run(node.save(self.driver))
        return {'uuid': node.uuid, 'group_id': node.group_id}

    def _episodes(self, scope):
        return self._run(EpisodicNode.get_by_group_ids(self.driver, [self._gid(scope)]))

    @staticmethod
    def _rec(n):
        try:
            data = json.loads(n.content)
        except Exception:  # noqa: BLE001
            data = n.content
        return {'scope': n.source_description.split(':', 1)[-1], 'key': n.name, 'data': data, 'uuid': n.uuid}

    def load(self, scope, key):
        return [self._rec(n) for n in self._episodes(scope) if n.name == key]

    def search(self, scope, query, k=10):
        q = query.lower()
        return [self._rec(n) for n in self._episodes(scope) if q in (n.name + ' ' + n.content).lower()][:k]


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=9101)
    ap.add_argument('--db', default='/tmp/riu-motores/graphiti.kuzu')
    a = ap.parse_args()
    serve(GraphitiEngine(a.db), a.port)
