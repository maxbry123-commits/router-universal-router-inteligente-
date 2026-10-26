"""Chat -> Harness -> Router -> LOOP/Cola/Watchdog por HTTP y MCP, contra la app real."""
import json
from mvp.test_control import Base, CAB, servicio


class LoopPuente(Base):
    def setUp(self):
        super().setUp(); self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None); super().tearDown()

    def rpc(self, metodo, params=None):
        return self.client.post("/mcp?key=api-ficticia", json={"jsonrpc": "2.0", "id": 1, "method": metodo, "params": params or {}})

    def llamar(self, nombre, args):
        r = self.rpc("tools/call", {"name": nombre, "arguments": args}).json()
        return r if "error" in r else json.loads(r["result"]["content"][0]["text"])

    def http(self, plugin, accion, cuerpo=None):
        return self.client.post("/plugins/%s/call/%s" % (plugin, accion), headers=CAB, json=cuerpo or {})

    def test_los_tres_plugins_responden_por_http(self):
        for plugin, servicio in (("nct_loop", "nct_loop"), ("cola50", "cit50"), ("watchdog48", "watchdog48")):
            r = self.http(plugin, "status")
            self.assertEqual(r.status_code, 200, r.text)
            self.assertEqual(r.json()["result"]["service"], servicio)

    def test_sin_clave_no_entra(self):
        self.assertEqual(self.client.post("/plugins/nct_loop/call/status", json={}).status_code, 401)

    def test_plugin_no_listado_sigue_404(self):
        self.assertEqual(self.http("ssh_bridge", "status").status_code, 404)

    def test_gobernar_sin_objetivo_da_error(self):
        self.assertIn("error", self.http("nct_loop", "gobernar", {}).json()["result"])

    def test_espejo_de_agentes_por_http(self):
        r = self.http("nct_loop", "agentes", {"tipo": "modelo"}).json()["result"]
        self.assertTrue({"qwen3.8-max", "glm-5.3", "deepseek-v4-pro"} <= {a["id"] for a in r["agentes"]})

    def test_mirrors_de_hermes_y_openclaw_por_http(self):
        for aid in ("hermes-agent", "openclaw"):
            r = self.http("nct_loop", "mirror_listar", {"agente": aid}).json()["result"]
            self.assertEqual({m["tipo"] for m in r["detalle"][aid]}, {"fork", "upstream"})

    def test_paralelo_rechaza_mas_de_cuatro(self):
        r = self.http("nct_loop", "paralelo", {"objetivos": ["a"] * 5}).json()["result"]
        self.assertIn("error", r)

    def nombres(self):
        return {t["name"] for t in self.rpc("tools/list").json()["result"]["tools"]}

    def test_tool_loop_no_se_ve_con_agentes_apagados(self):
        self.assertNotIn("loop", self.nombres())

    def test_tool_loop_por_mcp_con_agentes_encendidos(self):
        servicio.CONTROL.d["agentes_on"] = True
        servicio.CONTROL.d["ia"] = True
        self.assertIn("loop", self.nombres())
        self.assertEqual(self.llamar("loop", {"accion": "status"})["service"], "nct_loop")
        self.assertEqual(self.llamar("loop", {"plugin": "cola50", "accion": "status"})["service"], "cit50")
        self.assertIn("error", self.llamar("loop", {"plugin": "ssh_bridge", "accion": "status"}))
