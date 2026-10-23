"""Harness simulado por HTTP real; ninguna credencial externa requerida."""
import json
import os
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, Mock
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
        self.assertEqual(r.json(), {"texto": "ok", "tool_calls": [], "finish_reason": None})
        self.assertEqual(Falso.recibidas[-1][1]["action"], "llm")
        directo.assert_not_called()

    def test_cadena_http_completa(self):
        import socket, time, uvicorn, httpx
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0)); sock.listen()
        base = f"http://127.0.0.1:{sock.getsockname()[1]}"
        banco = SimpleNamespace(leer=lambda nombre: "acceso-test")
        env = {"RIU_ROUTER_URL": base, "RIU_DEEPSEEK_HARNESS_URL": base + "/plugins/deepseek_harness",
               "MVP_QWEN_BASE_URL": self.url}
        github = Mock(return_value="commit simulado verificado")
        with patch.dict(os.environ, env), patch("mvp.app.bank.abrir_desde_env", return_value=banco), patch.dict(servicio.mcp_route.GITHUB, {"github_leer": github, "github_escribir": github}), patch("mvp.app.hf_store.guardar", return_value={"ok": True}) as guardar_hf:
            servidor = uvicorn.Server(uvicorn.Config(servicio.app, log_level="critical"))
            hilo = threading.Thread(target=servidor.run, kwargs={"sockets": [sock]})
            cliente = httpx.Client(base_url=base, timeout=10, trust_env=False)
            hilo.start()
            try:
                for _ in range(100):
                    if servidor.started: break
                    time.sleep(0.02)
                self.assertTrue(servidor.started)
                cab = {"x-api-key": "acceso-test"}
                cuerpo = {"message": "hola", "modelo": "qwen3.8-max", "tools": False,
                          "agente_tool": False, "llm_tool": False,
                          "opciones": {"tools": [{"type": "function", "function": {"name": "groq_agente"}}]}}
                for motivo in ("stop", "length", None):
                    texto = "palabra " * 2000
                    Falso.cola = [(200, {"choices": [{"message": {"content": texto}, "finish_reason": motivo}]})]
                    r = cliente.post("/chat/send", json=cuerpo, headers=cab)
                    self.assertEqual(r.status_code, 200, r.text)
                    self.assertEqual((r.json()["reply"], r.json()["finish_reason"]), (texto, motivo))
                Falso.cola = [(200, {"choices": [{"message": {"content": "PONG"}, "finish_reason": "stop"}]})]
                r = cliente.post("/mcp", headers=cab, json={"jsonrpc": "2.0", "id": 1,
                    "method": "tools/call", "params": {"name": "chat", "arguments": {**cuerpo, "ficha_qwen": "1"}}})
                pid = r.json()["result"]["structuredContent"]["proceso_id"]
                r = cliente.post("/mcp", headers=cab, json={"jsonrpc": "2.0", "id": 2,
                    "method": "tools/call", "params": {"name": "resultado", "arguments": {"proceso_id": pid, "espera": 2}}})
                self.assertEqual(r.json()["result"]["structuredContent"]["finish_reason"], "stop")
                for nombre, controles, codigo in (("groq_agente", {"tools": True, "agente_tool": False}, 403),
                        ("llm", {"tools": True, "llm_tool": False}, 403),
                        ("github_leer", {"tools": True, "agente_tool": False}, 200),
                        ("github_escribir", {"tools": True, "agente_tool": False}, 200)):
                    Falso.cola = [(200, {"choices": [{"message": {"content": "", "tool_calls": [
                        {"id": "call-test", "type": "function", "function": {"name": nombre, "arguments": json.dumps({"repo": "prueba", "ruta": "README.md", "contenido": "prueba"})}}]}, "finish_reason": "tool_calls"}]})]
                    if codigo == 200:
                        Falso.cola.append((200, {"choices": [{"message": {"content": "Hecho"}, "finish_reason": "stop"}]}))
                    r = cliente.post("/chat/send", json={**cuerpo, **controles}, headers=cab)
                    self.assertEqual(r.status_code, codigo, r.text)
                Falso.cola = [(200, {"choices": [{"message": {"content": "PONG"}, "finish_reason": "stop"}]})]
                r = cliente.post("/chat/send", json={**cuerpo, "modelo": "DeepSeek V4 Pro"}, headers=cab)
                self.assertEqual(r.status_code, 200, r.text)
                self.assertEqual(Falso.recibidas[-1][1]["model"], "deepseek-v4-pro")
                self.assertTrue(all(p == "/chat/completions" for p, _, _ in Falso.recibidas))
                self.assertEqual(len(Falso.recibidas), 11)
                self.assertEqual(github.call_count, 2)
                self.assertEqual(github.call_args.args[0]["rama"], "main")
                self.assertEqual(servicio.mcp_route.github._token(), banco.leer("GITHUB_TOKEN"))
                Falso.cola = [(200, {"choices": [{"message": {"role": "assistant", "content": None, "tool_calls": [
                    {"id": "hf-call", "type": "function", "function": {"name": "almacen", "arguments": json.dumps({"accion": "guardar", "nombre": "prueba.txt", "valor": "dato"})}}]}, "finish_reason": "tool_calls"}]}),
                    (200, {"model": "qwen3.8-max", "choices": [{"message": {"content": "Guardado"}, "finish_reason": "stop"}]})]
                r = cliente.post("/chat/send", json={**cuerpo, "tools": True}, headers=cab)
                self.assertEqual(r.status_code, 200, r.text)
                guardar_hf.assert_called_once_with(banco.leer("HF_TOKEN"), "prueba.txt", "dato")
                self.assertEqual(r.json()["modelo_respuesta"], "qwen3.8-max")

                r = cliente.post("/chat/send", json={**cuerpo, "modelo": "modelo-inexistente"}, headers=cab)
                self.assertEqual(r.status_code, 400)
                self.assertEqual(len(Falso.recibidas), 13)
            finally:
                cliente.close()
                servidor.should_exit = True
                hilo.join(timeout=5)

    def test_sin_banco_no_llama_harness(self):
        servicio.app.state.banco = None
        r = self.http_client.post("/almacen", json={"accion": "guardar", "nombre": "x", "valor": "y"}, headers={"x-api-key": "acceso-test"})
        self.assertEqual(r.status_code, 503)
        self.assertFalse(Falso.recibidas)

if __name__ == "__main__":
    unittest.main(verbosity=2)
