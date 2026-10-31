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
