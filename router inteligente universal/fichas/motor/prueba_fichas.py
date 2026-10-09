"""Pruebas de las fichas con servidor falso (sin gastar API). Desde la carpeta fichas: python -m motor.prueba_fichas
Se corre en el job de HF de 16 GB, no en Vercel."""
import copy
import json
import os
import signal
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .api_engine import ErrorApi, Proveedor
from .ficha_os import FichaOS, MotorUso, cargar_ficha, leer_texto, proveedores_desde_yml, validar_ficha
from .memoria import Memoria, ProveedorMock
from .puerta import EsperaAgotada, Puerta

FICHAS = os.environ.get('FICHAS_DIR', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PAUSA = 0.25
S = {'inflight': 0, 'max': 0, 'log': [], 'lock': threading.Lock()}
RES = []


class Falso(BaseHTTPRequestHandler):
    def do_POST(self):
        carga = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        sis = carga['messages'][0]['content']
        nodo = sis.split('.')[0].replace('NODO ', '')
        modelo = self.path.split('/m/')[1]
        with S['lock']:
            S['inflight'] += 1
            S['max'] = max(S['max'], S['inflight'])
            t0 = time.time()
        time.sleep(PAUSA)
        with S['lock']:
            S['inflight'] -= 1
            S['log'].append((modelo, nodo, t0, time.time()))
        b = json.dumps({'choices': [{'message': {'content': 'ok ' + modelo + ' ' + nodo}}], 'usage': {'prompt_tokens': 100, 'completion_tokens': 50}}).encode()
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b)

    def log_message(self, *a):
        pass


def chequeo(nombre, ok, detalle=''):
    RES.append(ok)
    print(('PASS ' if ok else 'FAIL ') + nombre + (' | ' + str(detalle)[:170] if detalle else ''), flush=True)


def reset():
    with S['lock']:
        S['inflight'], S['max'], S['log'] = 0, 0, []


def llamadas(nodo=None):
    return [x for x in S['log'] if nodo is None or x[1] == nodo]


def solape_max(items):
    ev = sorted([(i[2], 1) for i in items] + [(i[3], -1) for i in items])
    c = m = 0
    for _, d in ev:
        c += d
        m = max(m, c)
    return m


def correr(f, task, tmp, base, puerta, mem=None, modelo=None, faltan=()):
    prov = ProveedorMock(os.path.join(tmp, 'mem')) if mem is None else mem
    m = f['memory']
    memoria = Memoria(prov, task, m['project_memory'], m['read_project_memory'], m['write_task_memory'], m['write_project_memory'])
    def mf(mod):
        if mod in faltan:
            raise ErrorApi('SIN_API ' + mod)
        return MotorUso([Proveedor(mod, base + '/m/' + mod, mod, 'K', 'libre', tmp)], timeout=5)
    return FichaOS(f, task, 'tarea de prueba', mf, puerta, memoria, modelo, dormir=lambda s: None).correr(), memoria


def mini(nodos, **dsl):
    f = {'ficha': 'mini', 'tipo': 'dag', 'modelos': {'a': 'texto', 'b': 'texto', 'c': 'texto'}, 'todos_los_modelos': ['a', 'b', 'c'], 'memory': {'project_memory': 'YAIWES', 'read_project_memory': True, 'write_task_memory': True, 'write_project_memory': False},
         'dsl': {'tokens': {'budget': 12000}, 'cache': {'enabled': False}, 'parallel': {'max_parallel': 4, 'mode': 'partial'}, 'retry': {'max_attempts': 1}, 'timeouts': {'queue_seconds': 600}}, 'nodos': nodos}
    for k, v in dsl.items():
        f['dsl'][k] = v
    return f


def nodo(i, m, w, deps=None, seguro=True):
    return {'id': i, 'modelo': m, 'rol': 'prueba', 'depende_de': deps or [], 'parallel_safe': seguro, 'read_paths': [], 'write_paths': w, 'locks': []}


