# Servidor HTTP minimo (solo libreria estandar) con el contrato que usa ComponentAdapter:
#   GET / (2xx = CONNECTED), POST /save {scope,key,data}, GET /load?scope&key, GET /search?scope&query&k -> {records: [...]}
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


class ReadOnlyError(Exception):
    pass


def serve(engine, port, host='127.0.0.1'):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def _send(self, code, obj):
            raw = json.dumps(obj, ensure_ascii=False, default=str).encode('utf-8')
            self.send_response(code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            u = urlparse(self.path)
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            try:
                if u.path in ('/', '/health'):
                    return self._send(200, engine.health())
                if u.path == '/load':
                    return self._send(200, {'records': engine.load(q.get('scope', ''), q.get('key', ''))})
                if u.path == '/search':
                    return self._send(200, {'records': engine.search(q.get('scope', ''), q.get('query', ''), int(q.get('k', '10')))})
                return self._send(404, {'error': 'ruta desconocida'})
            except Exception as exc:  # noqa: BLE001
                return self._send(500, {'error': type(exc).__name__, 'detalle': str(exc)[:200]})

        def do_POST(self):
            if urlparse(self.path).path != '/save':
                return self._send(404, {'error': 'ruta desconocida'})
            try:
                n = int(self.headers.get('Content-Length', '0'))
                body = json.loads(self.rfile.read(n) or b'{}')
                return self._send(200, engine.save(body['scope'], body['key'], body.get('data')))
            except ReadOnlyError as exc:
                return self._send(405, {'error': 'READ_ONLY', 'detalle': str(exc)})
            except Exception as exc:  # noqa: BLE001
                return self._send(500, {'error': type(exc).__name__, 'detalle': str(exc)[:200]})

    ThreadingHTTPServer((host, port), Handler).serve_forever()
