"""Pruebas sin red: /chat/agents refleja el catalogo unico y el estado REAL del Harness."""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fastapi.testclient import TestClient
from mvp import app as servicio
from agentes.adaptadores.modelos import AGENTES

CLAVE = "clave-catalogo-ficticia"


class CatalogoAgentes(unittest.TestCase):
    def pedir(self, capacidades, cabeceras=None):
        async def fake_capacidades():
            return capacidades

        with patch.dict(os.environ, {"RIU_API_KEY": CLAVE, "MVP_PLAN": "personal"}):
            with patch.object(servicio, "swe_capacidades", fake_capacidades):
                cliente = TestClient(servicio.app)
                try:
                    return cliente.get("/chat/agents", headers=cabeceras or {})
                finally:
                    cliente.close()

    def test_no_publica_catalogo_sin_autenticacion(self):
        r = self.pedir({"harness": "ok", "agentes": {}}, {})
        self.assertEqual(r.status_code, 401)

    def test_seis_agentes_aparecen_aun_sin_harness_sin_inventar_disponibilidad(self):
        r = self.pedir({"harness": "no_disponible", "agentes": {}}, {"x-api-key": CLAVE})
        self.assertEqual(r.status_code, 200, r.text)
        j = r.json()
        self.assertEqual({a["id"] for a in j["agents"]}, set(AGENTES))
        self.assertEqual(len(j["agents"]), 6)
        self.assertEqual(j["harness"], "no_disponible")
        self.assertTrue(all(a["estado"] == "SIN VERIFICAR" and a["disponible"] is False for a in j["agents"]))

    def test_disponibilidad_proviene_del_harness_no_del_frontend(self):
        estados = {"codex": {"disponible": True, "estado": "DISPONIBLE"},
                   "openclaw": {"disponible": True, "estado": "SIN VERIFICAR"},
                   "openhands": {"disponible": False, "estado": "NO INSTALADO", "motivo": "sdk_ausente"}}
        j = self.pedir({"harness": "ok", "agentes": estados}, {"x-api-key": CLAVE}).json()
        por_id = {a["id"]: a for a in j["agents"]}
        self.assertTrue(por_id["codex"]["disponible"])
        self.assertFalse(por_id["openclaw"]["disponible"])
        self.assertEqual(por_id["openclaw"]["estado"], "SIN VERIFICAR")
        self.assertEqual(por_id["openhands"]["estado"], "NO INSTALADO")
        self.assertFalse(por_id["claude-code"]["disponible"])


if __name__ == "__main__":
    unittest.main()
