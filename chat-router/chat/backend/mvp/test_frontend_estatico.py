"""El Router (Hugging Face) sirve del clon los MISMOS archivos que Vercel despliega desde main."""
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

import frontend_estatico

FRONT = frontend_estatico.CARPETA
NUEVOS = ["swe-selectores.js", "swe-claves.js", "ventana-claves.js", "shell.js", "shell.html"]


class TestFrontendEstatico(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        frontend_estatico.montar(app)
        self.c = TestClient(app)

    def test_sirve_los_archivos_nuevos_byte_a_byte_sin_cache(self):
        for n in NUEVOS:
            r = self.c.get("/chat/ui/" + n)
            self.assertEqual(r.status_code, 200, n)
            self.assertEqual(r.content, (FRONT / n).read_bytes(), n)
            self.assertEqual(r.headers.get("cache-control"), "no-cache", n)
        self.assertEqual(self.c.get("/").content, (FRONT / "shell.html").read_bytes())

    def test_todo_lo_que_pide_shell_html_existe(self):
        html = (FRONT / "shell.html").read_text()
        for ruta in re.findall(r'/chat/ui/([A-Za-z0-9_.-]+\.(?:js|css))', html):
            self.assertTrue((FRONT / ruta).is_file(), ruta)
            self.assertEqual(self.c.get("/chat/ui/" + ruta).content, (FRONT / ruta).read_bytes(), ruta)

    def test_ruta_con_query_de_version_sirve_el_mismo_archivo(self):
        r = self.c.get("/chat/ui/swe-selectores.js?v=abcdef123456")
        self.assertEqual(r.content, (FRONT / "swe-selectores.js").read_bytes())

    def test_version_json_hf_es_json_y_commit_no_html_fallback(self):
        # HF usa los mismos JS actualizados por autopull pero no corre build.sh.
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            (raiz / "shell.html").write_text("<!doctype html>", encoding="utf-8")
            app = FastAPI()
            frontend_estatico.montar(app, raiz=raiz)
            with patch.object(frontend_estatico.subprocess, "check_output", return_value="a" * 40):
                r = TestClient(app).get("/chat/ui/version.json")
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.json(), {"commit": "a" * 40})
            self.assertEqual(r.headers.get("cache-control"), "no-cache")
            self.assertIn("application/json", r.headers.get("content-type", ""))

    def test_el_fuente_es_el_de_git_sin_modificar_por_build_sh(self):
        """HF no corre build.sh: si el fuente trajera ?v= fijos, el clon y Vercel divergirian."""
        for f in FRONT.glob("*.js"):
            self.assertFalse(re.search(r"from\s+['\"]\./[\w.-]+\.js\?v=", f.read_text()), f.name)


if __name__ == "__main__":
    unittest.main()
