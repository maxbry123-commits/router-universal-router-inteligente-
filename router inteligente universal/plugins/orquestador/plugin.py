"""Orquestador de agentes — seccion "Chat BOTS" debajo de cada chat abierto. Cada agente es un sub-chat aislado:
hilo, system, memoria (id), archivos y sandbox propios. Max 50 agentes por seccion.

Persistencia: NADA en un SQLite aparte. Todo va a la fachada canonica memoria_yaiwes (la misma que usa el chat):
SQLite primario riu_chat.sqlite3 -> replica graph-sqlite-fallback + state-hub/dataset (facade.save) -> autosync al
bucket COMAND-CENTER-1/yaiwes-memoria-storage -> restauracion en frio al arrancar. La RAM es solo cache; si el Router
reinicia, el agente se rehidrata desde SQLite y el sandbox se rematerializa desde los archivos guardados.
LLM: COMPONENTE -> HARNESS (puente_chat chat_async/resultado) -> HTTP -> FICHA -> MODELO. No toca fichas."""
from __future__ import annotations
import base64, json, os, re, secrets, threading, time, urllib.request
from pathlib import Path
from typing import Any

from . import sandbox as _sbx
from . import deploy as _dep

DUENO = 'chat-ui'
MAX_AGENTES = 50
STREAM_N = 4
_LOCK = threading.RLock()
_CACHE: dict[str, dict] = {}
MODELOS = [('ficha-qwen38max', 'qw-qwen-3-8-max', 'Qwen 3.8 Max'), ('ficha-qwen38flash', 'qw-qwen-3-8-flash', 'Qwen 3.8 Flash'),
           ('ficha-qwen37max', 'qw-qwen-3-7-max', 'Qwen 3.7 Max'), ('ficha-qwen37plus', 'qw-qwen-3-7-plus', 'Qwen 3.7 Plus'),
           ('ficha-qwen36flash', 'qw-qwen-3-6-flash', 'Qwen 3.6 Flash'), ('ficha-dsv4pro', 'qw-deepseek-v4-pro', 'DeepSeek V4 Pro'),
           ('ficha-dsv4flash', 'qw-deepseek-v4-flash', 'DeepSeek V4 Flash'), ('ficha-glm52', 'qw-glm-5-2', 'GLM 5.2')]
_HARNESS = {f: h for f, h, _ in MODELOS}
ESTADOS = ('activo', 'trabajando', 'bloqueado', 'aprobacion', 'terminado', 'error')
ICONOS = ['🤖', '🧠', '🛠️', '🔎', '✍️', '📊', '🧪', '🛰️']


# ---------- memoria canonica ----------
def _mem():
    from integration.chat_mvp.memoria_loader import _memory
    return _memory()


def _sec(s):
    return re.sub(r'[^\w.-]', '', str(s or 'web-general'))[:50] or 'web-general'


def _scope(seccion):
    return (DUENO + ':orq:' + _sec(seccion))[:80]


def _ultimo(scope, key):
    r = _mem().sqlite.load(scope, key)  # la verdad: SQLite primario, el mas reciente primero
    return r[0]['data'] if r else None


def _indice(seccion):
    return list(_ultimo(_scope(seccion), 'indice') or [])


def _guardar(a, replicas=True):
    """Persistencia de un agente. replicas=True -> facade.save (SQLite + grafo + state-hub...). False -> solo SQLite (latidos del stream)."""
    with _LOCK:
        _CACHE[a['id']] = a
        m = _mem()
        (m.save if replicas else m.sqlite.save)(_scope(a['seccion']), 'agente:' + a['id'], a)
    return a


def _cargar(aid, seccion=None):
    with _LOCK:
        if aid in _CACHE:
            return _CACHE[aid]
    for sec in ([seccion] if seccion else []) + [s for s in (_ultimo(DUENO + ':orq:secciones', 'lista') or [])]:
        a = _ultimo(_scope(sec), 'agente:' + str(aid))
        if a and not a.get('borrado'):
            with _LOCK:
                _CACHE[aid] = a
            return a
    return None


def _sandbox(a):
    """Carpeta de trabajo del agente; si no existe (reinicio / restauracion en frio) se rematerializa desde la memoria."""
    p = Path(os.getenv('RIU_ORQ_DIR') or '/tmp/riu-data/orquestador') / 'sandbox' / re.sub(r'[^a-z0-9-]', '', a['id'])
    (p / 'archivos').mkdir(parents=True, exist_ok=True)
    for f in a.get('archivos') or []:
        dst = p / 'archivos' / f['nombre']
        if not dst.exists():
            d = _ultimo(_scope(a['seccion']), f['clave'])
            if d and d.get('b64'):
                dst.write_bytes(base64.b64decode(d['b64']))
    return p


