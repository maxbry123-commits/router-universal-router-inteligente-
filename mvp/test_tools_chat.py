"""Cadena completa chat -> Harness -> modelo falso con tool_calls -> /mcp -> estado del Router: pendientes, yaiwes_md y sala deben quedar guardados."""
import json
import os
import socket
import threading
import time
import unittest
from http.server import ThreadingHTTPServer
from types import SimpleNamespace
from unittest.mock import patch
import httpx
import uvicorn
from mvp import app as servicio, control
from mvp.test_harness import Falso


def llamada(nombre, args):
    return (200, {"choices": [{"message": {"content": None, "tool_calls": [{"id": "c1", "type": "function", "function": {"name": nombre, "arguments": json.dumps(args)}}]}, "finish_reason": "tool_calls"}]})


FIN = (200, {"choices": [{"message": {"content": "Hecho"}, "finish_reason": "stop"}]})


class ToolsDelChat(unittest.TestCase):
    def test_herramientas_de_control_desde_el_modelo(self):
        http = ThreadingHTTPServer(("127.0.0.1", 0), Falso); threading.Thread(target=http.serve_forever, daemon=True).start()
        sock = socket.socket(); sock.bind(("127.0.0.1", 0)); sock.listen()
        base = f"http://127.0.0.1:{sock.getsockname()[1]}"
        banco = SimpleNamespace(leer=lambda n: {"RIU_API_KEY": "acceso-test", "QWEN_API_KEY": "k"}.get(n))
        env = {"RIU_API_KEY": "acceso-test", "RIU_ROUTER_URL": base, "RIU_DEEPSEEK_HARNESS_URL": base + "/plugins/deepseek_harness", "MVP_QWEN_BASE_URL": f"http://127.0.0.1:{http.server_port}"}
        servicio.CONTROL.d, servicio.CONTROL.sincronizado, servicio.CONTROL.persistente = control._vacio(), True, False
        with patch.dict(os.environ, env), patch("mvp.app.bank.abrir_desde_env", return_value=banco), patch("mvp.app.hf_store.guardar", return_value={"ok": True}):
            servicio.app.state.banco = banco
            srv = uvicorn.Server(uvicorn.Config(servicio.app, log_level="critical")); hilo = threading.Thread(target=srv.run, kwargs={"sockets": [sock]}); hilo.start()
            cli = httpx.Client(base_url=base, timeout=20, trust_env=False)
            try:
                for _ in range(100):
                    if srv.started: break
                    time.sleep(0.02)
                cab = {"x-api-key": "acceso-test"}
                for nombre, args in (("pendientes", {"accion": "agregar", "texto": "sol-x"}), ("yaiwes_md", {"accion": "escribir", "texto": "proyecto-x"}), ("sala", {"accion": "crear", "nombre": "sala-x"})):
                    Falso.cola = [llamada(nombre, args), FIN]
                    r = cli.post("/chat/send", headers=cab, json={"message": "hazlo", "modelo": "qwen3.8-max", "tools": True, "agente_tool": False, "llm_tool": False})
                    self.assertEqual(r.status_code, 200, r.text)
                self.assertEqual([p["texto"] for p in servicio.CONTROL.d["pendientes"]], ["sol-x"])
                self.assertEqual(servicio.CONTROL.d["handoff"], {"yaiwes": "proyecto-x"})
                self.assertEqual([s["nombre"] for s in servicio.CONTROL.d["salas"].values()], ["sala-x"])
                Falso.cola = [llamada("pendientes", {"accion": "listar"}), FIN]
                r = cli.post("/plugins/puente_chat/call/chat_async", headers=cab, json={"message": "lista", "modelo": "qwen3.8-max", "tools": True, "request_id": "diag-1"}).json()["result"]
                for _ in range(40):
                    r = cli.post("/plugins/puente_chat/call/resultado", headers=cab, json={"proceso_id": r["proceso_id"], "espera": 1}).json()["result"]
                    if r["estado"] != "procesando": break
                self.assertEqual(r.get("herramientas_usadas"), ["pendientes"])  # visible para el diagnostico
                Falso.cola = [llamada("almacen", {"accion": "listar", "nombre": "x"}), FIN]  # BUG: «GAP: Almacen HF permite solo leer y guardar» cortaba el chat
                r = cli.post("/chat/send", headers=cab, json={"message": "lista el almacen", "modelo": "qwen3.8-max", "tools": True})
                self.assertEqual((r.status_code, r.json().get("reply")), (200, "Hecho"), r.text)  # el modelo recibe el error como resultado de la herramienta y sigue
                self.assertIn("solo leer y guardar", json.dumps(Falso.recibidas[-1][1]["messages"][-1], ensure_ascii=False))
            finally:
                srv.should_exit = True; hilo.join(timeout=5); http.shutdown()
