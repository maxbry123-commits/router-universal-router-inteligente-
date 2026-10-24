"""/memoria: respaldo del historial y de las pestañas del chat (contrato de chat-ancla.js) en el bucket HF."""
import unittest
from unittest.mock import patch
from test_control import Base, CAB


class TestMemoria(Base):
    def guardar(self, scope, key, data, codigo=200):
        r = self.client.post("/memoria/save", json={"scope": scope, "key": key, "data": data}, headers=CAB)
        self.assertEqual(r.status_code, codigo, r.text); return r.json()

    def test_guardar_y_cargar_la_ultima_version_de_la_llave(self):
        self.guardar("chat-ui:pestanas", "lista", {"chats": [{"sesion": "a"}], "borrados": []})
        self.guardar("chat-ui:pestanas", "lista", {"chats": [{"sesion": "b"}], "borrados": ["a"]})
        rs = self.client.get("/memoria/load", params={"scope": "chat-ui:pestanas", "key": "lista"}, headers=CAB).json()["records"]
        ultimo = max(rs, key=lambda r: r["id"])["data"]
        self.assertEqual(ultimo["chats"], [{"sesion": "b"}])

    def test_buscar_devuelve_todos_los_mensajes_del_scope(self):
        for i, rol in enumerate(("user", "bot")):
            self.guardar("chat-ui:hist:web-1", "m-%d-%s" % (i, rol), {"rol": rol, "texto": "hola %d" % i, "ts": i + 1})
        r = self.client.get("/memoria/search", params={"scope": "chat-ui:hist:web-1", "query": "", "k": 100000}, headers=CAB).json()
        self.assertEqual(sorted(f["data"]["texto"] for f in r["results"]["sqlite"]), ["hola 0", "hola 1"])

    def test_persiste_en_el_bucket_y_sobrevive_al_reinicio(self):
        self.guardar("chat-ui:hist:web-2", "m-1-user", {"rol": "user", "texto": "x", "ts": 1})
        from mvp import memoria; memoria.CACHE.clear()
        r = self.client.get("/memoria/search", params={"scope": "chat-ui:hist:web-2"}, headers=CAB).json()
        self.assertEqual(len(r["results"]["sqlite"]), 1)

    def test_oculta_credenciales_en_vez_de_bloquear_la_cola(self):
        self.guardar("chat-ui:hist:web-3", "m-1-user", {"rol": "user", "texto": "mi token ghp_ABCDEFGHIJKLMNOPQRST", "ts": 1})
        r = self.client.get("/memoria/search", params={"scope": "chat-ui:hist:web-3"}, headers=CAB).json()
        self.assertNotIn("ghp_", r["results"]["sqlite"][0]["data"]["texto"])

    def test_sin_clave_401_y_scope_vacio_400(self):
        self.assertEqual(self.client.post("/memoria/save", json={"scope": "s", "key": "k", "data": {}}).status_code, 401)
        self.guardar("", "k", {}, 400)

    def test_fallo_de_lectura_no_pisa_el_historial(self):
        self.guardar("chat-ui:hist:web-4", "m-1-user", {"rol": "user", "texto": "valioso", "ts": 1})
        from mvp import memoria; memoria.CACHE.clear(); antes = dict(self.nube)
        with patch("mvp.app.hf_store.leer", side_effect=RuntimeError("fallo de lectura HF")):
            self.guardar("chat-ui:hist:web-4", "m-2-user", {"rol": "user", "texto": "x", "ts": 2}, 502)
        self.assertEqual(self.nube, antes)

    def test_scope_desconocido_devuelve_lista_vacia(self):
        r = self.client.get("/memoria/load", params={"scope": "nada", "key": "x"}, headers=CAB)
        self.assertEqual(r.status_code, 200); self.assertEqual(r.json()["records"], [])


if __name__ == "__main__":
    unittest.main()
