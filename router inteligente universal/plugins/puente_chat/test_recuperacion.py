"""Contrato local de recuperación: no invoca ningún proveedor externo."""
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


ROOT = Path(__file__).parent


def cargar(ruta, nombre):
    spec = importlib.util.spec_from_file_location(nombre, str(ruta))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


plugin = cargar(ROOT / 'plugin.py', 'puente_chat_prueba')
llamadas = cargar(ROOT / 'fichas/motores_llamado.py', 'llamadas_prueba')
estado = cargar(ROOT / 'fichas/motores_estado.py', 'estado_prueba')
sentinela = cargar(ROOT / 'fichas/sentinela.py', 'sentinela_prueba')


class MemoriaFalsa:
    def __init__(self):
        self.filas = []

    def save(self, scope, clave, dato):
        self.filas.append({'data': dato})

    def search(self, scope, clave, limite):
        return self.filas[-limite:]


class Recuperacion(unittest.TestCase):
    def setUp(self):
        plugin._DEADLINE.set(None)
        plugin._TASK_DEADLINE.set(None)
        plugin._BUENA.clear()

    def test_las_doce_fichas_comparten_politica(self):
        fichas = [json.loads(f.read_text()) for f in (ROOT / 'fichas').glob('modelo-*.json')]
        self.assertEqual(len(fichas), 12)
        self.assertEqual({f['timeout_s'] for f in fichas}, {90})
        self.assertEqual({f['recuperacion'] for f in fichas}, {'riu.ficha.3x3.v1'})
        self.assertTrue(all(f['tiempos_s'] == {'llamada': 90, 'paso': 270, 'tarea': 900} for f in fichas))
        self.assertTrue(all(len(f['motores_llamado']) == len(f['motores_estado']) == 3 for f in fichas))
        self.assertFalse(any('deepseek' in f['id'].lower() for f in fichas))
        self.assertEqual(len(plugin.FICHAS) + len(plugin.RESPALDO), len(fichas))

    def test_tres_llamadas_y_reserva_otro_proveedor(self):
        self.assertEqual(llamadas.rotar_claves(2, 1), [1, 0, 1])
        self.assertEqual(llamadas.rotar_claves(1), [0, 0, 0])
        candidatos = llamadas.reserva_proveedor(plugin.FICHAS, 'nv-glm-5-3')
        self.assertEqual(len(candidatos), 2)
        self.assertEqual(plugin.FICHAS[candidatos[0]][1], 'groq')
        self.assertTrue(all(plugin.FICHAS[c][1] in ('groq', 'nvidia') for c in candidatos))

    def test_fallo_detectable_salta_sin_esperar(self):
        proveedor = types.ModuleType('integration.chat_mvp.providers')
        proveedor.env_keys = lambda nombre: ['clave-1', 'clave-2']
        proveedor.base_url = lambda nombre: 'https://proveedor.invalid'
        integ = types.ModuleType('integration')
        chat = types.ModuleType('integration.chat_mvp')
        chat.providers = proveedor
        respuestas = iter([(503, {'error': 'ocupado'}), (200, {'choices': [{'message': {'content': 'fin'}}]})])
        visitas = []

        def http(metodo, url, clave, cuerpo, timeout):
            visitas.append((clave, timeout))
            return next(respuestas)

        with patch.dict(sys.modules, {'integration': integ, 'integration.chat_mvp': chat,
                                      'integration.chat_mvp.providers': proveedor}), patch.object(plugin, '_http', side_effect=http):
            status, data = plugin._llamar_api('nvidia', 'm', [{'role': 'user', 'content': 'x'}], 100, 90, None)
        self.assertEqual(status, 200)
        self.assertEqual([v[0] for v in visitas], ['clave-1', 'clave-2'])
        self.assertTrue(all(0 < t <= 90 for _, t in visitas))

    def test_watchdog_corta_a_los_noventa_segundos(self):
        tiempos = []

        def colgado(req, timeout):
            tiempos.append(timeout)
            raise TimeoutError('sin respuesta')

        with patch.object(plugin.urllib.request, 'urlopen', side_effect=colgado):
            status, d = plugin._http('POST', 'https://proveedor.invalid', 'clave-falsa', {}, 400)
        self.assertEqual(status, 0)
        self.assertEqual(d['error'], 'PROVEEDOR_TIMEOUT_O_RED')
        self.assertEqual(tiempos, [90])

    def test_tres_motores_de_estado_recuperan_y_reconstruyen(self):
        memoria, cache = MemoriaFalsa(), {}
        mensajes = [
            {'role': 'assistant', 'tool_calls': [{'id': '1', 'function': {
                'name': 'consultar', 'arguments': '{"a": 1}'}}]},
            {'role': 'tool', 'tool_call_id': '1', 'content': 'resultado'},
        ]
        estado.checkpoint_local(cache, 'chat-a', mensajes)
        estado.checkpoint_persistente(memoria, 'chat-a', 'chat-a', mensajes)
        mensajes[1]['content'] = 'cambiado'
        self.assertEqual(estado.checkpoint_local(cache, 'chat-a')[1]['content'], 'resultado')
        self.assertEqual(estado.checkpoint_persistente(memoria, 'chat-a', 'chat-a')[1]['content'], 'resultado')
        self.assertEqual(estado.reconstruir_herramientas(cache['chat-a'])[('consultar', '{"a": 1}')], 'resultado')
        self.assertIsNone(estado.checkpoint_local(cache, 'chat-b'))
        self.assertIn('ultimo checkpoint', llamadas.continuar_desde_checkpoint(mensajes, cache['chat-a'])[-1]['content'])

    def test_reinicio_usa_checkpoint_y_se_detiene_en_exito(self):
        registro = []
        mensajes = [{'role': 'user', 'content': 'inicio'}]
        checkpoint = []

        def guardar(ms):
            checkpoint[:] = [dict(m) for m in ms]

        def paso(ms):
            registro.append([dict(m) for m in ms])
            if len(registro) == 1:
                ms.append({'role': 'assistant', 'content': 'parcial'})
                return {'error': 'PROVEEDOR_TIMEOUT_O_RED'}, []
            return {'choices': [{'finish_reason': 'stop', 'message': {'content': 'terminado'}}]}, []

        resultado = sentinela.ejecutar([('modelo', paso)], mensajes, guardar, lambda: checkpoint)
        self.assertTrue(resultado['completada'])
        self.assertEqual(len(registro), 2)
        self.assertEqual(registro[1][0]['content'], 'inicio')
        self.assertFalse(any(m.get('content') == 'parcial' for m in registro[1]))

    def test_tres_reinicios_agotan_sin_fingir_final(self):
        resultado = sentinela.ejecutar(
            [('modelo', lambda ms: ({'choices': [{'finish_reason': 'length', 'message': {'content': 'parcial'}}]}, []))],
            [{'role': 'user', 'content': 'x'}], max_vueltas=100)
        self.assertFalse(resultado['completada'])
        self.assertEqual(resultado['resultado'][0]['error'], 'RECOVERY_EXHAUSTED')
        self.assertEqual(sum(i['item'] == 'modelo' for i in resultado['items']), 3)

    def test_herramienta_confirmada_no_se_ejecuta_dos_veces(self):
        ejecuciones = []
        herramienta = types.SimpleNamespace(
            TOOLS=[], ejecutar=lambda nombre, args: ejecuciones.append((nombre, args)) or 'guardado')
        mensajes = [{'role': 'user', 'content': 'trabaja'}]

        def ciclo(ident):
            salidas = iter([
                (200, {'choices': [{'message': {'role': 'assistant', 'content': '',
                    'tool_calls': [{'id': ident, 'function': {'name': 'escribir', 'arguments': '{"x":1}'}}]}}]}),
                (200, {'choices': [{'finish_reason': 'stop', 'message': {'content': 'terminado'}}]}),
            ])
            return lambda ms, tl: next(salidas)

        with patch.object(plugin, '_herr', return_value=herramienta):
            plugin._bucle(ciclo('a'), mensajes)
            plugin._bucle(ciclo('b'), mensajes)
        self.assertEqual(ejecuciones, [('escribir', {'x': 1})])

    def test_pipeline_xray_no_declara_exito_si_falla(self):
        with patch.object(plugin, '_xray', return_value={'error': 'SIN_ARCHIVO'}), patch.object(
                plugin, '_guardar', side_effect=AssertionError('No debe guardar resultado ficticio')):
            r = plugin._especial('xray', 'motor-xray', 'sesion', 'texto')
        self.assertEqual(r['error'], 'SIN_ARCHIVO')

    def test_pipeline_llama_reserva_de_otro_proveedor(self):
        visitas = []

        def simular(prov, modelo, ms, mt, tope, tools):
            visitas.append(prov)
            return ((0, {'error': 'red'}) if len(visitas) == 1 else
                    (200, {'choices': [{'message': {'content': 'recuperado'}}]}))

        with patch.object(plugin, '_llamar_api', side_effect=simular):
            texto = plugin._paso_llm('nvidia', 'z-ai/glm-5.3', [{'role': 'user', 'content': 'x'}])
        self.assertEqual(texto, 'recuperado')
        self.assertEqual(visitas, ['nvidia', 'groq'])


if __name__ == '__main__':
    unittest.main()
