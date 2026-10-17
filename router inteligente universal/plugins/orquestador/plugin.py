"""Orquestador de agentes (prototipo). Cada agente = una seccion de chat aislada y anclada al chat principal:
hilo propio, system propio, memoria (id), sandbox (carpeta) y archivos propios. La LLM se llama SOLO por el harness
puente_chat (chat_async + resultado): en el Space en proceso; con RIU_PUENTE_URL por HTTP. No toca fichas."""
from __future__ import annotations
import base64, json, os, re, secrets, sqlite3, threading, time, urllib.request
from pathlib import Path
from typing import Any

DATA = Path(os.getenv('RIU_ORQ_DIR') or '/tmp/riu-data/orquestador')
DB = DATA / 'orquestador.sqlite3'
MAX_AGENTES = 20
STREAM_N = 4
_LOCK = threading.RLock()
# Ficha 4 (ficha4-workflow-yaiwes): modelos de texto -> id del harness (mismo mapa que fichas_qwen._QW)
MODELOS = [('ficha-qwen38max', 'qw-qwen-3-8-max', 'Qwen 3.8 Max'), ('ficha-qwen38flash', 'qw-qwen-3-8-flash', 'Qwen 3.8 Flash'),
           ('ficha-qwen37max', 'qw-qwen-3-7-max', 'Qwen 3.7 Max'), ('ficha-qwen37plus', 'qw-qwen-3-7-plus', 'Qwen 3.7 Plus'),
           ('ficha-qwen36flash', 'qw-qwen-3-6-flash', 'Qwen 3.6 Flash'), ('ficha-dsv4pro', 'qw-deepseek-v4-pro', 'DeepSeek V4 Pro'),
           ('ficha-dsv4flash', 'qw-deepseek-v4-flash', 'DeepSeek V4 Flash'), ('ficha-glm52', 'qw-glm-5-2', 'GLM 5.2')]
_HARNESS = {f: h for f, h, _ in MODELOS}
ESTADOS = ('activo', 'trabajando', 'bloqueado', 'aprobacion', 'terminado', 'error')
ICONOS = ['🤖', '🧠', '🛠️', '🔎', '✍️', '📊', '🧪', '🛰️']


def _db():
    DATA.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(DB), timeout=5, check_same_thread=False)
    c.execute('PRAGMA busy_timeout=5000')
    c.execute('CREATE TABLE IF NOT EXISTS agentes (id TEXT PRIMARY KEY, datos TEXT NOT NULL, creado REAL)')
    return c


def _cargar(aid):
    with _LOCK, _db() as c:
        r = c.execute('SELECT datos FROM agentes WHERE id=?', (aid,)).fetchone()
    return json.loads(r[0]) if r else None


def _guardar(a):
    with _LOCK, _db() as c:
        c.execute('INSERT OR REPLACE INTO agentes(id,datos,creado) VALUES(?,?,?)', (a['id'], json.dumps(a, ensure_ascii=False), a.get('creado') or time.time()))
    return a


def _todos():
    with _LOCK, _db() as c:
        return [json.loads(r[0]) for r in c.execute('SELECT datos FROM agentes ORDER BY creado')]


def _sandbox(aid):
    p = DATA / 'sandbox' / re.sub(r'[^a-z0-9-]', '', aid)
    (p / 'archivos').mkdir(parents=True, exist_ok=True)
    return p


def _linea(a, txt):
    a.setdefault('stream', []).append(time.strftime('%H:%M:%S') + ' ' + str(txt)[:140])
    a['stream'] = a['stream'][-40:]


def _vista(a, completo=False):
    v = {k: a.get(k) for k in ('id', 'nombre', 'icono', 'modelo', 'modelo_nombre', 'estado', 'sistema', 'memoria_id', 'origen', 'creado_por', 'chat_sesion', 'latencia_ms')}
    v['stream'] = (a.get('stream') or [])[-STREAM_N:]
    v['archivos'] = [x['nombre'] for x in a.get('archivos') or []]
    v['mensajes_n'] = len(a.get('mensajes') or [])
    if completo:
        v['mensajes'] = a.get('mensajes') or []
        v['instrucciones'] = a.get('instrucciones') or []
    return v


# ---------- harness ----------
def _puente(accion, cuerpo):
    url = os.getenv('RIU_PUENTE_URL')
    if url:  # HTTP al harness (prueba local contra el Space, o Router remoto)
        h = {'Content-Type': 'application/json', 'Origin': 'https://riu-jev-bridge.vercel.app'}
        if os.getenv('RIU_ROUTER_API_KEY'):
            h['X-API-Key'] = os.getenv('RIU_ROUTER_API_KEY')
        r = urllib.request.Request(url.rstrip('/') + '/' + accion, data=json.dumps(cuerpo).encode(), headers=h, method='POST')
        d = json.loads(urllib.request.urlopen(r, timeout=30).read() or b'{}')
        return d.get('result', d) if isinstance(d, dict) else {}
    from plugins.puente_chat import plugin as pc  # en el Space: el mismo harness del chat, en proceso
    return pc.handle(accion, cuerpo)