def prueba_puerta(tmp):
    p = Puerta(os.path.join(tmp, 'p1.db'), puestos=4)
    st = {'act': 0, 'max': 0, 'fin': 0}
    lk = threading.Lock()

    def agente(i):
        pm = p.pedir('f' + str(i), 'n', 50, 1)
        with lk:
            st['act'] += 1
            st['max'] = max(st['max'], st['act'])
        time.sleep(0.3)
        with lk:
            st['act'] -= 1
            st['fin'] += 1
        p.liberar(pm)
    t0 = time.time()
    hs = [threading.Thread(target=agente, args=(i,)) for i in range(10)]
    [h.start() for h in hs]
    [h.join() for h in hs]
    chequeo('COLA: 10 agentes, nunca mas de 4 activos y todos terminan', st['max'] == 4 and st['fin'] == 10, (st, round(time.time() - t0, 1)))
    c = Puerta(os.path.join(tmp, 'p2.db'), puestos=1)
    c.pedir('x', 'a')
    t0 = time.time()
    try:
        c.pedir('y', 'b', espera_max=1)
        ok = False
    except EsperaAgotada:
        ok = 0.9 < time.time() - t0 < 3
    chequeo('COLA: si no hay puesto espera y luego da error', ok, round(time.time() - t0, 1))
    chequeo('COLA: espera maxima por defecto = 10 min', Puerta(os.path.join(tmp, 'p3.db')).espera_max == 600)
    ruta = os.path.join(tmp, 'p4.db')
    cod = 'from motor.puerta import Puerta; import time; Puerta(' + repr(ruta) + ', 1).pedir("m", "n"); time.sleep(60)'
    pr = subprocess.Popen([sys.executable, '-c', cod], env=dict(os.environ, PYTHONPATH=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    d = Puerta(ruta, 1)
    for _ in range(100):
        time.sleep(0.1)
        if d.estado()['activos'] == 1:
            break
    pr.send_signal(signal.SIGKILL)
    pr.wait()
    t0 = time.time()
    try:
        d.pedir('otra', 'n', espera_max=5)
        ok = time.time() - t0 < 3
    except EsperaAgotada:
        ok = False
    chequeo('WATCHDOG: ficha muerta libera su puesto', ok, round(time.time() - t0, 1))
    g = Puerta(os.path.join(tmp, 'p5.db'), puestos=4)
    a = g.pedir('f', 'a', 50, 2)
    threading.Timer(0.8, lambda: g.liberar(a)).start()
    t0 = time.time()
    pg = g.pedir('f', 'grupo', 50, 3, espera_max=5)
    esp = time.time() - t0
    chequeo('COLA modo grupo: 3 puestos juntos, espera hasta que haya 3', esp > 0.6, round(esp, 1))
    g.liberar(pg)


def prueba_ficha_dag(tmp, base, f2):
    reset()
    puerta = Puerta(os.path.join(tmp, 'f2.db'), 4)
    t0 = time.time()
    res, mem = correr(f2, 'T-2', tmp, base, puerta)
    n = {k: llamadas(k) for k in ('N1', 'N2', 'N3', 'N4', 'N6', 'N7')}
    ok_par = solape_max(n['N1'] + n['N2'] + n['N3']) == 3
    fin123 = max(x[3] for k in ('N1', 'N2', 'N3') for x in n[k])
    chequeo('FICHA 2: termina en PASS', res['estado'] == 'PASS', (res['estado'], res['nodos'].get('N7'), round(time.time() - t0, 1)))
    chequeo('FICHA 2: N1, N2, N3 corren en paralelo', ok_par, solape_max(n['N1'] + n['N2'] + n['N3']))
    chequeo('FICHA 2: N4 (Qwen 3.8 Max) espera a los 3 y es el ejecutor', n['N4'][0][2] >= fin123 and n['N4'][0][0] == 'ficha-qwen38max', n['N4'][0][0])
    n5 = [x for x in S['log'] if x[1] == 'N5:' + x[0]] or [x for x in S['log'] if x[1].startswith('N5')]
    orden = n['N4'][0][3] <= min(x[2] for x in n5) and max(x[3] for x in n5) <= n['N6'][0][2] and n['N6'][0][3] <= n['N7'][0][2]
    chequeo('FICHA 2: orden N4 -> N5 -> N6 (GLM 5.2) -> N7 (Qwen 3.8 Max)', orden and n['N6'][0][0] == 'ficha-glm52' and n['N7'][0][0] == 'ficha-qwen38max')
    chequeo('FICHA 2: nunca mas de 4 llamadas a la vez a la API', S['max'] <= 4, S['max'])
    chequeo('FICHA 2: 12 goals de entrada con los 14 modelos participando', len(res['saltados']) == 0 and len([x for x in S['log'] if x[1].startswith('N0')]) == 14, (len(res['saltados']), len(S['log'])))
    chequeo('FICHA 2: tokens = consumo real de la API', res['tokens']['total_used'] == len(S['log']) * 150, (res['tokens'], len(S['log'])))
    chequeo('FICHA 2: ledger por nodo y memoria del proyecto solo tras PASS', bool(mem.cargar('ledger', 'N7')) and bool(mem.p.load('project/YAIWES', 'resultado/T-2')), '')
    reset()
    res2, _ = correr(f2, 'T-2', tmp, base, puerta, mem.p)
    chequeo('CACHE: segunda corrida no vuelve a llamar a la API', res2['estado'] == 'PASS' and len(S['log']) == 0 and res2['tokens']['cached_used'] > 0, (len(S['log']), res2['tokens']['cached_used']))
    reset()
    res3, _ = correr(f2, 'T-3', tmp, base, puerta, None, None, ('ficha-qwenimg30pro', 'ficha-qwenasr'))
    chequeo('GOALS: un modelo sin API no frena la ficha y queda registrado como saltado', res3['estado'] == 'PASS' and sorted(set(s['modelo'] for s in res3['saltados'])) == ['ficha-qwenasr', 'ficha-qwenimg30pro'] and len(res3['saltados']) == 4, len(res3['saltados']))


def prueba_rutas_budget_cola(tmp, base):
    puerta = Puerta(os.path.join(tmp, 'r.db'), 4)
    reset()
    correr(mini([nodo('A', 'a', ['config.json']), nodo('B', 'b', ['config.json'])]), 'T-r1', tmp, base, puerta)
    chequeo('RUTAS: dos nodos que escriben el mismo archivo van uno detras de otro', solape_max(S['log']) == 1, solape_max(S['log']))
    reset()
    correr(mini([nodo('A', 'a', ['frontend/chat.js']), nodo('B', 'b', ['backend/router.py'])]), 'T-r2', tmp, base, puerta)
    chequeo('RUTAS: archivos distintos corren en paralelo', solape_max(S['log']) == 2, solape_max(S['log']))
    reset()
    correr(mini([nodo('A', 'a', ['x/'], seguro=False), nodo('B', 'b', ['y/'])]), 'T-r3', tmp, base, puerta)
    chequeo('PARALLEL_SAFE=false: el nodo corre solo', solape_max(S['log']) == 1)
    reset()
    r, _ = correr(mini([nodo('A', 'a', ['x/']), nodo('B', 'b', ['y/'], ['A'])], tokens={'budget': 100}), 'T-b', tmp, base, puerta)
    chequeo('TOKENS: pasar el presupuesto = GAP y los que dependen no corren', r['estado'] == 'GAP' and r['nodos'] == {'A': 'gap', 'B': 'gap'} and len(S['log']) == 1, r['nodos'])
    ocupa = Puerta(os.path.join(tmp, 'q.db'), 1)
    pm = ocupa.pedir('otro', 'n')
    r, _ = correr(mini([nodo('A', 'a', ['x/'])], timeouts={'queue_seconds': 1}), 'T-q', tmp, base, ocupa)
    chequeo('COLA: sin puesto en el tiempo maximo el nodo da GAP COLA_AGOTADA', r['estado'] == 'GAP', r['nodos'])
    ocupa.liberar(pm)
    g = Puerta(os.path.join(tmp, 'g.db'), 4)
    a = g.pedir('otro', 'n', 50, 2)
    threading.Timer(1.0, lambda: g.liberar(a)).start()
    reset()
    t0 = time.time()
    correr(mini([nodo('A', 'a', ['p1/']), nodo('B', 'b', ['p2/']), nodo('C', 'c', ['p3/'])], parallel={'max_parallel': 4, 'mode': 'group'}), 'T-g', tmp, base, g)
    ini = min(x[2] for x in S['log']) - t0
    chequeo('MODO GRUPO: los 3 nodos entran juntos cuando hay 3 puestos', ini > 0.8 and solape_max(S['log']) == 3, (round(ini, 1), solape_max(S['log'])))


def prueba_memoria(tmp):
    p = ProveedorMock(os.path.join(tmp, 'm'))
    t1, t2 = Memoria(p, 'T01'), Memoria(p, 'T02')
    t1.guardar('memory', 'k', {'a': 1})
    aislado = t1.cargar('memory', 'k') and not t2.cargar('memory', 'k')
    try:
        t1.promover('r', {'x': 1}, False)
        sin = False
    except PermissionError:
        sin = True
    try:
        t1.escribir_en_proyecto('r', {'x': 1})
        directo = False
    except PermissionError:
        directo = True
    t1.promover('r', {'x': 1}, True)
    chequeo('MEMORIA: cada tarea en su cajon, sin PASS no se promueve, y lo promovido lo lee el resto', bool(aislado) and sin and directo and bool(t2.leer_del_proyecto('r')))


def prueba_tres_fichas(tmp, base, F):
    f1, f2, f3 = F
    errs = [validar_ficha(f, FICHAS + '/' + d) for f, d in ((f1, 'ficha1-modelos'), (f2, 'ficha2-dag-codigo'), (f3, 'ficha3-frontend'))]
    chequeo('3 FICHAS: validas y cableadas al README anclado', errs == [[], [], []], errs)
    n4 = lambda f: [n for n in f['nodos'] if n['id'] == 'N4'][0]['modelo']
    chequeo('3 FICHAS: ejecutor de la ficha 2 = Qwen 3.8 Max, de la ficha 3 = DeepSeek V4 Pro; la 1 son 14 individuales sin Ask Council',
            n4(f2) == 'ficha-qwen38max' and n4(f3) == 'ficha-dsv4pro' and len(f1['selector']) == 14 and f1['ask_council'] is False and f1['tipo'] == 'individual')
    chequeo('3 FICHAS: cola 4 / espera 10 min / memoria sin escritura directa al proyecto en las 3',
            all(f['cola_global']['puestos'] == 4 and f['cola_global']['espera_max_s'] == 600 and f['memory']['write_project_memory'] is False and f['memory']['provider'] == 'harness' for f in F))
    reset()
    puerta = Puerta(os.path.join(tmp, 'tres.db'), 4)
    prov = ProveedorMock(os.path.join(tmp, 'mem3'))
    out = {}

    def run(clave, f, task, modelo=None):
        out[clave] = correr(f, task, tmp, base, puerta, prov, modelo)[0]
    hs = [threading.Thread(target=run, args=('f1', f1, 'T-f1', 'ficha-glm52')), threading.Thread(target=run, args=('f2', f2, 'T-f2')), threading.Thread(target=run, args=('f3', f3, 'T-f3'))]
    t0 = time.time()
    [h.start() for h in hs]
    [h.join() for h in hs]
    chequeo('3 FICHAS A LA VEZ: las tres terminan en PASS sin mezclar sus DAG', all(o['estado'] == 'PASS' for o in out.values()), {k: v['estado'] for k, v in out.items()})
    chequeo('3 FICHAS A LA VEZ: entre todas nunca pasan de 4 puestos de API', S['max'] <= 4 and S['max'] >= 3, (S['max'], len(S['log']), round(time.time() - t0, 1)))
    n4f3 = [x for x in S['log'] if x[1] == 'N4' and x[0] == 'ficha-dsv4pro']
    chequeo('FICHA 3: el ejecutor DeepSeek V4 Pro corrio el paso 4', len(n4f3) == 1)


def prueba_api14(tmp):
    P = proveedores_desde_yml(leer_texto(FICHAS + '/modelos-14/harness-modelos-14.cordis.yml'), tmp)
    k = set(p._k for p in P.values())
    ok = len(P) == 14 and len(k) == 1 and '' not in k and all(p.url.startswith('https://coding-intl.dashscope.aliyuncs.com/v1/') for p in P.values())
    chequeo('API 14: la misma clave y la misma direccion en las 14 ranuras', ok, 'ids con modelo: ' + str([n for n, p in P.items() if p.modelo]))


if __name__ == '__main__':
    tmp = tempfile.mkdtemp()
    srv = ThreadingHTTPServer(('127.0.0.1', 0), Falso)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = 'http://127.0.0.1:' + str(srv.server_address[1])
    F = [cargar_ficha(FICHAS + '/' + d + '/ficha.json') for d in ('ficha1-modelos', 'ficha2-dag-codigo', 'ficha3-frontend')]
    prueba_puerta(tmp)
    prueba_ficha_dag(tmp, base, F[1])
    prueba_rutas_budget_cola(tmp, base)
    prueba_memoria(tmp)
    prueba_tres_fichas(tmp, base, F)
    prueba_api14(tmp)
    print('RESULTADO_FICHAS', sum(RES), '/', len(RES), flush=True)
    sys.exit(0 if all(RES) else 1)
