"""Motor de archivos: origen -> lista -> destino con servidor HTTP y repo git locales (nada sale a internet)."""
import io
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import zipfile
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mvp import archivos
from mvp.archivos import destino_git, origen as org
from mvp.archivos.seguridad import MotorError


def _zip(ruta, archivos_):
    with zipfile.ZipFile(ruta, "w") as z:
        for nombre, datos in archivos_.items():
            z.writestr(nombre, datos)


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.web = tempfile.mkdtemp()
        _zip(Path(cls.web) / "demo.zip", {"a/uno.txt": "hola mundo", "a/dos.md": "# doc\nbuscame aqui", "b/tres.bin": "x" * 50})
        _zip(Path(cls.web) / "malo.zip", {"../../fuera.txt": "peligro"})
        cls.http = ThreadingHTTPServer(("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=cls.web))
        threading.Thread(target=cls.http.serve_forever, daemon=True).start()
        cls.url = "http://127.0.0.1:%d" % cls.http.server_port

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()

    def setUp(self):
        self.raiz = tempfile.mkdtemp()
        self.env = patch.dict(os.environ, {"RIU_MOTOR_RAIZ": self.raiz, "RIU_MOTOR_PERMITIR_LOCAL": "1"})
        self.env.start()

    def tearDown(self):
        self.env.stop()

    def correr(self, jobs):
        r = archivos.llamar("ejecutar", {"cola": jobs})
        self.assertNotIn("error", r, r)
        for _ in range(100):
            e = archivos.llamar("estado", {"id": r["id"]})
            if e["estado"] not in ("en_cola", "corriendo"):
                return e
            time.sleep(0.1)
        self.fail("la cola no termino")


class DescargarYExtraer(Base):
    def test_descarga_extrae_y_escribe_readme_con_sha256(self):
        e = self.correr([{"accion": "descargar", "origen": self.url + "/demo.zip", "destino": "paquete"}])
        self.assertEqual((e["estado"], e["trabajos"][0]["estado"], e["trabajos"][0]["archivos"]), ("terminado", "ok", 3), e)
        d = Path(self.raiz) / "paquete"
        self.assertEqual((d / "a" / "uno.txt").read_text(), "hola mundo")
        self.assertTrue((d / "README.md").exists() and (d / "MANIFEST.json").exists())
        self.assertIn("sha256", (d / "MANIFEST.json").read_text())

    def test_zip_con_ruta_peligrosa_se_bloquea(self):
        e = self.correr([{"accion": "descargar", "origen": self.url + "/malo.zip", "destino": "x"}])
        self.assertIn("ZIP_SLIP_BLOQUEADO", e["trabajos"][0]["error"])
        self.assertFalse((Path(self.raiz).parent / "fuera.txt").exists())

    def test_destino_fuera_de_la_raiz_se_rechaza(self):
        e = self.correr([{"accion": "descargar", "origen": self.url + "/demo.zip", "destino": "../escape"}])
        self.assertIn("RUTA_FUERA_DE_RAIZ", e["trabajos"][0]["error"])

    def test_url_de_red_interna_se_bloquea_sin_el_permiso_de_pruebas(self):
        with patch.dict(os.environ, {"RIU_MOTOR_PERMITIR_LOCAL": ""}):
            e = self.correr([{"accion": "descargar", "origen": self.url + "/demo.zip", "destino": "x"}])
        self.assertIn("URL_RED_INTERNA_BLOQUEADA", e["trabajos"][0]["error"])


class CopiarMoverListarBuscar(Base):
    def preparar(self):
        self.correr([{"accion": "descargar", "origen": self.url + "/demo.zip", "destino": "base", "readme": False}])

    def test_copiar_no_sobrescribe_en_silencio(self):
        self.preparar()
        e = self.correr([{"accion": "copiar", "origen": "base", "destino": "copia"}, {"accion": "copiar", "origen": "base", "destino": "copia"}])
        self.assertEqual([t["estado"] for t in e["trabajos"]], ["ok", "error"])
        self.assertIn("DESTINO_YA_EXISTE", e["trabajos"][1]["error"])
        e = self.correr([{"accion": "copiar", "origen": "base", "destino": "copia", "sobrescribir": True}])
        self.assertEqual(e["trabajos"][0]["estado"], "ok")

    def test_mover_borra_el_origen_solo_despues_de_verificar(self):
        self.preparar()
        e = self.correr([{"accion": "mover", "origen": "base", "destino": "movido", "readme": False}])
        self.assertEqual(e["trabajos"][0]["estado"], "ok", e)
        self.assertFalse((Path(self.raiz) / "base").exists())
        self.assertEqual((Path(self.raiz) / "movido" / "a" / "uno.txt").read_text(), "hola mundo")

    def test_listar_un_zip_de_url_y_buscar_texto(self):
        self.preparar()
        e = self.correr([{"accion": "listar", "origen": self.url + "/demo.zip"}, {"accion": "buscar", "origen": "base", "patron": "buscame"}])
        self.assertIn("3 archivos", e["trabajos"][0]["resumen"])
        self.assertTrue(any("dos.md" in m for m in e["trabajos"][1]["muestra"]), e)


class Cola(Base):
    def test_varios_origenes_en_cola_y_estado_persistido(self):
        e = self.correr([{"accion": "descargar", "origen": self.url + "/demo.zip", "destino": "uno"}, {"source": self.url + "/demo.zip", "dest": "dos"}])
        self.assertEqual([t["estado"] for t in e["trabajos"]], ["ok", "ok"])
        self.assertTrue((Path(self.raiz) / "dos" / "b" / "tres.bin").exists())

    def test_la_cola_acepta_yaml_y_json_en_texto(self):
        yaml_ = "- accion: descargar\n  origen: %s/demo.zip\n  destino: desde_yaml\n" % self.url
        self.assertEqual(archivos.leer_cola(yaml_)[0]["destino"], "desde_yaml")
        self.assertEqual(archivos.leer_cola('{"cola": [{"origen": "x"}]}')[0]["origen"], "x")

    def test_cola_invalida_se_rechaza_antes_de_empezar(self):
        self.assertIn("ACCION_INVALIDA", archivos.llamar("ejecutar", {"cola": [{"accion": "borrar", "origen": "x"}]})["error"])
        self.assertIn("COLA_VACIA", archivos.llamar("ejecutar", {})["error"])

    def test_raiz_y_explorador(self):
        self.correr([{"accion": "descargar", "origen": self.url + "/demo.zip", "destino": "p"}])
        self.assertEqual(archivos.llamar("raiz")["raiz"], str(Path(self.raiz).resolve()))
        nombres = [x["nombre"] for x in archivos.llamar("listar_raiz", {})["entradas"]]
        self.assertEqual(nombres, ["p"])
        self.assertIn("RUTA_FUERA_DE_RAIZ", archivos.llamar("listar_raiz", {"ruta": "../.."})["error"])


class OrigenGit(Base):
    def test_clona_un_repo_y_copia_una_subcarpeta_sin_dot_git(self):
        repo = Path(tempfile.mkdtemp())
        (repo / "src").mkdir()
        (repo / "src" / "f.py").write_text("print(1)")
        for c in (["init", "-q", "-b", "main"], ["add", "-A"], ["-c", "user.email=a@b", "-c", "user.name=t", "commit", "-qm", "x"]):
            subprocess.run(["git", *c], cwd=repo, check=True, capture_output=True)
        e = self.correr([{"accion": "descargar", "origen": "git:file://" + str(repo), "destino": "clon"}])
        self.assertEqual(e["trabajos"][0]["estado"], "ok", e)
        self.assertTrue((Path(self.raiz) / "clon" / "src" / "f.py").exists())
        self.assertFalse((Path(self.raiz) / "clon" / ".git").exists())

    def test_parsea_formas_de_github(self):
        self.assertEqual(org.parsear_git("https://github.com/o/r/tree/main/a/b"), ("o", "r", "main", "a/b"))
        self.assertEqual(org.parsear_git("git:o/r@dev/x"), ("o", "r", "dev", "x"))
        self.assertEqual(org.clasificar("github.com/o/r"), "git")


class DestinoGit(Base):
    def remoto_local(self):
        base = Path(tempfile.mkdtemp())
        bare = base / "maxbry123-commits" / "Dest.git"
        bare.mkdir(parents=True)
        sub = lambda *a, cwd=None: subprocess.run(["git", "-c", "user.email=a@b", "-c", "user.name=t", *a], cwd=cwd, check=True, capture_output=True, text=True)
        sub("init", "-q", "--bare", "-b", "main", str(bare))
        semilla = base / "semilla"
        sub("clone", "-q", str(bare), str(semilla))
        (semilla / "LEEME.md").write_text("base")
        sub("add", "-A", cwd=semilla)
        sub("commit", "-qm", "base", cwd=semilla)
        sub("push", "-q", "origin", "HEAD:main", cwd=semilla)
        return base, bare, sub

    def test_publica_con_copia_fiel_lotes_y_lectura_de_vuelta(self):
        base, bare, sub = self.remoto_local()
        (Path(self.raiz) / "fuente" / "x").mkdir(parents=True)
        (Path(self.raiz) / "fuente" / "x" / "a.bin").write_bytes(b"\x00\x01\r\n datos \xff")
        (Path(self.raiz) / "fuente" / "b.txt").write_text("linea\r\n")
        with patch.dict(os.environ, {"RIU_MOTOR_GIT_BASE": str(base)}), patch.object(destino_git, "LOTE_BYTES", 8):
            r = archivos.llamar("ejecutar", {"cola": [{"accion": "copiar", "origen": "fuente", "destino": "git:maxbry123-commits/Dest/importado", "readme": False}]}, lambda: "token-falso")
            for _ in range(100):
                e = archivos.llamar("estado", {"id": r["id"]})
                if e["estado"] not in ("en_cola", "corriendo"):
                    break
                time.sleep(0.1)
            self.assertEqual(e["trabajos"][0]["estado"], "ok", e)
            self.assertIn("publicado maxbry123-commits/Dest@main", e["trabajos"][0]["resumen"])
        ver = base / "ver"
        sub("clone", "-q", str(bare), str(ver))
        self.assertEqual((ver / "importado" / "x" / "a.bin").read_bytes(), b"\x00\x01\r\n datos \xff")  # bytes identicos, sin conversion de saltos de linea
        self.assertEqual((ver / "importado" / "b.txt").read_bytes(), b"linea\r\n")
        self.assertEqual((ver / "LEEME.md").read_text(), "base")
        self.assertGreaterEqual(int(sub("rev-list", "--count", "HEAD", cwd=ver).stdout), 3)  # lotes pequenos: varios commits

    def test_no_pisa_lo_que_ya_existe_en_el_repo(self):
        base, bare, sub = self.remoto_local()
        (Path(self.raiz) / "fuente").mkdir()
        (Path(self.raiz) / "fuente" / "LEEME.md").write_text("otro")
        with patch.dict(os.environ, {"RIU_MOTOR_GIT_BASE": str(base)}):
            r = archivos.llamar("ejecutar", {"cola": [{"accion": "copiar", "origen": "fuente", "destino": "git:maxbry123-commits/Dest", "readme": False}]}, lambda: "t")
            for _ in range(100):
                e = archivos.llamar("estado", {"id": r["id"]})
                if e["estado"] not in ("en_cola", "corriendo"):
                    break
                time.sleep(0.1)
        self.assertIn("DESTINO_YA_EXISTE", e["trabajos"][0]["error"])

    def test_solo_la_cuenta_del_router_y_exige_token(self):
        with self.assertRaises(MotorError) as c:
            destino_git.parsear("git:otro/repo/carpeta")
        self.assertIn("SOLO_CUENTA_DEL_ROUTER", str(c.exception))
        self.assertEqual(destino_git.parsear("git:maxbry123-commits/Maxbry-AGI@main/x/y"), ("maxbry123-commits", "Maxbry-AGI", "main", "x/y"))
        e = self.correr([{"accion": "descargar", "origen": self.url + "/demo.zip", "destino": "git:maxbry123-commits/Maxbry-AGI/prueba"}])
        self.assertIn("GITHUB_TOKEN_NO_DISPONIBLE", e["trabajos"][0]["error"])


if __name__ == "__main__":
    unittest.main()
