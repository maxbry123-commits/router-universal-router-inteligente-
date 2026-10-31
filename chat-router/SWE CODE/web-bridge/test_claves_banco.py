"""Puente al banco de claves: el bridge lee las claves de Groq/NVIDIA del banco del Router MVP (solo lectura) y guarda las que le pegan en un banco propio cifrado,
para que sobrevivan reinicios sin variables de Hugging Face. Reutiliza mvp.bank (misma cifra), sin tocar el Router."""
import json, os, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parent))
import claves_banco
from mvp import bank


class TestClavesBanco(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.router = os.path.join(self.d, "router.bin"); self.propio = os.path.join(self.d, "banco-swe.bin")
        self.env = patch.dict(os.environ, {"RIU_API_KEY": "acceso-prueba", "RIU_BANCO_ROUTER": self.router, "BRIDGE_STATE_DIR": self.d})
        self.env.start()
    def tearDown(self): self.env.stop()

    def test_lee_las_claves_del_banco_del_router_sin_escribirlo(self):
        b = bank.abrir(self.router, "acceso-prueba"); b.guardar("GROQ_API_KEY", "gsk-router-1"); b.guardar("NVIDIA_API_KEY_1", "nv-router-1"); b.guardar("HF_TOKEN", "hf-no-debe-salir")
        antes = open(self.router, "rb").read()
        r = claves_banco.leer()
        self.assertEqual(r, {"groq": ["gsk-router-1"], "nvidia": ["nv-router-1"]})
        self.assertNotIn("hf-no-debe-salir", json.dumps(r))
        self.assertEqual(open(self.router, "rb").read(), antes, "solo lectura")

    def test_guarda_en_un_banco_propio_cifrado_y_lo_recupera(self):
        claves_banco.guardar({"groq": ["gsk-pegada"], "nvidia": "nv-pegada"})
        self.assertTrue(os.path.exists(self.propio))
        self.assertNotIn(b"gsk-pegada", open(self.propio, "rb").read(), "cifrado en disco")
        self.assertEqual(claves_banco.leer(), {"groq": ["gsk-pegada"], "nvidia": ["nv-pegada"]})

    def test_une_banco_del_router_y_propio_sin_repetir(self):
        b = bank.abrir(self.router, "acceso-prueba"); b.guardar("GROQ_API_KEY", "gsk-a")
        claves_banco.guardar({"groq": ["gsk-a", "gsk-b"]})
        self.assertEqual(claves_banco.leer()["groq"], ["gsk-a", "gsk-b"])

    def test_sin_clave_de_acceso_o_banco_inexistente_no_revienta(self):
        with patch.dict(os.environ, {"RIU_API_KEY": ""}):
            self.assertEqual(claves_banco.leer(), {"groq": [], "nvidia": []})
        self.assertEqual(claves_banco.leer(), {"groq": [], "nvidia": []})


if __name__ == "__main__":
    unittest.main()