def _texto(r):
    if not isinstance(r, dict):
        return ''
    ch = r.get('choices') or []
    if ch:
        return str((ch[0].get('message') or {}).get('content') or '')
    return str(r.get('respuesta') or r.get('reply') or r.get('text') or r.get('content') or '')


def _mensajes_llm(a):
    sis = (a.get('sistema') or 'Eres un agente del orquestador. Responde en espanol, claro y breve.')
    sis += '\nTu nombre: %s. Memoria: %s. Sandbox: %s.' % (a['nombre'], a['memoria_id'], a['sandbox'])
    sis += '\nSi necesitas aprobacion del Director antes de seguir, escribe [APROBACION] al inicio. Si estas bloqueado, escribe [BLOQUEADO].'
    for ins in a.get('instrucciones') or []:
        sis += '\nInstruccion: ' + ins[:2000]
    for f in a.get('archivos') or []:
        try:
            t = Path(f['ruta']).read_text(encoding='utf-8', errors='replace')[:6000]
            sis += '\n--- Archivo adjunto %s ---\n%s' % (f['nombre'], t)
        except Exception:  # noqa: BLE001
            pass
    hist = [m for m in (a.get('mensajes') or []) if m.get('role') in ('user', 'assistant')][-12:]
    return [{'role': 'system', 'content': sis}] + [{'role': m['role'], 'content': m['content'][:6000]} for m in hist]


# ---------- acciones ----------
def crear(p, creado_por='director'):
    if len(_todos()) >= MAX_AGENTES:
        return {'error': 'MAX_AGENTES', 'max': MAX_AGENTES}
    modelo = str(p.get('modelo') or 'ficha-qwen38flash')
    if modelo not in _HARNESS:
        return {'error': 'MODELO_NO_FICHA4', 'validos': list(_HARNESS)}
    aid = 'ag-' + secrets.token_hex(4)
    nombre = (str(p.get('nombre') or '').strip() or 'Agente ' + aid[3:7])[:40]
    a = {'id': aid, 'nombre': nombre, 'icono': str(p.get('icono') or ICONOS[len(_todos()) % len(ICONOS)])[:4],
         'modelo': modelo, 'modelo_nombre': next(n for f, _, n in MODELOS if f == modelo), 'sistema': str(p.get('sistema') or '')[:4000],
         'estado': 'activo', 'memoria_id': 'mem-' + aid, 'sandbox': str(_sandbox(aid)), 'archivos': [], 'instrucciones': [], 'mensajes': [],
         'stream': [], 'origen': p.get('origen'), 'creado_por': creado_por, 'chat_sesion': str(p.get('chat_sesion') or '')[:80], 'creado': time.time()}
    _linea(a, 'creado por %s · %s' % (creado_por, a['modelo_nombre']))
    return {'agente': _vista(_guardar(a))}


def mirror(p):
    de = str(p.get('de') or '')
    if de == 'chat':
        base = {'nombre': 'Mirror chat', 'sistema': 'Eres un mirror del chat principal: trabajas en paralelo con el mismo contexto.',
                'mensajes': [m for m in (p.get('mensajes') or []) if isinstance(m, dict)][-12:], 'archivos': [], 'instrucciones': []}
    else:
        base = _cargar(de)
        if not base:
            return {'error': 'AGENTE_NO_EXISTE'}
    r = crear({'nombre': ('Mirror ' + base['nombre'])[:40], 'sistema': base.get('sistema'), 'modelo': p.get('modelo') or base.get('modelo') or 'ficha-qwen38flash',
               'origen': de, 'icono': '🪞', 'chat_sesion': p.get('chat_sesion')}, p.get('creado_por') or 'director')
    if 'agente' not in r:
        return r
    a = _cargar(r['agente']['id'])
    a['mensajes'] = [{'role': m.get('role'), 'content': str(m.get('content') or '')} for m in base.get('mensajes') or []]
    a['instrucciones'] = list(base.get('instrucciones') or [])
    for f in base.get('archivos') or []:  # copia los archivos a SU sandbox (aislado)
        try:
            dst = Path(a['sandbox']) / 'archivos' / f['nombre']
            dst.write_bytes(Path(f['ruta']).read_bytes())
            a['archivos'].append({'nombre': f['nombre'], 'ruta': str(dst), 'bytes': dst.stat().st_size})
        except Exception:  # noqa: BLE001
            pass
    _linea(a, 'mirror de %s: %d mensajes, %d archivos' % (de, len(a['mensajes']), len(a['archivos'])))
    return {'agente': _vista(_guardar(a))}


