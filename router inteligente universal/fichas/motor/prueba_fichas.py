"""Pruebas de las fichas con servidor falso (sin gastar API). Desde la carpeta fichas: python -m motor.prueba_fichas
Se corre en el job de HF de 16 GB, no en Vercel."""
import json
import os
import signal
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .api_engine import Proveedor
from .ficha_os import FichaOS, MotorUso, cargar_ficha, leer_texto, proveedores_desde_yml, validar_ficha
from .locks import Candados
from .memoria import Memoria, ProveedorMock
from .puerta import EsperaAgotada, Puerta

AQUI = os.path.dirname(os.path.abspath(__file__))
FICHAS = os.environ.get('FICHAS_DIR', os.path.dirname(AQUI))
CFG = json.load(open(os.path.join(AQUI, 'puerta.config.json')))
PAUSA = 0.25
S = {'inflight': 0, 'max': 0, 'log': [], 'lock': threading.Lock()}
RES = []
IDS = {'ficha-qwen38max': 'qwen3.8-max', 'ficha-qwen38flash': 'qwen3.8-flash', 'ficha-qwen37max': 'qwen3.7-max', 'ficha-qwen37plus': 'qwen3.7-plus',
       'ficha-qwen36flash': 'qwen3.6-flash', 'ficha-qwenimg30pro': 'qwen-image-3.0-pro', 'ficha-qwentts': 'qwen-audio-3.0-tts-plus',
       'ficha-qwenrt': 'qwen-audio-3.0-realtime-plus', 'ficha-qwenasr': 'qwen-audio-3.0-asr-flash', 'ficha-glm52': 'glm-5.2',
       'ficha-dsv4pro': 'deepseek-v4-pro', 'ficha-dsv4pro0813': 'deepseek-v4-pro-0813', 'ficha-dsv4flash': 'deepseek-v4-flash-0731', 'ficha-wan27img': 'wan2.7-image'}
CUATRO = {'ficha-dsv4pro', 'ficha-glm52', 'ficha-qwen37max', 'ficha-qwen38max'}


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
            S['log'].append((modelo, nodo, t0, time.time(), carga['messages'][1]['content'], carga['messages'][0]['content']))
        salida = 900 if modelo == 'grande' else 50
        b = json.dumps({'choices': [{'message': {'content': 'ok ' + modelo + ' ' + nodo}}], 'usage': {'prompt_tokens': 100, 'completion_tokens': salida}}).encode()
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


def harness_ok(nodo, salida, ctx):
    return {'exit_code': 0, 'files_changed': ['codigo/x.py'], 'tests': {'ran': True, 'passed': True}, 'receipt': 'r-' + nodo['id']}


def correr(f, task, tmp, base, puerta, mem=None, modelo=None, candados=None, harness=harness_ok, especiales=None, texto='tarea de prueba'):
    prov = ProveedorMock(os.path.join(tmp, 'mem')) if mem is None else mem
    m = f['memory']
    memoria = Memoria(prov, task, m['project_memory'], m['read_project_memory'], m['write_task_memory'], m['write_project_memory'])
    mf = lambda mod: MotorUso([Proveedor(mod, base + '/m/' + mod, mod, 'K', 'libre', tmp)], timeout=5)
    return FichaOS(f, task, texto, mf, puerta, memoria, modelo, dormir=lambda s: None, candados=candados, harness=harness, especiales=especiales, plantilla=PL if f.get('plantilla') else '', mejoras=MJ if f.get('plantilla') else '').correr(), memoria


def _leer_plantilla(clave):
    ruta = os.path.join(FICHAS, 'plantilla', 'PLANTILLA_XRAY_V2.yaml' if clave == 'p' else 'MEJORAS_FICHAS.yaml')
    return open(ruta, encoding='utf-8').read() if os.path.exists(ruta) else ''


PL, MJ = _leer_plantilla('p'), _leer_plantilla('m')


def correr_ficha(f, *a, **k):
    """Las fichas reales llevan la plantilla; los mini-DAG de las pruebas no."""
    return correr(f, *a, **k)


