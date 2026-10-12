"""Prueba del boton Respuesta rapida (fast_reply), las 8 pruebas T1-T8, una peticion HTTP cada una al Router.
Uso: ROUTER_URL=http://127.0.0.1:8000 python3 job_fast_reply_t.py [T1 T2 ...]"""
import json, os, sys, time, urllib.request as u

U = os.environ['ROUTER_URL'].rstrip('/')
P = '/plugins/fichas_qwen/call/'
K = os.environ.get('RIU_ROUTER_API_KEY', '')  # el Router exige clave aun en localhost


def post(path, body, t=60):
    r = u.Request(U + P + path, data=json.dumps(body).encode(), headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + K, 'X-API-Key': K})
    return json.load(u.urlopen(r, timeout=t))


def chat(ficha, msg, modelo='ficha-qwen38flash', extra=None, limite=420):
    t = time.time()
    b = {'ficha_qwen': ficha, 'modelo': modelo, 'messages': [{'role': 'user', 'content': msg}], 'sesion': 'fr-%s-%d' % (ficha, int(t))}
    b.update(extra or {})
    pid = post('chat_async', b)['result']['proceso_id']
    while time.time() - t < limite:
        time.sleep(1)
        x = post('resultado', {'proceso_id': pid})['result']
        if x.get('estado') != 'procesando':
            x['_t_total_ms'] = int((time.time() - t) * 1000)
            return x
    return {'estado': 'TIMEOUT', '_t_total_ms': int((time.time() - t) * 1000)}


def llm(body):
    t = time.time()
    x = post('llm', body)
    x = x.get('result') if isinstance(x.get('result'), dict) else x
    x['_t_total_ms'] = int((time.time() - t) * 1000)
    return x


def cuenta(x):
    m = [(z.get('metricas') or {}) for z in (x.get('traza') or [])]
    return sum(int(k.get('numero_llamadas_modelo') or 0) for k in m), sum(int(k.get('numero_tool_calls') or 0) for k in m)


RES = []


def fila(tag, ficha, ok, x, extra=''):
    ll, tc = cuenta(x)
    modelo = next((z.get('modelo') for z in (x.get('traza') or []) if z.get('modelo') != 'goals'), x.get('modelo'))
    RES.append(bool(ok))
    print(json.dumps({'test': tag, 'PASS': bool(ok), 'ficha': ficha, 'modelo': modelo, 'execution_path': x.get('execution_path'), 'numero_llamadas': ll,
                      'tool_calls': tc, 'ms': x.get('_t_total_ms', x.get('ms')), 'extra': extra}, ensure_ascii=False), flush=True)


def rapida(x, modelo=None):
    ll, tc = cuenta(x)
    t0 = (x.get('traza') or [{}])[0]
    return x.get('execution_path') == 'FAST_QA' and ll == 1 and tc == 0 and bool(x.get('reply')) and (modelo is None or t0.get('modelo') == modelo)


F = {'fast_reply': True}
SEL = sys.argv[1:] or ['T%d' % i for i in range(1, 9)]
if 'T1' in SEL:
    x = chat('1', '¿Qué es una API? Responde en una frase.', modelo='ficha-dsv4flash', extra=F)
    fila('T1 F1 + rapida + pregunta', '1', rapida(x, 'ficha-dsv4flash'), x, str(x.get('reply'))[:70])
if 'T2' in SEL:
    x = chat('2', '¿Qué es un DAG? Responde en una frase.', extra=F)
    fila('T2 F2 + rapida + pregunta', '2', rapida(x, 'ficha-qwen38flash'), x, str(x.get('reply'))[:70])
if 'T3' in SEL:
    x = chat('3', '¿Qué es CSS Grid? Responde en una frase.', extra=F)
    fila('T3 F3 + rapida + pregunta', '3', rapida(x, 'ficha-qwen38flash'), x, str(x.get('reply'))[:70])
if 'T4' in SEL:
    x = chat('4', '¿Qué es una API? Responde en una frase.', extra=dict(F, task_type='question'))
    fila('T4 F4 + rapida + question', '4', rapida(x, 'ficha-qwen38flash'), x, str(x.get('reply'))[:70])
if 'T5' in SEL:
    x = chat('2', 'Corrige este código: def f(x): return x +', extra=F)
    fila('T5 F2 + rapida + corrige codigo = HEAVY', '2', x.get('execution_path') == 'HEAVY' and x.get('fast_lane') is False, x, str(x.get('estado_tarea')))
if 'T6' in SEL:
    x = chat('3', 'Modifica panel-chat.js y prueba el frontend.', extra=F)
    fila('T6 F3 + rapida + modifica archivo = HEAVY', '3', x.get('execution_path') == 'HEAVY' and x.get('fast_lane') is False, x, str(x.get('estado_tarea')))
if 'T7' in SEL:
    x = llm({'caller_id': 'chat', 'task_type': 'architecture', 'messages': [{'role': 'user', 'content': 'Diseña la arquitectura de un sistema de colas.'}]})
    fila('T7 F4 architecture = HEAVY', '4', x.get('fast_lane') is False and x.get('modelo') == 'ficha-qwen38max', x, str({k: x.get(k) for k in ('error', 'detalle', 'modelo', 'fast_lane', 'estado')})[:300])
if 'T8' in SEL:
    a = chat('1', '¿Qué es una API? Responde en una frase.')
    b = chat('2', '¿Qué diferencia hay entre REST y WebSocket?')
    fila('T8 sin boton: F1 sigue rapida y F2 sigue en consíl', '1+2', a.get('execution_path') == 'FAST_QA' and b.get('execution_path') == 'FAST_CONSULT', b, 'F1=%s F2=%s' % (a.get('execution_path'), b.get('execution_path')))
print('RESUMEN_FAST_REPLY %d/%d PASS' % (sum(RES), len(RES)), flush=True)
sys.exit(0 if all(RES) else 1)