def _linea(a, txt):
    a.setdefault('stream', []).append(time.strftime('%H:%M:%S') + ' ' + str(txt)[:140])
    a['stream'] = a['stream'][-40:]


def _vista(a, completo=False):
    v = {k: a.get(k) for k in ('id', 'seccion', 'nombre', 'icono', 'modelo', 'modelo_nombre', 'estado', 'sistema', 'memoria_id', 'origen', 'creado_por', 'latencia_ms')}
    v['stream'] = (a.get('stream') or [])[-STREAM_N:]
    v['archivos'] = [x['nombre'] for x in a.get('archivos') or []]
    v['mensajes_n'] = len(a.get('mensajes') or [])
    if completo:
        v['mensajes'] = a.get('mensajes') or []
        v['instrucciones'] = a.get('instrucciones') or []
        v['ejecuciones'] = (a.get('ejecuciones') or [])[-5:]
    return v


# ---------- harness ----------
def _puente(accion, cuerpo):
    url = os.getenv('RIU_PUENTE_URL') or ((os.getenv('RIU_ROUTER_URL') or 'http://127.0.0.1:' + str(os.getenv('PORT') or '7860')).rstrip('/') + '/plugins/puente_chat/call')
    h = {'Content-Type': 'application/json', 'Origin': 'https://riu-jev-bridge.vercel.app'}
    if os.getenv('RIU_ROUTER_API_KEY'):
        h['X-API-Key'] = os.getenv('RIU_ROUTER_API_KEY'); h['Authorization'] = 'Bearer ' + os.getenv('RIU_ROUTER_API_KEY')
    r = urllib.request.Request(url.rstrip('/') + '/' + accion, data=json.dumps(cuerpo).encode(), headers=h, method='POST')
    d = json.loads(urllib.request.urlopen(r, timeout=30).read() or b'{}')
    return d.get('result', d) if isinstance(d, dict) else {}


def _texto(r):
    if not isinstance(r, dict):
        return ''
    ch = r.get('choices') or []
    if ch:
        return str((ch[0].get('message') or {}).get('content') or '')
    return str(r.get('respuesta') or r.get('reply') or r.get('text') or r.get('content') or '')


def _mensajes_llm(a):
    sb = _sandbox(a)
    sis = (a.get('sistema') or 'Eres un agente del orquestador. Responde en espanol, claro y breve.')
    sis += '\nTu nombre: %s. Memoria: %s. Sandbox: %s.' % (a['nombre'], a['memoria_id'], sb)
    sis += '\nPara ejecutar codigo en tu sandbox aislado, responde con un bloque ```python ... ``` y la palabra [EJECUTAR] al final; el Director lo ejecuta y ves la salida.'
    sis += '\nSi necesitas aprobacion del Director antes de seguir, escribe [APROBACION] al inicio. Si estas bloqueado, escribe [BLOQUEADO].'
    for ins in a.get('instrucciones') or []:
        sis += '\nInstruccion: ' + ins[:2000]
    for f in a.get('archivos') or []:
        try:
            sis += '\n--- Archivo adjunto %s ---\n%s' % (f['nombre'], (sb / 'archivos' / f['nombre']).read_text(encoding='utf-8', errors='replace')[:6000])
        except Exception:  # noqa: BLE001
            pass
    hist = [m for m in (a.get('mensajes') or []) if m.get('role') in ('user', 'assistant')][-12:]
    return [{'role': 'system', 'content': sis}] + [{'role': m['role'], 'content': m['content'][:6000]} for m in hist]


# ---------- acciones ----------
def listar(seccion):
    out = []
    for aid in _indice(seccion):
        a = _cargar(aid, seccion)
        if a:
            out.append(_vista(a))
    return out


