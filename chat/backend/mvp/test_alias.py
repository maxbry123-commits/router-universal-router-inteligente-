"""Nombres antiguos de modelo (ficha-qwen38max, qw-glm-5-3, dsv4pro…) se traducen al id del catálogo en HTTP y MCP."""
import os, unittest
from unittest.mock import patch
from mvp import modelos


class TestAlias(unittest.TestCase):
    def setUp(self):
        self.p = patch.dict(os.environ, {"MVP_PLAN": "personal"}); self.p.start()
    def tearDown(self):
        self.p.stop()

    def test_alias_antiguos(self):
        for viejo, nuevo in [("ficha-qwen38max", "qwen3.8-max"), ("ficha-qwen37plus", "qwen3.7-plus"), ("qw-glm-5-3", "glm-5.3"), ("ficha-glm52", "glm-5.2"),
                             ("ficha-dsv4pro", "deepseek-v4-pro"), ("ficha-dsv4pro0813", "deepseek-v4-pro-0813"), ("Qwen 3.8 Max", "qwen3.8-max"), ("qwen3.8-max", "qwen3.8-max")]:
            self.assertEqual(modelos.validar(viejo), nuevo, viejo)

    def test_desconocido_sigue_rechazado_con_lista(self):
        with self.assertRaises(ValueError) as e:
            modelos.validar("no-existe")
        self.assertIn("qwen3.8-max", str(e.exception))


if __name__ == "__main__":
    unittest.main()