def mini(nodos, **dsl):
    f = {'ficha': 'mini', 'tipo': 'dag', 'modelos': {'a': 'texto', 'b': 'texto', 'c': 'texto', 'grande': 'texto'}, 'memory': {'project_memory': 'YAIWES', 'read_project_memory': True, 'write_task_memory': True, 'write_project_memory': False},
         'dsl': {'tokens': {'task_budget': 12000, 'max_output_tokens': 1500}, 'cache': {'enabled': False}, 'parallel': {'max_parallel': 4, 'mode': 'partial'}, 'retry': {'max_attempts': 1}, 'timeouts': {'queue_seconds': 600}}, 'nodos': nodos}
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
    pc = Puerta.desde_config(os.path.join(tmp, 'p3.db'), os.path.join(AQUI, 'puerta.config.json'))
    chequeo('POOL: una sola fuente de verdad (4 puestos, 10 min, pool qwen-token-plan)', pc.puestos == 4 and pc.espera_max == 600 and pc.pool == 'qwen-token-plan', (pc.puestos, pc.espera_max, pc.pool))
    ruta = os.path.join(tmp, 'p4.db')
    cod = 'from motor.puerta import Puerta; import time; Puerta(' + repr(ruta) + ', 1).pedir("m", "n"); time.sleep(60)'
    pr = subprocess.Popen([sys.executable, '-c', cod], env=dict(os.environ, PYTHONPATH=os.path.dirname(AQUI)))
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
    chequeo('COLA modo grupo: 3 puestos juntos, espera hasta que haya 3', time.time() - t0 > 0.6, round(time.time() - t0, 1))
    g.liberar(pg)


def prueba_ficha_dag(tmp, base, f2, f3):
    reset()
    puerta = Puerta(os.path.join(tmp, 'f2.db'), 4)
    t0 = time.time()
    res, mem = correr(f2, 'T-2', tmp, base, puerta)
    n = {k: llamadas(k) for k in ('N0', 'N1', 'N2', 'N3', 'N4', 'N5', 'N6', 'N7')}
    ids = [x['id'] for x in f2['nodos']]
    g = [x for x in f2['nodos'] if x.get('tipo') == 'goals']
    chequeo('FICHA 2: 12 goals entrada + Council de 3 + ejecutor + 12 goals salida + 2 revisiones', ids == ['N0', 'N1', 'N2', 'N3', 'N4', 'N5', 'N6', 'N7'] and [x['id'] for x in g] == ['N0', 'N5'] and all(len(x['goals']) == 12 and x['ejecutar_api'] is False for x in g), ids)
    chequeo('FICHA 2: entrega la SALIDA del ultimo paso (Qwen 3.8 Max)', res['estado'] == 'SALIDA' and 'ok ficha-qwen38max N7' in res['salida'], (res['estado'], res['salida'][:40], round(time.time() - t0, 1)))
    chequeo('FICHA 2: con evidencia del Harness queda marcada como verificada', res['verificado'] is True and res['avisos'] == [], (res['verificado'], res['avisos']))
    chequeo('FICHA 2: N0 y N5 (goals) son datos: 0 llamadas a la API, 0 puestos de cola', len(n['N0']) == 0 and len(n['N5']) == 0 and res['nodos']['N0'] == 'ok' and res['nodos']['N5'] == 'ok')
    chequeo('FICHA 2: N1, N2, N3 hacen exactamente 3 llamadas en paralelo y reciben los goals de entrada', len(n['N1']) + len(n['N2']) + len(n['N3']) == 3 and solape_max(n['N1'] + n['N2'] + n['N3']) == 3 and all('CRITERIOS goals_de_entrada' in n[k][0][4] for k in ('N1', 'N2', 'N3')))
    fin123 = max(x[3] for k in ('N1', 'N2', 'N3') for x in n[k])
    chequeo('FICHA 2: N4 (Qwen 3.8 Max) ejecuta despues de los tres, con sus propuestas y los goals de entrada', n['N4'][0][2] >= fin123 and n['N4'][0][0] == 'ficha-qwen38max' and all('[' + k + ']' in n['N4'][0][4] for k in ('N1', 'N2', 'N3')) and 'CRITERIOS goals_de_entrada' in n['N4'][0][4])
    chequeo('FICHA 2: N6 (GLM 5.2) recibe N4 + goals de salida N5; N7 (Qwen 3.8 Max) recibe N6 + N5', '[N4]' in n['N6'][0][4] and '[N5]' in n['N6'][0][4] and '[N6]' in n['N7'][0][4] and '[N5]' in n['N7'][0][4] and n['N6'][0][0] == 'ficha-glm52' and n['N7'][0][0] == 'ficha-qwen38max' and n['N4'][0][3] <= n['N6'][0][2] and n['N6'][0][3] <= n['N7'][0][2])
    chequeo('FICHA 2: usa unicamente DeepSeek V4 Pro, GLM 5.2, Qwen 3.7 Max y Qwen 3.8 Max', set(x[0] for x in S['log']) == CUATRO and set(f2['modelos']) == CUATRO, sorted(set(x[0] for x in S['log'])))
    chequeo('FICHA 2: 6 llamadas en total y nunca mas de 4 a la vez', len(S['log']) == 6 and S['max'] <= 4, (len(S['log']), S['max']))
    chequeo('FICHA 2: tokens = consumo real de la API', res['tokens']['total_api_tokens'] == 6 * 150, res['tokens'])
    chequeo('FICHA 2: ledger por nodo y solo lo verificado se promueve a la memoria del proyecto', bool(mem.cargar('ledger', 'N7')) and bool(mem.p.load('project/YAIWES', 'resultado/T-2')))
    reset()
    res2, _ = correr(f2, 'T-2', tmp, base, puerta, mem.p)
    t = res2['tokens']
    chequeo('CACHE: la cache local no se cuenta como cached_tokens de la API', res2['estado'] == 'SALIDA' and t['local_cache_hits'] == 3 and t['estimated_tokens_avoided'] > 0 and t['api_cached_input_tokens'] == 0 and len(S['log']) == 3, (t['local_cache_hits'], t['api_cached_input_tokens'], len(S['log'])))
    reset()
    r3, _ = correr(f3, 'T-3', tmp, base, puerta)
    n3 = {k: llamadas(k) for k in ('N1', 'N4')}
    g3 = [x['id'] for x in f3['nodos'] if x.get('tipo') == 'goals']
    chequeo('FICHA 3: mismo Ask Council con sus 24 goals y ejecuta DeepSeek V4 Pro; usa solo esos 4 modelos', r3['estado'] == 'SALIDA' and g3 == ['N0', 'N5'] and n3['N4'][0][0] == 'ficha-dsv4pro' and set(x[0] for x in S['log']) == CUATRO and len(S['log']) == 6 and set(f3['modelos']) == CUATRO)
    reset()
    sin, m4 = correr(f2, 'T-4', tmp, base, puerta, None, None, None, None)
    chequeo('SALIDA SIEMPRE: sin Harness igual se entrega la salida, marcada SIN verificar (GAP_HARNESS_EXECUTOR) y no se promueve', sin['estado'] == 'SALIDA' and bool(sin['salida']) and sin['verificado'] is False and 'GAP_HARNESS_EXECUTOR' in str(sin['avisos']) and not m4.p.load('project/YAIWES', 'resultado/T-4'), sin['avisos'])
    reset()
    inc, _ = correr(f2, 'T-5', tmp, base, puerta, None, None, None, lambda nodo, s, c: {'exit_code': 0, 'receipt': 'x'})
    chequeo('SALIDA SIEMPRE: evidencia incompleta (sin tests) entrega la salida pero sin verificar', inc['estado'] == 'SALIDA' and bool(inc['salida']) and inc['verificado'] is False and 'EVIDENCIA_INCOMPLETA' in str(inc['avisos']))


