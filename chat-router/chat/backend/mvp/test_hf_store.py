"""hf_store: cada operación usa un HfFileSystem nuevo (sin la caché de directorios que hacía fallar «leer» justo después de «guardar»)
y «no existe» se distingue de un fallo de red (NoExiste) para que /memoria no pise un historial que no pudo leer."""
import unittest
from unittest.mock import patch
from mvp import hf_store


class Falso:
    archivos, creados = {}, []
    def __init__(self, token=None, skip_instance_cache=False):
        Falso.creados.append(skip_instance_cache)
    def open(self, ruta, modo):
        fs = self
        class A:
            def __enter__(s): return s
            def __exit__(s, *a): return False
            def write(s, b): Falso.archivos[ruta] = b
            def read(s):
                if ruta not in Falso.archivos: raise FileNotFoundError(ruta)
                return Falso.archivos[ruta]
        return A()


class TestHF(unittest.TestCase):
    def test_leer_despues_de_guardar_con_instancia_nueva(self):
        with patch.object(hf_store, "HfFileSystem", Falso):
            hf_store.guardar("hf-x", "prueba/a.json", "ok")
            self.assertEqual(hf_store.leer("hf-x", "prueba/a.json")["valor"], "ok")
        self.assertTrue(all(Falso.creados))

    def test_no_existe_es_distinto_de_fallo(self):
        with patch.object(hf_store, "HfFileSystem", Falso):
            with self.assertRaises(hf_store.NoExiste):
                hf_store.leer("hf-x", "prueba/nada.json")
        self.assertTrue(issubclass(hf_store.NoExiste, RuntimeError))  # quien ya captura RuntimeError sigue igual


if __name__ == "__main__":
    unittest.main()
