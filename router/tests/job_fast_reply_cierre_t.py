"""Cierre Fichas 1-4 (respuesta rapida): modelos de Ficha 1, trazas reales de Fichas 2 y 3, rutas de Ficha 4 y Graphiti/Graphify en FAST_QA.
Uso: ROUTER_URL=http://127.0.0.1:8000 RIU_ROUTER_API_KEY=... python3 job_fast_reply_cierre_t.py [F1M GRAPH F2TR F3TR F4R]"""
import json, os, sys, time, urllib.request as u
from concurrent.futures import ThreadPoolExecutor

U = os.environ['ROUTER_URL'].rstrip('/')
P = '/plugins/fichas_qwen/call/'
K = os.environ.get('RIU_ROUTER_API_KEY', '')
FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'plugins', 'fichas_qwen', 'fichas')
F = {'fast_reply': True}
RES = []


def post(path, body, t=60):
    r = u.Request(U + P + path, data=json.dumps(body).encode(), headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + K, 'X-API-Key': K})
    return json.load(u.urlopen(r, timeout=t))


def chat(ficha, msg, modelo='ficha-qwen38flash', extra=None, limite=420, sesion=None):
    t = time.time()
    b = {'ficha_qwen': ficha, 'modelo': modelo, 'messages': [{'role': 'user', 'content': msg}], 'sesion': sesion or 'ci-%s-%d' % (ficha, int(t * 1000))}
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


def modelo_de(x):
    return next((z.get('modelo') for z in (x.get('traza') or []) if z.get('modelo') and z.get('modelo') != 'goals'), x.get('modelo'))


def emit(tag, ok, **kw):
    RES.append(bool(ok))
    print(json.dumps(dict(test=tag, PASS=bool(ok), **kw), ensure_ascii=False), flush=True)


def ficha_json(n):
    return json.load(open(os.path.join(FD, n + '.json'), encoding='utf-8'))


SEL = sys.argv[1:] or ['F1M', 'GRAPH', 'F4R', 'F2TR', 'F3TR']
TEXTO = ['ficha-qwen38max', 'ficha-qwen38flash', 'ficha-qwen37max', 'ficha-qwen37plus', 'ficha-qwen36flash', 'ficha-dsv4pro', 'ficha-dsv4pro0813', 'ficha-dsv4flash', 'ficha-glm52']

if 'F1M' in SEL:  # Ficha 1: TODOS los modelos del selector, uno por uno, con FAST_QA
    f1 = ficha_json('ficha1-modelos'); sel = [m.get('id') if isinstance(m, dict) else m for m in f1['selector']]
    def uno(m):
        try:
            x = chat('1', 'Responde solo OK', modelo=m, extra=F, limite=240)
        except Exception as e:  # noqa: BLE001
            return m, {'estado': 'ERROR', 'reply': str(e)[:120], '_t_total_ms': 0}
        return m, x
    with ThreadPoolExecutor(4) as ex:
        for m, x in ex.map(uno, sel):
            ll, tc = cuenta(x); mod = modelo_de(x); r = str(x.get('reply') or '')
            if m in TEXTO:
                ok = x.get('execution_path') == 'FAST_QA' and ll == 1 and tc == 0 and mod == m and bool(r)
            else:  # imagen y voz: GAP_NO_EXECUTOR permitido (Parche 2)
                ok = 'NO_EXECUTOR' in (r + json.dumps(x, ensure_ascii=False))
            emit('F1 ' + m, ok, tipo='texto' if m in TEXTO else 'imagen/voz', execution_path=x.get('execution_path'), modelo=mod, numero_llamadas=ll, tool_calls=tc, ms=x.get('_t_total_ms'), reply=r[:60])

if 'GRAPH' in SEL:  # Graphiti y Graphify en FAST_QA = 0 (contador dentro del proceso del Router; control con ancla)
    def gc():
        try:
            time.sleep(0.8); return json.load(open('/tmp/gcount.json'))
        except Exception:  # noqa: BLE001
            return None
    if gc() is None:
        emit('GRAPH contador', False, detalle='sin contador (FR_GRAPH no activo)')
    else:
        for fi in ['1', '2', '3', '4']:
            a = gc(); x = chat(fi, 'Responde solo OK', extra=F, limite=240); b = gc(); ll, tc = cuenta(x)
            dg = b['graphiti'] - a['graphiti']; df = b['graphify'] - a['graphify']
            emit('GRAPH F%s FAST_QA' % fi, x.get('execution_path') == 'FAST_QA' and dg == 0 and df == 0 and tc == 0, execution_path=x.get('execution_path'), graphiti_calls=dg, graphify_calls=df, tool_calls=tc, numero_llamadas=ll)
        a = gc(); x = chat('1', '¿Qué es una API?', extra={'anclados': ['archivo:test.md']}, limite=300); b = gc()
        dg = b['graphiti'] - a['graphiti']; df = b['graphify'] - a['graphify']
        print(json.dumps({'test': 'GRAPH control (sin FAST, con ancla)', 'INFO': True, 'execution_path': x.get('execution_path'), 'graphiti_calls': dg, 'graphify_calls': df, 'detalle': 'si ambos son 0 el contador no detecta Graphiti con esta ancla'}, ensure_ascii=False), flush=True)