def prueba_ficha1(tmp, base, f1):
    reset()
    puerta = Puerta(os.path.join(tmp, 'f1.db'), 4)
    r, _ = correr(f1, 'T-1', tmp, base, puerta, modelo='ficha-glm52')
    chequeo('FICHA 1: SELECTOR -> 1 modelo -> EJECUTAR -> SALIDA (una sola llamada, sin Council ni goals)', r['estado'] == 'SALIDA' and r['verificado'] is None and len(S['log']) == 1 and S['log'][0][0] == 'ficha-glm52' and f1['ask_council'] is False and 'nodos' not in f1 and 'goals' not in f1 and f1['dsl']['parallel']['enabled'] is False and f1['dsl']['parallel']['max_parallel'] == 1)
    reset()
    r, _ = correr(f1, 'T-1b', tmp, base, puerta, modelo='ficha-qwenimg30pro')
    chequeo('FICHA 1: un modelo de imagen/voz no se llama por chat (GAP_ENDPOINT_NO_CHAT, 0 llamadas)', r['estado'] == 'GAP' and len(S['log']) == 0 and 'GAP_ENDPOINT_NO_CHAT' in str(r['gaps']))


def prueba_candados_budget_cola(tmp, base):
    puerta = Puerta(os.path.join(tmp, 'r.db'), 4)
    cand = Candados(os.path.join(tmp, 'c.db'))
    out = {}

    def run(k, f, task):
        out[k] = correr(f, task, tmp, base, puerta, None, None, cand)[0]
    reset()
    hs = [threading.Thread(target=run, args=('a', mini([nodo('A', 'a', ['config.json'])]), 'T-x1')), threading.Thread(target=run, args=('b', mini([nodo('B', 'b', ['config.json'])]), 'T-x2'))]
    [h.start() for h in hs]
    [h.join() for h in hs]
    chequeo('LOCKS ENTRE FICHAS: dos fichas que escriben el mismo path NO corren juntas', len(S['log']) == 2 and solape_max(S['log']) == 1 and all(o['estado'] == 'SALIDA' for o in out.values()), solape_max(S['log']))
    reset()
    hs = [threading.Thread(target=run, args=('a', mini([nodo('A', 'a', ['frontend/a.js'])]), 'T-y1')), threading.Thread(target=run, args=('b', mini([nodo('B', 'b', ['backend/b.py'])]), 'T-y2'))]
    [h.start() for h in hs]
    [h.join() for h in hs]
    chequeo('LOCKS ENTRE FICHAS: paths distintos SI corren juntas', solape_max(S['log']) == 2, solape_max(S['log']))
    reset()
    correr(mini([nodo('A', 'a', ['config.json']), nodo('B', 'b', ['config.json'])]), 'T-r1', tmp, base, puerta)
    chequeo('RUTAS dentro de una ficha: mismo archivo = uno detras de otro', solape_max(S['log']) == 1)
    reset()
    correr(mini([nodo('A', 'a', ['x/'], seguro=False), nodo('B', 'b', ['y/'])]), 'T-r3', tmp, base, puerta)
    chequeo('PARALLEL_SAFE=false: el nodo corre solo', solape_max(S['log']) == 1)
    reset()
    r, _ = correr(mini([nodo('A', 'grande', ['x/']), nodo('B', 'grande', ['y/'], ['A']), nodo('C', 'grande', ['z/'], ['B'])], tokens={'task_budget': 2500, 'max_output_tokens': 900}), 'T-b', tmp, base, puerta)
    chequeo('TOKENS: el presupuesto es de la FICHA completa (no por nodo): el 3.er nodo da GAP_BUDGET', r['estado'] == 'GAP' and r['nodos'] == {'A': 'ok', 'B': 'ok', 'C': 'gap'} and 'GAP_BUDGET' in str(r['gaps'].get('C')), (r['nodos'], len(S['log'])))
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


