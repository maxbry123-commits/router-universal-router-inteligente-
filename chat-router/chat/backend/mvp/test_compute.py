"""Pruebas HTTP locales del cliente Qwen."""
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from mvp import compute
from mvp.compute import llamar


class Simulador(BaseHTTPRequestHandler):
    cola = []
    n = 0
    recibido = None

    def do_POST(self):
        type(self).n += 1
        type(self).recibido = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
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
        Simulador.n, Simulador.cola, Simulador.recibido = 0, [], None

    def llamada(self, opciones=None, modelo="qwen3.8-max"):
        return llamar([{"role": "user", "content": "hola"}],
                      modelo, self.url, "clave-test", opciones)

    def test_texto(self):
        Simulador.cola = [(200, {"choices": [{"message": {"content": "hola"}}]})]
        self.assertEqual(self.llamada()["texto"], "hola")

    def test_401(self):
        Simulador.cola = [(401, {})]
        with self.assertRaisesRegex(RuntimeError, "401"):
            self.llamada()
        self.assertEqual(Simulador.n, 1)

    @patch("mvp.compute.time.sleep")
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

    def test_finish_reason(self):
        Simulador.cola = [(200, {"choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}]})]
        self.assertEqual(self.llamada()["finish_reason"], "stop")

    def test_thinking_qwen(self):
        Simulador.cola = [(200, {"choices": [{"message": {"content": "ok"}}]})]
        self.llamada()
        self.assertIs(Simulador.recibido["enable_thinking"], True)

    def test_thinking_deepseek(self):
        Simulador.cola = [(200, {"choices": [{"message": {"content": "ok"}}]})]
        self.llamada(modelo="deepseek-v4-pro")
        self.assertNotIn("enable_thinking", Simulador.recibido)

    def test_reasoning_effort(self):
        Simulador.cola = [(200, {"choices": [{"message": {"content": "ok"}}]})]
        self.llamada({"reasoning_effort": "low"})
        self.assertEqual(Simulador.recibido["reasoning_effort"], "low")


if __name__ == "__main__":
    unittest.main(verbosity=2)


class DosUrlBase(unittest.TestCase):
    def test_user_agent_y_alterna_si_la_oficial_rechaza(self):
        vistos = []
        def sol(url, payload, clave):
            vistos.append(url)
            if "aliyuncs.com" in url:
                raise compute.error.HTTPError(url, 401, "no", {}, None)
            return {"choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}], "model": "glm-5.3"}
        with patch("mvp.compute._solicitar", sol):
            r = compute.llamar([{"role": "user", "content": "hola"}], "glm-5.3", compute.modelos.cargar()["base_url"], "sk-sp-x")
        self.assertEqual(r["modelo_respuesta"], "glm-5.3")
        self.assertEqual([("aliyuncs" in u) for u in vistos], [True, False])  # primero la oficial, luego QwenCloud
        with patch("mvp.compute.request.urlopen") as uo:
            uo.return_value.__enter__.return_value.read.return_value = b"{}"
            try:
                compute._solicitar("https://x/chat/completions", {}, "k")
            except Exception:
                pass
            self.assertEqual(uo.call_args.args[0].get_header("User-agent"), "qwencloud-skills")

    def test_error_400_no_prueba_la_alterna(self):
        vistos = []
        def sol(url, payload, clave):
            vistos.append(url); raise compute.error.HTTPError(url, 400, "malo", {}, None)
        with patch("mvp.compute._solicitar", sol):
            with self.assertRaises(RuntimeError):
                compute.llamar([{"role": "user", "content": "x"}], "glm-5.3", compute.modelos.cargar()["base_url"], "k")
        self.assertEqual(len(vistos), 1)
