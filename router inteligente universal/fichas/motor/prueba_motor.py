"""Pruebas locales con un servidor falso (no gasta cupo de ninguna API). Uso, desde la carpeta fichas: python -m motor.prueba_motor"""
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .api_engine import BLOQUE, LIMITE_LLAMADA, TIMEOUT, ErrorApi, Motor, Proveedor
from .limites import Guarda
from .tareas import Cola, MARCA_OK, Trabajador

ESTADO = {'n': {}, 'cargas': []}


class Falso(BaseHTTPRequestHandler):
    def do_POST(self):
        ruta = self.path
        ESTADO['n'][ruta] = ESTADO['n'].get(ruta, 0) + 1
        n = ESTADO['n'][ruta]
        carga = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        ESTADO['cargas'].append((ruta, carga))
        if ruta == '/caido':
            return self._r(500, {})
        if ruta == '/limite' and n == 1:
            self.send_response(429)
            self.send_header('Retry-After', '0')
            self.end_headers()
            return
        if ruta == '/lento' and n == 1:
            time.sleep(3)
        if ruta == '/ok':
            time.sleep(0.4)
        txt = carga['messages'][-1]['content']
        salida = 'avance'
        if 'paso=3' in txt:
            salida = 'listo ' + MARCA_OK
        self._r(200, {'choices': [{'message': {'content': salida}}]})

    def _r(self, code, d):
        b = json.dumps(d).encode()
        self.send_response(code)
        self.end_headers()
        try:
            self.wfile.write(b)
        except Exception:
            pass

    def log_message(self, *a):
        pass


def servidor():
    s = ThreadingHTTPServer(('127.0.0.1', 0), Falso)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s, 'http://127.0.0.1:' + str(s.server_address[1])


RES = []


def chequeo(nombre, ok, detalle=''):
    RES.append(ok)
    print(('PASS ' if ok else 'FAIL ') + nombre + (' | ' + str(detalle) if detalle else ''))


def pruebas_api(base, tmp):
    mk = lambda ruta, perfil='libre', nom=None: Proveedor(nom or ruta.strip('/'), base + ruta, 'm', 'K', perfil, tmp)
    chequeo('timeout de llamada = 1,5 min', TIMEOUT == 90, TIMEOUT)
    m = Motor([mk('/limite')], dormir=lambda s: None)
    chequeo('API 1 reintento tras 429', m.llamar([{'role': 'user', 'content': 'hola'}]) == 'avance' and ESTADO['n']['/limite'] == 2)
    m = Motor([mk('/caido'), mk('/bueno')], dormir=lambda s: None)
    r = m.llamar([{'role': 'user', 'content': 'hola'}])
    chequeo('API 2 cambia de proveedor si uno cae', r == 'avance' and m.i == 1, m.bitacora[-1] if m.bitacora else '')
    ESTADO['cargas'].clear()
    m = Motor([mk('/bloques')], dormir=lambda s: None)
    m.llamar([{'role': 'user', 'content': 'x' * 30000}])
    tam = [sum(len(x['content']) for x in c['messages']) for _, c in ESTADO['cargas']]
    chequeo('API 3 parte en bloques de 8500 al pasar 18000', len(tam) == 4 and max(tam) < LIMITE_LLAMADA and LIMITE_LLAMADA == 18000, tam)
    m = Motor([mk('/lento')], timeout=1, dormir=lambda s: None)
    chequeo('API timeout corta y reintenta', m.llamar([{'role': 'user', 'content': 'hola'}]) == 'avance' and ESTADO['n']['/lento'] >= 2)
    g = Guarda('t', 'groq_free', tmp, reloj=lambda: 1000.0)
    chequeo('limite Groq: peticion mayor al TPM pide partir', g.espera(9000) == -1)
    for _ in range(25):
        g.registrar(10)
    chequeo('limite Groq: 25 llamadas en 1 min obliga a esperar', g.espera(10) > 0, round(g.espera(10), 1))
    m = Motor([mk('/ok1', 'groq_free', 'g'), mk('/ok2')], dormir=lambda s: None)
    gg = m.provs[0].guarda
    gg.reloj = lambda: 1000.0
    ev = [[1000.0 - 50000 + i, 100] for i in range(900)]
    gg._escribir(ev)
    m.llamar([{'role': 'user', 'content': 'hola'}])
    chequeo('API 2 pasa a otra si la diaria se agota (24 h)', m.i == 1, m.bitacora[-1] if m.bitacora else '')


