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
    c = s.parsear('TERMINA CON: FIN7')
    llamadas = []
    t, inf = s.salida({'contrato': c, 'contrato_txt': 'TERMINA CON: FIN7'}, 'q', 'hola', lambda p: llamadas.append(p) or 'hola FIN7')
    assert t == 'hola FIN7' and inf['estado'] == 'CORREGIDA' and len(llamadas) == 1
    t, inf = s.salida({'contrato': c, 'contrato_txt': ''}, 'q', 'hola', lambda p: 'sigue mal')
    assert inf['estado'] == 'NO_CUMPLE'


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


def test_termina_con_en_lenguaje_natural():
    for t in ('termina con SENTINELA7', 'Termina con SENTINELA7.', 'La respuesta termina siempre con «SENTINELA7»', 'termina con: SENTINELA7'):
        assert s.parsear(t)['termina'] == 'SENTINELA7', t
    assert s.parsear('empieza con VALE')['empieza'] == 'VALE'
    c = s.parsear('Termina con una pregunta')  # varias palabras: regla libre (viaja al modelo, no se valida literal)
    assert c['termina'] == '' and c['libres'] == ['Termina con una pregunta']
    c = s.parsear('termina con SENTINELA7')
    assert s.validar('ok SENTINELA7', c) == [] and s.validar('ok', c) == ['TERMINA CON: SENTINELA7']
