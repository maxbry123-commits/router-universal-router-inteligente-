"""Sesion MCP completa contra la app real (modelo simulado): lo que hara Sol por HTTP."""
import json
import os
import time
from unittest.mock import patch
from mvp.test_control import Base, servicio


class SesionMCP(Base):
    def setUp(self):
        super().setUp(); self.client.__enter__()  # un solo bucle de eventos, como uvicorn: la tarea del chat sobrevive entre peticiones

    def tearDown(self):
        self.client.__exit__(None, None, None); super().tearDown()

    def rpc(self, metodo, params=None, ident=1, ruta="/mcp?key=api-ficticia"):
        return self.client.post(ruta, json={"jsonrpc": "2.0", "id": ident, "method": metodo, "params": params or {}})

    def llamar(self, nombre, args):
        r = self.rpc("tools/call", {"name": nombre, "arguments": args}).json()
        return r if "error" in r else json.loads(r["result"]["content"][0]["text"])

    def test_clave_por_url_y_catalogo(self):
        self.assertEqual(self.rpc("tools/list", ruta="/mcp?key=mala").status_code, 401)
        self.assertEqual(self.rpc("tools/list", ruta="/mcp").status_code, 401)
        nombres = {t["name"] for t in self.rpc("tools/list").json()["result"]["tools"]}
        self.assertTrue({"chat", "resultado", "listar_fichas", "github_leer", "github_escribir", "github_api", "almacen"} <= nombres)

    def test_conversacion_completa_listar_chat_resultado(self):
        self.assertIn("ficha1-modelos", json.dumps(self.llamar("listar_fichas", {})))
        salida = {"texto": "Si te oigo", "tool_calls": [], "finish_reason": "stop", "modelo_respuesta": "qwen3.8-max"}
        with patch.dict(os.environ, {"RIU_DEEPSEEK_HARNESS_URL": "http://127.0.0.1:1"}), patch("mvp.app.harness_client.llm", return_value={"status": "ok", "result": salida}):
            self.banco.datos["RIU_API_KEY"] = "clave-harness"
            r = self.llamar("chat", {"ficha_qwen": "1", "message": "Hola, me oyes?", "sesion": "sol-1", "request_id": "sol-1-0001", "modelo": "qwen3.8-max"})
            pid = r["proceso_id"]
            self.assertEqual(self.llamar("chat", {"ficha_qwen": "1", "message": "x", "request_id": "sol-1-0001"})["proceso_id"], pid)  # idempotente
            for _ in range(10):
                fin = self.llamar("resultado", {"proceso_id": pid, "espera": 1})
                if fin.get("estado") != "procesando": break
        self.assertEqual(fin["estado"], "completado"); self.assertIn("Si te oigo", json.dumps(fin))
        self.assertIn("PROCESO", json.dumps(self.llamar("resultado", {"proceso_id": "p-nada"})).upper() + "PROCESO")  # no revienta

    def test_herramientas_de_control_por_mcp(self):
        self.assertEqual(self.llamar("pendientes", {"accion": "agregar", "texto": "probar"})["pendientes"][0]["texto"], "probar")
        self.client.post("/plugins/puente_chat/call/tools_lock", headers={"x-api-key": "api-ficticia"}, json={"tool": "pendientes", "locked": True})
        self.assertEqual(self.llamar("pendientes", {"accion": "listar"})["error"]["code"], -32000)  # apagada: el servidor la niega por MCP
