"""Tarea larga en curso: el Space se pide /health a si mismo y se reporta en /health; el latido se detiene solo."""
import asyncio
import os
from unittest.mock import patch
from mvp import mantener_vivo as mv
from mvp.test_control import Base, CAB, servicio


class Latido(Base):
    def setUp(self):
        super().setUp(); mv._tarea = None; mv.HASTA["t"] = 0.0  # una tarea de otro bucle de eventos no cuenta

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


class SinVercel(Base):
    def setUp(self):
        super().setUp(); mv._tarea = None; mv.HASTA["t"] = 0.0

    def test_el_router_sirve_el_chat_y_no_sale_de_su_carpeta(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("<html", r.text.lower())
        self.assertEqual(r.headers["cache-control"], "no-cache")
        js = self.client.get("/chat/ui/api.js")
        self.assertIn("RIU_PLUGIN", js.text)
        fuera = self.client.get("/chat/ui/..%2F..%2Fbackend%2Fmvp%2Fapp.py")
        self.assertNotIn("FastAPI(", fuera.text)          # un archivo fuera de chat/frontend nunca se entrega
        self.assertEqual(self.client.get("/chat/ui/no-existe.js").text, r.text)  # lo que no existe devuelve el chat

    def test_mantener_encendido_24_horas_sin_tareas(self):
        import time
        r = self.client.post("/plugins/puente_chat/call/mantener_encendido", headers=CAB, json={"horas": 24})
        hasta = r.json()["result"]["hasta"]
        self.assertAlmostEqual(hasta - time.time(), 24 * 3600, delta=60)
        self.assertEqual(self.client.get("/health", headers=CAB).json()["mantener_hasta"], hasta)
        self.assertEqual(self.client.post("/plugins/puente_chat/call/mantener_encendido", headers=CAB, json={"horas": "x"}).status_code, 400)
        self.assertEqual(self.client.post("/plugins/puente_chat/call/mantener_encendido", json={"horas": 1}).status_code, 401)

    def test_el_latido_sigue_sin_tareas_mientras_dure_el_plazo(self):
        import time
        pings = []
        async def correr():
            with patch.object(mv, "LATIDO_S", 0), patch.dict(os.environ, {"SPACE_HOST": "demo.hf.space"}):
                mv.HASTA["t"] = time.time() + 0.05
                mv.asegurar(lambda: 0, lambda url: pings.append(url) or True)
                await mv._tarea
        asyncio.run(correr())
        self.assertGreaterEqual(len(pings), 1)           # con 0 tareas, igual late mientras no venza el plazo
        mv.HASTA["t"] = 0.0

    def test_un_millon_de_tokens_cabe_en_una_peticion(self):
        enorme = [{"role": "user", "content": "a" * 3_900_000}]   # ~975.000 tokens
        async def modelo(mensajes, modelo, opciones):
            return {"texto": "ok", "tool_calls": [], "finish_reason": "stop"}
        with patch.object(servicio, "_llamar_modelo", modelo):
            r = self.client.post("/chat", headers=CAB, json={"mensajes": enorme})
        self.assertEqual(r.status_code, 200, r.text[:200])