if 'F4R' in SEL:  # Ficha 4: rutas reales por task_type (HTTP /llm) y rechazo de fast_reply en rutas pesadas (chat)
    RUT = [('question', 'ficha-qwen38flash', True), ('simple', 'ficha-qwen38flash', True), ('chat', 'ficha-qwen38flash', True), ('frontend', 'ficha-dsv4flash', False), ('reason', 'ficha-qwen37max', False),
           ('architecture', 'ficha-qwen38max', False), ('complex', 'ficha-qwen38max', False), ('planning', 'ficha-qwen38max', False)]
    for tt, mod, rapido in RUT:
        x = llm({'caller_id': 'chat', 'task_type': tt, 'fast_reply': True, 'messages': [{'role': 'user', 'content': 'Responde solo OK'}]})
        emit('F4 /llm task_type=%s + fast_reply' % tt, x.get('modelo') == mod and bool(x.get('fast_lane')) == rapido, esperado=mod, modelo=x.get('modelo'), fast_lane=x.get('fast_lane'), ms=x.get('_t_total_ms'), error=x.get('error'))
    for tt in ['architecture', 'complex', 'planning', 'reason', 'frontend']:
        x = chat('4', 'Responde solo OK', extra=dict(F, task_type=tt), limite=300)
        emit('F4 chat fast_reply + task_type=%s rechazado' % tt, x.get('execution_path') == 'HEAVY' and x.get('fast_lane') is False, execution_path=x.get('execution_path'), fast_lane=x.get('fast_lane'), modelo=modelo_de(x), ms=x.get('_t_total_ms'))
    x = chat('4', 'Responde solo OK', extra=dict(F, task_type='question'), limite=300)
    emit('F4 chat fast_reply + question = FAST_QA flash', x.get('execution_path') == 'FAST_QA' and modelo_de(x) == 'ficha-qwen38flash', execution_path=x.get('execution_path'), modelo=modelo_de(x), ms=x.get('_t_total_ms'))


def traza_filas(x, esp):
    return [{'nodo': z.get('nodo'), 'modelo': z.get('modelo'), 'esperado': esp.get(z.get('nodo')), 'ok': z.get('ok'), 'ms': z.get('ms')} for z in (x.get('traza') or [])]


def ficha_traza(fi, nombre, req, aud, consulta):
    fj = ficha_json(nombre); esp = {n['id']: n.get('modelo') for n in fj['nodos'] if n.get('modelo')}
    print(json.dumps({'test': 'F%s modelos declarados' % fi, 'INFO': True, 'nodos': esp}, ensure_ascii=False), flush=True)
    if consulta:  # FAST_CONSULT real (sin boton)
        x = chat(fi, '¿Qué diferencia hay entre REST y WebSocket?', limite=420); fl = traza_filas(x, esp); ll, tc = cuenta(x)
        emit('F%s FAST_CONSULT traza real' % fi, x.get('execution_path') == 'FAST_CONSULT' and fl and all((f['modelo'] == f['esperado']) for f in fl if f['esperado']), execution_path=x.get('execution_path'), numero_llamadas=ll, tool_calls=tc, traza=fl, ms=x.get('_t_total_ms'))
    S = 'ci-traza-%s-%d' % (fi, int(time.time()))
    x1 = chat(fi, 'Crea el archivo prueba_fast.txt con el texto OK.', extra=F, sesion=S, limite=1500); f1 = traza_filas(x1, esp); n1 = {f['nodo'] for f in f1}; l1, t1 = cuenta(x1)
    emit('F%s HEAVY plan (con fast_reply) traza real' % fi, x1.get('execution_path') == 'HEAVY' and set(req) <= n1 and all((f['modelo'] == f['esperado']) for f in f1 if f['esperado']), execution_path=x1.get('execution_path'), estado_tarea=x1.get('estado_tarea'), numero_llamadas=l1, tool_calls=t1, nodos_requeridos=req, nodos_vistos=sorted(n for n in n1 if n), traza=f1, ms=x1.get('_t_total_ms'))
    x2 = chat(fi, '/aprobar', sesion=S, limite=2400); f2 = traza_filas(x2, esp); n2 = {f['nodo'] for f in f2}; l2, t2 = cuenta(x2)
    print(json.dumps({'test': 'F%s tras /aprobar' % fi, 'INFO': True, 'execution_path': x2.get('execution_path'), 'estado_tarea': x2.get('estado_tarea'), 'nodos': sorted(n for n in n2 if n), 'numero_llamadas': l2, 'tool_calls': t2, 'traza': f2, 'reply': str(x2.get('reply') or '')[:200], 'ms': x2.get('_t_total_ms')}, ensure_ascii=False), flush=True)
    todo = {f['nodo'] for f in f1 + f2}
    emit('F%s auditores y N4 con su modelo' % fi, set(aud) <= todo and all((f['modelo'] == f['esperado']) for f in f1 + f2 if f['esperado']), auditores_requeridos=aud, nodos_vistos=sorted(n for n in todo if n), traza_aprobacion=f2)


if 'F2TR' in SEL:
    ficha_traza('2', 'ficha2-dag-codigo', ['N1', 'N2', 'N3', 'N3B', 'N4'], ['N4', 'N6', 'N7'], True)
if 'F3TR' in SEL:
    ficha_traza('3', 'ficha3-frontend', ['N1', 'N2', 'N3', 'N3B', 'N3D', 'N4'], ['N4', 'N6', 'N7', 'N8'], False)
print('RESUMEN_CIERRE %d/%d PASS' % (sum(RES), len(RES)), flush=True)
sys.exit(0 if RES and all(RES) else 1)
