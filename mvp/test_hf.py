"""HF falso: datos, permisos, rutas y aislamiento de credenciales."""
import inspect
import os
import pathlib
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from fastapi.testclient import TestClient
from huggingface_hub import HfFileSystem
from mvp import hf_store, app as servicio
class TestHF(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.local = pathlib.Path(self.dir.name) / "dato.txt"
        self.local.write_text("respuesta", encoding="utf-8")
        self.archivos = {}
        self.tokens = []
        pruebas = self
        class FsFalso:
            def __init__(self, token=None):
                pruebas.tokens.append(token)
            def open(self, ruta, modo):
                if "r" in modo and ruta not in pruebas.archivos and pruebas.leer_defecto is None:
                    raise FileNotFoundError(ruta)
                return ArchivoFalso(ruta, modo)
        class ArchivoFalso:
            def __init__(self, ruta, modo):
                self.ruta, self.modo = ruta, modo
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def write(self, datos):
                if pruebas.falla: raise Exception("hf-ficticio credencial privada")
                pruebas.archivos[self.ruta] = datos
            def read(self):
                return pruebas.archivos.get(self.ruta, pruebas.leer_defecto)
        self.falla = False
        self.leer_defecto = b"respuesta"
        self.p1 = patch("mvp.hf_store.HfFileSystem", FsFalso)
        self.p1.start()
        self.env = patch.dict(os.environ, {"RIU_API_KEY": "api-ficticia"})
        self.env.start()
        self.antes = getattr(servicio.app.state, "banco", None)
        servicio.app.state.banco = SimpleNamespace(leer=lambda k: "hf-ficticio" if k == "HF_TOKEN" else None)
        self.client = TestClient(servicio.app)
    def tearDown(self):
        self.client.close(); servicio.app.state.banco = self.antes
        self.env.stop(); self.p1.stop(); self.dir.cleanup()
    def test_guardar_dataset_prefijo_token(self):
        salida = hf_store.guardar("hf-ficticio", "conversaciones/uno.json", "mensaje")
        self.assertEqual(salida, {"ok": True, "destino": "hf", "id": "conversaciones/uno.json", "commit": None})
        self.assertEqual(self.archivos, {"hf://buckets/COMAND-CENTER-1/yaiwes-memoria-storage/riu-chat/conversaciones/uno.json": b"mensaje"})
        self.assertEqual(self.tokens, ["hf-ficticio"])
        self.assertNotIn("hf-ficticio", repr(salida))
    def test_leer_dataset(self):
        salida = hf_store.leer("hf-ficticio", "conversaciones/uno.json")
        self.assertEqual(salida["valor"], "respuesta")
        self.assertEqual(self.tokens, ["hf-ficticio"])
    def test_ids_inseguros(self):
        for id_ in ("../secreto", "/absoluto", "a/../b", "a//b", "a\\b", "C:archivo", "foo.py", ".env", "a/.oculto", "", 123):
            with self.subTest(id_=id_), self.assertRaises(ValueError): hf_store._ruta(id_)
        self.assertEqual(self.archivos, {})
    def test_no_codigo_claves_ni_valores_grandes(self):
        for valor in ("sk-sp-0123456789ABCDEFGHI", "github_pat_abcdefghijklmnop", "hf_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456", "a" * 1_000_001):
            with self.subTest(valor_len=len(valor)), self.assertRaises(ValueError):
                hf_store.guardar("hf-ficticio", "registro.txt", valor)
        self.assertEqual(self.archivos, {})

    def test_token_obligatorio_y_error_sanitizado(self):
        with self.assertRaisesRegex(RuntimeError, "HF_TOKEN ausente"):
            hf_store.guardar(None, "x.txt", "dato")
        self.falla = True
        with self.assertRaisesRegex(RuntimeError, "fallo de escritura HF") as ctx:
            hf_store.guardar("hf-ficticio", "x.txt", "dato")
        self.assertNotIn("hf-ficticio", str(ctx.exception))

    def test_almacen_hf_con_auth(self):
        data = {"accion": "guardar", "destino": "hf", "nombre": "registro.json", "valor": "hola"}
        self.assertEqual(self.client.post("/almacen", json=data).status_code, 401)
        r = self.client.post("/almacen", json=data, headers={"x-api-key": "api-ficticia"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.tokens[-1], "hf-ficticio")
        self.assertNotIn("hf-ficticio", r.text)

    def test_almacen_hf_lectura_y_limites(self):
        cab = {"x-api-key": "api-ficticia"}
        r = self.client.post("/almacen", json={"accion": "leer", "destino": "hf", "nombre": "uno.txt"}, headers=cab)
        self.assertEqual((r.status_code, r.json()["valor"]), (200, "respuesta"))
        for accion in ("computar", "status"):
            self.assertEqual(self.client.post("/almacen", json={"accion": accion, "destino": "hf", "tarea": "t"}, headers=cab).status_code, 400)
        self.assertEqual(self.client.post("/almacen", json={"accion": "leer", "destino": "hf", "nombre": "../x"}, headers=cab).status_code, 400)
        self.assertEqual(self.client.post("/almacen", json={"accion": "leer", "destino": "otro", "nombre": "x"}, headers=cab).status_code, 400)

    def test_banco_sin_hf_token(self):
        servicio.app.state.banco = SimpleNamespace(leer=lambda _: None)
        r = self.client.post("/almacen", json={"accion": "leer", "destino": "hf", "nombre": "x"}, headers={"x-api-key": "api-ficticia"})
        self.assertEqual(r.status_code, 503)
        self.assertEqual(self.tokens, [])

    def test_harness_por_defecto_no_se_toca(self):
        with patch("mvp.app.harness_client.leer", return_value={"dato": "ok"}) as viejo:
            servicio.app.state.banco = SimpleNamespace(leer=lambda _: "harness-test")
            r = self.client.post("/almacen", json={"accion": "leer", "nombre": "a"}, headers={"x-api-key": "api-ficticia"})
        self.assertEqual((r.status_code, r.json()), (200, {"dato": "ok"}))
        viejo.assert_called_once_with("harness-test", "a")
        self.assertEqual(self.tokens, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
