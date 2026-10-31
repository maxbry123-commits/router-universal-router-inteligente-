"""Un modelo EXTERNO pedido (groq/, nvidia/) con el Router MVP caido no cambia en silencio a lfm2.5-350m:
primero se intenta ese mismo modelo por el bridge y solo si eso falla se degrada a local, DICIENDOLO (aviso_modelo). Sin claves reales."""
import json, os, sys, threading, unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from plugins.deepseek_harness import server as h

MSGS = [{"role": "user", "content": "hola"}]


def bridge(falla_si=lambda modelo: False):
    vistos = []
    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            cuerpo = json.loads(self.rfile.read(int(self.headers["Content-Length"]))); vistos.append(cuerpo["model"])
            if falla_si(cuerpo["model"]):
                self.send_response(502); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(b'{"error":{"code":"RESPALDO_AGOTADO"}}'); return
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps({"modelo_usado": cuerpo["model"], "choices": [{"message": {"role": "assistant", "content": "responde " + cuerpo["model"]}, "finish_reason": "stop"}]}).encode())
        def log_message(self, *a): pass
    s = HTTPServer(("127.0.0.1", 0), H); threading.Thread(target=s.serve_forever, daemon=True).start()
    return s, "http://127.0.0.1:%d" % s.server_port, vistos


def router(codigo):
    def f(plugin, accion, datos=None, timeout=0):
        if accion == "mcp": return {"result": {"tools": [{"name": "github_leer", "description": "d", "inputSchema": {"type": "object"}}]}}
        return {"error": codigo, "status": "degraded"}
    return f


class ModeloExterno(unittest.TestCase):
    def llm(self, modelo, url, codigo="URLError"):
        with patch.dict(os.environ, {"RIU_SWE_BRIDGE_URL": url, "RIU_ROUTER_URL": "http://127.0.0.1:1"}), patch.object(h, "llamar", router(codigo)):
            return h.llm({"modelo": modelo, "messages": MSGS})

    def test_router_caido_y_modelo_externo_se_pide_por_el_bridge_con_ese_mismo_modelo(self):
        for modelo in ("nvidia/z-ai/glm-5.3", "groq/qwen/qwen3.8-27b"):
            s, url, vistos = bridge()
            r = self.llm(modelo, url); s.shutdown()
            self.assertEqual(vistos, [modelo]); self.assertEqual(r["modelo_respuesta"], modelo); self.assertEqual(r["modelo_solicitado"], modelo)
            self.assertEqual(r["texto"], "responde " + modelo); self.assertNotIn("aviso_modelo", r)

    def test_si_el_bridge_falla_con_ese_modelo_se_degrada_a_local_y_se_dice(self):
        s, url, vistos = bridge(falla_si=lambda m: m.startswith("nvidia/"))
        r = self.llm("nvidia/z-ai/glm-5.3", url); s.shutdown()
        self.assertEqual(vistos, ["nvidia/z-ai/glm-5.3", "lfm2.5-350m"])
        self.assertEqual(r["modelo_solicitado"], "nvidia/z-ai/glm-5.3"); self.assertEqual(r["modelo_respuesta"], "lfm2.5-350m")
        self.assertIn("nvidia/z-ai/glm-5.3", r["aviso_modelo"]); self.assertIn("lfm2.5-350m", r["aviso_modelo"])

    def test_si_tambien_falla_el_local_es_error_y_no_se_inventa_respuesta(self):
        s, url, vistos = bridge(falla_si=lambda m: True)
        with self.assertRaises(RuntimeError):
            self.llm("groq/qwen/qwen3.8-27b", url)
        s.shutdown()

    def test_una_cuota_o_error_del_modelo_en_el_router_no_dispara_el_bridge(self):
        s, url, vistos = bridge()
        with self.assertRaises(RuntimeError):
            self.llm("nvidia/z-ai/glm-5.3", url, codigo="HTTP 429")
        s.shutdown(); self.assertEqual(vistos, [])

    def test_modelo_no_externo_sigue_cayendo_a_local_pero_ahora_con_aviso(self):
        s, url, vistos = bridge()
        r = self.llm("qwen3.8-max", url); s.shutdown()
        self.assertEqual(vistos, ["lfm2.5-350m"]); self.assertEqual(r["modelo_respuesta"], "lfm2.5-350m"); self.assertIn("qwen3.8-max", r["aviso_modelo"])

    def test_con_el_router_vivo_el_modelo_externo_sigue_por_el_router(self):
        s, url, vistos = bridge()
        def llamar(plugin, accion, datos=None, timeout=0):
            if accion == "mcp": return {"result": {"tools": [{"name": "github_leer", "description": "d", "inputSchema": {"type": "object"}}]}}
            return {"texto": "del router", "tool_calls": [], "finish_reason": "stop", "modelo_respuesta": "nvidia/z-ai/glm-5.3"}
        with patch.dict(os.environ, {"RIU_SWE_BRIDGE_URL": url, "RIU_ROUTER_URL": "http://127.0.0.1:1"}), patch.object(h, "llamar", llamar):
            r = h.llm({"modelo": "nvidia/z-ai/glm-5.3", "messages": MSGS})
        s.shutdown(); self.assertEqual(vistos, []); self.assertEqual(r["texto"], "del router")

    def test_es_externo(self):
        for m in ("groq/qwen/qwen3.8-27b", "nvidia/z-ai/glm-5.3"): self.assertTrue(h.es_externo(m), m)
        for m in ("web-qwen38max", "lfm2.5-350m", "qwen3.8-max", "", None, "groqx/a"): self.assertFalse(h.es_externo(m), str(m))