class FalsoMM(BaseHTTPRequestHandler):
    """Servidor falso de la ruta multimodal-generation (imagen y voz a texto)."""
    visto = []

    def do_POST(self):
        carga = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        FalsoMM.visto.append((self.path, carga, self.headers.get('Authorization')))
        if carga['model'].startswith('qwen-audio'):
            c = [{'text': 'hola mundo'}]
        else:
            c = [{'image': 'http://img.falso/x.png'}]
        b = json.dumps({'output': {'choices': [{'message': {'content': c}}]}}).encode()
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b)

    def log_message(self, *a):
        pass


def prueba_especiales(tmp, f1):
    import types
    from .ficha_os import ProveedorDirecto
    from .modelos_especiales import RUTA_GEN, WS_TTS, fabrica_especiales
    srv = ThreadingHTTPServer(('127.0.0.1', 0), FalsoMM)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    host = 'http://127.0.0.1:' + str(srv.server_address[1])
    provs = {k: ProveedorDirecto(k, 'x', IDS[k], 'sk-sp-prueba', tmp) for k in ('ficha-qwenimg30pro', 'ficha-wan27img', 'ficha-qwentts', 'ficha-qwenrt', 'ficha-qwenasr')}
    fake = types.ModuleType('dashscope')
    audio_pkg, tts_v2 = types.ModuleType('dashscope.audio'), types.ModuleType('dashscope.audio.tts_v2')
    usado = {}

    class SS:
        def __init__(self, model, voice, format):
            usado['model'], usado['voice'] = model, voice

        def call(self, t):
            usado['texto'] = t
            return b'ID3falso'
    tts_v2.SpeechSynthesizer, tts_v2.AudioFormat = SS, types.SimpleNamespace(MP3_22050HZ_MONO_256KBPS='mp3')
    guardados = {k: sys.modules.get(k) for k in ('dashscope', 'dashscope.audio', 'dashscope.audio.tts_v2')}
    sys.modules.update({'dashscope': fake, 'dashscope.audio': audio_pkg, 'dashscope.audio.tts_v2': tts_v2})
    try:
        esp = fabrica_especiales(provs, host=host, carpeta=tmp)
        puerta = Puerta(os.path.join(tmp, 'esp.db'), 4)
        FalsoMM.visto.clear()
        r, _ = correr(f1, 'T-img', tmp, '', puerta, modelo='ficha-qwenimg30pro', especiales=esp, texto='dibuja un gato')
        ruta, carga, auth = FalsoMM.visto[0]
        chequeo('MODELO 10 Qwen Image 3.0 Pro: usa la ruta documentada multimodal-generation y devuelve la URL de la imagen', r['estado'] == 'SALIDA' and r['salida'] == 'IMAGEN http://img.falso/x.png' and ruta == RUTA_GEN and carga['input']['messages'][0]['content'] == [{'text': 'dibuja un gato'}] and carga['parameters'] == {'size': '1024*1024'} and carga['model'] == 'qwen-image-3.0-pro' and auth == 'Bearer sk-sp-prueba', (r['estado'], r['salida']))
        r, _ = correr(f1, 'T-wan', tmp, '', puerta, modelo='ficha-wan27img', especiales=esp, texto='un perro')
        chequeo('MODELO 11 Wan 2.7 Image: misma ruta de imagen con su id wan2.7-image', r['estado'] == 'SALIDA' and FalsoMM.visto[-1][1]['model'] == 'wan2.7-image', r['salida'])
        r, _ = correr(f1, 'T-tts', tmp, '', puerta, modelo='ficha-qwentts', especiales=esp, texto='hola equipo')
        ok_audio = r['salida'].startswith('AUDIO ') and open(r['salida'][6:], 'rb').read() == b'ID3falso'
        chequeo('MODELO 12 Qwen TTS: usa el WebSocket del SDK (wss .../api-ws/v1/inference) y guarda el audio', r['estado'] == 'SALIDA' and ok_audio and usado['model'] == 'qwen-audio-3.0-tts-plus' and usado['texto'] == 'hola equipo' and fake.base_websocket_api_url == WS_TTS and fake.api_key == 'sk-sp-prueba', usado)
        r, _ = correr(f1, 'T-asr', tmp, '', puerta, modelo='ficha-qwenasr', especiales=esp, texto='http://audio.falso/a.wav')
        chequeo('MODELO 14 Qwen ASR: manda el audio (URL) por la ruta multimodal-generation y devuelve el texto', r['estado'] == 'SALIDA' and r['salida'] == 'hola mundo' and FalsoMM.visto[-1][1]['input']['messages'][0]['content'] == [{'audio': 'http://audio.falso/a.wav'}] and FalsoMM.visto[-1][1]['model'] == 'qwen-audio-3.0-asr-flash', r['salida'])
    finally:
        for k, v in guardados.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v


