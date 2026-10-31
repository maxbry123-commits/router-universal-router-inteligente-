"""mini_router: recuperacion del ultimo paso confirmado, rotacion de claves/proveedores y continuacion por length. Sin red real."""
import importlib, json, os, socket, tempfile, threading, unittest, urllib.error
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import patch
import mini_router

PASOS = [{"modelo": "m", "nodo": n, "agente": "a", "entrada": "x", "salida": "y"} for n in ("escribe", "revisa", "ejecuta")]
SECRETO = "gsk_" + "Z" * 30


def servidor_guion(respuestas):
    """Cada POST consume una respuesta (codigo, dict-o-texto); la ultima se repite."""
    vistos, cola = [], list(respuestas)
    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            vistos.append((self.headers.get("Authorization"), json.loads(self.rfile.read(int(self.headers["Content-Length"])))))
            codigo, cuerpo = cola.pop(0) if len(cola) > 1 else cola[0]
            self.send_response(codigo); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(cuerpo if isinstance(cuerpo, dict) else {"choices": [{"message": {"content": cuerpo}, "finish_reason": "stop"}]}).encode())
        def log_message(self, *a): pass
    s = HTTPServer(("127.0.0.1", 0), H); threading.Thread(target=s.serve_forever, daemon=True).start()
    return s, "http://127.0.0.1:%d" % s.server_port, vistos


def resp(texto, fin="stop"): return {"choices": [{"message": {"content": texto}, "finish_reason": fin}]}


class Base(unittest.TestCase):
    def setUp(self):
        self.s, self.tmp = [], tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {"RIU_MINI_STATE": self.tmp.name}); self.env.start()
    def tearDown(self):
        self.env.stop(); self.tmp.cleanup(); [s.shutdown() for s in self.s]
    def externos(self, **kw):  # kw: via=(url, var, modelo)
        return patch.dict(mini_router.EXTERNOS, kw, clear=True), patch.dict(mini_router.URLS, {"S1": "http://127.0.0.1:9"}, clear=True)
    def srv(self, *r):
        s, u, v = servidor_guion(r); self.s.append(s); return u, v


