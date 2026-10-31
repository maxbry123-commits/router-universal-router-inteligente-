"""Autenticacion del Router: clave no ASCII = 401 (no 500), el 401 no revela longitudes, y ?key= solo vale en el endpoint MCP. Claves de prueba ficticias."""
import json
from mvp.test_control import Base, servicio


class AuthClave(Base):
    def test_clave_no_ascii_en_cabecera_es_401_no_500(self):
        for cab in ({"X-API-Key": "clavé-ñ".encode("latin-1", "ignore")}, {"X-API-Key": b"cl\xe9"}, {"Authorization": b"Bearer cl\xe9\xf1"}):
            r = self.client.get("/chat/providers", headers=cab)
            self.assertEqual(r.status_code, 401, (cab, r.text))

    def test_clave_no_ascii_en_la_url_del_mcp_es_401(self):
        r = self.client.post("/mcp?key=cl%C3%A9-%E2%82%AC", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        self.assertEqual(r.status_code, 401)

    def test_autorizado_con_str_no_ascii_devuelve_false_y_la_clave_buena_sigue_pasando(self):
        self.assertFalse(servicio.autorizado(None, "clavé"))
        self.assertFalse(servicio.autorizado("Bearer ñandú", None))
        self.assertTrue(servicio.autorizado(None, "api-ficticia"))
        self.assertTrue(servicio.autorizado("Bearer api-ficticia", None))
        with self.subTest("clave esperada tambien no ASCII"):
            from unittest.mock import patch
            import os
            with patch.dict(os.environ, {"RIU_MCP_KEY": "clavé-esperada"}):
                self.assertTrue(servicio.autorizado(None, "clavé-esperada"))
                self.assertFalse(servicio.autorizado(None, "clavé-otra"))

    def test_el_401_no_revela_longitudes(self):
        r = self.client.get("/chat/providers", headers={"X-API-Key": "mala-123456", "Authorization": "Bearer otra"})
        self.assertEqual(r.status_code, 401)
        detalle = r.json()["detail"]
        self.assertNotRegex(detalle, r"\d+\s*car")
        self.assertNotIn("10", detalle); self.assertNotIn("recibido", detalle)
        self.assertIn("clave de acceso invalida", detalle)

    def test_key_en_la_url_solo_abre_el_endpoint_mcp(self):
        r = self.client.post("/mcp?key=api-ficticia", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        self.assertEqual(r.status_code, 200)
        for ruta in ("/chat/providers", "/chat/agents", "/chat/swe/capacidades", "/memoria/load"):
            r = self.client.get(ruta + "?key=api-ficticia")
            self.assertEqual(r.status_code, 401, ruta)
        r = self.client.post("/almacen?key=api-ficticia", json={})
        self.assertEqual(r.status_code, 401)
        # con la cabecera sigue funcionando en los demas
        r = self.client.get("/chat/providers", headers={"X-API-Key": "api-ficticia"})
        self.assertEqual(r.status_code, 200)

    def test_cabecera_en_mcp_sigue_valiendo(self):
        r = self.client.post("/mcp", headers={"X-API-Key": "api-ficticia"}, json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        self.assertEqual(r.status_code, 200)
