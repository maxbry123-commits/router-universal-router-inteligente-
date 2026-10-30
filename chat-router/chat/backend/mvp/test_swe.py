"""SWE CODE / SWEN CODE free dentro del selector del chat: los ids web-*, swecode-* y los modelos locales HF salen por el bridge
o por la cola S1-S3; si no responden, cae a Groq, luego a NVIDIA y al final a HF local (mismo acceso que el chat, sin cablear nada nuevo)."""
import json, os, threading, unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import patch
from test_control import Base, CAB
from mvp import modelos, swe


def servidor(respuestas):
    """Bridge falso en loopback: respuestas = {ruta_modelo: (codigo, contenido)}; guarda lo que recibe."""
    vistos = []
    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            cuerpo = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            vistos.append(cuerpo)
            codigo, texto = respuestas.get(cuerpo["model"], (500, ""))
            self.send_response(codigo); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps({"model": "modelo_usado:" + cuerpo["model"], "choices": [{"message": {"role": "assistant", "content": texto}, "finish_reason": "stop"}]}).encode())
        def log_message(self, *a): pass
    s = HTTPServer(("127.0.0.1", 0), H); threading.Thread(target=s.serve_forever, daemon=True).start()
    return s, "http://127.0.0.1:%d" % s.server_port, vistos


class TestSwe(Base):
    def test_ids_swe_son_validos_y_el_resto_no_cambia(self):
        for m in ("web-qwen38max", "swecode-despliega", "lfm2.5-350m", "hf-liquid-lfm25", "swe-codex-qwen25-15b"):
            self.assertEqual(modelos.validar(m), m)
        with self.assertRaises(ValueError):
            modelos.validar("web-inventado")

    def test_el_catalogo_del_router_incluye_los_modelos_swe(self):
        ids = [m["model_id"] for m in self.client.get("/chat/providers/qwen/models", headers=CAB).json()["models"]]
        for m in ("web-qwen38max", "web-qwen37max", "web-dsv4-flash", "swecode-consulta", "swecode-despliega", "hf-liquid-lfm25"):
            self.assertIn(m, ids)
        self.assertIn("qwen3.8-max", ids)  # los demas modelos del selector siguen

    def test_web_va_al_bridge_con_el_modelo_y_devuelve_el_modelo_usado(self):
        s, url, vistos = servidor({"web-qwen38max": (200, "hola desde la web")})
        with patch.dict(os.environ, {"WEB_BRIDGE_URL": url}):
            r = self.client.post("/chat", headers=CAB, json={"modelo": "web-qwen38max", "mensajes": [{"role": "user", "content": "hola"}]})
        s.shutdown()
        self.assertEqual(r.status_code, 200, r.text); self.assertEqual(r.json()["texto"], "hola desde la web")
        self.assertEqual(vistos[0]["model"], "web-qwen38max"); self.assertEqual(r.json()["modelo_respuesta"], "modelo_usado:web-qwen38max")

    def test_alias_del_selector_local_van_a_la_cola_hf_con_el_id_real(self):
        s, url, vistos = servidor({"lfm2.5-350m": (200, "liquid")})
        with patch.dict(os.environ, {"SWECODE_URL_S1": url}):
            r = self.client.post("/chat", headers=CAB, json={"modelo": "hf-liquid-lfm25", "mensajes": [{"role": "user", "content": "hola"}]})
        s.shutdown()
        self.assertEqual(r.json()["texto"], "liquid"); self.assertEqual(vistos[0]["model"], "lfm2.5-350m")

    def test_la_cola_salta_al_siguiente_servidor_si_el_primero_no_responde(self):
        s, url, vistos = servidor({"lfm2.5-350m": (200, "desde S2")})
        with patch.dict(os.environ, {"SWECODE_URL_S1": "http://127.0.0.1:9", "SWECODE_URL_S2": url}):
            r = self.client.post("/chat", headers=CAB, json={"modelo": "lfm2.5-350m", "mensajes": [{"role": "user", "content": "hola"}]})
        s.shutdown()
        self.assertEqual(r.json()["texto"], "desde S2")

    def test_si_la_web_falla_cae_a_groq_y_luego_a_nvidia_y_al_final_a_hf_local(self):
        sw, web, _ = servidor({})  # el bridge devuelve 500
        sl, local, vl = servidor({"lfm2.5-350m": (200, "respaldo HF")})
        llamadas = []
        def externo(mensajes, modelo, banco=None, opciones=None):
            llamadas.append(modelo)
            raise RuntimeError("sin respuesta")
        self.banco.datos.update({"GROQ_API_KEY": "gsk-x", "NVIDIA_API_KEY": "nvapi-x"})
        env = {"WEB_BRIDGE_URL": web, "SWECODE_URL_S1": local}
        with patch.dict(os.environ, env), patch("mvp.externos.llamar", externo):
            r = self.client.post("/chat", headers=CAB, json={"modelo": "web-qwen38max", "mensajes": [{"role": "user", "content": "hola"}]})
        sw.shutdown(); sl.shutdown()
        self.assertEqual(r.json()["texto"], "respaldo HF")
        self.assertEqual([m.split("/")[0] for m in llamadas], ["groq", "nvidia"])
        self.assertEqual(r.json()["via_respaldo"], "hf-local")

    def test_si_groq_responde_no_se_llega_a_nvidia(self):
        sw, web, _ = servidor({"web-qwen38max": (200, "")})  # contenido vacio = fallo
        self.banco.datos.update({"GROQ_API_KEY": "gsk-x", "NVIDIA_API_KEY": "nvapi-x"})
        llamadas = []
        def externo(mensajes, modelo, banco=None, opciones=None):
            llamadas.append(modelo)
            return {"texto": "respuesta groq", "tool_calls": [], "finish_reason": "stop", "modelo_respuesta": modelo}
        with patch.dict(os.environ, {"WEB_BRIDGE_URL": web}), patch("mvp.externos.llamar", externo):
            r = self.client.post("/chat", headers=CAB, json={"modelo": "web-qwen38max", "mensajes": [{"role": "user", "content": "hola"}]})
        sw.shutdown()
        self.assertEqual(r.json()["texto"], "respuesta groq"); self.assertEqual(len(llamadas), 1); self.assertEqual(r.json()["via_respaldo"], "groq")

    def test_url_no_https_ni_loopback_se_rechaza(self):
        with self.assertRaises(ValueError):
            swe._base("http://ejemplo.com")


if __name__ == "__main__":
    unittest.main()