class TestRecuperacion(Base):
    def llamadas(self, falla_en=None):
        calls = []
        def fake(modelo, mensajes, servidor="S1"):
            calls.append(mensajes[0]["content"])
            if falla_en is not None and len(calls) == falla_en: raise RuntimeError("caida")
            return "salida%d" % len(calls), "groq"
        return calls, fake

    def test_reanuda_tras_reinicio_sin_repetir_etapas_done(self):
        calls, fake = self.llamadas(falla_en=2)
        with patch.object(mini_router, "llamar_via", fake):
            r1 = mini_router.correr("obj", PASOS, tarea_id="t-1")
        self.assertEqual((r1["estado"], r1["paso_fallido"]), ("FAIL", "revisa")); self.assertEqual(len(calls), 2)
        importlib.reload(mini_router)  # reinicio simulado: solo queda lo escrito en disco
        calls2, fake2 = self.llamadas()
        with patch.object(mini_router, "llamar_via", fake2):
            r2 = mini_router.correr("obj", PASOS, tarea_id="t-1")
        self.assertEqual(r2["estado"], "DONE"); self.assertEqual(len(calls2), 2, "escribe (DONE) no se repite")
        self.assertIn("salida1", calls2[0], "revisa recibe la salida confirmada de escribe")
        reanudados = [x["nodo"] for x in r2["recibos"] if x.get("reanudado")]
        self.assertEqual(reanudados, ["escribe"])

    def test_tarea_terminada_no_llama_a_nadie(self):
        calls, fake = self.llamadas()
        with patch.object(mini_router, "llamar_via", fake):
            r1 = mini_router.correr("obj", PASOS, tarea_id="t-2")
            r2 = mini_router.correr("obj", PASOS, tarea_id="t-2")
        self.assertEqual(len(calls), 3); self.assertEqual(r2["resultado"], r1["resultado"]); self.assertEqual(r2["estado"], "DONE")

    def test_objetivo_distinto_con_mismo_tarea_id_empieza_de_cero(self):
        calls, fake = self.llamadas()
        with patch.object(mini_router, "llamar_via", fake):
            mini_router.correr("obj A", PASOS, tarea_id="t-3"); mini_router.correr("obj B", PASOS, tarea_id="t-3")
        self.assertEqual(len(calls), 6)

    def test_sin_tarea_id_no_persiste_nada(self):
        calls, fake = self.llamadas()
        with patch.object(mini_router, "llamar_via", fake):
            mini_router.correr("obj", PASOS)
        self.assertEqual(os.listdir(self.tmp.name), [])

    def test_estado_sin_claves(self):
        u, v = self.srv((200, resp("eco de la clave " + SECRETO + " Bearer abcdefgh12345678")))
        g, h = self.externos(groq=(u, "GROQ_API_KEY", "m"))
        with g, h, patch.dict(os.environ, {"GROQ_API_KEY": SECRETO}):
            r = mini_router.correr("obj", PASOS[:1], tarea_id="t-4")
        self.assertEqual(r["estado"], "DONE")
        crudo = open(os.path.join(self.tmp.name, "t-4.json"), encoding="utf-8").read()
        self.assertNotIn(SECRETO, crudo); self.assertNotIn("abcdefgh12345678", crudo)
        d = json.loads(crudo); self.assertEqual(d["estado"], "DONE")
        paso = d["pasos"]["0:escribe"]; self.assertEqual((paso["estado"], paso["proveedor"], paso["modelo"]), ("DONE", "groq", "m"))

    def test_escritura_atomica(self):
        calls, fake = self.llamadas()
        with patch.object(mini_router, "llamar_via", fake):
            mini_router.correr("obj", PASOS[:1], tarea_id="t-5")
            antes = open(os.path.join(self.tmp.name, "t-5.json")).read()
            with patch("os.replace", side_effect=OSError("corte")):
                with self.assertRaises(OSError):
                    mini_router._guardar_estado("t-5", {"estado": "X"})
        self.assertEqual(open(os.path.join(self.tmp.name, "t-5.json")).read(), antes)
        self.assertEqual([f for f in os.listdir(self.tmp.name) if not f.endswith(".json")], [])

    def test_tarea_id_se_sanea_y_dir_sigue_a_bridge_state_dir(self):
        calls, fake = self.llamadas()
        with patch.object(mini_router, "llamar_via", fake):
            mini_router.correr("obj", PASOS[:1], tarea_id="../../x")
        self.assertEqual(len(os.listdir(self.tmp.name)), 1)
        self.assertFalse(os.path.exists(os.path.join(os.path.dirname(self.tmp.name), "x.json")))
        with patch.dict(os.environ, {"RIU_MINI_STATE": "", "BRIDGE_STATE_DIR": "/data/estado"}):
            self.assertEqual(mini_router._estado_dir(), "/data/estado/mini_router")


