"""mini_router: si ningun slot HF responde, el paso cae a Groq y luego a NVIDIA (mismas claves del chat: GROQ_API_KEY, NVIDIA_API_KEY)."""
import json, os, threading, unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import patch
import mini_router


def servidor(codigo, texto):
    vistos = []
    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            vistos.append((self.path, self.headers.get("Authorization"), json.loads(self.rfile.read(int(self.headers["Content-Length"])))))
            self.send_response(codigo); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps({"choices": [{"message": {"content": texto}}]}).encode())
        def log_message(self, *a): pass
    s = HTTPServer(("127.0.0.1", 0), H); threading.Thread(target=s.serve_forever, daemon=True).start()
    return s, "http://127.0.0.1:%d" % s.server_port, vistos


class TestRespaldoExterno(unittest.TestCase):
    def tearDown(self): [s.shutdown() for s in getattr(self, "s", [])]

    def probar(self, groq, nvidia, env):
        sg, ug, vg = servidor(*groq); sn, un, vn = servidor(*nvidia); self.s = [sg, sn]
        with patch.dict(mini_router.URLS, {"S1": "http://127.0.0.1:9"}, clear=True), \
             patch.dict(mini_router.EXTERNOS, {"groq": (ug, "GROQ_API_KEY", "m-groq"), "nvidia": (un, "NVIDIA_API_KEY", "m-nv")}), \
             patch.dict(os.environ, env):
            return mini_router.llamar("lfm2.5-350m", [{"role": "user", "content": "hola"}]), vg, vn

    def test_si_los_slots_caen_responde_groq_con_su_clave(self):
        r, vg, vn = self.probar((200, "de groq"), (200, "de nvidia"), {"GROQ_API_KEY": "gsk-1", "NVIDIA_API_KEY": "nv-1"})
        self.assertEqual(r, "de groq"); self.assertEqual(vn, [])
        self.assertEqual(vg[0][1], "Bearer gsk-1"); self.assertEqual(vg[0][2]["model"], "m-groq")

    def test_si_groq_falla_responde_nvidia(self):
        r, vg, vn = self.probar((500, ""), (200, "de nvidia"), {"GROQ_API_KEY": "gsk-1", "NVIDIA_API_KEY": "nv-1"})
        self.assertEqual(r, "de nvidia"); self.assertEqual(len(vg), 1)

    def test_sin_claves_se_propaga_el_error_de_los_slots(self):
        with patch.dict(os.environ, {"GROQ_API_KEY": "", "NVIDIA_API_KEY": ""}):
            with self.assertRaises(Exception):
                self.probar((200, "x"), (200, "y"), {"GROQ_API_KEY": "", "NVIDIA_API_KEY": ""})


if __name__ == "__main__":
    unittest.main()
