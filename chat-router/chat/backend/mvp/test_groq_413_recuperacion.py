"""Regresion 413 real: catalogo compacto sin alterar mensajes ni contratos."""
import ast
import copy
from pathlib import Path
import re
from unittest.mock import patch
import pytest
from mvp import externos as e


def test_codigo_interno_prevalece_sobre_proxy():
    tree = ast.parse(Path(__file__).with_name('app.py').read_text())
    funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ('_codigo', '_pasajero', '_contexto_grande')]
    scope = {'re': re, '_TEXTO_PASAJERO': re.compile('timeout')}
    exec(compile(ast.Module(body=funcs, type_ignores=[]), 'app.py', 'exec'), scope)
    for code in (400, 401, 403, 404, 410, 413, 422):
        msg = f'Router HTTP 502: PROVEEDOR_GROQ_HTTP_{code}: peticion_invalida'
        assert scope['_codigo'](msg) == code
        assert not scope['_pasajero'](msg)
    assert scope['_pasajero']('Router HTTP 502: PROVEEDOR_GROQ_HTTP_429')


def test_413_compacta_solo_catalogo_y_reintenta_una_vez():
    msgs = [{'role': 'system', 'content': 'regla'}, {'role': 'user', 'content': 'objetivo'}]
    schema = {'type': 'object', 'description': 'doc' * 3000, 'required': ['description'],
              'properties': {'description': {'type': 'string', 'enum': ['description'], 'description': 'doc'},
                             'title': {'type': 'string', 'const': 'title'}}, 'additionalProperties': False}
    tools = [{'type': 'function', 'function': {'name': 'github_leer', 'description': 'doc' * 1000, 'parameters': schema}}]
    original = copy.deepcopy(tools)
    seen = []
    def solicitar(url, payload, clave, timeout):
        seen.append(copy.deepcopy(payload))
        if len(seen) == 1:
            raise e.ErrorHTTP(413)
        return {'choices': [{'message': {'content': 'OK'}, 'finish_reason': 'stop'}], 'usage': {'completion_tokens': 1}}
    with patch.object(e, 'claves', return_value=['ficticia']), patch.object(e, '_solicitar', side_effect=solicitar):
        result = e.llamar(msgs, 'groq/qwen/qwen3.8-27b', opciones={'tools': tools})
    assert result['texto'] == 'OK'
    assert result['metricas']['catalogo_compactado'] is True
    assert len(seen) == 2 and all(p['messages'] == msgs for p in seen)
    assert tools == original
    compact = seen[1]['tools'][0]['function']['parameters']
    assert compact['required'] == ['description']
    assert compact['properties']['description']['enum'] == ['description']
    assert compact['properties']['title']['const'] == 'title'
    assert compact['additionalProperties'] is False


def test_413_persistente_no_bucle_ni_cambio_modelo():
    tools = [{'type': 'function', 'function': {'name': 'leer', 'description': 'x' * 500, 'parameters': {'type': 'object'}}}]
    with patch.object(e, 'claves', return_value=['ficticia']), patch.object(e, '_solicitar', side_effect=e.ErrorHTTP(413)) as call:
        with pytest.raises(e.ErrorProveedor) as error:
            e.llamar([{'role': 'user', 'content': 'hola'}], 'groq/qwen/qwen3.8-27b', opciones={'tools': tools})
    assert error.value.codigo == 413 and call.call_count == 2


def test_formato_system_conserva_instrucciones_codigo_y_usuario():
    system = 'Regla A\n\nRegla B\n\n```python\nx = """\n\ntexto\n"""\n```\n\nFin\n'
    user = {'role': 'user', 'content': 'exacto\n\n  espacios'}
    msgs = [{'role': 'system', 'content': system}, user]
    out = e._sistemas_sin_blancos(msgs)
    assert out[0]['content'] == 'Regla A\nRegla B\n```python\nx = """\n\ntexto\n"""\n```\nFin\n'
    assert out[1] is user and msgs[0]['content'] == system
    decorado = [{'role':'system', 'content':'================ REGLAS ================\n' + '=' * 112 + '\nNo borrar.\n'}]
    assert e._sistemas_sin_blancos(decorado)[0]['content'] == 'REGLAS\nNo borrar.\n'


def test_limite_numerico_no_expone_cuerpo_error():
    error = e.ErrorHTTP(413, cuerpo='secret org-interno Limit 7000, Requested 7019')
    assert (error.limite_tokens, error.pedidos_tokens) == (7000, 7019)
    assert str(error) == 'HTTP 413'


def test_413_sin_tools_recupera_formato_y_conserva_user_verbatim():
    msgs = [{'role': 'system', 'content': 'regla\n\n' * 100}, {'role': 'user', 'content': 'texto\n\n literal'}]
    vistos = []
    def solicitar(url, payload, clave, timeout):
        vistos.append(copy.deepcopy(payload))
        if len(vistos) == 1:
            raise e.ErrorHTTP(413, cuerpo='Limit 7000, Requested 7019')
        return {'choices': [{'message': {'content': 'OK'}, 'finish_reason': 'stop'}], 'usage': {}}
    with patch.object(e, 'claves', return_value=['ficticia']), patch.object(e, '_solicitar', side_effect=solicitar):
        result = e.llamar(msgs, 'groq/qwen/qwen3.8-27b')
    assert result['texto'] == 'OK' and len(vistos) == 2
    assert result['metricas']['formato_system_compactado'] is True
    assert vistos[1]['messages'][1] == msgs[1]
    assert len(vistos[1]['messages'][0]['content']) < len(msgs[0]['content'])