def enviar(p):
    a = _cargar(str(p.get('id') or ''))
    if not a:
        return {'error': 'AGENTE_NO_EXISTE'}
    if a.get('pid'):
        return {'error': 'AGENTE_OCUPADO', 'agente': _vista(a)}
    msg = str(p.get('mensaje') or '').strip()
    if not msg:
        return {'error': 'MENSAJE_VACIO'}
    a['mensajes'].append({'role': 'user', 'content': msg[:8000], 't': time.time()})
    _linea(a, 'tú: ' + msg[:80])
    try:
        r = _puente('chat_async', {'model': _HARNESS[a['modelo']], 'messages': _mensajes_llm(a), 'sesion': 'agente-' + a['id'],
                                   'tools_habilitadas': False, 'max_tokens': int(p.get('max_tokens') or 1200),
                                   'request_id': 'orq-' + a['id'] + '-' + str(len(a['mensajes'])), '_t_submit': time.time()})
    except Exception as x:  # noqa: BLE001
        r = {'error': 'GAP_HARNESS_HTTP', 'detalle': type(x).__name__}
    if r.get('proceso_id'):
        a.update(pid=r['proceso_id'], t0=time.time(), estado='trabajando')
        _linea(a, 'harness → %s · proceso %s' % (a['modelo_nombre'], r['proceso_id'][:6]))
    else:
        a['estado'] = 'bloqueado' if r.get('error') == 'CHAT_OCUPADO_REINTENTA' else 'error'
        _linea(a, 'error: %s' % (r.get('error') or 'sin proceso_id'))
    return {'agente': _vista(_guardar(a))}


