"""Puente al banco de claves: el bridge lee las claves de Groq/NVIDIA del banco del Router MVP (solo lectura) y guarda las que le pegan en un banco propio cifrado,
para que sobrevivan reinicios sin variables de Hugging Face. Reutiliza mvp.bank (misma cifra), sin tocar el Router."""
import json, os, subprocess, sys, tempfile, unittest
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

    def test_prueba_todas_las_variables_de_acceso_no_solo_la_primera(self):
        """El banco puede estar cifrado con RIU_PUBLIC_CHAT_KEY aunque RIU_API_KEY este definida y sea otra."""
        b = bank.abrir(self.propio, "clave-publica-del-chat"); b.guardar("GROQ_API_KEY", "gsk-con-otra-var")
        with patch.dict(os.environ, {"RIU_API_KEY": "otra-distinta", "RIU_PUBLIC_CHAT_KEY": "clave-publica-del-chat"}):
            self.assertEqual(claves_banco.leer()["groq"], ["gsk-con-otra-var"])

    def test_diagnostico_solo_cuenta_nunca_valores(self):
        b = bank.abrir(self.propio, "acceso-prueba"); b.guardar("GROQ_API_KEY", "gsk-secreta-1"); b.guardar("NVIDIA_API_KEY", "nv-secreta-1")
        d = claves_banco.diagnostico()
        self.assertEqual((d["propio"]["existe"], d["propio"]["abre_con"], d["propio"]["groq"], d["propio"]["nvidia"]), (True, 0, 1, 1))
        self.assertFalse(d["router"]["existe"])
        self.assertNotIn("secreta", json.dumps(d))
        bank.abrir(self.router, "otra-clave")  # banco del Router cifrado con otra clave: no abre, y no revienta
        d = claves_banco.diagnostico()
        self.assertTrue(d["router"]["existe"]); self.assertIsNone(d["router"]["abre_con"]); self.assertIn("error", d["router"])

    def test_sin_clave_de_acceso_o_banco_inexistente_no_revienta(self):
        with patch.dict(os.environ, {"RIU_API_KEY": ""}):
            self.assertEqual(claves_banco.leer(), {"groq": [], "nvidia": []})
        self.assertEqual(claves_banco.leer(), {"groq": [], "nvidia": []})

    def test_borrar_vacia_el_banco_propio_y_no_toca_el_del_router(self):
        b = bank.abrir(self.router, "acceso-prueba"); b.guardar("GROQ_API_KEY", "gsk-router")
        antes = open(self.router, "rb").read()
        claves_banco.guardar({"groq": ["gsk-pegada"], "nvidia": ["nv-pegada"]})
        self.assertTrue(claves_banco.borrar())
        self.assertTrue(os.path.exists(self.propio), "queda un banco propio cifrado y vacio (se puede publicar)")
        self.assertEqual(bank.abrir(self.propio, "acceso-prueba").nombres(), [])
        self.assertEqual(claves_banco.leer(), {"groq": ["gsk-router"], "nvidia": []})
        self.assertEqual(open(self.router, "rb").read(), antes, "el banco del Router no se toca")

    def test_borrar_sin_banco_previo_funciona_y_sin_clave_de_acceso_falla(self):
        self.assertTrue(claves_banco.borrar())
        with patch.dict(os.environ, {"RIU_API_KEY": ""}):
            with self.assertRaises(RuntimeError):
                claves_banco.borrar()

    def test_guardar_borra_las_claves_que_ya_no_vienen_en_la_lista(self):
        """Una clave quitada del panel no reaparece al releer el banco (antes solo se sobrescribian los nombres nuevos)."""
        claves_banco.guardar({"groq": ["gsk-a", "gsk-b", "gsk-c"], "nvidia": ["nv-a", "nv-b"]})
        claves_banco.guardar({"groq": ["gsk-b"]})
        self.assertEqual(claves_banco.leer(), {"groq": ["gsk-b"], "nvidia": ["nv-a", "nv-b"]}, "nvidia no vino: no se toca")
        self.assertEqual(bank.abrir(self.propio, "acceso-prueba").nombres(), ["GROQ_API_KEY", "NVIDIA_API_KEY", "NVIDIA_API_KEY_1"])
        claves_banco.guardar({"groq": [], "nvidia": ["nv-z"]})
        self.assertEqual(claves_banco.leer(), {"groq": [], "nvidia": ["nv-z"]}, "lista vacia = borrar todas las de ese proveedor")
        self.assertEqual(bank.abrir(self.propio, "acceso-prueba").nombres(), ["NVIDIA_API_KEY"])

    def test_guardar_conserva_la_clave_de_acceso_con_la_que_se_cifro_el_banco(self):
        bank.abrir(self.propio, "clave-publica-del-chat").guardar("GROQ_API_KEY", "gsk-vieja")
        with patch.dict(os.environ, {"RIU_API_KEY": "otra-distinta", "RIU_PUBLIC_CHAT_KEY": "clave-publica-del-chat"}):
            claves_banco.guardar({"groq": ["gsk-nueva"]})
        self.assertEqual(bank.abrir(self.propio, "clave-publica-del-chat").leer("GROQ_API_KEY"), "gsk-nueva")
        with self.assertRaises(ValueError):
            bank.abrir(self.propio, "otra-distinta")
        self.assertEqual([f for f in os.listdir(self.d) if "nuevo" in f], [], "sin temporales")

    def test_guardar_no_toca_otras_entradas_del_banco_propio(self):
        bank.abrir(self.propio, "acceso-prueba").guardar("OTRA_COSA", "valor-ajeno")
        claves_banco.guardar({"groq": ["gsk-a"]}); claves_banco.guardar({"groq": []})
        self.assertEqual(bank.abrir(self.propio, "acceso-prueba").nombres(), ["OTRA_COSA"])

    def test_el_script_se_basta_solo_sin_pythonpath(self):
        """Corre `claves_banco.py` como lo lanza el bridge, con el entorno vacio de PYTHONPATH: el propio script ubica router-mvp y chat-router/chat/backend."""
        env = {"PATH": os.environ["PATH"], "HOME": self.d, "RIU_API_KEY": "acceso-prueba", "RIU_BANCO_ROUTER": self.router, "BRIDGE_STATE_DIR": self.d}
        r = subprocess.run([sys.executable, str(Path(claves_banco.__file__).resolve()), "leer"], env=env, capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr[-300:] + r.stdout[-300:])
        self.assertEqual(json.loads(r.stdout), {"groq": [], "nvidia": []})


if __name__ == "__main__":
    unittest.main()
