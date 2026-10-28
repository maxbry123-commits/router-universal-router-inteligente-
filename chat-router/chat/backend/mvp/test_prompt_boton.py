"""System prompt de punta a punta por HTTP real: el boton lo enciende/apaga y el proveedor recibe (o no) el texto completo, tras el Harness DeepSeek."""
import json
import os
import socket
import sys
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mvp import app as servicio, prompt, harness_client
from mvp.test_harness import Falso
from http.server import ThreadingHTTPServer

TROZO = "Actúa como: el ROL DEL NODO indicado más abajo"  # de system_core.md ya con sus huecos llenos
RESPUESTA = (200, {"model": "qwen3.8-max", "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}]})


class TestPromptBoton(unittest.TestCase):
    def test_boton_system_prompt_de_punta_a_punta(self):
        import httpx, uvicorn
        proveedor = ThreadingHTTPServer(("127.0.0.1", 0), Falso)
        threading.Thread(target=proveedor.serve_forever, daemon=True).start()
        sock = socket.socket(); sock.bind(("127.0.0.1", 0)); sock.listen()
        base = f"http://127.0.0.1:{sock.getsockname()[1]}"
        env = {"RIU_ROUTER_URL": base, "RIU_API_KEY": "acceso-test", "RIU_DEEPSEEK_HARNESS_URL": base + "/plugins/deepseek_harness",
               "MVP_QWEN_BASE_URL": f"http://127.0.0.1:{proveedor.server_address[1]}", "MVP_PLAN": "personal"}
        completo, formato = prompt.sistema(), prompt.formato()
        self.assertIn(TROZO, completo)
        self.assertNotIn(TROZO, formato)
        with patch.dict(os.environ, env), patch("mvp.app.bank.abrir_desde_env", return_value=SimpleNamespace(leer=lambda n: "acceso-test")), \
                patch("mvp.app.hf_store.guardar", return_value={"ok": True}), patch.dict(servicio.CONTROL.d, {"prompt_on": False}), \
                patch.object(harness_client, "_enviar", wraps=harness_client._enviar) as enviar:
            servidor = uvicorn.Server(uvicorn.Config(servicio.app, log_level="critical"))
            hilo = threading.Thread(target=servidor.run, kwargs={"sockets": [sock]})
            cliente = httpx.Client(base_url=base, timeout=20, trust_env=False)
            hilo.start()
            try:
                for _ in range(100):
                    if servidor.started: break
                    time.sleep(0.02)
                self.assertTrue(servidor.started)
                cab = {"x-api-key": "acceso-test"}

                def boton(locked):
                    r = cliente.post("/plugins/puente_chat/call/agent_access_lock", headers=cab, json={"quien": "prompt", "locked": locked})
                    self.assertEqual(r.status_code, 200, r.text)
                    return json.dumps(r.json())

                def system_al_proveedor():
                    Falso.recibidas, Falso.cola = [], [RESPUESTA]
                    r = cliente.post("/chat/send", headers=cab, json={"message": "hola", "modelo": "qwen3.8-max", "tools": False, "agente_tool": False, "llm_tool": False})
                    self.assertEqual(r.status_code, 200, r.text)
                    enviados = [c[1] for c in Falso.recibidas if c[0] == "/chat/completions"]
                    self.assertEqual(len(enviados), 1)
                    sistemas = [m["content"] for m in enviados[0]["messages"] if m["role"] == "system"]
                    return sistemas[0] if sistemas else ""

                self.assertIn('"prompt_locked": true', json.dumps(cliente.post("/plugins/puente_chat/call/agent_access_lock", headers=cab, json={}).json()))  # estado inicial: apagado de fabrica
                sistema = system_al_proveedor()  # (i) OFF
                self.assertIn(formato, sistema)
                self.assertNotIn(TROZO, sistema)
                self.assertIn('"prompt_locked": false', boton(False))  # (ii) ON
                sistema = system_al_proveedor()
                self.assertIn(formato, sistema)
                self.assertIn(TROZO, sistema)
                self.assertIn(completo, sistema)  # sin recortar ni editar
                self.assertGreaterEqual(len(sistema), len(completo))
                self.assertTrue(sistema.startswith(formato))  # capas: formato primero, luego el system prompt
                self.assertLess(sistema.index(formato), sistema.index(TROZO))
                self.assertTrue(enviar.call_count == 2 and all(c.args[0] == "llm" for c in enviar.call_args_list), enviar.call_count)  # todos los chats pasaron por el Harness (HTTP)
                self.assertIn('"prompt_locked": true', boton(True))  # (iii) OFF otra vez
                sistema = system_al_proveedor()
                self.assertIn(formato, sistema)
                self.assertNotIn(TROZO, sistema)
                self.assertEqual(enviar.call_count, 3)
            finally:
                servidor.should_exit = True
                hilo.join(timeout=5)
                cliente.close()
                proveedor.shutdown()


if __name__ == "__main__":
    unittest.main()
