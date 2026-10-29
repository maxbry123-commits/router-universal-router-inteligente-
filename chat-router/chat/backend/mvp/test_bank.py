"""Pruebas locales del banco; sin conectarse al Space ni a GitHub."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bank import abrir


class TestBanco(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.ruta = Path(self.dir.name) / "banco.bin"
        self.banco = abrir(self.ruta, "clave-local-de-prueba")

    def tearDown(self):
        self.dir.cleanup()

    def test_guardar_y_leer(self):
        self.banco.guardar("QWEN_API_KEY", "secreto-local-prueba")
        otro = abrir(self.ruta, "clave-local-de-prueba")
        self.assertEqual(otro.leer("QWEN_API_KEY"), "secreto-local-prueba")
        self.assertEqual(otro.nombres(), ["QWEN_API_KEY"])

    def test_clave_incorrecta(self):
        self.banco.guardar("QWEN_API_KEY", "secreto-local-prueba")
        with self.assertRaisesRegex(ValueError, "clave incorrecta") as error:
            abrir(self.ruta, "otra-clave")
        self.assertNotIn("secreto-local-prueba", str(error.exception))

    def test_binario_no_contiene_texto_claro(self):
        self.banco.guardar("QWEN_API_KEY", "secreto-local-prueba")
        contenido = self.ruta.read_bytes()
        self.assertTrue(contenido.startswith(b"MVPB1"))
        self.assertNotIn(b"secreto-local-prueba", contenido)

    def test_bootstrap_no_sobrescribe(self):
        with patch.dict(os.environ, {"HF_TOKEN": "valor-primero"}):
            self.banco.bootstrap_desde_env()
        with patch.dict(os.environ, {"HF_TOKEN": "valor-segundo"}):
            self.banco.bootstrap_desde_env()
        self.assertEqual(self.banco.leer("HF_TOKEN"), "valor-primero")


if __name__ == "__main__":
    unittest.main(verbosity=2)


class TestClaveDeAccesoDelEntorno(unittest.TestCase):
    def test_el_banco_actualiza_riu_api_key_si_cambia_en_el_entorno(self):
        import os, tempfile
        from unittest.mock import patch
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ, {"RIU_API_KEY": "clave-vieja"}):
            b = abrir(Path(d) / "b.bin", "clave-vieja"); b.bootstrap_desde_env()
            self.assertEqual(b.leer("RIU_API_KEY"), "clave-vieja")
            os.environ["RIU_API_KEY"] = "clave-nueva"
            b.bootstrap_desde_env()
            self.assertEqual(b.leer("RIU_API_KEY"), "clave-nueva")
