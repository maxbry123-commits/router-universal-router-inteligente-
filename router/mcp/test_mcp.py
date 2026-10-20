"""Pruebas offline: transporte HTTP reemplazado por un falso. Sin red, sin llaves reales."""
import base64, json, os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from mcp import config, server, tools, transport  # noqa: E402

KEY, PAT, CHAT = "k-prueba-mcp-123", "pat-prueba-456", "chat-prueba-789"


class Falso:
    def __init__(self, rutas):
        self.rutas, self.llamadas = rutas, []

    def __call__(self, metodo, url, headers=None, cuerpo=None, espera=40):
        self.llamadas.append((metodo, url, headers or {}, cuerpo))
        for (m, frag), resp in self.rutas:
            if m == metodo and frag in url:
                if isinstance(resp, Exception):
                    raise resp
                return resp(cuerpo) if callable(resp) else resp
        return 404, {"message": "no ruta"}


class Base(unittest.TestCase):
    def setUp(self):
        os.environ.update(RIU_MCP_KEY=KEY, RIU_GITHUB_PAT=PAT, RIU_CHAT_KEY=CHAT, RIU_ROUTER_URL="http://router.test")
        os.environ.pop("RIU_MCP_ESCRITURA", None)
        os.environ.pop("RIU_MCP_RAMAS", None)
        self._orig = transport.enviar

    def tearDown(self):
        transport.enviar = self._orig

    def fake(self, rutas):
        f = Falso(rutas); transport.enviar = f; return f

    def llamar(self, nombre, args):
        st, r = server.handle_http({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": nombre, "arguments": args}}, {"X-API-Key": KEY}, {})
        self.assertEqual(st, 200)
        return r["result"]["isError"], json.loads(r["result"]["content"][0]["text"])


class Auth(Base):
    def test_sin_llave_401(self):
        st, _ = server.handle_http({"jsonrpc": "2.0", "id": 1, "method": "ping"}, {}, {})
        self.assertEqual(st, 401)

    def test_llave_mala_401_y_buena_ok(self):
        self.assertEqual(server.handle_http({"method": "ping", "id": 1}, {"X-API-Key": "x"}, {})[0], 401)
        self.assertEqual(server.handle_http({"method": "ping", "id": 1}, {"Authorization": "Bearer " + KEY}, {})[0], 200)
        self.assertEqual(server.handle_http({"method": "ping", "id": 1}, {}, {"key": KEY})[0], 200)

    def test_servidor_cerrado_sin_llave_configurada(self):
        del os.environ["RIU_MCP_KEY"]
        self.assertEqual(server.handle_http({"method": "ping", "id": 1}, {"X-API-Key": ""}, {})[0], 401)

    def test_tools_list_tiene_las_7(self):
        _, r = server.handle_http({"method": "tools/list", "id": 2}, {"X-API-Key": KEY}, {})
        self.assertEqual({t["name"] for t in r["result"]["tools"]},
                         {"github_leer", "github_escribir", "router_estado", "plugin_llamar", "chat_enviar", "probar_modelo", "ver_proceso"})


class GitHub(Base):
    def test_leer(self):
        self.fake([(("GET", "/contents/a.txt"), (200, {"sha": "s1", "content": base64.b64encode(b"l1\nl2\nl3").decode()}))])
        err, o = self.llamar("github_leer", {"repo": "r", "ruta": "a.txt", "rama": "feat/modos-router", "lineas": "2-3"})
        self.assertFalse(err); self.assertEqual(o["contenido"], "l2\nl3")

    def test_escribir_main_rechazado_sin_red(self):
        f = self.fake([])
        err, o = self.llamar("github_escribir", {"repo": "r", "ruta": "a", "contenido": "x", "rama": "main"})
        self.assertTrue(err); self.assertEqual(o["error"], "RAMA_NO_PERMITIDA"); self.assertEqual(f.llamadas, [])

    def _rutas_escritura(self, devuelto):
        return [(("GET", "ref=feat%2Fmodos-router"), (404, {})),
                (("PUT", "/contents/a.txt"), (201, {"commit": {"sha": "c0ffee"}})),
                (("GET", "ref=c0ffee"), (200, {"content": base64.b64encode(devuelto.encode()).decode()}))]

    def test_escribir_ok_con_readback(self):
        self.fake(self._rutas_escritura("hola"))
        err, o = self.llamar("github_escribir", {"repo": "r", "ruta": "a.txt", "contenido": "hola", "rama": "feat/modos-router"})
        self.assertFalse(err); self.assertTrue(o["readback_ok"]); self.assertEqual(o["commit"], "c0ffee")

    def test_readback_distinto_es_fallo(self):
        self.fake(self._rutas_escritura("OTRA COSA"))
        err, o = self.llamar("github_escribir", {"repo": "r", "ruta": "a.txt", "contenido": "hola", "rama": "feat/modos-router"})
        self.assertTrue(err); self.assertEqual(o["error"], "READBACK_NO_COINCIDE")

    def test_put_403_es_fallo(self):
        self.fake([(("GET", "contents"), (404, {})), (("PUT", "contents"), (403, {"message": "no"}))])
        err, o = self.llamar("github_escribir", {"repo": "r", "ruta": "a", "contenido": "x", "rama": "reorganizacion"})
        self.assertTrue(err); self.assertEqual(o["error"], "GITHUB_403")

    def test_red_caida_es_fallo(self):
        self.fake([(("GET", "contents"), OSError("sin red"))])
        err, o = self.llamar("github_leer", {"repo": "r", "ruta": "a"})
        self.assertTrue(err); self.assertEqual(o["error"], "RED")

    def test_sin_pat_es_fallo(self):
        del os.environ["RIU_GITHUB_PAT"]
        err, o = self.llamar("github_leer", {"repo": "r", "ruta": "a"})
        self.assertTrue(err); self.assertEqual(o["error"], "FALTA_GITHUB_PAT")

    def test_ruta_traversal(self):
        err, o = self.llamar("github_leer", {"repo": "r", "ruta": "../x"})
        self.assertTrue(err); self.assertEqual(o["error"], "RUTA_INVALIDA")

    def test_escritura_desactivada(self):
        os.environ["RIU_MCP_ESCRITURA"] = "0"
        err, o = self.llamar("github_escribir", {"repo": "r", "ruta": "a", "contenido": "x", "rama": "reorganizacion"})
        self.assertEqual(o["error"], "ESCRITURA_DESACTIVADA")


class Router(Base):
    def test_estado_ok_y_fallo(self):
        self.fake([(("GET", "/health"), (200, {"ok": True})), (("POST", "/plugins/puente_chat/call/status"), (200, {"status": "ok", "result": {"modelos": 7}}))])
        err, o = self.llamar("router_estado", {}); self.assertFalse(err); self.assertEqual(o["puente_chat"]["modelos"], 7)
        self.fake([(("GET", "/health"), (200, {})), (("POST", "status"), (503, {"detail": "plugin chat apagado"}))])
        err, o = self.llamar("router_estado", {}); self.assertTrue(err)

    def test_plugin_llamar_ruta_y_headers(self):
        f = self.fake([(("POST", "/plugins/hf_storage/call/ls"), (200, {"status": "ok", "result": [1]}))])
        err, o = self.llamar("plugin_llamar", {"plugin": "hf_storage", "accion": "ls", "payload": {"a": 1}})
        self.assertFalse(err); self.assertEqual(f.llamadas[0][3], {"a": 1}); self.assertEqual(f.llamadas[0][2]["X-API-Key"], CHAT)

    def test_plugin_llamar_bloqueos_e_invalidos(self):
        f = self.fake([])
        for a in ({"plugin": "banco", "accion": "get_keys"}, {"plugin": "../x", "accion": "a"}, {"plugin": "p", "accion": "a/b"}):
            err, o = self.llamar("plugin_llamar", a); self.assertTrue(err)
        self.assertEqual(f.llamadas, [])

    def test_status_no_ok_es_fallo(self):
        self.fake([(("POST", "/plugins/x/call/y"), (200, {"status": "error", "result": None}))])
        err, o = self.llamar("plugin_llamar", {"plugin": "x", "accion": "y"}); self.assertTrue(err); self.assertEqual(o["error"], "PLUGIN_NO_OK")

    def test_chat_enviar_y_ver_proceso(self):
        f = self.fake([(("POST", "call/chat_async"), (200, {"status": "ok", "result": {"estado": "procesando", "proceso_id": "p1"}})),
                       (("POST", "call/resultado"), (200, {"status": "ok", "result": {"choices": [{"message": {"content": "OK"}}]}}))])
        err, o = self.llamar("chat_enviar", {"model": "nv-kimi-k3", "mensaje": "hola"}); self.assertFalse(err); self.assertEqual(o["proceso_id"], "p1")
        self.assertEqual(f.llamadas[0][3]["model"], "nv-kimi-k3")
        err, o = self.llamar("ver_proceso", {"proceso_id": "p1"}); self.assertTrue(o["terminado"])

    def test_probar_modelo_pass_pendiente_fallo(self):
        n = {"i": 0}
        def res(_):
            n["i"] += 1
            return (200, {"status": "ok", "result": ({"estado": "procesando"} if n["i"] < 3 else {"choices": [{"message": {"content": "OK"}}]})})
        self.fake([(("POST", "call/chat_async"), (200, {"status": "ok", "result": {"proceso_id": "p"}})), (("POST", "call/resultado"), res)])
        o = tools.probar_modelo({"model": "m", "espera_s": 0}, dormir=lambda s: None); self.assertEqual(o["veredicto"], "PASS")
        self.fake([(("POST", "call/chat_async"), (200, {"status": "ok", "result": {"proceso_id": "p"}})), (("POST", "call/resultado"), (200, {"status": "ok", "result": {"estado": "procesando"}}))])
        o = tools.probar_modelo({"model": "m", "intentos": 2}, dormir=lambda s: None); self.assertEqual(o["veredicto"], "PENDIENTE"); self.assertFalse(o["ok"])
        self.fake([(("POST", "call/chat_async"), (500, {"detail": "x"}))])
        o = tools.probar_modelo({"model": "m"}, dormir=lambda s: None); self.assertEqual(o["veredicto"], "FALLO")


class Secretos(Base):
    def test_secretos_no_salen(self):
        self.fake([(("GET", "contents"), (500, "boom " + PAT + " " + KEY + " " + CHAT))])
        st, r = server.handle_http({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "github_leer", "arguments": {"repo": "r", "ruta": "a"}}}, {"X-API-Key": KEY}, {})
        txt = json.dumps(r)
        for s in (PAT, KEY, CHAT): self.assertNotIn(s, txt)

    def test_codigo_sin_secretos_ni_url_con_key(self):
        d = os.path.dirname(os.path.abspath(__file__))
        for f in os.listdir(d):
            if f.endswith((".py", ".md")) and f != "test_mcp.py":
                t = open(os.path.join(d, f), encoding="utf-8").read()
                self.assertNotIn("?key=" + "x", t)
                for pat in ("ghp_", "github_pat_", "hf_" + "A", "sk-"):
                    self.assertNotIn(pat, t, f)

    def test_no_importa_plugins(self):
        d = os.path.dirname(os.path.abspath(__file__))
        for f in ("config.py", "transport.py", "tools.py", "server.py"):
            t = open(os.path.join(d, f), encoding="utf-8").read()
            self.assertNotRegex(t, r"(?m)^\s*(from|import)\s+plugins")


if __name__ == "__main__":
    unittest.main(verbosity=2)