def prueba_plantilla_y_ficha4(tmp, base, F):
    f1, f2, f3, f4 = F
    cfg4 = json.load(open(os.path.join(AQUI, 'pools', 'nvidia-groq.json')))
    reset()
    puerta = Puerta(os.path.join(tmp, 'pl.db'), 4)
    correr(f1, 'T-p1', tmp, base, puerta, modelo='ficha-glm52', texto='tarea de Max uno')
    correr(f2, 'T-p2', tmp, base, puerta, texto='tarea de Max dos')
    correr(f3, 'T-p3', tmp, base, puerta, texto='tarea de Max tres')
    r4, _ = correr(f4, 'T-p4', tmp, base, Puerta(os.path.join(tmp, 'pl4.db'), 4), texto='tarea de Max cuatro')
    llamadas_ok = len(S['log'])
    sis_ok = all('schema: yaiwes.node-executor/xray-v2' in x[5] and '=== BEGIN_INPUT_BLOCK ===' in x[5] and 'MEJORAS' in x[5] for x in S['log'])
    verbatim = all(('tarea de Max' in x[5].split('<user_query mode="verbatim">')[1].split('</user_query>')[0]) for x in S['log'])
    chequeo('PLANTILLA: las 4 fichas mandan la plantilla XRAY-V2 completa + mejoras en CADA llamada', llamadas_ok == 1 + 6 + 6 + 6 and sis_ok, llamadas_ok)
    chequeo('PLANTILLA: la entrada de cada nodo va dentro del bloque <user_query mode=verbatim>', verbatim)
    chequeo('PLANTILLA: ninguna llamada pasa el limite de la ficha (no se parte en bloques)', all(len(x[5]) + len(x[4]) < 60000 for x in S['log']))
    chequeo('FICHA 4 (NVIDIA/Groq): mismo Ask Council con goals; analizan Kimi K3, GLM 5.3 y Qwen 3.8 (Groq); ejecuta Glimmer 30B; revisan GLM 5.3 y Qwen 3.8 (Groq)',
            r4['estado'] == 'SALIDA' and [x['id'] for x in f4['nodos']] == ['N0', 'N1', 'N2', 'N3', 'N4', 'N5', 'N6', 'N7']
            and [x['modelo'] for x in f4['nodos'] if x.get('modelo')] == ['ficha-kimi3', 'ficha-glm53', 'ficha-qwen38groq', 'ficha-glimmer30b', 'ficha-glm53', 'ficha-qwen38groq']
            and set(f4['modelos']) == {'ficha-kimi3', 'ficha-glm53', 'ficha-qwen38groq', 'ficha-glimmer30b'} and f4['cola']['pool'] == 'nvidia-groq' and cfg4['pool'] == 'nvidia-groq' and cfg4['puestos'] == 4, r4['estado'])
    chequeo('FICHA 4: valida, con su propio pool (nvidia-groq) y la plantilla', validar_ficha(f4, FICHAS + '/ficha4-nvidia-groq', cfg4) == [], validar_ficha(f4, FICHAS + '/ficha4-nvidia-groq', cfg4))
    sin = json.loads(json.dumps(f2))
    sin.pop('plantilla')
    chequeo('PLANTILLA: una ficha sin plantilla no es valida, y FichaOS se niega a correr sin cargarla', any('plantilla' in e for e in validar_ficha(sin, FICHAS + '/ficha2-dag-codigo', CFG)) and _rechaza(f2))