def cola_nueva(tmp, nombre):
    c = Cola(os.path.join(tmp, nombre, 'cola.db'))
    return c


def entorno(tmp, nombre, url, extra=None):
    carpeta = os.path.join(tmp, nombre)
    prov = os.path.join(carpeta, 'prov.json')
    json.dump([{'nombre': 'f', 'url': url + '/ok', 'modelo': 'm', 'key_env': 'K', 'perfil': 'libre'}], open(prov, 'w'))
    e = dict(os.environ, FICHA_CARPETA=carpeta, FICHA_PROVEEDORES=prov, FICHA_LATIDO_MAX='4', PYTHONPATH=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    e.update(extra or {})
    return e


def pasos_ok(c):
    with c.c() as cx:
        return [r[0] for r in cx.execute('select paso from pasos order by tarea,paso')]


def prueba_reinicio(tmp, url, nombre, modo):
    c = cola_nueva(tmp, nombre)
    tid = c.agregar('tarea de prueba ' + nombre)
    extra = {}
    if modo in ('salir', 'colgar'):
        extra = {'FICHA_PRUEBA_FALLA': modo + ':2', 'FICHA_PRUEBA_MARCA': os.path.join(tmp, nombre, 'marca')}
    e = entorno(tmp, nombre, url, extra)
    t0 = time.time()
    if modo == 'huerfana':  # sistema 5: tarea en curso con trabajador muerto
        with c.c() as cx:
            cx.execute("update tareas set estado='en_curso',pid=999999 where id=?", (tid,))
        subprocess.run([sys.executable, '-m', 'motor', 'correr', '--una'], env=e, timeout=60)
    else:
        p = subprocess.Popen([sys.executable, '-m', 'motor', 'supervisar', '--una'], env=e)
        if modo == 'matar':  # sistema 4: matan al trabajador desde afuera
            for _ in range(100):
                time.sleep(0.2)
                est = c.estado()[0]
                if est['pid'] and c.ultimo_paso(tid) >= 1:
                    os.kill(est['pid'], signal.SIGKILL)
                    break
        p.wait(timeout=90)
    est = c.estado()[0]['estado']
    pasos = pasos_ok(c)
    log = open(os.path.join(tmp, nombre, 'inicios.log')).read().splitlines()
    ok = est == 'cerrada' and pasos == [1, 2, 3] and (len(log) >= 2 if modo != 'huerfana' else 'reactivadas=1' in log[0])
    chequeo('REINICIO ' + modo + ': el motor se activo y la tarea termina sola', ok, (est, pasos, 'arranques=' + str(len(log)), log[0], round(time.time() - t0, 1)))


def prueba_mensajes(tmp, url):
    c = cola_nueva(tmp, 'msg')
    c.agregar('tarea con mensaje')
    c.mensaje('cambia el color a azul')
    ESTADO['cargas'].clear()
    e = entorno(tmp, 'msg', url)
    subprocess.run([sys.executable, '-m', 'motor', 'correr', '--una'], env=e, timeout=60)
    vistos = [c_ for _, c_ in ESTADO['cargas'] if 'MENSAJES_DEL_DIRECTOR' in c_['messages'][-1]['content']]
    chequeo('mensaje del Director entra sin parar la tarea', len(vistos) == 1 and c.estado()[0]['estado'] == 'cerrada', len(vistos))


if __name__ == '__main__':
    tmp = tempfile.mkdtemp()
    srv, url = servidor()
    pruebas_api(url, tmp)
    for n, modo in enumerate(['salir', 'matar', 'colgar', 'huerfana'], 1):
        prueba_reinicio(tmp, url, 'r' + str(n), modo)
    prueba_mensajes(tmp, url)
    shutil.rmtree(tmp, ignore_errors=True)
    print('RESULTADO', sum(RES), '/', len(RES))
    sys.exit(0 if all(RES) else 1)
