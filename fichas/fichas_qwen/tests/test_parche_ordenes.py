"""ORDENES 01/07 offline: tool_stream solo en glm52 con tools; recibo MOTOR:<Tn>; una tarea CODE solo cierra con mutacion real.
Desde la raiz del repo:  PYTHONPATH=. python3 fichas/fichas_qwen/tests/test_parche_ordenes.py"""
import json, re, sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / 'fichas' / 'fichas_qwen' / 'modos'))
import plugins.puente_chat.plugin as pcm  # noqa: E402
import motor_objetivo as mo  # noqa: E402


def test_orden01_tool_stream_solo_glm52_con_tools():
    pol = json.loads((RAIZ / 'fichas/fichas_qwen/fichas/politicas_modelo.json').read_text(encoding='utf-8'))['politicas_modelo']
    con = {k for k, v in pol.items() if isinstance(v, dict) and (v.get('con_tools') or {}).get('tool_stream')}
    assert con == {'ficha-glm52'}, con
    p = pol['ficha-glm52']
    assert pcm._extras(p, [{'type': 'function'}]).get('tool_stream') is True
    assert 'tool_stream' not in pcm._extras(p, [])


def test_orden07_regex_de_tarea_coincide_con_el_prompt_real():
    obj = {'objetivo': 'X'}; t = {'id': 'T7', 'texto': 'haz algo'}
    prompt = mo._prompt_vuelta(obj, t, '', None)
    src = (RAIZ / 'fichas/fichas_qwen/plugin.py').read_text(encoding='utf-8')
    assert "TAREA ACTUAL\\s*\\((T\\d+)\\)" in src
    assert re.search(r'TAREA ACTUAL\s*\((T\d+)\)', prompt).group(1) == 'T7'


def test_orden07_code_exige_mutacion_real():
    src = (RAIZ / 'fichas/fichas_qwen/modos/motor_objetivo.py').read_text(encoding='utf-8')
    assert "int(r.get('mutaciones_ok') or 0) > 0 if modo_actual == 'code'" in src
    assert 'informe formateado' not in src


def test_orden07_comportamiento_lectura_no_cierra_y_mutacion_si():
    def mk(mut):
        def llamar(modo, prompt):
            if modo == 'auditor':
                return {'texto': '{"cumplido": true, "evidencia": "x"}', 'herramientas_ok': 1, 'mutaciones_ok': 1}
            return {'texto': '{"tarea":"T1","estado":"hecho","resultado":"ok","evidencia":"e","nuevas_tareas":[]}', 'herramientas_ok': 1, 'mutaciones_ok': mut}
        return llamar
    lim = {'objetivo': 'p', 'tareas': ['t1'], 'proceso_id': 'o7', 'limites': {'max_vueltas': 3, 'pausa_entre_vueltas_s': 0}}
    r0 = mo.correr_objetivo(dict(lim), mk(0), lambda s: None, lambda t: None)
    assert r0['estado'] != 'CUMPLIDO', r0
    r1 = mo.correr_objetivo(dict(lim, proceso_id='o7b'), mk(1), lambda s: None, lambda t: None)
    assert r1['estado'] == 'CUMPLIDO', r1
    r2 = mo.correr_objetivo(dict(lim, proceso_id='o7c'), lambda m, p: {'texto': 'informe narrativo sin JSON', 'herramientas_ok': 3, 'mutaciones_ok': 3}, lambda s: None, lambda t: None)
    assert r2['estado'] != 'CUMPLIDO', r2


if __name__ == '__main__':
    n = 0
    for k, f in list(globals().items()):
        if k.startswith('test_'):
            f(); n += 1; print('PASS', k)
    print('ORDENES: %d/%d PASS' % (n, n))