def estado(p):
    a = _cargar(str(p.get('id') or ''))
    if not a:
        return {'error': 'AGENTE_NO_EXISTE'}
    if a.get('pid'):
        try:
            r = _puente('resultado', {'proceso_id': a['pid'], 'espera': min(4.0, float(p.get('espera') or 0))})
        except Exception as x:  # noqa: BLE001
            r = {'estado': 'procesando', '_red': type(x).__name__}
        if r.get('estado') == 'procesando':
            prog = str(r.get('progreso') or '')
            if prog and prog != a.get('_prog'):
                a['_prog'] = prog
                _linea(a, prog[:120])
            elif time.time() - float(a.get('_tl') or 0) > 6:
                a['_tl'] = time.time()
                _linea(a, 'trabajando… %d s' % int(time.time() - a['t0']))
        else:
            ms = int((time.time() - a.pop('t0', time.time())) * 1000)
            a.pop('pid', None); a.pop('_prog', None)
            txt = _texto(r)
            if r.get('error') or not txt:
                a['estado'] = 'error'
                _linea(a, 'error: %s' % (r.get('error') or 'respuesta vacia'))
            else:
                a['mensajes'].append({'role': 'assistant', 'content': txt, 't': time.time(), 'ms': ms})
                a['latencia_ms'] = ms
                a['estado'] = 'aprobacion' if txt.lstrip().startswith('[APROBACION]') else 'bloqueado' if txt.lstrip().startswith('[BLOQUEADO]') else 'terminado'
                _linea(a, '%s · %d s %03d ms: %s' % (a['estado'], ms // 1000, ms % 1000, txt.replace('\n', ' ')[:70]))
        _guardar(a)
    return {'agente': _vista(a, completo=True)}


def subir(p):
    a = _cargar(str(p.get('id') or ''))
    if not a:
        return {'error': 'AGENTE_NO_EXISTE'}
    if p.get('instruccion'):
        a['instrucciones'].append(str(p['instruccion'])[:2000])
        _linea(a, '+ instrucción: ' + str(p['instruccion'])[:60])
    if p.get('datos_b64'):
        datos = str(p['datos_b64'])
        if len(datos) > 4_000_000:
            return {'error': 'ARCHIVO_MUY_GRANDE'}
        nombre = re.sub(r'[^\w.\- ]', '_', str(p.get('nombre') or 'archivo'))[:100] or 'archivo'
        dst = Path(a['sandbox']) / 'archivos' / nombre
        dst.write_bytes(base64.b64decode(datos))
        a['archivos'] = [x for x in a['archivos'] if x['nombre'] != nombre] + [{'nombre': nombre, 'ruta': str(dst), 'bytes': dst.stat().st_size}]
        _linea(a, '+ archivo %s (%d B) → sandbox' % (nombre, dst.stat().st_size))
    return {'agente': _vista(_guardar(a), completo=True)}


def chat_crear(p):
    """La LLM del chat decide el agente (tool crear_agente): devuelve JSON {nombre, sistema, modelo} y se crea."""
    pedido = str(p.get('pedido') or '').strip()
    if not pedido:
        return {'error': 'PEDIDO_VACIO'}
    sis = ('Eres la LLM del chat principal con la tool crear_agente. Responde SOLO un JSON: '
           '{"nombre": str corto, "sistema": instrucciones del agente, "modelo": uno de %s}. Elige el modelo segun la tarea '
           '(codigo complejo: ficha-qwen38max o ficha-dsv4pro; rapido: ficha-qwen38flash o ficha-dsv4flash).' % json.dumps(list(_HARNESS)))
    t0 = time.time()
    r = _puente('chat_async', {'model': _HARNESS[str(p.get('modelo_chat') or 'ficha-qwen38flash')] if str(p.get('modelo_chat') or '') in _HARNESS else 'qw-qwen-3-8-flash',
                               'messages': [{'role': 'system', 'content': sis}, {'role': 'user', 'content': pedido[:4000]}],
                               'sesion': 'orq-chat', 'tools_habilitadas': False, 'max_tokens': 600})
    while r.get('estado') == 'procesando' and time.time() - t0 < 80:
        r = _puente('resultado', {'proceso_id': r['proceso_id'], 'espera': 5})
    txt = _texto(r)
    m = re.search(r'\{.*\}', txt, re.S)
    try:
        spec = json.loads(m.group(0)) if m else {}
    except Exception:  # noqa: BLE001
        spec = {}
    if not spec.get('nombre'):
        return {'error': 'LLM_SIN_JSON', 'detalle': txt[:300] or r.get('error')}
    out = crear({'nombre': spec.get('nombre'), 'sistema': spec.get('sistema'), 'modelo': spec.get('modelo') if spec.get('modelo') in _HARNESS else 'ficha-qwen38flash',
                 'chat_sesion': p.get('chat_sesion')}, 'llm-chat')
    out['ms'] = int((time.time() - t0) * 1000)
    return out


def handle(action: str, payload: dict[str, Any]) -> dict[str, Any]:
    p = payload or {}
    if action == 'status':
        return {'ok': True, 'agentes': len(_todos()), 'db': str(DB), 'harness': 'http' if os.getenv('RIU_PUENTE_URL') else 'proceso'}
    if action == 'modelos':
        return {'ficha': 'ficha4-workflow-yaiwes', 'modelos': [{'id': f, 'harness': h, 'nombre': n} for f, h, n in MODELOS], 'estados': list(ESTADOS)}
    if action == 'listar':
        return {'agentes': [_vista(a) for a in _todos()], 'max': MAX_AGENTES}
    if action == 'crear':
        return crear(p, 'llm-chat' if p.get('creado_por') == 'llm-chat' else 'director')
    if action == 'borrar':
        aid = str(p.get('id') or '')
        with _LOCK, _db() as c:
            n = c.execute('DELETE FROM agentes WHERE id=?', (aid,)).rowcount
        import shutil
        shutil.rmtree(DATA / 'sandbox' / re.sub(r'[^a-z0-9-]', '', aid), ignore_errors=True)
        return {'borrado': bool(n)}
    if action == 'mirror':
        return mirror(p)
    if action == 'enviar':
        return enviar(p)
    if action == 'estado':
        return estado(p)
    if action == 'aprobar':
        a = _cargar(str(p.get('id') or ''))
        if not a:
            return {'error': 'AGENTE_NO_EXISTE'}
        a['estado'] = 'activo'; _linea(a, 'aprobado por el Director')
        return {'agente': _vista(_guardar(a))}
    if action == 'configurar':  # el Director o la LLM del chat cambian el modelo (ficha 4) o el system del agente
        a = _cargar(str(p.get('id') or ''))
        if not a:
            return {'error': 'AGENTE_NO_EXISTE'}
        if p.get('modelo'):
            if p['modelo'] not in _HARNESS:
                return {'error': 'MODELO_NO_FICHA4', 'validos': list(_HARNESS)}
            a['modelo'] = p['modelo']; a['modelo_nombre'] = next(n for f, _, n in MODELOS if f == p['modelo'])
            _linea(a, 'modelo → ' + a['modelo_nombre'])
        if p.get('sistema') is not None:
            a['sistema'] = str(p['sistema'])[:4000]; _linea(a, 'system actualizado')
        return {'agente': _vista(_guardar(a))}
    if action == 'subir':
        return subir(p)
    if action == 'archivos':
        a = _cargar(str(p.get('id') or ''))
        return {'archivos': [{'nombre': x['nombre'], 'bytes': x['bytes']} for x in (a or {}).get('archivos') or []]} if a else {'error': 'AGENTE_NO_EXISTE'}
    if action == 'chat_crear':
        return chat_crear(p)
    return {'error': 'ACCION_DESCONOCIDA'}