def _rechaza(f):
    try:
        FichaOS(f, 'T', 'x', None, None, None)
        return False
    except ValueError:
        return True


def prueba_realtime_falso(tmp):
    import types
    from .modelos_especiales import WS_REALTIME, voz_en_vivo
    enviados, cab = [], {}

    class Con:
        eventos = iter([{'type': 'session.created'}, {'type': 'response.audio_transcript.delta', 'delta': 'ho'}, {'type': 'response.audio_transcript.delta', 'delta': 'la'}, {'type': 'response.done'}])

        def send(self, s):
            enviados.append(json.loads(s))

        def recv(self):
            return json.dumps(next(self.eventos))

        def close(self):
            pass
    fake = types.ModuleType('websocket')

    def crear(url, header=None, timeout=None):
        cab['url'], cab['header'] = url, header
        return Con()
    fake.create_connection = crear
    guardado = sys.modules.get('websocket')
    sys.modules['websocket'] = fake
    try:
        r = voz_en_vivo('qwen-audio-3.0-realtime-plus', 'hola', 'sk-sp-x')
    finally:
        if guardado is None:
            sys.modules.pop('websocket', None)
        else:
            sys.modules['websocket'] = guardado
    tipos = [e['type'] for e in enviados]
    chequeo('MODELO 13 Qwen Realtime: WebSocket documentado, manda el texto del usuario, pide respuesta y junta lo que contesta', r == 'hola' and tipos == ['session.update', 'conversation.item.create', 'response.create'] and cab['url'] == WS_REALTIME + '?model=qwen-audio-3.0-realtime-plus' and cab['header'] == ['Authorization: Bearer sk-sp-x'], (r, tipos))


