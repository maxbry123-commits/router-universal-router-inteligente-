"""Prueba FAST LANE / FAST_CONSULT (Fichas 1-4): peticiones individuales por HTTP al Router. Uso: ROUTER_URL=https://<job>--8000.hf.jobs python3 job_fast_lane_t.py"""
import json, os, sys, time, urllib.request as u

U = os.environ['ROUTER_URL'].rstrip('/')
P = '/plugins/fichas_qwen/call/'


def post(path, body, t=60):
    r = u.Request(U + P + path, data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
    return json.load(u.urlopen(r, timeout=t))


def chat(ficha, msg, modelo='ficha-qwen38flash', extra=None, limite=420):
    t = time.time()
    b = {'ficha_qwen': ficha, 'modelo': modelo, 'messages': [{'role': 'user', 'content': msg}], 'sesion': 'fl-%s-%d' % (ficha, int(t))}
    b.update(extra or {})
    pid = post('chat_async', b)['result']['proceso_id']
    while time.time() - t < limite:
        time.sleep(1)
        x = post('resultado', {'proceso_id': pid})['result']
        if x.get('estado') != 'procesando':
            x['_t_total_ms'] = int((time.time() - t) * 1000)
            return x
    return {'estado': 'TIMEOUT', '_t_total_ms': int((time.time() - t) * 1000)}


def fila(tag, ok, x, extra=''):
    tz = x.get('traza') or []
    m = [(z.get('nodo'), (z.get('metricas') or {})) for z in tz]
    print(json.dumps({'test': tag, 'PASS': bool(ok), 'fast_lane': x.get('fast_lane'), 'path': x.get('execution_path'), 'ms': x.get('_t_total_ms', x.get('ms')),
                      'metricas': m, 'extra': extra}, ensure_ascii=False), flush=True)


SEL = sys.argv[1:] or list('ABCDEFGH')
if 'A' in SEL:
    x = chat('1', '¿Qué es una API? Responde en una frase.')
    mt = (x.get('traza') or [{}])[0].get('metricas') or {}
    r = str(x.get('reply') or '')
    fila('A F1 simple', x.get('fast_lane') is True and mt.get('perfil_usado') == 'fast' and mt.get('numero_llamadas_modelo') == 1 and mt.get('numero_tool_calls') == 0 and r and 'DIAGRAMA' not in r, x, r[:80])
if 'B' in SEL:
    x = chat('1', '¿Qué es arquitectura hexagonal?')
    fila('B F1 arquitectura-pregunta', x.get('fast_lane') is True, x)
if 'C' in SEL:
    x = chat('1', 'Modifica el archivo app.py y corrige el error.')
    fila('C F1 ejecucion', x.get('fast_lane') is False, x, str(x.get('estado_tarea')))
if 'D' in SEL:
    x = chat('1', '¿Qué es una API?', extra={'anclados': ['archivo:test.md']})
    fila('D F1 con ancla', x.get('fast_lane') is False, x)
def llm(body):
    t = time.time()
    x = post('llm', body)
    x = x.get('result') if isinstance(x.get('result'), dict) else x
    x['_t_total_ms'] = int((time.time() - t) * 1000)
    return x
if 'E' in SEL:
    x = llm({'caller_id': 'chat', 'task_type': 'simple', 'messages': [{'role': 'user', 'content': '¿Qué es una API?'}]})
    fila('E F4 simple', x.get('fast_lane') is True and x.get('modelo') == 'ficha-qwen38flash' and x.get('reply'), x, x.get('modelo'))
if 'F' in SEL:
    x = llm({'caller_id': 'graphiti', 'task_type': 'small', 'messages': [{'role': 'user', 'content': 'Responde solo OK'}]})
    fila('F F4 graphiti', x.get('fast_lane') is False, x, x.get('modelo'))
if 'G' in SEL:
    x = llm({'caller_id': 'chat', 'task_type': 'architecture', 'messages': [{'role': 'user', 'content': 'Responde solo OK'}]})
    fila('G F4 arquitectura', x.get('fast_lane') is False and x.get('modelo') == 'ficha-qwen38max', x, x.get('modelo'))
if 'H' in SEL:
    x = llm({'caller_id': 'agent', 'task_type': 'simple', 'messages': [{'role': 'user', 'content': 'Responde solo OK'}]})
    fila('H F4 agente', x.get('fast_lane') is False, x, x.get('modelo'))
if 'I' in SEL:
    x = chat('2', '¿Qué arquitectura recomiendas para separar estos módulos?')
    r = str(x.get('reply') or '')
    fila('I F2 consulta', x.get('execution_path') == 'FAST_CONSULT' and r.startswith('ASK CONSIL') and 'DECISIÓN' in r, x, '%d nodos' % len(x.get('traza') or []))
if 'J' in SEL:
    x = chat('3', '¿Qué estructura de paneles recomiendas para este frontend?')
    r = str(x.get('reply') or '')
    fila('J F3 consulta', x.get('execution_path') == 'FAST_CONSULT' and r.startswith('ASK CONSIL FRONTEND'), x, '%d nodos' % len(x.get('traza') or []))
if 'K' in SEL:
    x = chat('3', 'Modifica el frontend y corrige los archivos')
    fila('K F3 escape', x.get('fast_lane') is False and x.get('execution_path') == 'HEAVY', x, str(x.get('estado_tarea')))
