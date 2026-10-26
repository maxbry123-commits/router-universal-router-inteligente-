"""MCP JSON-RPC por HTTP real, sin claves ni proveedores externos."""
import os
import pathlib
import sys
import unittest
from unittest.mock import patch
from fastapi import FastAPI, Header, HTTPException
from fastapi.testclient import TestClient
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from mvp import mcp_route


class TestMCP(unittest.TestCase):
    def setUp(self):
        self.chat_calls, self.almacen_calls, self.ficha_calls = [], [], []
        async def chat(args):
            self.chat_calls.append(args)
            return {'texto': 'respuesta', 'tool_calls': []}
        async def almacen(args):
            self.almacen_calls.append(args)
            return {'ok': True}
        async def ficha(plugin, accion, args):
            self.ficha_calls.append((plugin, accion, args))
            if accion == 'fichas':
                return {'status': 'ok', 'result': {'fichas': [{'id': 'ficha1'}]}}
            if accion == 'chat_async':
                return {'status': 'ok', 'result': {'proceso_id': 'p-1', 'estado': 'procesando'}}
            return {'status': 'ok', 'result': {'proceso_id': 'p-1', 'estado': 'listo'}}
        def auth(x_api_key: str | None = Header(None), authorization: str | None = Header(None)):
            if x_api_key != 'local-test' and authorization != 'Bearer local-test':
                raise HTTPException(status_code=401, detail='acceso denegado')
        self.api = FastAPI()
        self.api.add_api_route('/plugins/{plugin}/call/{accion}', ficha, methods=['POST'])
        mcp_route.montar(self.api, auth, chat, almacen)
        self.client = TestClient(self.api)
        self.plan = patch.dict(os.environ, {'MVP_PLAN': 'personal'})
        self.plan.start()

    def tearDown(self):
        self.plan.stop()
        self.client.close()

    def enviar(self, metodo, params=None, id_=1):
        datos = {'jsonrpc': '2.0', 'id': id_, 'method': metodo}
        if params is not None:
            datos['params'] = params
        return self.client.post('/mcp', json=datos, headers={'x-api-key': 'local-test'})

    def test_proteccion_autenticacion(self):
        d = {'jsonrpc': '2.0', 'id': 1, 'method': 'ping'}
        self.assertEqual(self.client.post('/mcp', json=d).status_code, 401)
        self.assertEqual(self.client.post('/mcp', json=d, headers={'x-api-key': 'incorrecto'}).status_code, 401)
        self.assertEqual(self.client.post('/mcp', json=d, headers={'authorization': 'Bearer local-test'}).status_code, 200)

    def test_initialize_y_ping(self):
        self.assertEqual(self.enviar('initialize').json()['result']['capabilities'], {'tools': {}})
        self.assertEqual(self.enviar('ping').json()['result'], {})

    def test_tools_list_contratos_reales(self):
        tools = self.enviar('tools/list').json()['result']['tools']
        self.assertEqual({x['name'] for x in tools}, {'chat', 'almacen', 'memoria', 'listar_fichas', 'resultado', 'salud',
                                                       'github_leer', 'github_escribir', 'github_api'})
        self.assertTrue(all(x['inputSchema']['type'] == 'object' for x in tools))

    def test_chat_modelo_defecto(self):
        r = self.enviar('tools/call', {'name': 'chat', 'arguments': {'mensajes': [{'role': 'user', 'content': 'hola'}]}})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['result']['structuredContent']['texto'], 'respuesta')
        self.assertEqual(self.chat_calls[0]['modelo'], 'qwen3.8-max')

    def test_modelo_no_permitido_plan_personal(self):
        r = self.enviar('tools/call', {'name': 'chat', 'arguments': {'modelo': 'qwen3.6-plus', 'mensajes': [{'role':'user','content':'hola'}]}})
        self.assertEqual(r.json()['error']['code'], -32602)
        self.assertFalse(self.chat_calls)

    def test_modelo_multimodal_rechazado(self):
        r = self.enviar('tools/call', {'name': 'chat', 'arguments': {'modelo': 'wan3.0-video', 'mensajes': [{'role':'user','content':'hola'}]}})
        self.assertEqual(r.json()['error']['code'], -32602)
        self.assertFalse(self.chat_calls)
        r = self.enviar('tools/call', {'name':'chat', 'arguments':{'ficha_qwen':'ficha1', 'modelo':'wan3.0-video'}})
        self.assertNotIn('error', r.json())  # por la ficha los modelos de imagen, voz y video SI se aceptan: ella genera el medio
        self.assertEqual(len(self.ficha_calls), 1)
        r = self.enviar('tools/call', {'name':'chat', 'arguments':{'ficha_qwen':'ficha1', 'modelo':'no-existe'}})
        self.assertEqual(r.json()['error']['code'], -32602)

    def test_almacen(self):
        r = self.enviar('tools/call', {'name': 'almacen', 'arguments': {'accion': 'leer', 'nombre': 'x'}})
        self.assertEqual(r.json()['result']['structuredContent'], {'ok': True})
        self.assertEqual(self.almacen_calls, [{'accion': 'leer', 'nombre': 'x'}])

    def test_fichas_y_resultado_reutilizan_handler(self):
        for nombre, args, accion in [('listar_fichas', {}, 'fichas'),
                                     ('chat', {'ficha_qwen': 'ficha1', 'message': 'hola'}, 'chat_async'),
                                     ('resultado', {'proceso_id': 'p-1'}, 'resultado')]:
            with self.subTest(nombre=nombre):
                r = self.enviar('tools/call', {'name': nombre, 'arguments': args})
                self.assertEqual(r.status_code, 200)
                self.assertIn('structuredContent', r.json()['result'])
                self.assertEqual(self.ficha_calls[-1], ('fichas_qwen', accion, args))
        self.assertFalse(self.chat_calls)

    def test_github_funciones_existentes(self):
        for nombre, args in [('github_leer', {'repo':'repositorio'}),
                             ('github_escribir', {'repo':'repositorio', 'ruta':'x', 'contenido':'text'}),
                             ('github_api', {'metodo':'GET', 'ruta':'/user'})]:
            with self.subTest(nombre=nombre):
                with patch.dict(mcp_route.GITHUB, {nombre: lambda a: 'resultado github'}):
                    r = self.enviar('tools/call', {'name': nombre, 'arguments': args})
                self.assertEqual(r.json()['result']['content'][0]['text'], 'resultado github')

    def test_parametros_invalidos(self):
        for parametros in (None, {'name': 'chat', 'arguments': []}, {'name': 'desconocida'},
                           {'name': 'resultado', 'arguments': {}}, {'name': 'github_escribir', 'arguments': {'repo': 'x'}},
                           {'name': 'chat', 'arguments': {'mensajes': 'texto'}}):
            with self.subTest(parametros=parametros):
                self.assertEqual(self.enviar('tools/call', parametros).json()['error']['code'], -32602)
        self.assertFalse(self.chat_calls)

    def test_metodo_inexistente(self):
        self.assertEqual(self.enviar('tools/otro').json()['error']['code'], -32601)

    def test_notificacion_sin_respuesta(self):
        r = self.enviar('notifications/initialized')
        self.assertEqual((r.status_code, r.content), (202, b''))

    def test_jsonrpc_invalido_y_parseo(self):
        headers = {'x-api-key': 'local-test'}
        for cuerpo in ({'jsonrpc': '1.0', 'id': 9, 'method': 'ping'}, [], {'jsonrpc': '2.0', 'id': 1}):
            r = self.client.post('/mcp', json=cuerpo, headers=headers)
            self.assertEqual(r.json()['error']['code'], -32600)
        r = self.client.post('/mcp', content='no-json', headers=headers)
        self.assertEqual(r.json()['error']['code'], -32700)


if __name__ == '__main__':
    unittest.main(verbosity=2)


class TestMediosYGithubPorMcp(unittest.TestCase):
    def test_chat_acepta_modelos_de_medios_y_la_ruta_de_github_conserva_las_barras(self):
        from mvp import modelos
        self.assertIn("qwen-image-3.0-pro", dict(modelos.catalogo()))
        import urllib.parse
        from router import mcp_puente_github as g
        vistos = []
        with patch.object(g, "_peticion", lambda m, u, c=None, e=40: (vistos.append(u), (200, {"type": "file", "content": ""}))[1]), patch.object(g, "_token", lambda: "t"):
            g.github_leer({"repo": "r", "ruta": "Prueba/sol-escritura.txt", "rama": "main"})
        self.assertIn("/contents/Prueba/sol-escritura.txt?ref=main", vistos[0])
