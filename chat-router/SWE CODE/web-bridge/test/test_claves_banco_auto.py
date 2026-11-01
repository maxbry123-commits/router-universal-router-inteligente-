"""Credenciales multi-proveedor: usa un banco temporal, nunca toca HF ni los secretos reales."""
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


PATH = Path(__file__).resolve().parents[1] / "claves_banco.py"
spec = importlib.util.spec_from_file_location("claves_banco_prueba", PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class TestClaveDobleRouter(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.banco = str(Path(self.tmp.name) / "banco.bin")
        self.router = str(Path(self.tmp.name) / "router.bin")
        self.patches = [
            patch.object(mod, "_ruta_propia", return_value=self.banco),
            patch.object(mod, "_ruta_router", return_value=self.router),
            patch.object(mod, "_candidatas", return_value=["FAKE-ACCESS"]),
        ]
        for v in self.patches: v.start()
        self.addCleanup(self.tmp.cleanup)
        for v in self.patches: self.addCleanup(v.stop)

    def test_auto_detecta_y_agrega_sin_borrar_claves_previas(self):
        a = mod.anadir({"proveedor": "auto", "secret": "gsk_TEST_000001"})
        b = mod.anadir({"proveedor": "auto", "secret": "nvapi-TEST-000002"})
        c = mod.anadir({"proveedor": "groq", "secret": "gsk_TEST_000003"})
        self.assertEqual([a["proveedor"], b["proveedor"], c["cantidad"]], ["groq", "nvidia", 2])
        self.assertEqual(len(mod.leer()["groq"]), 2)
        self.assertEqual(len(mod.leer()["nvidia"]), 1)
        self.assertEqual(mod.catalogo()["proveedores"][0]["cantidad"], 2)

    def test_otro_sdk_almacena_metadatos_sin_anunciar_inferencia(self):
        r = mod.anadir({"proveedor": "otro-sdk", "secret": "fake-sdk-token-long", "tipo": "sdk"})
        self.assertFalse(r["compatible"])
        c = mod.catalogo()
        self.assertTrue(any(v["id"] == "otro_sdk" and v["cantidad"] == 1 and not v["compatible"] for v in c["proveedores"]))
        self.assertNotIn("fake-sdk-token-long", str(c))
        self.assertNotIn("fake-sdk-token-long", str(r))

    def test_token_sin_prefijo_requiere_proveedor_explicito(self):
        with self.assertRaisesRegex(ValueError, "PROVEEDOR_REQUERIDO"):
            mod.anadir({"proveedor": "auto", "secret": "unknown-test-key"})
        self.assertFalse(os.path.exists(self.banco))

    def test_no_acepta_claves_vacias_y_no_modifica_el_banco(self):
        with self.assertRaisesRegex(ValueError, "CLAVE_INVALIDA"):
            mod.anadir({"proveedor": "nvidia", "secret": "short"})
        self.assertFalse(os.path.exists(self.banco))


if __name__ == "__main__":
    unittest.main()
