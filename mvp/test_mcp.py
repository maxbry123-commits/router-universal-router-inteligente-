"""S08: MCP JSON-RPC por HTTP real, sin claves ni proveedores externos."""
import os
import pathlib
import sys
import unittest
from unittest.mock import patch
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from mvp import mcp_route


class TestMCP(unittest.TestCase):
    def setUp(self):
        self.chat_calls, self.almacen_calls = [], []
        async def chat(args):
            self.chat_calls.append(args)
            return {"texto": "respuesta", "tool_calls": []}
        async def almacen(args):
            self.almacen_calls.append(args)
            return {"ok": True}
        def verificar(x_api_key=None):
            if x_api_key != "local-test":
                raise HTTPException(status_code=401, detail="acceso denegado")
        from fastapi import Header
        def auth(x_api_key: str | None = Header(None)):
            return verificar(x_api_key)
        self.api = FastAPI()
        mcp_route.montar(self.api, auth, chat, almacen)
        self.client = TestClient(self.api)
        self.plan = patch.dict(os.environ, {"MVP_PLAN": "personal"})
        self.plan.start()

    def tearDown(self):
        self.plan.stop()
        self.client.close()

    def enviar(self, metodo, params=None, id_=1):
        datos = {"jsonrpc": "2.0", "id": id_, "method": metodo}
        if params is not None:
            datos["params"] = params
        return self.client.post("/mcp", json=datos, headers={"x-api-key": "local-test"})

    def test_proteccion_autenticacion(self):
        self.assertEqual(self.client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "ping"}).status_code, 401)

    def test_initialize_y_ping(self):
        self.assertEqual(self.enviar("initialize").json()["result"]["capabilities"], {"tools": {}})
        self.assertEqual(self.enviar("ping").json()["result"], {})

    def test_tools_list(self):
        nombres = [x["name"] for x in self.enviar("tools/list").json()["result"]["tools"]]
        self.assertEqual(nombres, ["chat", "almacen"])

    def test_chat_modelo_defecto(self):
        r = self.enviar("tools/call", {"name": "chat", "arguments": {"mensajes": [{"role": "user", "content": "hola"}]}})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["result"]["structuredContent"]["texto"], "respuesta")
        self.assertEqual(self.chat_calls[0]["modelo"], "qwen3.8-max")

    def test_modelo_no_permitido_plan_personal(self):
        r = self.enviar("tools/call", {"name": "chat", "arguments": {"modelo": "qwen3.6-plus", "mensajes": []}})
        self.assertEqual(r.json()["error"]["code"], -32602)
        self.assertFalse(self.chat_calls)

    def test_modelo_multimodal_rechazado(self):
        r = self.enviar("tools/call", {"name": "chat", "arguments": {"modelo": "wan3.0-video", "mensajes": []}})
        self.assertEqual(r.json()["error"]["code"], -32602)
        self.assertFalse(self.chat_calls)

    def test_almacen(self):
        r = self.enviar("tools/call", {"name": "almacen", "arguments": {"accion": "leer", "nombre": "x"}})
        self.assertEqual(r.json()["result"]["structuredContent"], {"ok": True})
        self.assertEqual(self.almacen_calls, [{"accion": "leer", "nombre": "x"}])

    def test_parametros_invalidos(self):
        for parametros in (None, {"name": "chat", "arguments": []}, {"name": "desconocida"}):
            with self.subTest(parametros=parametros):
                self.assertEqual(self.enviar("tools/call", parametros).json()["error"]["code"], -32602)
        self.assertFalse(self.chat_calls)

    def test_metodo_inexistente(self):
        self.assertEqual(self.enviar("tools/otro").json()["error"]["code"], -32601)

    def test_notificacion_sin_respuesta(self):
        r = self.enviar("notifications/initialized")
        self.assertEqual((r.status_code, r.content), (202, b""))

    def test_jsonrpc_invalido(self):
        r = self.client.post("/mcp", json={"jsonrpc": "1.0", "id": 9, "method": "ping"}, headers={"x-api-key": "local-test"})
        self.assertEqual(r.json()["error"]["code"], -32600)


if __name__ == "__main__":
    unittest.main(verbosity=2)
