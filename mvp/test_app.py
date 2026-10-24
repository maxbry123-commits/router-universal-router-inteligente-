"""Pruebas del endpoint real HTTP con dependencias ya permitidas."""
import json
import os
import pathlib
import socket
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib import error, request
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import uvicorn
from mvp import app as servicio, bank


class TestApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.env = patch.dict(os.environ, {"RIU_API_KEY": "clave-local-prueba",
                                       "QWEN_API_KEY": "token-qwen-ficticio", "MVP_PLAN": "personal"})
        cls.env.start()
        banco = bank.abrir(pathlib.Path(cls.temp.name) / "banco.bin", "clave-local-prueba")
        banco.guardar("QWEN_API_KEY", "token-qwen-ficticio")
        cls.parche = patch("mvp.app.bank.abrir_desde_env", return_value=banco)
        cls.parche.start()
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        sock.listen()
        cls.url = f"http://127.0.0.1:{sock.getsockname()[1]}"
        cls.servidor = uvicorn.Server(uvicorn.Config(servicio.app, log_level="critical"))
        cls.hilo = threading.Thread(target=cls.servidor.run, kwargs={"sockets": [sock]})
        cls.hilo.start()
        import time
        for _ in range(100):
            if cls.servidor.started:
                break
            time.sleep(0.02)
        assert cls.servidor.started, "servidor de prueba no arranco"

    @classmethod
    def tearDownClass(cls):
        cls.servidor.should_exit = True
        cls.hilo.join(timeout=5)
        cls.parche.stop()
        cls.env.stop()
        cls.temp.cleanup()

    def pedir(self, ruta, datos=None, clave=False):
        headers = {"Content-Type": "application/json"}
        if clave:
            headers["Authorization" if clave == "bearer" else "x-api-key"] = "Bearer clave-local-prueba" if clave == "bearer" else "clave-local-prueba"
        req = request.Request(self.url + ruta, data=json.dumps(datos).encode() if datos is not None else None, headers=headers)
        try:
            with request.urlopen(req, timeout=5) as respuesta:
                return respuesta.status, json.load(respuesta)
        except error.HTTPError as fallo:
            return fallo.code, json.load(fallo)

    def test_chat_sin_clave(self):
        estado, _ = self.pedir("/chat", {"mensajes": [{"role": "user", "content": "hola"}]})
        self.assertEqual(estado, 401)

    @patch("mvp.app.compute.llamar")
    def test_chat_con_clave(self, falso):
        falso.return_value = {"texto": "respuesta", "tool_calls": [], "finish_reason": "stop"}
        estado, datos = self.pedir("/chat", {"mensajes": [{"role": "user", "content": "hola"}], "modelo": ""}, True)
        self.assertEqual((estado, datos), (200, {"texto": "respuesta", "tool_calls": [], "finish_reason": "stop"}))
        self.assertEqual(falso.call_args.args[1], "qwen3.8-max")

    @patch("mvp.app.compute.llamar")
    def test_finish_reason(self, falso):
        falso.return_value = {"texto": "ok", "tool_calls": [], "finish_reason": "stop"}
        estado, datos = self.pedir("/chat", {"mensajes": [{"role": "user", "content": "hola"}]}, True)
        self.assertEqual(estado, 200)
        self.assertEqual(datos["finish_reason"], "stop")

    @patch("mvp.app.compute.llamar")
    def test_agente_tool_bloqueada(self, falso):
        falso.return_value = {"texto": "", "finish_reason": "tool_calls",
                              "tool_calls": [{"function": {"name": "groq_agente"}}]}
        estado, datos = self.pedir("/chat", {"mensajes": [{"role": "user", "content": "hola"}],
                                             "tools": True, "agente_tool": False}, True)
        self.assertEqual(estado, 403)
        self.assertIn("agente_tool=false", datos["detail"])

    @patch("mvp.app.compute.llamar")
    def test_llm_tool_bloqueada(self, falso):
        falso.return_value = {"texto": "", "finish_reason": "tool_calls",
                              "tool_calls": [{"function": {"name": "llm"}}]}
        estado, datos = self.pedir("/chat", {"mensajes": [{"role": "user", "content": "hola"}],
                                             "tools": True, "llm_tool": False}, True)
        self.assertEqual(estado, 403)
        self.assertIn("llm_tool=false", datos["detail"])

    def test_chat_send_y_async_controles(self):
        salida = {"status": "ok", "result": {"texto": "ok", "tool_calls": [], "finish_reason": "stop"}}
        with patch.dict(os.environ, {"RIU_DEEPSEEK_HARNESS_URL": "https://harness.invalid"}), \
             patch("mvp.app.clave_harness", return_value="prueba"), \
             patch("mvp.app.harness_client.llm", return_value=salida):
            estado, datos = self.pedir("/chat/send", {"message": "hola"}, True)
            self.assertEqual((estado, datos["finish_reason"]), (200, "stop"))
            estado, datos = self.pedir("/plugins/fichas_qwen/call/chat_async",
                                      {"message": "hola", "request_id": "sol2-test"}, True)
            self.assertEqual(estado, 200)
            pid = datos["result"]["proceso_id"]
            estado, datos = self.pedir("/plugins/fichas_qwen/call/resultado",
                                      {"proceso_id": pid, "espera": 2}, True)
            self.assertEqual((estado, datos["result"]["finish_reason"]), (200, "stop"))

    def test_health_sin_secretos(self):
        estado, publico = self.pedir("/health")
        self.assertEqual((estado, publico), (200, {"status": "ok"}))
        estado, privado = self.pedir("/health", clave=True)
        self.assertEqual((estado, privado["plan"], privado["modelo_defecto"]), (200, "personal", "qwen3.8-max"))
        self.assertTrue(privado["banco_abierto"] and privado["clave_qwen_presente"])
        self.assertIn("commit", privado)
        self.assertNotIn("token-qwen-ficticio", str(privado))

    def test_chat_bearer(self):
        with patch("mvp.app.compute.llamar", return_value={"texto": "ok", "tool_calls": []}):
            estado, _ = self.pedir("/chat", {"mensajes": [{"role": "user", "content": "hola"}]}, "bearer")
        self.assertEqual(estado, 200)

    def test_banco_no_abierto(self):
        with patch.object(servicio.app.state, "banco", None):
            self.assertEqual(self.pedir("/health")[1]["status"], "degraded")
            self.assertEqual(self.pedir("/chat", {"mensajes": [{"role": "user", "content": "hola"}]}, True)[0], 503)

    def test_plan_y_multimodal_rechazados(self):
        for modelo in ("qwen3.6-plus", "wan3.0-video"):
            with self.subTest(modelo=modelo):
                estado, _ = self.pedir("/chat", {"modelo": modelo, "mensajes": [{"role": "user", "content": "hola"}]}, True)
                self.assertEqual(estado, 400)


if __name__ == "__main__":
    unittest.main(verbosity=2)


class TestVariasClavesDeAcceso(unittest.TestCase):
    def test_cualquier_variable_de_acceso_abre_la_puerta(self):
        with patch.dict(os.environ, {"RIU_API_KEY": "principal", "RIU_MCP_KEY": "de-prueba"}, clear=False):
            self.assertTrue(servicio.autorizado(None, "principal"))
            self.assertTrue(servicio.autorizado("Bearer de-prueba", None))
            self.assertFalse(servicio.autorizado(None, "otra"))
            self.assertFalse(servicio.autorizado(None, None))
