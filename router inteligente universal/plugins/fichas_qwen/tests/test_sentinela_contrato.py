"""Constitucion sentinela: contrato -> validador determinista -> 1 juez-corrector solo si falla. OFF no corre."""
from plugins.fichas_qwen import sentinela_contrato as s


def test_parsear_y_validar():
    c = s.parsear('Responde en español\nTERMINA CON: SENTINELA7\nPROHIBIDO: lorem\nMAX_LINEAS: 3')
    assert s.verificables(c) == 3 and c['libres'] == ['Responde en español']
    assert s.validar('hola', c) == ['TERMINA CON: SENTINELA7']
    assert s.validar('hola SENTINELA7', c) == []
    assert 'PROHIBIDO: lorem' in s.validar('lorem SENTINELA7', c)


def test_esquema_y_arreglo_determinista():
    c = s.parsear('ESQUEMA: {"type":"object","required":["ok"],"properties":{"ok":{"type":"boolean"}}}')
    assert s.validar('{"ok": "si"}', c) == ['ESQUEMA: $.ok debe ser boolean']
    t, inf = s.salida({'contrato': c, 'contrato_txt': ''}, 'q', 'Aqui va:\n```json\n{"ok": true}\n```', lambda p: 'nunca')
    assert inf['estado'] in ('PASO', 'CORREGIDA')


def test_juez_un_solo_reintento():
    c = s.parsear('DEBE: FIN7')
    llamadas = []
    t, inf = s.salida({'contrato': c, 'contrato_txt': 'DEBE: FIN7'}, 'q', 'hola', lambda p: llamadas.append(p) or 'hola FIN7')
    assert t == 'hola FIN7' and inf['estado'] == 'CORREGIDA' and inf['via'] == 'juez_llm_1_reintento' and len(llamadas) == 1
    t, inf = s.salida({'contrato': c, 'contrato_txt': ''}, 'q', 'hola', lambda p: 'sigue mal')
    assert inf['estado'] == 'NO_CUMPLE'


def test_termina_con_sentinela7_paso_y_arreglo_sin_llm():
    c = s.parsear('TERMINA CON: SENTINELA7')
    t, inf = s.salida({'contrato': c, 'contrato_txt': ''}, 'q', 'hola SENTINELA7', lambda p: 1 / 0)
    assert t == 'hola SENTINELA7' and inf['estado'] == 'PASO'  # el modelo cumplio: no se toca
    llamadas = []
    t, inf = s.salida({'contrato': c, 'contrato_txt': ''}, 'q', 'linea 1\nlinea 2', lambda p: llamadas.append(p) or 'x')
    assert t.endswith('SENTINELA7') and t.startswith('linea 1\nlinea 2') and inf['via'] == 'arreglo_determinista' and not llamadas
    cj = s.parsear('FORMATO: json\nTERMINA CON: Z')  # con JSON no se agrega nada (romperia el JSON)
    assert s.arreglo_determinista('{"a": 1}', cj) == '{"a": 1}'
    assert s.arreglo_determinista('GAP X', c) == 'GAP X'


def test_off_no_valida_y_bug_constitucion_texto():
    assert s.preparar({'message': 'x'})['activo'] is False
    ctx = s.preparar({'sentinela': {'on': True}, 'constitucion': {'texto': 'TERMINA CON: Z9'}})  # el chat manda constitucion.texto
    assert ctx['contrato']['termina'] == 'Z9' and 'TERMINA CON: Z9' in ctx['bloque']
    ctx = s.preparar({'system_prompt': {'nombre': 'a', 'texto': 'Empieza con VALE'}})
    assert ctx['contrato'] is None and 'Empieza con VALE' in ctx['bloque']  # system prompt: viaja, no valida


def test_archivo_real_viaja_y_se_valida():
    ctx = s.preparar({'ancla_real': {'on': True, 'archivos': [{'nombre': 'a.py', 'contenido': 'def f(:\n'}]}})
    a = ctx['archivos'][0]
    assert a['sintaxis_ok'] is False and 'def f(:' in ctx['bloque']
    assert s.ejecutar_sandbox('print(1)', 'python')['ejecutado'] in (True, False)


def test_bloque_contrato_sin_archivos_y_graphify_nombre_seguro(tmp_path, monkeypatch):
    ctx = s.preparar({'sentinela': {'on': True, 'contrato': 'TERMINA CON: SENTINELA7'}, 'system_prompt': 'Rol X',
                      'ancla_real': {'on': True, 'archivos': [{'nombre': 'a.txt', 'contenido': 'DATO-ARCHIVO'}]}})
    assert 'DATO-ARCHIVO' in ctx['bloque'] and 'DATO-ARCHIVO' not in ctx['bloque_contrato']
    assert 'SENTINELA7' in ctx['bloque_contrato'] and 'Rol X' in ctx['bloque_contrato']
    monkeypatch.setenv('RIU_DATA_DIR', str(tmp_path))
    escritos = []

    class GF:
        def __init__(self, source_root, output_dir):
            escritos.extend(p.name for p in source_root.iterdir())

        def build(self):
            return {'status': 'X'}
    r = s.graphify_anclar('ses', [{'nombre': '../../evil.py', '_txt': 'x=1'}, {'nombre': '..', '_txt': 'y=1'}], GF)
    assert r == {'status': 'X'} and sorted(escritos) == ['archivo', 'evil.py']
    assert not (tmp_path / 'evil.py').exists()
