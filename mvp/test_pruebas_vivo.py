"""El ejecutor de pruebas reales debe seguir corriendo de punta a punta (con un Router simulado) y dejar su informe."""
import os
import tempfile
import unittest
from unittest.mock import patch
from mvp.pruebas_vivo import correr, pruebas


class ClienteFalso:
    def __init__(self, base, clave): self.n = 0
    def health(self): return {"status": "ok", "commit": "x"}
    def mcp(self, metodo, params=None): return 200, {"result": {"tools": [{"name": "chat"}]}}
    def post(self, ruta, cuerpo, timeout=60): return 200, {}
    def herramienta(self, nombre, args): return True, {"pendientes": [], "texto": ""}
    def chat(self, modelo, mensaje=None, rid="x", vueltas=20, **extra):
        return {"estado": "completado", "choices": [{"message": {"content": "PONG-%s 391 42" % modelo}}]}


class Ejecutor(unittest.TestCase):
    def test_corre_completo_y_escribe_el_informe(self):
        pruebas.FILAS.clear()
        with tempfile.TemporaryDirectory() as d, patch("mvp.pruebas_vivo.correr.Cliente", ClienteFalso), patch.dict(os.environ, {"RIU_KEY": "k"}):
            antes = os.getcwd(); os.chdir(d)
            try:
                correr.main(["correr", "--solo", "glm-5.3"])
                informe = open("informe_sol.md", encoding="utf-8").read()
            finally:
                os.chdir(antes)
        self.assertIn("glm-5.3", informe)
        self.assertTrue(any(f["prueba"] == "eco" and f["estado"] == "PASS" for f in pruebas.FILAS))
        self.assertEqual(sum(1 for f in pruebas.FILAS if f["prueba"] == "tool github escribir"), 1)  # una sola vez
