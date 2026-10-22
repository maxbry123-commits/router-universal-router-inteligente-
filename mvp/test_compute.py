"""Pruebas HTTP locales del cliente Qwen."""
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
from compute import llamar


class Simulador(BaseHTTPRequestHandler):
    cola = []
    n = 0

    def do_POST(self):
        type(self).n += 1
        codigo, datos = self.cola.pop(0)
        self.send_response(codigo)
        self.end_headers()
        self.wfile.write(json.dumps(datos).encode())

    def log_message(self, *args):
        pass


class TestQwen(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.http = ThreadingHTTPServer(("127.0.0.1", 0), Simulador)
        cls.hilo = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.hilo.start()
        cls.url = f"http://127.0.0.1:{cls.http.server_port}/v1"

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        cls.hilo.join(timeout=2)

    def setUp(self):
        Simulador.n, Simulador.cola = 0, []

    def llamada(self, opciones=None):
        return llamar([{"role": "user", "content": "hola"}],
                      "qwen-test", self.url, "clave-test", opciones)

    def test_texto(self):
        Simulador.cola = [(200, {"choices": [{"message": {"content": "hola"}}]})]
        self.assertEqual(self.llamada()["texto"], "hola")

    def test_401(self):
        Simulador.cola = [(401, {})]
        with self.assertRaisesRegex(RuntimeError, "401"):
            self.llamada()
        self.assertEqual(Simulador.n, 1)

    @patch("compute.time.sleep")
    def test_503(self, _):
        Simulador.cola = [(503, {}), (503, {}),
                          (200, {"choices": [{"message": {"content": "ok"}}]})]
        self.assertEqual(self.llamada()["texto"], "ok")
        self.assertEqual(Simulador.n, 3)

    def test_tools(self):
        llamadas = [{"id": "call-1", "type": "function",
                     "function": {"name": "buscar", "arguments": "{}"}}]
        Simulador.cola = [(200, {"choices": [{"message": {"tool_calls": llamadas}}]})]
        self.assertEqual(self.llamada({"tool_choice": "auto"})["tool_calls"], llamadas)


if __name__ == "__main__":
    unittest.main(verbosity=2)
