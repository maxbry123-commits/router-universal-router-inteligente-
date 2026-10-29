import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import pytest
from click.testing import CliRunner

from cli_anything.memoria.memoria_cli import cli

TODOS = ('AGENTDB', 'GRAPHITI', 'GRAPHIFY', 'MEMANTO', 'FALKORDB', 'POSTGRESQL')


def falso(solo_lectura=False):
    datos = []

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            return

        def _j(self, code, obj):
            b = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header('Content-Length', str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def do_GET(self):
            u = urlparse(self.path)
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            if u.path == '/':
                return self._j(200, {'status': 'ok', 'engine': 'falso'})
            if u.path == '/load':
                return self._j(200, {'records': [d for d in datos if d['scope'] == q['scope'] and d['key'] == q['key']]})
            if u.path == '/search':
                return self._j(200, {'records': [d for d in datos if q['query'].lower() in json.dumps(d).lower()]})
            return self._j(404, {})

        def do_POST(self):
            if solo_lectura:
                return self._j(405, {'error': 'SOLO_LECTURA'})
            d = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            datos.append(d)
            return self._j(200, {'id': len(datos)})

    s = ThreadingHTTPServer(('127.0.0.1', 0), H)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s, 'http://127.0.0.1:%d' % s.server_address[1]


@pytest.fixture()
def pool(monkeypatch):
    for n in TODOS:
        monkeypatch.delenv('RIU_%s_URL' % n, raising=False)
        monkeypatch.delenv('RIU_%s_HTTP_URL' % n, raising=False)
    servidores = []
    for nombre, ro in (('AGENTDB', False), ('GRAPHITI', False), ('GRAPHIFY', True)):
        s, u = falso(ro)
        servidores.append(s)
        monkeypatch.setenv('RIU_%s_URL' % nombre, u)
    yield
    for s in servidores:
        s.shutdown()


def correr(*args):
    r = CliRunner().invoke(cli, ['--json', *args])
    return r.exit_code, (json.loads(r.output) if r.output.strip() else None)


def test_estado(pool):
    code, d = correr('motores', 'estado')
    est = {m['motor']: m['estado'] for m in d['motores']}
    assert code == 0 and est['agentdb'] == est['graphiti'] == est['graphify'] == 'CONNECTED'
    assert est['memanto'] == est['falkordb'] == est['postgresql'] == 'GAP'


def test_guardar_respeta_solo_lectura(pool):
    code, d = correr('memoria', 'guardar', 'p', 'k1', json.dumps({'texto': 'hola orquesta'}))
    assert code == 0 and d['guardado_en'] == ['agentdb', 'graphiti']
    assert d['omitidos']['graphify'] == 'solo lectura'


def test_cargar_y_buscar_sin_repetidos(pool):
    correr('memoria', 'guardar', 'p', 'k1', json.dumps({'texto': 'hola orquesta'}))
    code, d = correr('memoria', 'cargar', 'p', 'k1')
    assert d['motor'] == 'agentdb' and d['records'][0]['data'] == {'texto': 'hola orquesta'}
    code, d = correr('memoria', 'buscar', 'p', 'orquesta')
    assert len(d['resultados']) == 1 and d['resultados'][0]['motores'] == ['agentdb', 'graphiti']


def test_determinista(pool):
    correr('memoria', 'guardar', 'p', 'a', json.dumps({'t': 'uno dos'}))
    correr('memoria', 'guardar', 'p', 'b', json.dumps({'t': 'uno'}))
    assert correr('memoria', 'buscar', 'p', 'uno dos') == correr('memoria', 'buscar', 'p', 'uno dos')


def test_sin_motores_sale_con_error(monkeypatch):
    for n in TODOS:
        monkeypatch.delenv('RIU_%s_URL' % n, raising=False)
        monkeypatch.delenv('RIU_%s_HTTP_URL' % n, raising=False)
    code, d = correr('memoria', 'guardar', 'p', 'k', '{}')
    assert code == 1 and d['ok'] is False