def crear(p, creado_por='director'):
    seccion = _sec(p.get('seccion'))
    ids = _indice(seccion)
    if len(ids) >= MAX_AGENTES:
        return {'error': 'MAX_AGENTES', 'max': MAX_AGENTES}
    modelo = str(p.get('modelo') or 'ficha-qwen38flash')
    if modelo not in _HARNESS:
        return {'error': 'MODELO_NO_FICHA4', 'validos': list(_HARNESS)}
    aid = 'ag-' + secrets.token_hex(4)
    a = {'id': aid, 'seccion': seccion, 'nombre': (str(p.get('nombre') or '').strip() or 'Agente ' + aid[3:7])[:40],
         'icono': str(p.get('icono') or ICONOS[len(ids) % len(ICONOS)])[:4], 'modelo': modelo,
         'modelo_nombre': next(n for f, _, n in MODELOS if f == modelo), 'sistema': str(p.get('sistema') or '')[:4000],
         'estado': 'activo', 'memoria_id': 'mem-' + aid, 'archivos': [], 'instrucciones': [], 'mensajes': [], 'ejecuciones': [],
         'stream': [], 'origen': p.get('origen'), 'creado_por': creado_por, 'creado': time.time()}
    _linea(a, 'creado por %s · %s' % (creado_por, a['modelo_nombre']))
    m = _mem()
    with _LOCK:
        m.sqlite.save(_scope(seccion), 'indice', ids + [aid])
        secs = list(_ultimo(DUENO + ':orq:secciones', 'lista') or [])
        if seccion not in secs:
            m.sqlite.save(DUENO + ':orq:secciones', 'lista', secs + [seccion])
    _guardar(a)
    _sandbox(a)
    return {'agente': _vista(a)}


def borrar(p):
    a = _cargar(str(p.get('id') or ''), p.get('seccion'))
    if not a:
        return {'borrado': False}
    with _LOCK:
        _mem().sqlite.save(_scope(a['seccion']), 'indice', [x for x in _indice(a['seccion']) if x != a['id']])
        _CACHE.pop(a['id'], None)
    _mem().save(_scope(a['seccion']), 'agente:' + a['id'], {'id': a['id'], 'borrado': True, 't': time.time()})  # lapida; el historial sigue en SQLite
    import shutil
    shutil.rmtree(_sandbox(a), ignore_errors=True)
    return {'borrado': True}


def _subir_archivo(a, nombre, raw):
    nombre = re.sub(r'[^\w.\- ]', '_', str(nombre or 'archivo'))[:100] or 'archivo'
    clave = 'archivo:orq:%s:%s' % (a['id'], nombre)  # "archivo:" -> solo SQLite (regla de la fachada), entra al sync del bucket
    _mem().save(_scope(a['seccion']), clave, {'nombre': nombre, 'b64': base64.b64encode(raw).decode(), 'bytes': len(raw)})
    (_sandbox(a) / 'archivos' / nombre).write_bytes(raw)
    a['archivos'] = [x for x in a['archivos'] if x['nombre'] != nombre] + [{'nombre': nombre, 'clave': clave, 'bytes': len(raw)}]
    return nombre


def mirror(p):
    de = str(p.get('de') or '')
    seccion = _sec(p.get('seccion'))
    if de == 'chat':
        base = {'nombre': 'chat', 'sistema': 'Eres un mirror del chat principal: trabajas en paralelo con el mismo contexto.',
                'mensajes': [m for m in (p.get('mensajes') or []) if isinstance(m, dict)][-12:], 'archivos': [], 'instrucciones': []}
    else:
        base = _cargar(de, seccion)
        if not base:
            return {'error': 'AGENTE_NO_EXISTE'}
    r = crear({'seccion': seccion, 'nombre': ('Mirror ' + base['nombre'])[:40], 'sistema': base.get('sistema'),
               'modelo': p.get('modelo') or base.get('modelo') or 'ficha-qwen38flash', 'origen': de, 'icono': '🪞'}, p.get('creado_por') or 'director')
    if 'agente' not in r:
        return r
    a = _cargar(r['agente']['id'], seccion)
    a['mensajes'] = [{'role': m.get('role'), 'content': str(m.get('content') or '')} for m in base.get('mensajes') or []]
    a['instrucciones'] = list(base.get('instrucciones') or [])
    if base.get('archivos'):
        sb = _sandbox(base)
        for f in base['archivos']:
            try:
                _subir_archivo(a, f['nombre'], (sb / 'archivos' / f['nombre']).read_bytes())
            except Exception:  # noqa: BLE001
                pass
    _linea(a, 'mirror de %s: %d mensajes, %d archivos' % (de, len(a['mensajes']), len(a['archivos'])))
    return {'agente': _vista(_guardar(a))}


