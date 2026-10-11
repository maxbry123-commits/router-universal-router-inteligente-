#!/usr/bin/env python3
"""JOB DE PRUEBAS TOTAL: fichas 0-4 + fichas NV/GROQ, Harness->HTTP->Ficha 4, chat/almacenamiento/memoria, Graphiti, Graphify, Constitucion, frontend.
Uso:  FICHA_CLAVE_BANCO=<clave> python job_cierre_total.py        (la clave NUNCA se imprime)
Opcional: RIU_FICHA4_URL=<url real de /plugins/fichas_qwen/call/llm> y RIU_ROUTER_API_KEY para probar contra el Router real; sin eso usa un servidor HTTP local que sirve fichas_qwen.handle('llm').
Salida: tabla PASS/FAIL/GAP por prueba + JSON final en job_cierre_total.json. Codigo de salida 0 solo si todo PASS."""
import sys, os, json, base64, hashlib, shutil, subprocess, tempfile, threading, http.server, importlib.util, time
from pathlib import Path
RT = Path(__file__).resolve().parents[1]; R = RT.parent
DATA = tempfile.mkdtemp(prefix='job_cierre_')
REAL = bool(os.environ.get('RIU_FICHA4_URL'))
os.environ.update(RIU_DATA_DIR=DATA, RIU_GRAPHITI_ENABLE='1')
if not REAL:
    os.environ.update(RIU_FICHA4_URL='http://127.0.0.1:18765/plugins/fichas_qwen/call/llm', RIU_ROUTER_API_KEY=os.environ.get('RIU_ROUTER_API_KEY', 'test'))
sys.path.insert(0, str(RT))
RES = []
def reg(nombre, ok, detalle=''):
    RES.append({'test': nombre, 'estado': 'PASS' if ok is True else ('GAP' if ok is None else 'FAIL'), 'detalle': str(detalle)[:300]}); print(('PASS' if ok is True else 'GAP ' if ok is None else 'FAIL'), nombre, str(detalle)[:160], flush=True)
def load(name, path, sub=None):
    sp = importlib.util.spec_from_file_location(name, str(path), submodule_search_locations=sub); m = importlib.util.module_from_spec(sp); sys.modules[name] = m; sp.loader.exec_module(m); return m
def seguro(nombre, fn):
    try: fn()
    except Exception as e: reg(nombre, False, 'EXC ' + type(e).__name__ + ': ' + str(e)[:200])

# ---------- A. FICHAS ----------
FQ_DIR = RT / 'plugins' / 'fichas_qwen'; PCF = RT / 'plugins' / 'puente_chat' / 'fichas'
def t_fichas():
    for n in ('ficha1-modelos', 'ficha2-dag-codigo', 'ficha3-frontend', 'ficha4-workflow-yaiwes'):
        d = json.loads((FQ_DIR / 'fichas' / (n + '.json')).read_text(encoding='utf-8')); reg('FICHA_JSON_' + n, bool(d.get('ficha') and d.get('modelos') and d.get('dsl')), 'ficha=' + str(d.get('ficha')))
    f4 = json.loads((FQ_DIR / 'fichas' / 'ficha4-workflow-yaiwes.json').read_text(encoding='utf-8')); f1 = json.loads((FQ_DIR / 'fichas' / 'ficha1-modelos.json').read_text(encoding='utf-8'))
    reg('FICHA4_COPIA_FIEL_DE_FICHA1', {k: v for k, v in f4.items() if k not in ('ficha', 'proposito')} == {k: v for k, v in f1.items() if k not in ('ficha', 'proposito')}, 'solo difieren ficha/proposito')
    f0 = json.loads((PCF / 'ficha-0-servicios.json').read_text(encoding='utf-8'))
    reg('FICHA0_10_PUERTOS_LIBRES', len(f0.get('puertos', [])) >= 10 and f0.get('almacenamiento') == '/chat/storage' and bool(f0.get('computo_endpoint')), 'puertos=%s' % len(f0.get('puertos', [])))
    for n in ('groq-qwen-3-8', 'nv-kimi-k3', 'nv-glm-5-3', 'nv-muse-glimmer', 'nv-nemotron-lightning', 'nv-nemotron-super'):
        p = PCF / ('modelo-' + n + '.json'); d = json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
        reg('FICHA_MODELO_' + n, bool(d.get('id') == n and d.get('proveedor') in ('groq', 'nvidia')), 'proveedor=%s' % d.get('proveedor'))