class TestRotacion(Base):
    def test_429_rota_claves_y_luego_pasa_a_nvidia(self):
        ug, vg = self.srv((429, "rate")); un, vn = self.srv((200, "de nvidia"))
        g, h = self.externos(groq=(ug, "GROQ_API_KEY", "qwen/qwen3.8-27b"), nvidia=(un, "NVIDIA_API_KEY", "nv-m"))
        with g, h, patch.dict(os.environ, {"GROQ_API_KEY": "g1", "GROQ_API_KEY_2": "g2", "NVIDIA_API_KEY": "n1"}):
            self.assertEqual(mini_router.llamar_via("m", []), ("de nvidia", "nvidia"))
        self.assertEqual([x[0] for x in vg], ["Bearer g1", "Bearer g2"]); self.assertEqual(vn[0][0], "Bearer n1")

    def test_402_y_timeout_tambien_cambian(self):
        ug, vg = self.srv((402, "pago")); un, vn = self.srv((200, "ok nv"))
        g, h = self.externos(groq=(ug, "GROQ_API_KEY", "m"), nvidia=(un, "NVIDIA_API_KEY", "n"))
        with g, h, patch.dict(os.environ, {"GROQ_API_KEY": "g1", "NVIDIA_API_KEY": "n1"}):
            self.assertEqual(mini_router.llamar_via("m", [])[1], "nvidia")
        real = mini_router.urllib.request.urlopen
        def lento(req, timeout=None):
            if "127.0.0.1:%s" % ug.rsplit(":", 1)[1] in req.full_url: raise socket.timeout("timed out")
            return real(req, timeout=timeout)
        g, h = self.externos(groq=(ug, "GROQ_API_KEY", "m"), nvidia=(un, "NVIDIA_API_KEY", "n"))
        with g, h, patch.dict(os.environ, {"GROQ_API_KEY": "g1", "NVIDIA_API_KEY": "n1"}), patch.object(mini_router.urllib.request, "urlopen", lento):
            self.assertEqual(mini_router.llamar_via("m", []), ("ok nv", "nvidia"))

    def test_modelos_objetivo_por_defecto_y_lista_por_env(self):
        self.assertEqual(mini_router.MODELOS_DEFECTO["groq"], "qwen/qwen3.8-27b")
        self.assertEqual(mini_router._modelos("nvidia", mini_router.MODELOS_DEFECTO["nvidia"]),
                         ["meta/muse-glimmer-30b", "nvidia/nemotron-3-super-120b-a12b"])
        with patch.dict(os.environ, {"RIU_SWE_NVIDIA_MODELOS": "minimaxai/minimax-m3.1-flash, deepseek-ai/deepseek-v4.1-flash"}):
            self.assertEqual(mini_router._modelos("nvidia", "x"), ["x", "minimaxai/minimax-m3.1-flash", "deepseek-ai/deepseek-v4.1-flash"])

    def test_modelo_rechazado_404_prueba_el_siguiente_modelo(self):
        un, vn = self.srv((404, "no existe"), (200, "con el segundo"))
        g, h = self.externos(nvidia=(un, "NVIDIA_API_KEY", "meta/muse-glimmer-30b"))
        with g, h, patch.dict(os.environ, {"NVIDIA_API_KEY": "n1", "NVIDIA_API_KEY_2": "n2"}):
            self.assertEqual(mini_router.llamar_via("m", [])[0], "con el segundo")
        self.assertEqual([x[1]["model"] for x in vn], ["meta/muse-glimmer-30b", "nvidia/nemotron-3-super-120b-a12b"])
        self.assertEqual(len(vn), 2, "un 404 no gasta la otra clave en el mismo modelo")


class TestLength(Base):
    def test_length_continua_y_concatena(self):
        u, v = self.srv((200, resp("uno ", "length")), (200, resp("dos ", "length")), (200, resp("tres", "stop")))
        g, h = self.externos(groq=(u, "GROQ_API_KEY", "m"))
        with g, h, patch.dict(os.environ, {"GROQ_API_KEY": "g1"}):
            self.assertEqual(mini_router.llamar_via("m", [{"role": "user", "content": "hola"}]), ("uno dos tres", "groq"))
        self.assertEqual(len(v), 3)
        msgs = v[1][1]["messages"]; self.assertEqual(msgs[1], {"role": "assistant", "content": "uno "}); self.assertEqual(msgs[-1]["role"], "user")

    def test_tope_de_8_continuaciones(self):
        u, v = self.srv((200, resp("x", "length")))
        g, h = self.externos(groq=(u, "GROQ_API_KEY", "m"))
        with g, h, patch.dict(os.environ, {"GROQ_API_KEY": "g1"}):
            texto, _ = mini_router.llamar_via("m", [])
        self.assertEqual(mini_router.MAX_CONTINUACIONES, 8); self.assertEqual(len(v), 9); self.assertEqual(texto, "x" * 9)

    def test_length_en_slot_hf_y_corte_a_mitad_conserva_lo_recibido(self):
        u, v = self.srv((200, resp("a", "length")), (200, resp("b", "stop")))
        with patch.dict(mini_router.URLS, {"S1": u}, clear=True):
            self.assertEqual(mini_router.llamar_via("m", []), ("ab", "hf-slot"))
        ug, vg = self.srv((200, resp("parte1 ", "length")), (429, "rate"))
        un, vn = self.srv((200, resp("parte2", "stop")))
        g, h = self.externos(groq=(ug, "GROQ_API_KEY", "m"), nvidia=(un, "NVIDIA_API_KEY", "n"))
        with g, h, patch.dict(os.environ, {"GROQ_API_KEY": "g1", "NVIDIA_API_KEY": "n1"}):
            self.assertEqual(mini_router.llamar_via("m", [{"role": "user", "content": "q"}]), ("parte1 parte2", "nvidia"))
        self.assertEqual(vn[0][1]["messages"][-2], {"role": "assistant", "content": "parte1 "})


if __name__ == "__main__":
    unittest.main()
