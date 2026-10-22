"""Harness simulado por HTTP real; ninguna credencial externa requerida."""
import json
import os
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fastapi.testclient import TestClient
from mvp import app as servicio, harness_client as hc
class Falso(BaseHTTPRequestHandler):
    cola = []
    recibidas = []
    def do_POST(self):
        cuerpo = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        type(self).recibidas.append((self.path, cuerpo, self.headers.get("X-API-Key")))
        codigo, respuesta = self.cola.pop(0) if self.cola else (200, {"texto": "ok", "tool_calls": []})
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(respuesta).encode())
    def log_message(self, *args):
        pass
class TestHarness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.http = ThreadingHTTPServer(("127.0.0.1", 0), Falso)
        cls.hilo = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.hilo.start()
        cls.url = f"http://127.0.0.1:{cls.http.server_port}"
        cls.http_client = TestClient(servicio.app)
    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        cls.hilo.join(timeout=2)
        cls.http_client.close()
    def setUp(self):
        Falso.cola, Falso.recibidas = [], []
        self.env = patch.dict(os.environ, {"RIU_API_KEY": "acceso-test",
                        "RIU_DEEPSEEK_HARNESS_URL": self.url, "MVP_PLAN": "personal"})
        self.env.start()
        self.banco = getattr(servicio.app.state, "banco", None)
        servicio.app.state.banco = SimpleNamespace(leer=lambda nombre: "harness-test" if nombre == "RIU_API_KEY" else None)
    def tearDown(self):
        servicio.app.state.banco = self.banco
        self.env.stop()

    def test_operaciones_y_contrato(self):
        self.assertEqual(hc.status("harness-test")["texto"], "ok")
        hc.guardar("harness-test", "doc", "abc")
        hc.leer("harness-test", "doc")
        hc.computar("harness-test", {"op": "sumar"})
        hc.llm("harness-test", [{"role": "user", "content": "hola"}], "qwen3.8-max")
        self.assertEqual([r[1]["action"] for r in Falso.recibidas],
                         ["status", "invoke", "invoke", "invoke", "llm"])
        self.assertEqual(Falso.recibidas[1][1]["tool"], "guardar")
        self.assertTrue(all(r[0] == "/invoke" and r[2] == "harness-test" for r in Falso.recibidas))

    @patch("mvp.harness_client.time.sleep")
    def test_retry_maximo_dos_solo_503(self, esperar):
        Falso.cola = [(503, {}), (503, {}), (200, {"texto": "ok"})]
        self.assertEqual(hc.status("harness-test")["texto"], "ok")
        self.assertEqual(len(Falso.recibidas), 3)
        self.assertEqual(esperar.call_count, 2)

    @patch("mvp.harness_client.time.sleep")
    def test_401_no_reintentos(self, esperar):
        Falso.cola = [(401, {})]
        with self.assertRaisesRegex(RuntimeError, "HTTP 401"):
            hc.status("harness-test")
        self.assertEqual(len(Falso.recibidas), 1)
        esperar.assert_not_called()

    def test_post_almacen_y_proteccion(self):
        self.assertEqual(self.http_client.post("/almacen", json={"accion": "leer", "nombre": "x"}).status_code, 401)
        r = self.http_client.post("/almacen", json={"accion": "leer", "nombre": "x"}, headers={"x-api-key": "acceso-test"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Falso.recibidas[-1][1]["tool"], "leer")
        self.assertEqual(self.http_client.post("/almacen", json={"accion": "borrar"}, headers={"x-api-key": "acceso-test"}).status_code, 400)

    def test_chat_via_harness(self):
        with patch("mvp.app.compute.llamar") as directo:
            r = self.http_client.post("/chat", json={"via": "harness", "mensajes": [{"role": "user", "content": "hola"}]}, headers={"x-api-key": "acceso-test"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {"texto": "ok", "tool_calls": []})
        self.assertEqual(Falso.recibidas[-1][1]["action"], "llm")
        directo.assert_not_called()

    def test_sin_banco_no_llama_harness(self):
        servicio.app.state.banco = None
        r = self.http_client.post("/almacen", json={"accion": "guardar", "nombre": "x", "valor": "y"}, headers={"x-api-key": "acceso-test"})
        self.assertEqual(r.status_code, 503)
        self.assertFalse(Falso.recibidas)

if __name__ == "__main__":
    unittest.main(verbosity=2)
