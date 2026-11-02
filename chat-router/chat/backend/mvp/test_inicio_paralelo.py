"""El inicio en un Space con HF lento no acumula las esperas de control y preferencias."""
import asyncio
import time
import unittest
from unittest.mock import patch, Mock

from mvp import app as mvp_app


class TestInicioParalelo(unittest.TestCase):
    def test_esperas_independientes_se_solapan_sin_perder_control(self):
        async def lenta():
            await asyncio.sleep(0.08)
        def preferencia(_):
            time.sleep(0.08)
            return False

        class Banco:
            pass
        with patch.object(mvp_app.bank, "abrir_desde_env", return_value=Banco()), \
             patch.object(mvp_app.CONTROL, "cargar", side_effect=lenta) as control, \
             patch.object(mvp_app.mantener_vivo, "leer", side_effect=preferencia), \
             patch.object(mvp_app.mantener_vivo, "mantener", return_value=None), \
             patch.object(mvp_app, "_lanzar", return_value=None), \
             patch.object(mvp_app.subprocess, "run", return_value=Mock(returncode=1,stdout="")):
            async def arrancar():
                async with mvp_app.inicio(mvp_app.app):
                    self.assertFalse(mvp_app.mantener_vivo.SIEMPRE["on"])
            a = time.monotonic()
            asyncio.run(arrancar())
            diferencia = time.monotonic() - a
        control.assert_awaited_once()
        self.assertLess(diferencia, 0.15, "dos esperas no deben sumarse")
