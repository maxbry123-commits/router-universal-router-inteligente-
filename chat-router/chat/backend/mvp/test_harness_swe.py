"""El Harness atiende SWE CODE free / SWEN CODE por el router propio (el bridge): los ids SWE van al bridge y, si el Router MVP cae, el Harness sigue con modelos locales (sin herramientas)."""
import json, os, sys, threading, unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from plugins.deepseek_harness import server as h

MSGS = [{"role": "user", "content": "hola"}]


def bridge(texto="desde el bridge", codigo=200):
    vistos = []
    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            vistos.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            self.send_response(codigo); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps({"modelo_usado": "web-qwen38max", "choices": [{"message": {"role": "assistant", "content": texto}, "finish_reason": "stop"}]}).encode())
        def log_message(self, *a): pass
    s = HTTPServer(("127.0.0.1", 0), H); threading.Thread(target=s.serve_forever, daemon=True).start()
    return s, "http://127.0.0.1:%d" % s.server_port, vistos


class HarnessSwe(unittest.TestCase):
    def test_un_modelo_swe_va_al_bridge_y_no_al_router_mvp(self):
        s, url, vistos = bridge()
        llamadas = []
        def router(plugin, accion, datos=None, timeout=0):
            llamadas.append((plugin, accion)); return {"result": {"tools": []}}
        with patch.dict(os.environ, {"RIU_SWE_BRIDGE_URL": url}), patch.object(h, "llamar", router):
            r = h.llm({"modelo": "web-qwen38max", "messages": MSGS})
        s.shutdown()
        self.assertEqual(r["texto"], "desde el bridge"); self.assertEqual(r["modelo_respuesta"], "web-qwen38max")
        self.assertEqual(vistos[0]["model"], "web-qwen38max"); self.assertNotIn(("fichas_qwen", "llm"), llamadas)

    def test_con_el_router_mvp_caido_sigue_con_un_modelo_local_sin_herramientas(self):
        s, url, vistos = bridge("respuesta local")
        with patch.dict(os.environ, {"RIU_SWE_BRIDGE_URL": url}), patch.object(h, "llamar", lambda *a, **k: {"error": "caido", "status": "degraded"}):
            r = h.llm({"modelo": "qwen3.8-max", "messages": MSGS})
        s.shutdown()
        self.assertEqual(r["texto"], "respuesta local"); self.assertEqual(vistos[0]["model"], "lfm2.5-350m"); self.assertEqual(r["tool_calls"], [])

    def test_sin_bridge_configurado_el_router_caido_sigue_fallando_igual(self):
        with patch.dict(os.environ, {"RIU_SWE_BRIDGE_URL": ""}), patch.object(h, "llamar", lambda *a, **k: {"error": "caido", "status": "degraded"}):
            with self.assertRaises(RuntimeError):
                h.llm({"modelo": "qwen3.8-max", "messages": MSGS})

    def test_sin_variable_el_bridge_es_el_del_space_y_vacia_lo_desactiva(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("RIU_SWE_BRIDGE_URL", None)
            self.assertEqual(h._bridge_url(), "http://127.0.0.1:7870")
        with patch.dict(os.environ, {"RIU_SWE_BRIDGE_URL": ""}):
            self.assertEqual(h._bridge_url(), "")

    def test_la_tarea_del_chat_viaja_al_bridge_como_conv_id_para_retomar_y_guardar_memoria(self):
        s, url, vistos = bridge()
        with patch.dict(os.environ, {"RIU_SWE_BRIDGE_URL": url}), patch.object(h, "llamar", lambda *a, **k: {"result": {"tools": []}}):
            h.llm({"modelo": "web-qwen38max", "messages": MSGS, "tarea_id": "p-rq-abc123"})
        s.shutdown()
        self.assertEqual(vistos[0]["conv_id"], "p-rq-abc123")

    def test_las_tools_llegan_al_modelo_local_y_sus_tool_calls_vuelven_al_bucle_del_harness(self):
        tools = [{"type": "function", "function": {"name": "github_leer", "parameters": {"type": "object"}}}]
        llamada = {"id": "c1", "type": "function", "function": {"name": "github_leer", "arguments": "{}"}}
        vistos = []
        class H(BaseHTTPRequestHandler):
            def do_POST(self):
                vistos.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
                self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
                self.wfile.write(json.dumps({"choices": [{"finish_reason": "tool_calls", "message": {"role": "assistant", "content": None, "tool_calls": [llamada]}}]}).encode())
            def log_message(self, *a): pass
        s = HTTPServer(("127.0.0.1", 0), H); threading.Thread(target=s.serve_forever, daemon=True).start()
        with patch.dict(os.environ, {"RIU_SWE_BRIDGE_URL": "http://127.0.0.1:%d" % s.server_port}):
            r = h._bridge_chat(MSGS, "lfm2.5-350m", "t1", {"tools": tools, "tool_choice": "auto"})
        s.shutdown()
        self.assertEqual(vistos[0]["tools"], tools); self.assertEqual(r["tool_calls"][0]["function"]["name"], "github_leer")
        self.assertEqual(r["finish_reason"], "tool_calls")

    def test_el_fallback_local_solo_si_el_router_esta_caido_no_por_cuota_ni_errores_del_modelo(self):
        s, url, vistos = bridge("respuesta local")
        def router(codigo):
            def f(plugin, accion, datos=None, timeout=0):
                if accion == "mcp": return {"result": {"tools": [{"name": "github_leer", "description": "d", "inputSchema": {"type": "object"}}]}}
                return {"error": codigo, "status": "degraded"}
            return f
        with patch.dict(os.environ, {"RIU_SWE_BRIDGE_URL": url, "RIU_ROUTER_URL": "http://127.0.0.1:1"}):
            with patch.object(h, "llamar", router("HTTP 429")):
                with self.assertRaises(RuntimeError):
                    h.llm({"modelo": "qwen3.8-max", "messages": MSGS})
            self.assertEqual(vistos, [], "una cuota agotada no se disfraza de respuesta de un modelo local")
            with patch.object(h, "llamar", router("URLError")):
                r = h.llm({"modelo": "qwen3.8-max", "messages": MSGS})
        s.shutdown()
        self.assertEqual(r["texto"], "respuesta local"); self.assertEqual(r["modelo_respuesta"], "web-qwen38max")

    def test_reanudar_con_acumulado_y_fallo_no_revienta_con_unbound(self):
        with patch.dict(os.environ, {"RIU_SWE_BRIDGE_URL": ""}), patch.object(h, "llamar", lambda *a, **k: {"error": "URLError", "status": "degraded", "result": {"tools": []}}):
            with self.assertRaises(RuntimeError):
                h.llm({"modelo": "qwen3.8-max", "messages": MSGS, "acumulado": "previo"})

    def test_la_url_del_bridge_se_valida_por_host_no_por_prefijo(self):
        for mala in ("http://127.0.0.1.evil.com:80", "http://localhost.evil.com", "http://127.0.0.1@evil.com", "http://ejemplo.com", "ftp://127.0.0.1"):
            with patch.dict(os.environ, {"RIU_SWE_BRIDGE_URL": mala}):
                self.assertEqual(h._bridge_url(), "", mala)
        for buena in ("http://127.0.0.1:7870", "http://localhost:7870", "https://bridge.ejemplo.com"):
            with patch.dict(os.environ, {"RIU_SWE_BRIDGE_URL": buena}):
                self.assertEqual(h._bridge_url(), buena)

    def test_respuesta_del_bridge_con_message_null_es_error_controlado(self):
        class H2(BaseHTTPRequestHandler):
            def do_POST(self):
                self.rfile.read(int(self.headers["Content-Length"])); self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
                self.wfile.write(json.dumps({"choices": [{"message": None}]}).encode())
            def log_message(self, *a): pass
        s = HTTPServer(("127.0.0.1", 0), H2); threading.Thread(target=s.serve_forever, daemon=True).start()
        with patch.dict(os.environ, {"RIU_SWE_BRIDGE_URL": "http://127.0.0.1:%d" % s.server_port}):
            with self.assertRaises(RuntimeError):
                h._bridge_chat(MSGS, "web-qwen38max")
        s.shutdown()

    def test_ids_swe(self):
        for m in ("web-qwen38max", "swecode-despliega", "hf-liquid-lfm25", "lfm2.5-350m"):
            self.assertTrue(h.es_swe(m), m)
        for m in ("qwen3.8-max", "glm-5.3", "groq/llama", None):
            self.assertFalse(h.es_swe(m), m)


if __name__ == "__main__":
    unittest.main()
