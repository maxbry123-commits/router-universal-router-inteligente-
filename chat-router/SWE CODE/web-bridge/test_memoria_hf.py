"""OpenClaw guarda y lee en la MISMA memoria del chat Yaiwes (bucket HF, carpeta memoria/): sin sistema nuevo, via mvp.memoria."""
import json, os, subprocess, sys, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parent))
import memoria_hf
from mvp import memoria, hf_store


class FakeBucket:
    def __init__(self): self.d = {}
    def guardar(self, clave, nombre, valor):
        assert clave == "hf-token-prueba"; self.d[nombre] = valor; return {"ok": True}
    def leer(self, clave, nombre):
        if nombre not in self.d: raise hf_store.NoExiste("no existe")
        return {"valor": self.d[nombre]}


class TestMemoriaHF(unittest.TestCase):
    def setUp(self):
        self.b = FakeBucket(); memoria.CACHE.clear()
        self.p = [patch.object(hf_store, "guardar", self.b.guardar), patch.object(hf_store, "leer", self.b.leer), patch.dict(os.environ, {"HF_TOKEN": "hf-token-prueba"})]
        [p.start() for p in self.p]
    def tearDown(self): [p.stop() for p in self.p]

    def test_guarda_en_el_mismo_archivo_de_memoria_que_usa_el_chat(self):
        r = memoria_hf.main(["save", "openclaw:proyecto-a", "asesoria-1"], json.dumps({"texto": "plan"}))
        self.assertTrue(r["ok"])
        self.assertIn("memoria/openclaw_proyecto-a.json", self.b.d)  # mismo patron memoria/<scope>.json del chat

    def test_lee_lo_que_guardo(self):
        memoria_hf.main(["save", "openclaw:p", "k1"], json.dumps({"x": 1}))
        memoria.CACHE.clear()
        self.assertEqual(memoria_hf.main(["load", "openclaw:p", "k1"], "")["records"][0]["data"], {"x": 1})

    def test_search_devuelve_el_historial_de_la_sesion(self):
        memoria_hf.main(["save", "openclaw:p", "m-1-user"], json.dumps({"rol": "user", "texto": "hola"}))
        memoria.CACHE.clear()
        r = memoria_hf.main(["search", "openclaw:p", "", "50"], "")
        self.assertEqual(r["results"]["sqlite"][0]["data"]["texto"], "hola")

    def test_las_credenciales_no_se_guardan(self):
        memoria_hf.main(["save", "openclaw:p", "k"], json.dumps({"t": "clave sk-abcdefghijklmnopqr"}))
        self.assertNotIn("sk-abcdefghijklmnopqr", self.b.d["memoria/openclaw_p.json"])

    def test_sin_token_error_claro(self):
        with patch.dict(os.environ, {"HF_TOKEN": ""}):
            with self.assertRaises(RuntimeError):
                memoria_hf.main(["save", "openclaw:p", "k"], "{}")

    def test_el_script_se_basta_solo_sin_pythonpath(self):
        """memoria_hf.py como lo lanza el bridge (sin PYTHONPATH): ubica solo router-mvp y chat-router/chat/backend; sin token responde error JSON corto, no ImportError."""
        env = {"PATH": os.environ["PATH"], "HOME": "/tmp"}
        r = subprocess.run([sys.executable, str(Path(memoria_hf.__file__).resolve()), "load", "openclaw:p", "k"], env=env, capture_output=True, text=True, timeout=60)
        self.assertEqual(json.loads(r.stdout)["ok"], False)
        self.assertIn("HF_TOKEN", json.loads(r.stdout)["error"])
        self.assertNotIn("ModuleNotFoundError", r.stderr)


if __name__ == "__main__":
    unittest.main()