if __name__ == "__main__":
    unittest.main()


class ClaveNoAscii(unittest.TestCase):
    """/invoke: una clave no ASCII (cabecera o esperada) es 401 sin revelar nada, nunca 500."""
    def test_clave_no_ascii_es_401(self):
        from fastapi.testclient import TestClient
        with patch.dict(os.environ, {"RIU_API_KEY": "clave-http-solo-prueba"}):
            c = TestClient(h.app)
            for cab in (b"cl\xe9ve", b"\xc3\xb1", "mala"):
                r = c.post("/invoke", json={"action": "status"}, headers={"X-API-Key": cab})
                self.assertEqual(r.status_code, 401, cab); self.assertEqual(r.json(), {"status": "error", "error": "clave de acceso invalida"})
            self.assertEqual(c.post("/invoke", json={"action": "status"}).status_code, 401)
        with patch.dict(os.environ, {"RIU_API_KEY": "clavé-esperada"}):
            c = TestClient(h.app)
            self.assertEqual(h.invoke({"action": "status"}, x_api_key="clavé-esperada")["status"], "ok")  # llamada directa: el TestClient reinterpreta los bytes de la cabecera
            self.assertEqual(h.invoke({"action": "status"}, x_api_key="clavé-otra").status_code, 401)


class SinRedireccion(unittest.TestCase):
    def test_el_bridge_no_sigue_redirecciones(self):
        robado = []
        class D(BaseHTTPRequestHandler):
            def do_POST(self): robado.append(1); self.send_response(200); self.end_headers(); self.wfile.write(b"{}")
            def log_message(self, *a): pass
        d = HTTPServer(("127.0.0.1", 0), D)
        class R(BaseHTTPRequestHandler):
            def do_POST(self):
                self.rfile.read(int(self.headers["Content-Length"])); self.send_response(307); self.send_header("Location", "http://127.0.0.1:%d/x" % d.server_port); self.end_headers()
            def log_message(self, *a): pass
        o = HTTPServer(("127.0.0.1", 0), R)
        for x in (d, o): threading.Thread(target=x.serve_forever, daemon=True).start()
        with patch.dict(os.environ, {"RIU_SWE_BRIDGE_URL": "http://127.0.0.1:%d" % o.server_port}):
            with self.assertRaises(RuntimeError):
                h._bridge_chat(MSGS, "web-qwen38max")
        for x in (d, o): x.shutdown()
        self.assertEqual(robado, [])


class CredencialAlBridge(unittest.TestCase):
    """El bridge exige credencial en toda ruta salvo /health: el Harness manda su clave de acceso en X-API-Key en cada llamada (claves ficticias)."""
    def _cabeceras(self, entorno):
        vistas = []
        class H(BaseHTTPRequestHandler):
            def do_POST(self):
                self.rfile.read(int(self.headers["Content-Length"])); vistas.append({k.lower(): v for k, v in self.headers.items()})
                self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
                self.wfile.write(json.dumps({"choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}]}).encode())
            def log_message(self, *a): pass
        s = HTTPServer(("127.0.0.1", 0), H); threading.Thread(target=s.serve_forever, daemon=True).start()
        limpio = {k: "" for k in h.ACCESO_BRIDGE + ("BRIDGE_TOKEN",)}
        with patch.dict(os.environ, {**limpio, "RIU_SWE_BRIDGE_URL": "http://127.0.0.1:%d" % s.server_port, **entorno}):
            h._bridge_chat(MSGS, "web-qwen38max")
        s.shutdown(); return vistas[0]

    def test_manda_x_api_key_con_la_clave_de_acceso_del_harness(self):
        self.assertEqual(self._cabeceras({"RIU_API_KEY": "clave-harness-ficticia"})["x-api-key"], "clave-harness-ficticia")

    def test_usa_otra_clave_de_acceso_si_no_hay_riu_api_key_y_bridge_token_va_aparte(self):
        c = self._cabeceras({"RIU_MCP_KEY": "clave-mcp-ficticia", "BRIDGE_TOKEN": "token-ficticio"})
        self.assertEqual(c["x-api-key"], "clave-mcp-ficticia"); self.assertEqual(c["x-bridge-key"], "token-ficticio")

    def test_sin_ninguna_credencial_no_inventa_cabeceras(self):
        c = self._cabeceras({}); self.assertNotIn("x-api-key", c); self.assertNotIn("x-bridge-key", c)

    def test_la_clave_no_aparece_en_los_errores(self):
        class R(BaseHTTPRequestHandler):
            def do_POST(self):
                self.rfile.read(int(self.headers["Content-Length"])); self.send_response(401); self.end_headers()
            def log_message(self, *a): pass
        s = HTTPServer(("127.0.0.1", 0), R); threading.Thread(target=s.serve_forever, daemon=True).start()
        with patch.dict(os.environ, {"RIU_API_KEY": "clave-harness-ficticia-secreta", "RIU_SWE_BRIDGE_URL": "http://127.0.0.1:%d" % s.server_port}):
            with self.assertRaises(RuntimeError) as cm:
                h._bridge_chat(MSGS, "web-qwen38max")
        s.shutdown(); self.assertNotIn("ficticia-secreta", str(cm.exception))