seguro('FICHAS', t_fichas)

# ---------- B. FICHA 4 + HARNESS HTTP ----------
fq = pc = None; LLM_LOG = []
def t_carga():
    global fq, pc
    fq = load('fq_job', FQ_DIR / 'plugin.py'); pc = load('pc_job', RT / 'plugins' / 'puente_chat' / 'plugin.py')
    reg('PLUGINS_CARGAN', True)
    st = fq.handle('status', {}); reg('FICHAS_QWEN_STATUS', isinstance(st, dict) and 'error' not in st, str(st)[:120])
    reg('ALIAS_4', fq.ALIAS.get('4') == 'ficha4-workflow-yaiwes', str(fq.ALIAS.get('4')))
seguro('CARGA', t_carga)
class Hd(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        b = json.loads(self.rfile.read(int(self.headers.get('Content-Length', '0'))) or b'{}'); r = fq.handle('llm', b)
        LLM_LOG.append((b.get('caller_id'), b.get('task_type'), r.get('modelo'), bool(r.get('reply')), r.get('error')))
        o = json.dumps({'status': 'ok', 'result': r}).encode(); self.send_response(200); self.send_header('Content-Type', 'application/json'); self.send_header('Content-Length', str(len(o))); self.end_headers(); self.wfile.write(o)
if not REAL and fq:
    threading.Thread(target=http.server.ThreadingHTTPServer(('127.0.0.1', 18765), Hd).serve_forever, daemon=True).start()
CLAVE = bool(os.environ.get('FICHA_CLAVE_BANCO') or os.environ.get('RIU_VAULT_PASSPHRASE'))
def t_llm():
    if not CLAVE: reg('LLM_FICHA4_QWEN38FLASH', None, 'GAP: falta FICHA_CLAVE_BANCO'); return
    r = pc.llm_call({'caller_id': 'job', 'plugin_id': 'job', 'workflow_id': 'job', 'project_id': 'p', 'task_id': 't', 'task_type': 'small', 'messages': [{'role': 'user', 'content': 'Responde solo: LISTO'}]})
    reg('LLM_HARNESS_HTTP_FICHA4_FLASH', bool(r.get('reply')) and r.get('modelo') == 'ficha-qwen38flash', 'modelo=%s err=%s' % (r.get('modelo'), r.get('error')))
    r2 = pc.llm_call({'caller_id': 'job', 'task_type': 'code', 'messages': [{'role': 'user', 'content': 'Responde solo: OK'}]})
    reg('LLM_FICHA4_ENRUTA_CODE_A_MAX', r2.get('modelo') == 'ficha-qwen38max', 'modelo=%s err=%s' % (r2.get('modelo'), r2.get('error')))
seguro('LLM', t_llm)

# ---------- C. MEMORIA / ALMACENAMIENTO / ANCLAJE ----------
def t_memoria():
    mf = load('memoria_yaiwes', R / 'chat router' / '04-MEMORIA' / 'memoria_yaiwes' / '__init__.py', [str(R / 'chat router' / '04-MEMORIA' / 'memoria_yaiwes')])
    from integration.chat_mvp.store import Store
    f = mf.MemoryFacade(Store(DATA)); pc._memoria = lambda: (f, pc._scope_for); pc._GRAPHITI_CABLEADO.clear(); g = f.components['graphiti']
    reg('MEMORIA_SQLITE_ES_LA_VERDAD', f.sqlite is not None)
    pc._cablear_graphiti('', '', {'project_id': 's1', 'task_id': 't1', 'workflow_id': 'memory-anchor', 'plugin_id': 'graphiti'})
    CUERPO = 'Plan Harness YAIWES ZQX_ARCHIVO: el Harness usa puente_chat y Graphiti es indice derivado.'
    pc.handle('subir', {'nombre': 'archivo.txt', 'sesion': 's1', 'tipo': 'text/plain', 'datos_b64': base64.b64encode(CUERPO.encode()).decode()})
    hits = g.search(pc._scope_for(pc.DUENO, 'chat:s1'), 'ZQX_ARCHIVO Harness', 5) + g.search(pc._scope_for(pc.DUENO, 'anchors:s1'), 'ZQX_ARCHIVO', 5)
    reg('T1_SUBIR_SIN_ANCLAR_SOLO_SQLITE', bool(pc._archivo_memoria('s1', 'archivo.txt')) and not hits, 'graphiti_hits=%d' % len(hits))
    if not CLAVE: reg('T2_ANCLAR_GRAPHITI', None, 'GAP: falta FICHA_CLAVE_BANCO'); reg('T2B_REINICIO', None, 'GAP: falta clave')
    else:
        pc._SNAP_ANC.clear(); ra = pc.resolver_anclados('s1', ['archivo:archivo.txt'], 't1', 'Harness'); sc = pc._scope_for(pc.DUENO, 'anchors:s1')
        h = g.search(sc, 'Harness puente_chat', 5); p = [x['provenance'] for x in h]; sha = ra['snapshot'][0]['sha256']
        reg('T2_ANCLAR_GRAPHITI_FUENTE_SHA_SNAPSHOT', bool(h) and any(x.get('source_id') == 'archivo.txt' and x.get('source_sha256') == sha and x.get('source_snapshot_id') for x in p), 'hits=%d gap=%s' % (len(h), ra.get('gap')))
        g.close(); f2 = mf.MemoryFacade(Store(DATA)); pc._memoria = lambda: (f2, pc._scope_for); g2 = f2.components['graphiti']
        h2 = g2.search(sc, 'Harness puente_chat', 5); reg('T2B_GRAPHITI_SOBREVIVE_REINICIO', bool(h2) and any(x['provenance'].get('source_sha256') == sha for x in h2)); g = g2; f = f2
        pc._SNAP_ANC.clear(); r2 = pc.resolver_anclados('s1', ['archivo:archivo.txt'], 't1', 'otra'); reg('ANCLAS_REHIDRATAN', bool(r2.get('rehidratado')) and r2['snapshot'][0]['sha256'] == sha)
    CT = 'CONST_ZQX_SUPREMA regla constitucional del Director'
    pc.handle('subir', {'nombre': 'miconst.md', 'sesion': 's1', 'tipo': 'text/markdown', 'datos_b64': base64.b64encode(CT.encode()).decode()})
    base, _ = pc._gov_base(); pl = {'gobernanza': {'enabled': True}, 'constitucion': {'texto': 'texto del Director', 'anclados': ['miconst.md']}, 'sesion': 's1'}
    gi, ge = pc._gov_pre_chat(pl, 's1', 'hola', ['constitucion:miconst.md'])
    reg('T3_CONSTITUCION_ESTRUCTURADA_Y_OFICIAL_DEL_HARNESS', ge is None and (gi or {}).get('sheriff') == 'PASS' and (gi or {}).get('id') == base.get('id'), str(ge)[:120])
    found = subprocess.run(['grep', '-rlE', base64.b64encode(CT.encode()).decode()[:40] + '|CONST_ZQX_SUPREMA', DATA], capture_output=True, text=True).stdout.split()
    bad = [x for x in found if not x.endswith(('.sqlite', '.sqlite3', '.db', '-wal', '-shm')) or 'graphiti' in x or 'graphify' in x]
    gh = [x for x in g.search(pc._scope_for(pc.DUENO, 'anchors:s1'), 'CONST_ZQX_SUPREMA', 5) if 'CONST_ZQX' in x['text']]
    reg('T4_CONSTITUCION_NO_EN_GRAPHITI_NI_GRAPHIFY', not bad and not gh, 'fuera=%s hits=%d' % ([os.path.basename(x) for x in bad], len(gh)))
    calls = []; pc._paso_llm = lambda *a, **k: (calls.append(a) or 'DIRECTO'); os.environ['RIU_FICHA4_URL'] = 'http://127.0.0.1:1/x'; os.environ.pop('RIU_ROUTER_URL', None)
    rs = g.save(pc._scope_for(pc.DUENO, 'anchors:s6'), 'k6', {'text': 'prueba GAP', 'source_id': 'x'})
    reg('T6_FICHA4_CAIDA_GAP_FICHA4_HTTP_SIN_BYPASS', rs.get('reason') == 'GAP_FICHA4_HTTP' and not calls, str(rs)[:140])
    g.close()
seguro('MEMORIA', t_memoria) if pc else reg('MEMORIA', False, 'plugins no cargaron')

# ---------- D. GRAPHIFY ----------
def t_graphify():
    shutil.rmtree(DATA + '/indices/graphify', ignore_errors=True); os.environ['RIU_GRAPHIFY_SOURCE_ROOT'] = str(RT / 'plugins' / 'puente_chat')
    mf = sys.modules['memoria_yaiwes']; from integration.chat_mvp.store import Store
    f = mf.MemoryFacade(Store(DATA)); gf = f.components['graphify']; h = gf.search('code', 'resolver_anclados', 5)
    reg('T5_GRAPHIFY_NODOS_EN_LA_RAIZ', bool(h), 'nodos=%d' % len(h))
    for x in Path(DATA).rglob('graph.json'): x.unlink()
    reg('GRAPHIFY_REBUILD_SI_FALTA_GRAPH', bool(gf.search('code', '_derivados', 5)))
seguro('GRAPHIFY', t_graphify) if pc else None

# ---------- E. FRONTEND ----------
def t_front():
    FD = R / 'chat router' / 'chat frontend'; nodo = shutil.which('node')
    if not nodo: reg('FRONTEND_SINTAXIS', None, 'GAP: node no disponible'); return
    tmp = Path(tempfile.mkdtemp()); malos = []
    for js in sorted(FD.glob('*.js')):
        (tmp / (js.stem + '.mjs')).write_text(js.read_text(encoding='utf-8'), encoding='utf-8')
        if subprocess.run([nodo, '--check', str(tmp / (js.stem + '.mjs'))], capture_output=True).returncode: malos.append(js.name)
    reg('FRONTEND_TODOS_LOS_JS_COMPILAN', not malos, 'malos=%s' % malos)
    ctx = (FD / 'contexto.js').read_text(encoding='utf-8'); cc = (FD / 'chat-contexto.js').read_text(encoding='utf-8'); api = (FD / 'api.js').read_text(encoding='utf-8')
    reg('FRONTEND_ENVIA_GOBERNANZA_Y_CONSTITUCION_ESTRUCTURADAS', 'datosGobernanza' in ctx and 'datosGobernanza' in cc and 'gobernanza' in api and 'constitucion' in api)
    reg('FRONTEND_CONSTITUCION_NO_VA_COMO_TEXTO_DEL_MENSAJE', 'CONSTITUCIÓN SENTINELA' not in ctx)
    reg('FRONTEND_ARCHIVOS_CONSTITUCION_COMO_constitucion:', '"constitucion:"' in ctx)
seguro('FRONTEND', t_front)

n = {k: sum(1 for r in RES if r['estado'] == k) for k in ('PASS', 'FAIL', 'GAP')}
print('\nRESUMEN', n, flush=True); Path(__file__).with_suffix('.json').write_text(json.dumps({'resumen': n, 'tests': RES}, ensure_ascii=False, indent=1), encoding='utf-8')
sys.exit(0 if not n['FAIL'] and not n['GAP'] else 1)
