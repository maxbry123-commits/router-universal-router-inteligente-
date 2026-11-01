"""Contrato del plugin de credenciales: sin claves reales ni redes externas."""
import asyncio
import unittest
from unittest.mock import patch
from fastapi import HTTPException
import httpx
from mvp import proveedor_claves as p


class CredencialesRouterTest(unittest.TestCase):
    def test_rechaza_ids_o_secretos_invalidos_antes_de_transportar(self):
        for cuerpo in [
            {"proveedor": "http://127.0.0.1", "secret": "abc123456"},
            {"proveedor": "nvidia", "secret": "abc"},
            {"proveedor": "auto", "secret": "clave con espacios"},
            {"proveedor": "groq", "tipo": "binario", "secret": "clave-falsa-123"},
        ]:
            with self.assertRaises(HTTPException) as exc:
                asyncio.run(p.llamar("anadir", cuerpo))
            self.assertEqual(exc.exception.status_code, 400)

    def test_router_solo_conecta_con_bridge_local_y_no_retorna_secreto(self):
        recibido = []
        def fake_backend(req):
            recibido.append((str(req.url), req.headers.get("x-api-key")))
            j = __import__("json").loads(req.content)
            assert j["proveedor"] == "groq" and j["secret"] == "gsk_fake_1234567"
            return httpx.Response(200, json={"ok": True, "proveedor": "groq", "cantidad": 1, "compatible": True})
        real = httpx.AsyncClient
        def mocked(*args, **kwargs):
            return real(transport=httpx.MockTransport(fake_backend), **{k:v for k,v in kwargs.items() if k!="trust_env"})
        with patch.dict("os.environ", {"RIU_API_KEY": "FAKE-ACCESS", "BRIDGE_PORT": "7870"}), patch.object(p.httpx, "AsyncClient", mocked):
            salida = asyncio.run(p.llamar("anadir", {"proveedor": "groq", "secret": "gsk_fake_1234567"}))
        self.assertTrue(salida["ok"])
        self.assertNotIn("secret", salida)
        self.assertEqual(recibido, [("http://127.0.0.1:7870/v1/credenciales", "FAKE-ACCESS")])

    def test_sin_acceso_interno_no_da_permiso_de_escritura(self):
        with patch.dict("os.environ", {"RIU_API_KEY": "", "BRIDGE_PORT": "7870"}):
            with self.assertRaises(HTTPException) as exc:
                asyncio.run(p.llamar("catalogo", {}))
        self.assertEqual(exc.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()
