"""Simulacion consil-latencia (sin red): Harness simulado a 0 s; cuenta llamadas al modelo por ruta (FAST_QA vs HEAVY) con 1 ancla."""
import importlib.util, json, os, sys, time
base = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, os.path.abspath(os.path.join(base, '..', '..')))
def mod(path, name):
    sp = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
    for k in ('_prog', '_meta', '_ck_guardar'): setattr(m, k, lambda *a, **k_: None)
    m._tarea_visor = lambda *a: ''; m._ck_cargar = lambda *a: None
    m._anexo = lambda *a, **k: ''; m._anexo_salida = lambda f, s, o: s
    m._gov_prepare = lambda *a, **k: {}
    return m
def run(m, fid, msg):
    f = json.load(open(os.path.join(base, 'fichas', fid + '.json'), encoding='utf-8'))
    ll = []
    def lh(modelo, prompt, ficha, n, o):
        ll.append(n.get('id')); return 'ok\nVEREDICTO: PASS\nPASS'
    m._llamar_harness = lh
    o = {'aprobado': False, 'muta': False, 'sesion': 'sim', 'cap_in': 'none', 'fast_reply': False, 'task_type': '', 'historial': '', 'tarea_id': 'T', 'caller_id': '', 'anclados': ['archivo:informe.md'], 'fid': fid}
    t = time.perf_counter()
    try: m._correr(f, msg, '', '', o); err = ''
    except Exception as x: err = type(x).__name__ + ':' + str(x)[:80]
    dt = time.perf_counter() - t
    return ('FAST_QA' if o.get('fast_lane') else 'HEAVY'), ll, dt, err
fmt = lambda s: '%d s %03d ms' % (int(s), int(round((s - int(s)) * 1000)))
# Uso: python3 sim_consil_latencia.py [plugin_antes.py]  (p. ej. git show origin/main:.../plugin.py > /tmp/plugin_main.py)
PARES = ([('ANTES', sys.argv[1])] if len(sys.argv) > 1 else []) + [('RAMA', os.path.join(base, 'plugin.py'))]
for tag, path in PARES:
    for fid in ('ficha2-dag-codigo', 'ficha3-frontend'):
        for msg in ('Di solo: hola', 'resume el documento anclado'):
            m = mod(path, 'sim_' + tag.split()[0])
            ruta, ll, dt, err = run(m, fid, msg)
            print(tag, fid, repr(msg), ruta, 'llamadas_modelo=%d' % len(ll), ll, fmt(dt), err)
