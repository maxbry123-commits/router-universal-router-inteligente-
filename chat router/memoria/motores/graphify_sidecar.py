# Sidecar de graphify: SOLO LECTURA (contrato: chat router/memoria/GRAPHIFY-READONLY-CONTRACT.json).
# Construye graph.json con el extractor AST local de graphify (sin LLM) sobre un corpus de codigo y lo consulta.
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sidecar_http import ReadOnlyError, serve  # noqa: E402
from graphify.build import build  # noqa: E402
from graphify.cluster import cluster  # noqa: E402
from graphify.export import to_json  # noqa: E402
from graphify.extract import extract  # noqa: E402
from graphify.serve import _load_graph, _score_nodes  # noqa: E402


class GraphifyEngine:
    name = 'graphify'

    def __init__(self, corpus, out):
        files = sorted(p for c in corpus for p in Path(c).rglob('*.py') if '__pycache__' not in p.parts)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        os.chdir(str(Path(out).resolve().parent.parent))  # graphify solo lee grafos dentro de ./graphify-out del directorio actual
        G = build([extract(files)])
        to_json(G, cluster(G), out)
        self.G = _load_graph(out)
        self.files = len(files)

    def health(self):
        return {'status': 'ok', 'engine': 'graphify', 'modo': 'SOLO LECTURA', 'archivos': self.files, 'nodos': self.G.number_of_nodes(), 'aristas': self.G.number_of_edges()}

    def save(self, scope, key, data):
        raise ReadOnlyError('graphify es solo lectura segun GRAPHIFY-READONLY-CONTRACT.json')

    def _rec(self, scope, nid):
        return {'scope': scope, 'key': nid, 'data': dict(self.G.nodes[nid])}

    def load(self, scope, key):
        return [self._rec(scope, key)] if key in self.G.nodes else []

    def search(self, scope, query, k=10):
        hits = [nid for score, nid in _score_nodes(self.G, query.lower().split()) if score > 0]
        return [self._rec(scope, nid) for nid in hits[:k]]


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=9103)
    ap.add_argument('--out', default='/tmp/riu-motores/graphify-out/graph.json')
    ap.add_argument('--corpus', nargs='+', required=True)
    a = ap.parse_args()
    serve(GraphifyEngine(a.corpus, a.out), a.port)
