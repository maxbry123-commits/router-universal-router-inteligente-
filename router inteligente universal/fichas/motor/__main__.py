import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .api_engine import Motor, cargar_proveedores
from .tareas import Cola, Trabajador, supervisar

AQUI = os.path.dirname(os.path.abspath(__file__))
CARPETA = os.environ.get('FICHA_CARPETA', os.path.join(AQUI, 'estado'))


def leer(nombre):
    ruta = os.path.join(AQUI, nombre)
    return open(ruta, encoding='utf-8').read() if os.path.exists(ruta) else ''


def cola():
    return Cola(os.path.join(CARPETA, 'cola.db'))


def trabajador(c):
    prov = os.environ.get('FICHA_PROVEEDORES', os.path.join(AQUI, 'proveedores.json'))
    latido = os.path.join(CARPETA, 'latido.txt')
    lmax = int(os.environ.get('FICHA_LATIDO_MAX', '600'))
    m = Motor(cargar_proveedores(prov, CARPETA), timeout=int(os.environ.get('FICHA_TIMEOUT', '90')))
    return Trabajador(c, m, leer('PLANTILLA_XRAY_V2.yaml'), leer('MEJORAS_PLANTILLA.yaml'), latido_max=lmax, archivo_latido=latido)


def servidor(c, puerto):
    """Entrada para hablarle al agente SIN detener la tarea: los mensajes quedan en cola y entran en el siguiente paso."""
    token = os.environ.get('FICHA_TOKEN_ENTRADA', '')

    class H(BaseHTTPRequestHandler):
        def _ok(self, d, code=200):
            b = json.dumps(d).encode()
            self.send_response(code)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b)

        def _auth(self):
            return bool(token) and self.headers.get('X-Token') == token

        def do_GET(self):
            self._ok(c.estado() if self._auth() else {'error': 'no'}, 200 if self._auth() else 403)

        def do_POST(self):
            if not self._auth():
                return self._ok({'error': 'no'}, 403)
            d = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))) or b'{}')
            if self.path == '/msg':
                c.mensaje(d['texto'], d.get('tarea'))
            elif self.path == '/tarea':
                c.agregar(d['texto'])
            else:
                return self._ok({'error': 'ruta'}, 404)
            self._ok({'ok': True})

        def log_message(self, *a):
            pass

    ThreadingHTTPServer(('127.0.0.1', puerto), H).serve_forever()


def main():
    a = sys.argv[1:] or ['ayuda']
    c = cola()
    if a[0] == 'tarea':
        print(c.agregar(a[1]))
    elif a[0] == 'msg':
        c.mensaje(a[1], int(a[2]) if len(a) > 2 else None)
    elif a[0] == 'estado':
        print(json.dumps(c.estado()))
    elif a[0] == 'correr':
        trabajador(c).correr(una_pasada='--una' in a)
    elif a[0] == 'supervisar':
        latido = os.path.join(CARPETA, 'latido.txt')
        cmd = [sys.executable, '-m', 'motor', 'correr'] + (['--una'] if '--una' in a else [])
        supervisar(cmd, c, latido, int(os.environ.get('FICHA_LATIDO_MAX', '600')), salir_vacio='--una' in a)
    elif a[0] == 'servidor':
        servidor(c, int(a[1]) if len(a) > 1 else 8765)
    else:
        print('uso: tarea "texto" | msg "texto" [id] | estado | correr [--una] | supervisar [--una] | servidor [puerto]')


if __name__ == '__main__':
    main()
