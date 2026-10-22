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
from huggingface_hub import HfApi, hf_hub_download
from mvp import hf_store, app as servicio
class TestHF(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.local = pathlib.Path(self.dir.name) / "dato.txt"
        self.local.write_text("respuesta", encoding="utf-8")
        self.upload = Mock(return_value=SimpleNamespace(oid="commit-falso"))
        self.p1 = patch("mvp.hf_store.HfApi", return_value=SimpleNamespace(upload_file=self.upload))
        self.download = Mock(return_value=str(self.local))
        self.p2 = patch("mvp.hf_store.hf_hub_download", self.download)
        self.p1.start(); self.p2.start()
        self.env = patch.dict(os.environ, {"RIU_API_KEY": "api-ficticia"})
        self.env.start()
        self.antes = getattr(servicio.app.state, "banco", None)
        servicio.app.state.banco = SimpleNamespace(leer=lambda k: "hf-ficticio" if k == "HF_TOKEN" else None)
        self.client = TestClient(servicio.app)
    def tearDown(self):
        self.client.close(); servicio.app.state.banco = self.antes
        self.env.stop(); self.p2.stop(); self.p1.stop(); self.dir.cleanup()
    def test_api_oficial_disponible(self):
        firma = inspect.signature(HfApi.upload_file)
        self.assertTrue({"path_or_fileobj", "path_in_repo", "repo_id", "repo_type", "token"}.issubset(firma.parameters))
        self.assertIn("repo_type", inspect.signature(hf_hub_download).parameters)
    def test_guardar_dataset_prefijo_token(self):
        salida = hf_store.guardar("hf-ficticio", "conversaciones/uno.json", "mensaje")
        self.assertEqual(salida, {"ok": True, "destino": "hf", "id": "conversaciones/uno.json", "commit": "commit-falso"})
        kwargs = self.upload.call_args.kwargs
        self.assertEqual((kwargs["repo_id"], kwargs["repo_type"], kwargs["path_in_repo"]),
                         ("COMAND-CENTER-1/yaiwes-memoria-storage", "dataset", "riu-chat/conversaciones/uno.json"))
        self.assertEqual((kwargs["token"], kwargs["path_or_fileobj"]), ("hf-ficticio", b"mensaje"))
        self.assertNotIn("hf-ficticio", repr(salida))
    def test_leer_dataset(self):
        salida = hf_store.leer("hf-ficticio", "conversaciones/uno.json")
        self.assertEqual(salida["valor"], "respuesta")
        self.assertEqual(self.download.call_args.kwargs["filename"], "riu-chat/conversaciones/uno.json")
        self.assertEqual(self.download.call_args.kwargs["token"], "hf-ficticio")
    def test_ids_inseguros(self):
        for id_ in ("../secreto", "/absoluto", "a/../b", "a//b", "a\\b", "C:archivo", "foo.py", ".env", "a/.oculto", "", 123):
            with self.subTest(id_=id_), self.assertRaises(ValueError): hf_store._ruta(id_)
        self.upload.assert_not_called()
    def test_no_codigo_claves_ni_valores_grandes(self):
        for valor in ("sk-sp-0123456789ABCDEFGHI", "github_pat_abcdefghijklmnop", "hf_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456", "a" * 1_000_001):
            with self.subTest(valor_len=len(valor)), self.assertRaises(ValueError):
                hf_store.guardar("hf-ficticio", "registro.txt", valor)
        self.upload.assert_not_called()

    def test_token_obligatorio_y_error_sanitizado(self):
        with self.assertRaisesRegex(RuntimeError, "HF_TOKEN ausente"):
            hf_store.guardar(None, "x.txt", "dato")
        self.upload.side_effect = Exception("hf-ficticio credencial privada")
        with self.assertRaisesRegex(RuntimeError, "fallo de escritura HF") as ctx:
            hf_store.guardar("hf-ficticio", "x.txt", "dato")
        self.assertNotIn("hf-ficticio", str(ctx.exception))

    def test_almacen_hf_con_auth(self):
        data = {"accion": "guardar", "destino": "hf", "nombre": "registro.json", "valor": "hola"}
        self.assertEqual(self.client.post("/almacen", json=data).status_code, 401)
        r = self.client.post("/almacen", json=data, headers={"x-api-key": "api-ficticia"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.upload.call_args.kwargs["token"], "hf-ficticio")
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
        self.download.assert_not_called()

    def test_harness_por_defecto_no_se_toca(self):
        with patch("mvp.app.harness_client.leer", return_value={"dato": "ok"}) as viejo:
            servicio.app.state.banco = SimpleNamespace(leer=lambda _: "harness-test")
            r = self.client.post("/almacen", json={"accion": "leer", "nombre": "a"}, headers={"x-api-key": "api-ficticia"})
        self.assertEqual((r.status_code, r.json()), (200, {"dato": "ok"}))
        viejo.assert_called_once_with("harness-test", "a")
        self.download.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