def prueba_real_todas(tmp, F):
    """Pruebas REALES (gastan plan). Solo si FICHA_PRUEBA_REAL=todas."""
    if os.environ.get('FICHA_PRUEBA_REAL') != 'todas':
        return
    from .ficha_os import fabrica_motores
    from .modelos_especiales import fabrica_especiales
    P = proveedores_desde_yml(leer_texto(FICHAS + '/modelos-14/harness-modelos-14.cordis.yml'), tmp)
    esp = fabrica_especiales(P, carpeta=tmp)
    for k, t in (('ficha-qwenimg30pro', 'un circulo rojo sobre fondo blanco'), ('ficha-wan27img', 'un gato azul')):
        try:
            s = esp(k, 'imagen', t)
            chequeo('REAL ' + k + ' imagen', s.startswith('IMAGEN http'), s[:90])
        except Exception as e:
            chequeo('REAL ' + k + ' imagen', False, e)
    try:
        s = esp('ficha-qwentts', 'texto-a-voz', 'hola equipo, esto es una prueba')
        chequeo('REAL ficha-qwentts texto a voz', s.startswith('AUDIO ') and os.path.getsize(s[6:]) > 1000, s[:90])
        a = esp('ficha-qwenasr', 'voz-a-texto', s[6:])
        chequeo('REAL ficha-qwenasr voz a texto (audio del TTS)', 'hola' in a.lower(), a[:90])
    except Exception as e:
        chequeo('REAL texto a voz y voz a texto', False, e)
    try:
        s = esp('ficha-qwenrt', 'voz-en-vivo', 'Responde solo con la palabra OK.')
        chequeo('REAL ficha-qwenrt voz en vivo', bool(s), s[:90])
    except Exception as e:
        chequeo('REAL ficha-qwenrt voz en vivo', False, e)
    P4 = proveedores_desde_yml(leer_texto(FICHAS + '/modelos-nvidia-groq/harness-modelos.cordis.yml'), tmp)
    for f, nombre, prov, cfgp in ((F[1], 'FICHA 2', P, 'puerta.config.json'), (F[2], 'FICHA 3', P, 'puerta.config.json'), (F[3], 'FICHA 4', P4, os.path.join('pools', 'nvidia-groq.json'))):
        m = f['memory']
        memoria = Memoria(ProveedorMock(os.path.join(tmp, 'real' + nombre[-1])), 'T-real' + nombre[-1], m['project_memory'], m['read_project_memory'], m['write_task_memory'], m['write_project_memory'])
        pu = Puerta.desde_config(os.path.join(tmp, 'real' + nombre[-1] + '.db'), os.path.join(AQUI, cfgp))
        t0 = time.time()
        res = FichaOS(f, 'T-real' + nombre[-1], 'Escribe una funcion Python suma(a, b) y explica en una linea que hace.', fabrica_motores(prov, 90, f['motor']['limite_llamada_chars']), pu, memoria,
                      plantilla=PL, mejoras=MJ, especiales=None).correr()
        chequeo('REAL ' + nombre + ' completa (6 llamadas reales con la plantilla)', res['estado'] == 'SALIDA' and len(res['salida']) > 20, (res['estado'], res['gaps'], res['tokens']['total_api_tokens'], round(time.time() - t0)))


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
    errs = [validar_ficha(f, FICHAS + '/' + d, CFG) for f, d in ((f1, 'ficha1-modelos'), (f2, 'ficha2-dag-codigo'), (f3, 'ficha3-frontend'))]
    chequeo('3 FICHAS: validas, cableadas al README anclado y apuntando al pool unico', errs == [[], [], []], errs)
    malo = json.loads(json.dumps(f2))
    malo['todos_los_modelos'] = list(f1['modelos'])
    malo['nodos'][0]['participan'] = 'todos'
    uno = json.loads(json.dumps(f1))
    uno['goals'] = [{'id': 'G01', 'texto': 'x'}]
    malo['cola_global'] = {'puestos': 9}
    chequeo('ANTI-REGRESION: el validador rechaza los 14 en el Council, goals con modelos, puestos propios y goals en la ficha 1', len(validar_ficha(malo, FICHAS + '/ficha2-dag-codigo', CFG)) >= 3 and len(validar_ficha(uno, FICHAS + '/ficha1-modelos', CFG)) >= 1)
    chequeo('3 FICHAS: ninguna lleva numeros de cola propios; memoria sin escritura directa al proyecto', all('cola_global' not in f and f['cola'] == {'pool': 'qwen-token-plan'} and f['memory']['write_project_memory'] is False and f['memory']['provider'] == 'harness' for f in F))
    reset()
    puerta = Puerta(os.path.join(tmp, 'tres.db'), 4)
    cand = Candados(os.path.join(tmp, 'tres_c.db'))
    prov = ProveedorMock(os.path.join(tmp, 'mem3'))
    out = {}

    def run(clave, f, task, modelo=None):
        out[clave] = correr(f, task, tmp, base, puerta, prov, modelo, cand)[0]
    hs = [threading.Thread(target=run, args=('f1', f1, 'T-f1', 'ficha-glm52')), threading.Thread(target=run, args=('f2', f2, 'T-f2')), threading.Thread(target=run, args=('f3', f3, 'T-f3'))]
    [h.start() for h in hs]
    [h.join() for h in hs]
    chequeo('3 FICHAS A LA VEZ: terminan sin mezclar sus DAG (las 2 de codigo comparten codigo/: una detras de otra)', out['f1']['estado'] == 'SALIDA' and out['f2']['estado'] == 'SALIDA' and out['f3']['estado'] == 'SALIDA', {k: v['estado'] for k, v in out.items()})
    chequeo('3 FICHAS A LA VEZ: entre todas nunca pasan de 4 llamadas de API', 3 <= S['max'] <= 4, (S['max'], len(S['log'])))


def prueba_token_plan(tmp):
    ruta = FICHAS + '/modelos-14/harness-modelos-14.cordis.yml'
    if not (os.path.exists(ruta) or os.path.exists(ruta + '.sello')):
        print('SKIP token plan: no hay modelos-14 en esta carpeta', flush=True)
        return
    P = proveedores_desde_yml(leer_texto(ruta), tmp)
    k = set(p._k for p in P.values())
    base = 'https://token-plan.maas.qwencloudapi.com/compatible-mode/v1/chat/completions'
    chequeo('TOKEN PLAN: base URL token-plan en las 14 (nunca coding/dashscope)', len(P) == 14 and all(p.url == base for p in P.values()) and not any('coding' in p.url or 'dashscope' in p.url for p in P.values()))
    chequeo('TOKEN PLAN: la misma clave dedicada sk-sp-* en las 14', len(k) == 1 and list(k)[0].startswith('sk-sp-'))
    chequeo('TOKEN PLAN: los 14 ids exactos del plan, sin inventar versiones', {n: p.modelo for n, p in P.items()} == IDS, {n: p.modelo for n, p in P.items() if IDS.get(n) != p.modelo})


def sondear(url, carga, key):
    import urllib.error
    import urllib.request
    q = urllib.request.Request(url, json.dumps(carga).encode(), {'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json', 'User-Agent': 'ficha-motor/1.0'})
    try:
        r = urllib.request.urlopen(q, timeout=120)
        return r.status, r.read()[:140].decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:200].decode('utf-8', 'replace')
    except Exception as e:
        return 'ERR', type(e).__name__


