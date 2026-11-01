"""Contratos de proveedor del Router MVP: modelos y banco real, sin redes."""
import os
import unittest
from unittest.mock import patch
from mvp import externos


class TestProveedoresDirectos(unittest.TestCase):
    def test_catalogo_urls_fijas_y_modelos_elegidos(self):
        esperado = {
            "deepseek": ("https://api.deepseek.com", "DEEPSEEK_API_KEY", "deepseek-v4-pro"),
            "minimax": ("https://api.minimax.io/v1", "MINIMAX_API_KEY", "MiniMax-M3"),
            "openai": ("https://api.openai.com/v1", "OPENAI_API_KEY", "gpt-5.6"),
        }
        for p, (url, nombre, modelo) in esperado.items():
            self.assertEqual(externos.PROVEEDORES[p]["base"], url)
            self.assertEqual(externos.PROVEEDORES[p]["var"], nombre)
            self.assertEqual(externos.proveedor(p + "/" + modelo), p)
            self.assertIn(p + "/" + modelo, externos.PROVEEDORES_NUEVOS)

    def test_proveedor_desconocido_no_permanece_permitido(self):
        self.assertIsNone(externos.proveedor("otro/mi-modelo"))

    def test_llaves_compatibles_salen_del_mismo_banco_cifrado(self):
        class Banco:
            def leer(self, n):
                return {"OPENAI_API_KEY": "TEST-OPENAI", "DEEPSEEK_API_KEY": "TEST-DEEPSEEK"}.get(n)
        with patch.dict(os.environ, {}, clear=True), patch.object(externos, "_banco_compartido", return_value=Banco()):
            self.assertEqual(externos.claves("openai"), ["TEST-OPENAI"])
            self.assertEqual(externos.claves("deepseek"), ["TEST-DEEPSEEK"])


if __name__ == "__main__":
    unittest.main()
