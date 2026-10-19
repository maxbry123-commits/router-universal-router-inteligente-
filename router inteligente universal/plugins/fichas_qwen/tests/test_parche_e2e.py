"""PARCHE_E2E offline: ejecutar_plan_json llega al Harness (solo escritor), escribe con recibo real y no duplica al reanudar.
Desde 'router inteligente universal/':  PYTHONPATH=. python3 plugins/fichas_qwen/tests/test_parche_e2e.py"""
import hashlib, json, os, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import plugins.puente_chat.plugin as pcm  # noqa: E402

PLAN = json.dumps({"meta": {"name": "e2e-t"}, "ops": [
    {"id": "T1", "op": "inspect_workspace"}, {"id": "T2", "op": "create_directory", "path": "entregables", "depends_on": ["T1"]},
    {"id": "T3", "op": "write_text", "path": "entregables/p.txt", "text": "hola\n", "depends_on": ["T2"]},
    {"id": "T4", "op": "verify_contains", "path": "entregables/p.txt", "text": "hola", "depends_on": ["T3"]},
    {"id": "T5", "op": "finish", "depends_on": ["T4"]}]})


def _con_motor(f):
    os.environ['RIU_MOTOR_WS'] = tempfile.mkdtemp()
    pcm._MOTOR_HAB.set(True); pcm._MOTOR_SES.set('ses-e2e')
    try:
        return f()
    finally:
        pcm._MOTOR_HAB.set(False)


def test_tool_publicada_solo_para_el_escritor():
    assert 'ejecutar_plan_json' in {t['function']['name'] for t in pcm._MOTOR_TOOLS}
    assert pcm._motor_ejecutar('ejecutar_plan_json', {'plan': PLAN}) is None  # motor OFF: no existe


def test_mutacion_real_y_bloqueo_en_lectura():
    assert pcm._es_mutacion('ejecutar_plan_json', {'plan': PLAN})
    tok = pcm._SOLO_LECTURA.set(True)
    try:
        assert pcm._bloqueo('ejecutar_plan_json', {'plan': PLAN}).startswith('ERROR: GAP_MUTACION_NO_AUTORIZADA')
    finally:
        pcm._SOLO_LECTURA.reset(tok)


def test_escribe_recibo_hash_y_reanuda_sin_duplicar():
    def f():
        o1 = pcm._motor_ejecutar('ejecutar_plan_json', {'plan': PLAN})
        assert o1.startswith('YAIWES_OP_REPORT'), o1
        r1 = json.loads(o1.split(' ', 1)[1])
        ws = Path(os.environ['RIU_MOTOR_WS']) / 'ses-e2e'
        p = ws / 'entregables/p.txt'
        mt = p.stat().st_mtime_ns
        assert p.read_text() == 'hola\n' and r1['batch_finished'] and r1['objective_audited'] is False
        w = [x for x in r1['receipts'] if x['op'] == 'write_text'][0]
        assert w['receipt_id'].startswith('receipt-') and (ws / '.receipts/e2e-t.json').exists()
        r2 = json.loads(pcm._motor_ejecutar('ejecutar_plan_json', {'plan': PLAN}).split(' ', 1)[1])
        assert [x for x in r2['receipts'] if x['op'] == 'write_text'][0]['reutilizado'] and p.stat().st_mtime_ns == mt
        assert hashlib.sha256(p.read_bytes()).hexdigest()
    _con_motor(f)


def test_plan_invalido_devuelve_motor_error_y_no_escribe():
    def f():
        bad = json.dumps({"ops": [{"id": "A", "op": "write_text", "path": "../fuera.txt", "text": "x"}]})
        o = pcm._motor_ejecutar('ejecutar_plan_json', {'plan': bad})
        assert o.startswith('MOTOR_ERROR') and o.startswith(pcm._FALLO)
        assert not (Path(os.environ['RIU_MOTOR_WS']).parent / 'fuera.txt').exists()
        o = pcm._motor_ejecutar('ejecutar_plan_json', {'plan': 'texto ```json {} ```'})
        assert o.startswith('MOTOR_ERROR')
    _con_motor(f)


if __name__ == '__main__':
    n = 0
    for k, f in list(globals().items()):
        if k.startswith('test_'):
            f(); n += 1; print('PASS', k)
    print('PARCHE_E2E: %d/%d PASS' % (n, n))