def prueba_real_14(tmp, f1):
    """Prueba REAL de cada uno de los 14 modelos de la ficha 1 con la clave del Token Plan. Solo si FICHA_PRUEBA_REAL=14."""
    if os.environ.get('FICHA_PRUEBA_REAL') != '14':
        return
    from .ficha_os import fabrica_motores
    P = proveedores_desde_yml(leer_texto(FICHAS + '/modelos-14/harness-modelos-14.cordis.yml'), tmp)
    m = f1['memory']
    base = 'https://token-plan.maas.qwencloudapi.com/compatible-mode/v1'
    key = P['ficha-glm52']._k
    for s in f1['selector']:
        mid, tipo, t0 = s['id'], s['tipo'], time.time()
        if tipo == 'texto':
            memoria = Memoria(ProveedorMock(os.path.join(tmp, 'm' + mid)), 'T-' + mid, m['project_memory'], m['read_project_memory'], m['write_task_memory'], m['write_project_memory'])
            res = FichaOS(f1, 'T-' + mid, 'Responde solo con la palabra OK.', fabrica_motores(P, 90), Puerta(os.path.join(tmp, mid + '.db'), 4), memoria, mid, dormir=lambda x: None).correr()
            chequeo('MODELO ' + str(s['cola']) + ' ' + s['nombre'] + ' (' + P[mid].modelo + ') por la ficha 1', res['estado'] == 'SALIDA' and res['tokens']['total_api_tokens'] > 0, (res['estado'], res['tokens']['total_api_tokens'], res['gaps'], round(time.time() - t0, 1)))
        elif tipo == 'imagen':
            print('INFO MODELO ' + str(s['cola']) + ' ' + s['nombre'] + ' (' + P[mid].modelo + ') /images/generations ->', sondear(base + '/images/generations', {'model': P[mid].modelo, 'prompt': 'un circulo rojo', 'n': 1}, key), flush=True)
        elif tipo == 'texto-a-voz':
            print('INFO MODELO ' + str(s['cola']) + ' ' + s['nombre'] + ' (' + P[mid].modelo + ') /audio/speech ->', sondear(base + '/audio/speech', {'model': P[mid].modelo, 'input': 'hola', 'voice': 'alloy'}, key), flush=True)
        else:
            print('INFO MODELO ' + str(s['cola']) + ' ' + s['nombre'] + ' (' + P[mid].modelo + ') NO PROBADO: ' + ('necesita un archivo de audio' if tipo == 'voz-a-texto' else 'usa websocket (tiempo real)'), flush=True)


def prueba_real_token_plan(tmp, f1):
    """UNA llamada real con UN solo modelo (qwen3.7-plus) por la ficha 1. Solo si FICHA_PRUEBA_REAL=1."""
    if os.environ.get('FICHA_PRUEBA_REAL') != '1':
        return
    from .ficha_os import fabrica_motores
    P = proveedores_desde_yml(leer_texto(FICHAS + '/modelos-14/harness-modelos-14.cordis.yml'), tmp)
    m = f1['memory']
    memoria = Memoria(ProveedorMock(os.path.join(tmp, 'memreal')), 'T-real', m['project_memory'], m['read_project_memory'], m['write_task_memory'], m['write_project_memory'])
    res = FichaOS(f1, 'T-real', 'Responde solo con la palabra OK.', fabrica_motores(P, 90), Puerta(os.path.join(tmp, 'real.db'), 4), memoria, 'ficha-qwen37plus', dormir=lambda s: None).correr()
    chequeo('REAL Token Plan: ficha 1 con qwen3.7-plus, una llamada real', res['estado'] == 'SALIDA' and res['tokens']['total_api_tokens'] > 0, (res['estado'], res['tokens']['total_api_tokens'], res['gaps']))


if __name__ == '__main__':
    tmp = tempfile.mkdtemp()
    srv = ThreadingHTTPServer(('127.0.0.1', 0), Falso)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = 'http://127.0.0.1:' + str(srv.server_address[1])
    F = [cargar_ficha(FICHAS + '/' + d + '/ficha.json') for d in ('ficha1-modelos', 'ficha2-dag-codigo', 'ficha3-frontend', 'ficha4-nvidia-groq')]
    prueba_puerta(tmp)
    prueba_ficha_dag(tmp, base, F[1], F[2])
    prueba_ficha1(tmp, base, F[0])
    prueba_especiales(tmp, F[0])
    prueba_realtime_falso(tmp)
    prueba_plantilla_y_ficha4(tmp, base, F)
    prueba_candados_budget_cola(tmp, base)
    prueba_memoria(tmp)
    prueba_tres_fichas(tmp, base, F[:3])
    prueba_token_plan(tmp)
    prueba_real_token_plan(tmp, F[0])
    prueba_real_14(tmp, F[0])
    prueba_real_todas(tmp, F)
    print('RESULTADO_FICHAS', sum(RES), '/', len(RES), flush=True)
    sys.exit(0 if all(RES) else 1)
