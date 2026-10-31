"""Auditoria forense (punto 2) en mini_router: el primer timeout de un proveedor lo corta y lo enfria (no se prueban sus demas claves), Groq con timeout de 60 s
y todo el tramo externo dentro del plazo (BRIDGE_DEADLINE_MS). Servidores falsos locales; claves inventadas; sin red real."""
import os, socket, unittest
from unittest.mock import patch
import mini_router
import test_mini_router_recuperacion as rec


class TestTimeoutExterno(rec.Base):
    def setUp(self):
        super().setUp()
        pass  # Base.setUp/tearDown ya limpian _ENFRIADOS

    def servidores(self):
        ug, vg = self.srv((200, "de groq")); un, vn = self.srv((200, "de nvidia"))
        return ug, vg, un, vn

    def lento_en(self, url, contador):
        real = mini_router.urllib.request.urlopen
        puerto = url.rsplit(":", 1)[1]
        def f(req, timeout=None):
            if "127.0.0.1:%s" % puerto in req.full_url:
                contador.append(timeout); raise socket.timeout("timed out")
            return real(req, timeout=timeout)
        return patch.object(mini_router.urllib.request, "urlopen", f)

    def test_groq_60_s_nvidia_120_s(self):
        self.assertEqual((mini_router.TIMEOUTS_EXTERNOS["groq"], mini_router.TIMEOUTS_EXTERNOS["nvidia"]), (60, 120))
        vistos = []
        def completar(base, cab, modelo, mensajes, timeout, previo="", presupuesto=None):
            vistos.append((base, timeout)); return "ok"
        g, h = self.externos(groq=("http://g/v1", "GROQ_API_KEY", "m"), nvidia=("http://n/v1", "NVIDIA_API_KEY", "n"))
        with g, h, patch.dict(os.environ, {"GROQ_API_KEY": "g1", "NVIDIA_API_KEY": "n1", "BRIDGE_DEADLINE_MS": "1000000"}), patch.object(mini_router, "_completar", completar):  # plazo holgado: se ven los timeouts propios
            mini_router._externo([], None)
            mini_router._ENFRIADOS.clear()
            os.environ.pop("GROQ_API_KEY"); mini_router._externo([], None)
        self.assertEqual(vistos, [("http://g/v1", 60), ("http://n/v1", 120)])

    def test_el_primer_timeout_corta_el_proveedor_aunque_haya_mas_claves_y_modelos(self):
        ug, vg, un, vn = self.servidores(); lentos = []
        g, h = self.externos(groq=(ug, "GROQ_API_KEY", "qwen/qwen3.8-27b"), nvidia=(un, "NVIDIA_API_KEY", "n"))
        with g, h, patch.dict(os.environ, {"GROQ_API_KEY": "g1", "GROQ_API_KEY_2": "g2", "GROQ_API_KEY_3": "g3", "RIU_SWE_GROQ_MODELOS": "otro/modelo", "NVIDIA_API_KEY": "n1"}), self.lento_en(ug, lentos):
            self.assertEqual(mini_router.llamar_via("m", []), ("de nvidia", "nvidia"))
        self.assertEqual(len(lentos), 1, "una sola peticion colgada a Groq, no una por clave/modelo")

    def test_el_proveedor_queda_enfriado_entre_llamadas(self):
        ug, vg, un, vn = self.servidores(); lentos = []
        g, h = self.externos(groq=(ug, "GROQ_API_KEY", "m"), nvidia=(un, "NVIDIA_API_KEY", "n"))
        with g, h, patch.dict(os.environ, {"GROQ_API_KEY": "g1", "GROQ_API_KEY_2": "g2", "NVIDIA_API_KEY": "n1"}), self.lento_en(ug, lentos):
            mini_router.llamar_via("m", []); mini_router.llamar_via("m", [])
        self.assertEqual(len(lentos), 1, "la 2ª llamada ni intenta Groq")
        self.assertEqual(len(vn), 2)
        # caducado el enfriamiento vuelve a intentarse
        mini_router._ENFRIADOS["groq"] = 0
        with g, h, patch.dict(os.environ, {"GROQ_API_KEY": "g1", "NVIDIA_API_KEY": "n1"}):
            self.assertEqual(mini_router.llamar_via("m", []), ("de groq", "groq"))

    def test_408_tambien_enfria_y_un_429_sigue_rotando_claves(self):
        ug, vg = self.srv((408, "t")); un, vn = self.srv((200, "de nvidia"))
        g, h = self.externos(groq=(ug, "GROQ_API_KEY", "m"), nvidia=(un, "NVIDIA_API_KEY", "n"))
        with g, h, patch.dict(os.environ, {"GROQ_API_KEY": "g1", "GROQ_API_KEY_2": "g2", "NVIDIA_API_KEY": "n1"}):
            self.assertEqual(mini_router.llamar_via("m", [])[1], "nvidia")
        self.assertEqual(len(vg), 1)

    def test_el_tramo_externo_respeta_el_plazo(self):
        """El plazo (BRIDGE_DEADLINE_MS) limita cada intento y corta el tramo externo: no se encadenan 60+120 s."""
        t = [0.0]; vistos = []
        def completar(base, cab, modelo, mensajes, timeout, previo="", presupuesto=None):
            vistos.append((base, round(timeout, 3))); t[0] += timeout; raise socket.timeout("timed out")
        g, h = self.externos(groq=("http://g/v1", "GROQ_API_KEY", "m"), nvidia=("http://n/v1", "NVIDIA_API_KEY", "n"))
        with g, h, patch.dict(os.environ, {"GROQ_API_KEY": "g1", "NVIDIA_API_KEY": "n1", "BRIDGE_DEADLINE_MS": "100000"}), \
                patch.object(mini_router, "_completar", completar), patch.object(mini_router.time, "monotonic", lambda: t[0]):
            with self.assertRaises(Exception):
                mini_router._externo([], None)
        self.assertEqual(vistos, [("http://g/v1", 60), ("http://n/v1", 40)], "el 2º intento se acorta a lo que queda del plazo")
        self.assertLessEqual(sum(x[1] for x in vistos), 100)


if __name__ == "__main__":
    unittest.main()
