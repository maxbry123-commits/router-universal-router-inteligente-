"""Trabajos en curso no vencen por tiempo: el resultado sigue consultable."""
import asyncio
import unittest
from unittest.mock import patch
from mvp import app as servicio, estado_tarea
from mvp.test_control import Base


class TrabajoSinVence(Base):
    def test_por_defecto_un_proceso_largo_no_vence(self):
        estado_tarea.marcar(self.banco, "p-lento", True)
        servicio.TRABAJOS.pop("p-lento", None)
        doc = {"estado": "procesando", "proceso_id": "p-lento", "creado": 1, "proceso_remoto": "r1", "destino": "http://a"}
        with patch.object(servicio.trabajos, "leer", return_value=doc):
            self.assertTrue(asyncio.run(servicio._recuperar("p-lento")))
        self.assertEqual(servicio.TRABAJOS["p-lento"], doc)
        servicio.TRABAJOS.pop("p-lento", None)
        estado_tarea.marcar(self.banco, "p-lento", False)

    def test_vence_solo_si_se_configura(self):
        doc = {"estado": "procesando", "proceso_id": "p-vex", "creado": 1}
        with patch.object(servicio, "TRABAJO_VENCE", 900), patch.object(servicio.trabajos, "leer", return_value=doc):
            self.assertFalse(asyncio.run(servicio._recuperar("p-vex")))
