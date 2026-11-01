"""Secretos solo atraviesan el relay HTTP administrativo; nunca se pasan a llm()."""
import unittest
from unittest.mock import patch
from plugins.deepseek_harness import server as h


class TestRelay(unittest.TestCase):
    def test_no_envia_llm_ni_tools(self):
        visto = []
        def router(plugin, accion, body, timeout=None):
            visto.append((plugin, accion, body))
            return {"ok": True, "proveedor": "groq", "cantidad": 1, "compatible": True}
        with patch.dict("os.environ", {"RIU_API_KEY": "FAKE-LOGIN"}), patch.object(h, "llamar", router), patch.object(h, "llm", side_effect=AssertionError("LLM no participa")):
            r = h.credenciales("anadir", {"proveedor": "groq", "secret": "gsk_FAKE_1234"}, x_api_key="FAKE-LOGIN")
        self.assertEqual(r["status"], "ok")
        self.assertEqual(visto[0][0:2], ("banco_proveedores", "anadir"))
        self.assertEqual(visto[0][2]["secret"], "gsk_FAKE_1234")
        self.assertNotIn("gsk_FAKE_1234", str(r))

    def test_rechaza_sin_login_sin_tocar_banco(self):
        with patch.dict("os.environ", {"RIU_API_KEY": "FAKE-LOGIN"}), patch.object(h, "llamar", side_effect=AssertionError("no debe llamar")):
            r = h.credenciales("anadir", {"secret": "gsk_FAKE_1234"}, x_api_key="OTRO")
        self.assertEqual(r.status_code, 401)

    def test_public_chat_key_is_accepted_as_access_control_not_model_key(self):
        visto = []
        def api(plugin, accion, cuerpo, timeout=None):
            visto.append((plugin, accion))
            return {"ok": True, "proveedores": [{"id": "openai", "cantidad": 1, "compatible": True}]}
        with patch.dict("os.environ", {"RIU_API_KEY": "FAKE-INTERNAL", "RIU_PUBLIC_CHAT_KEY": "FAKE-USER"}), patch.object(h, "llamar", api):
            r = h.credenciales("catalogo", {}, x_api_key="FAKE-USER")
        self.assertEqual(r["status"], "ok")
        self.assertEqual(visto, [("banco_proveedores", "catalogo")])


if __name__ == "__main__":
    unittest.main()