def enviar(p):
    a = _cargar(str(p.get('id') or ''), p.get('seccion'))
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
    a = _cargar(str(p.get('id') or ''), p.get('seccion'))
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
                a['_prog'] = prog; _linea(a, prog[:120]); _guardar(a, False)
            elif time.time() - float(a.get('_tl') or 0) > 6:
                a['_tl'] = time.time(); _linea(a, 'trabajando… %d s' % int(time.time() - a['t0'])); _guardar(a, False)
        else:
            ms = int((time.time() - float(a.pop('t0', time.time()))) * 1000)
            a.pop('pid', None); a.pop('_prog', None)
            txt = _texto(r)
            if r.get('error') or not txt:
                a['estado'] = 'error'; _linea(a, 'error: %s' % (r.get('error') or 'respuesta vacia'))
            else:
                a['mensajes'].append({'role': 'assistant', 'content': txt, 't': time.time(), 'ms': ms})
                a['latencia_ms'] = ms
                t = txt.lstrip()
                a['estado'] = 'aprobacion' if t.startswith('[APROBACION]') else 'bloqueado' if t.startswith('[BLOQUEADO]') else 'terminado'
                _linea(a, '%s · %d s %03d ms: %s' % (a['estado'], ms // 1000, ms % 1000, txt.replace('\n', ' ')[:70]))
            _guardar(a)
    return {'agente': _vista(a, completo=True)}


def ejecutar(p):
    """Ejecuta codigo en el sandbox aislado del agente (ver sandbox.py: HF Jobs > local con limites)."""
    a = _cargar(str(p.get('id') or ''), p.get('seccion'))
    if not a:
        return {'error': 'AGENTE_NO_EXISTE'}
    code = str(p.get('codigo') or '')
    if not code:
        ult = next((m['content'] for m in reversed(a.get('mensajes') or []) if m['role'] == 'assistant'), '')
        mm = re.search(r'```(?:python|py)?\n(.*?)```', ult, re.S)
        code = mm.group(1) if mm else ''
    if not code.strip():
        return {'error': 'SIN_CODIGO'}
    a['estado'] = 'trabajando'; _linea(a, '▶ ejecutando en sandbox (%s)…' % _sbx.proveedor()); _guardar(a, False)
    r = _sbx.ejecutar(code, _sandbox(a), int(p.get('timeout_s') or 30))
    a.setdefault('ejecuciones', []).append({'t': time.time(), 'codigo': code[:4000], **r})
    a['estado'] = 'terminado' if r.get('exit_code') == 0 else 'error'
    _linea(a, '%s exit %s · %d s %03d ms · %s' % (r.get('proveedor'), r.get('exit_code'), r['ms'] // 1000, r['ms'] % 1000, (r.get('stdout') or r.get('stderr') or '').replace('\n', ' ')[:60]))
    a['mensajes'].append({'role': 'assistant', 'content': '▶ Sandbox (%s, %s) exit %s\n%s' % (r.get('proveedor'), r.get('aislamiento'), r.get('exit_code'), ((r.get('stdout') or '') + (r.get('stderr') or ''))[:3000]), 't': time.time(), 'ms': r['ms']})
    _guardar(a)
    return {'agente': _vista(a, completo=True), 'ejecucion': r}


def subir(p):
    a = _cargar(str(p.get('id') or ''), p.get('seccion'))
    if not a:
        return {'error': 'AGENTE_NO_EXISTE'}
    if p.get('instruccion'):
        a['instrucciones'].append(str(p['instruccion'])[:2000]); _linea(a, '+ instrucción: ' + str(p['instruccion'])[:60])
    if p.get('datos_b64'):
        if len(str(p['datos_b64'])) > 4_000_000:
            return {'error': 'ARCHIVO_MUY_GRANDE'}
        raw = base64.b64decode(str(p['datos_b64']))
        n = _subir_archivo(a, p.get('nombre'), raw)
        _linea(a, '+ archivo %s (%d B) → memoria + sandbox' % (n, len(raw)))
    return {'agente': _vista(_guardar(a), completo=True)}


def chat_crear(p):
    pedido = str(p.get('pedido') or '').strip()
    if not pedido:
        return {'error': 'PEDIDO_VACIO'}
    sis = ('Eres la LLM del chat principal con la tool crear_agente. Responde SOLO un JSON: '
           '{"nombre": str corto, "sistema": instrucciones del agente, "modelo": uno de %s}. Elige el modelo segun la tarea '
           '(codigo complejo: ficha-qwen38max o ficha-dsv4pro; rapido: ficha-qwen38flash o ficha-dsv4flash).' % json.dumps(list(_HARNESS)))
    t0 = time.time()
    r = _puente('chat_async', {'model': 'qw-qwen-3-8-flash', 'messages': [{'role': 'system', 'content': sis}, {'role': 'user', 'content': pedido[:4000]}],
                               'sesion': 'orq-chat', 'tools_habilitadas': False, 'max_tokens': 600})
    while r.get('estado') == 'procesando' and time.time() - t0 < 80:
        r = _puente('resultado', {'proceso_id': r['proceso_id'], 'espera': 5})
    txt = _texto(r)
    mm = re.search(r'\{.*\}', txt, re.S)
    try:
        spec = json.loads(mm.group(0)) if mm else {}
    except Exception:  # noqa: BLE001
        spec = {}
    if not spec.get('nombre'):
        return {'error': 'LLM_SIN_JSON', 'detalle': txt[:300] or r.get('error')}
    out = crear({'seccion': p.get('seccion'), 'nombre': spec.get('nombre'), 'sistema': spec.get('sistema'),
                 'modelo': spec.get('modelo') if spec.get('modelo') in _HARNESS else 'ficha-qwen38flash'}, 'llm-chat')
    out['ms'] = int((time.time() - t0) * 1000)
    return out


def configurar(p):
    a = _cargar(str(p.get('id') or ''), p.get('seccion'))
    if not a:
        return {'error': 'AGENTE_NO_EXISTE'}
    if p.get('modelo'):
        if p['modelo'] not in _HARNESS:
            return {'error': 'MODELO_NO_FICHA4', 'validos': list(_HARNESS)}
        a['modelo'] = p['modelo']; a['modelo_nombre'] = next(n for f, _, n in MODELOS if f == p['modelo']); _linea(a, 'modelo → ' + a['modelo_nombre'])
    if p.get('sistema') is not None:
        a['sistema'] = str(p['sistema'])[:4000]; _linea(a, 'system actualizado')
    return {'agente': _vista(_guardar(a))}


def handle(action: str, payload: dict[str, Any]) -> dict[str, Any]:
    p = payload or {}
    if action == 'status':
        try:
            h = _mem().sqlite.health()
        except Exception as x:  # noqa: BLE001
            h = {'status': 'GAP', 'error': type(x).__name__}
        return {'ok': True, 'memoria': h, 'max_por_seccion': MAX_AGENTES, 'sandbox': _sbx.proveedor(), 'deploy': _dep.destinos()}
    if action == 'modelos':
        return {'ficha': 'ficha4-workflow-yaiwes', 'modelos': [{'id': f, 'harness': h, 'nombre': n} for f, h, n in MODELOS], 'estados': list(ESTADOS)}
    if action == 'listar':
        return {'agentes': listar(p.get('seccion')), 'max': MAX_AGENTES, 'seccion': _sec(p.get('seccion'))}
    acciones = {'crear': lambda: crear(p, 'llm-chat' if p.get('creado_por') == 'llm-chat' else 'director'), 'borrar': lambda: borrar(p),
                'mirror': lambda: mirror(p), 'enviar': lambda: enviar(p), 'estado': lambda: estado(p), 'subir': lambda: subir(p),
                'chat_crear': lambda: chat_crear(p), 'configurar': lambda: configurar(p), 'ejecutar': lambda: ejecutar(p)}
    if action in acciones:
        return acciones[action]()
    if action == 'aprobar':
        a = _cargar(str(p.get('id') or ''), p.get('seccion'))
        if not a:
            return {'error': 'AGENTE_NO_EXISTE'}
        a['estado'] = 'activo'; _linea(a, 'aprobado por el Director')
        return {'agente': _vista(_guardar(a))}
    if action == 'archivos':
        a = _cargar(str(p.get('id') or ''), p.get('seccion'))
        return {'archivos': [{'nombre': x['nombre'], 'bytes': x['bytes']} for x in (a or {}).get('archivos') or []]} if a else {'error': 'AGENTE_NO_EXISTE'}
    if action == 'token_guardar':
        return _dep.guardar_token(str(p.get('destino') or ''), str(p.get('token') or ''))
    if action == 'deploy':
        a = _cargar(str(p.get('id') or ''), p.get('seccion'))
        if not a:
            return {'error': 'AGENTE_NO_EXISTE'}
        r = _dep.desplegar(str(p.get('destino') or ''), str(p.get('repo') or ''), _sandbox(a) / 'archivos', str(p.get('rama') or 'main'), bool(p.get('dry_run')), p.get('confirmado') is True)
        _linea(a, 'deploy %s → %s: %s' % (p.get('destino'), p.get('repo'), r.get('estado') or r.get('error'))); _guardar(a)
        return r
    return {'error': 'ACCION_DESCONOCIDA'}
