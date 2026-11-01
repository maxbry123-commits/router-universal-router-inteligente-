"""A5-proveedores sobre mini_router: R8 (tabla unica de timeouts) y 186 (sin truncamientos silenciosos de documentos). Sin red ni claves reales."""
import json, os, tempfile, unittest
from unittest.mock import patch
import mini_router


class TestTimeoutsUnicos(unittest.TestCase):
    def test_misma_tabla_que_compute_y_nunca_supera_el_plazo_del_bridge(self):
        from mvp import compute
        for mid, t in compute.TIMEOUTS_MODELO_S.items():
            prov, modelo = mid.split("/", 1)
            self.assertEqual(mini_router.TIMEOUTS_MODELO_S[modelo], t, mid)
        self.assertEqual((mini_router.TIMEOUTS_EXTERNOS["groq"], mini_router.TIMEOUTS_EXTERNOS["nvidia"]), (60, 90))
        for v in mini_router.TIMEOUTS_EXTERNOS.values():
            self.assertLessEqual(v, mini_router._plazo_s())  # 100 s por defecto: ya no hay un 120 s por encima del plazo

    def test_la_peticion_usa_el_timeout_del_modelo_recortado_al_plazo(self):
        vistos = []
        def completar(base, cab, modelo, mensajes, timeout, previo="", presupuesto=None):
            vistos.append((modelo, timeout)); return "ok"
        env = {"NVIDIA_API_KEY": "n1", "GROQ_API_KEY": "", "BRIDGE_DEADLINE_MS": "1000000"}
        with patch.dict(mini_router.EXTERNOS, {"groq": ("http://g/v1", "GROQ_API_KEY", "qwen/qwen3.8-27b"), "nvidia": ("http://n/v1", "NVIDIA_API_KEY", "meta/muse-glimmer-30b")}), \
             patch.dict(os.environ, env), patch.object(mini_router, "_completar", completar):
            mini_router._externo([], None)
        self.assertEqual(vistos, [("meta/muse-glimmer-30b", 180)])  # la tabla manda; el plazo (aqui holgado) solo recorta
        vistos.clear()
        with patch.dict(mini_router.EXTERNOS, {"groq": ("http://g/v1", "GROQ_API_KEY", "qwen/qwen3.8-27b"), "nvidia": ("http://n/v1", "NVIDIA_API_KEY", "meta/muse-glimmer-30b")}), \
             patch.dict(os.environ, {**env, "BRIDGE_DEADLINE_MS": "30000"}), patch.object(mini_router, "_completar", completar):
            mini_router._externo([], None)
        self.assertLessEqual(vistos[0][1], 30)  # recortado a lo que queda del plazo


class TestDocumentosSinRecorteSilencioso(unittest.TestCase):
    def test_un_documento_largo_se_marca_como_truncado_en_el_texto_y_en_el_aviso(self):
        with tempfile.TemporaryDirectory() as d:
            ruta = os.path.join(d, "grande.txt"); open(ruta, "w", encoding="utf-8").write("x" * 150000)
            texto, aviso = mini_router._leer_doc(ruta)
            self.assertIn("TRUNCADO", texto); self.assertEqual(aviso["caracteres_originales"], 150000); self.assertEqual(aviso["caracteres_enviados"], 100000)
            corto = os.path.join(d, "corto.txt"); open(corto, "w", encoding="utf-8").write("hola")
            self.assertEqual(mini_router._leer_doc(corto), ("hola", None))

    def test_main_incluye_los_avisos_en_la_salida(self):
        import io, sys, contextlib
        with tempfile.TemporaryDirectory() as d:
            ruta = os.path.join(d, "grande.txt"); open(ruta, "w", encoding="utf-8").write("y" * 120000)
            salida = io.StringIO()
            with patch.object(sys, "argv", ["mini_router.py", "--doc", ruta, "objetivo"]), patch.object(mini_router, "correr", lambda o, p, tarea_id=None: {"estado": "DONE", "objetivo_recibido": o}), contextlib.redirect_stdout(salida):
                mini_router.main()
            r = json.loads(salida.getvalue())
            self.assertEqual(r["avisos"][0]["documento"], "grande.txt"); self.assertIn("TRUNCADO", r["objetivo_recibido"])


if __name__ == "__main__":
    unittest.main()
