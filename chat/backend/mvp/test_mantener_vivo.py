"""Tarea larga en curso: el Space se pide /health a si mismo y se reporta en /health; el latido se detiene solo."""
import asyncio
import os
from unittest.mock import patch
from mvp import mantener_vivo as mv
from mvp.test_control import Base, CAB, servicio


class Latido(Base):
    def test_el_latido_pega_mientras_hay_tareas_y_se_detiene_al_terminar(self):
        pings, quedan = [], [3]
        def contar():
            quedan[0] -= 1
            return quedan[0] >= 0
        async def correr():
            with patch.object(mv, "LATIDO_S", 0), patch.dict(os.environ, {"SPACE_HOST": "demo.hf.space"}):
                self.assertTrue(mv.asegurar(contar, lambda url: pings.append(url) or True))
                await mv._tarea
        asyncio.run(correr())
        self.assertEqual(pings, ["https://demo.hf.space/health"] * 3)
        self.assertTrue(mv.ULTIMO["ok"])

    def test_no_arranca_dos_latidos(self):
        async def correr():
            with patch.object(mv, "LATIDO_S", 0.05):
                self.assertTrue(mv.asegurar(lambda: True, lambda u: True))
                self.assertFalse(mv.asegurar(lambda: True, lambda u: True))
                mv._tarea.cancel()
        asyncio.run(correr())

    def test_health_con_clave_cuenta_las_tareas_en_curso(self):
        servicio.app.state.commit = "prueba"
        servicio.TRABAJOS["p-uno"] = {"estado": "procesando"}
        servicio.TRABAJOS["p-dos"] = {"estado": "completado"}
        try:
            r = self.client.get("/health", headers=CAB).json()
            self.assertEqual(r["tareas_en_curso"], 1)
            self.assertNotIn("tareas_en_curso", self.client.get("/health").json())  # sin clave no se ve nada de esto
        finally:
            servicio.TRABAJOS.pop("p-uno", None); servicio.TRABAJOS.pop("p-dos", None)

    def test_los_procesos_del_loop_tambien_cuentan(self):
        class F:
            def __init__(self, d): self.d = d
            def done(self): return self.d
        class M: _PROC = {"a": F(False), "b": F(True), "c": F(False)}
        with patch.dict(servicio.loop_puente._CARGADOS, {"nct_loop": M}):
            self.assertEqual(servicio.loop_puente.en_curso(), 2)
