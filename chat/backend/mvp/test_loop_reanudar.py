"""El LOOP sobrevive a un reinicio: el pedido se guarda, se relanza al arrancar y el chat sigue con el id viejo."""
import asyncio
from concurrent.futures import Future
from unittest.mock import patch
from mvp import estado_tarea, loop_puente, loop_reanudar as lr
from mvp.test_control import Base, servicio


class Modulo:
    _PROC = {}


class LoopReanudar(Base):
    def setUp(self):
        super().setUp(); lr.ALIAS.clear(); Modulo._PROC = {}

    def tearDown(self):
        real = loop_puente._CARGADOS.get("nct_loop")
        getattr(real, "_PROC", {}).clear()   # el gobernar real de la prueba HTTP no debe contar en otras pruebas
        super().tearDown()

    def test_se_guarda_mientras_corre_y_se_borra_al_terminar(self):
        f = Future(); Modulo._PROC = {"gob-1": f}
        with patch.dict(loop_puente._CARGADOS, {"nct_loop": Modulo}):
            clave = asyncio.run(lr.registrar(self.banco, "nct_loop", "gobernar", {"objetivo": "hazlo"}, {"estado": "procesando", "proceso_id": "gob-1"}))
            self.assertEqual(clave, "loop-gob-1")
            self.assertIn("loop-gob-1", estado_tarea.pendientes(self.banco))
            f.set_result({"status": "DONE_VERIFICADO"})
        self.assertNotIn("loop-gob-1", estado_tarea.pendientes(self.banco))   # termino: ya no hay nada que retomar

    def test_un_proceso_que_termina_con_error_tambien_se_borra(self):
        f = Future(); Modulo._PROC = {"gob-2": f}
        with patch.dict(loop_puente._CARGADOS, {"nct_loop": Modulo}):
            asyncio.run(lr.registrar(self.banco, "nct_loop", "gobernar", {"objetivo": "x"}, {"proceso_id": "gob-2"}))
            f.set_exception(RuntimeError("fallo"))
        self.assertEqual(estado_tarea.pendientes(self.banco), {})

    def test_no_se_guardan_acciones_de_consulta_ni_errores(self):
        for accion, res in (("estado", {"estado": "procesando", "proceso_id": "gob-3"}), ("gobernar", {"error": "falta objetivo"})):
            self.assertIsNone(asyncio.run(lr.registrar(self.banco, "nct_loop", accion, {}, res)))
        self.assertEqual(estado_tarea.pendientes(self.banco), {})

    def test_tras_el_reinicio_se_relanza_y_el_id_viejo_apunta_al_nuevo(self):
        estado_tarea.guardar(self.banco, "loop-gob-9", {"plugin": "nct_loop", "accion": "gobernar", "cuerpo": {"objetivo": "hazlo"}, "pids": ["gob-9"], "grupo": None})
        estado_tarea.marcar(self.banco, "loop-gob-9", True)
        lanzados = []
        Modulo._PROC = {"gob-nuevo": Future()}   # el proceso retomado sigue corriendo
        async def llamar(plugin, accion, cuerpo):
            lanzados.append((plugin, accion, cuerpo)); return {"estado": "procesando", "proceso_id": "gob-nuevo"}
        with patch.object(loop_puente, "llamar", llamar), patch.dict(loop_puente._CARGADOS, {"nct_loop": Modulo}):
            asyncio.run(lr.reanudar_todas(self.banco))
        self.assertEqual(lanzados, [("nct_loop", "gobernar", {"objetivo": "hazlo"})])
        self.assertEqual(lr.traducir({"proceso_id": "gob-9"}), {"proceso_id": "gob-nuevo"})   # el chat sigue preguntando por el viejo
        pend = estado_tarea.pendientes(self.banco)
        self.assertNotIn("loop-gob-9", pend)
        self.assertIn("loop-gob-nuevo", pend)                                                  # y el nuevo queda protegido por si hay otro reinicio

    def test_paralelo_traduce_el_grupo_y_cada_proceso(self):
        estado_tarea.guardar(self.banco, "loop-par-1", {"plugin": "nct_loop", "accion": "paralelo", "cuerpo": {"objetivos": ["a", "b"]}, "pids": ["gob-a", "gob-b"], "grupo": "par-1"})
        estado_tarea.marcar(self.banco, "loop-par-1", True)
        async def llamar(plugin, accion, cuerpo):
            return {"estado": "procesando", "grupo_id": "par-2", "procesos": ["gob-c", "gob-d"]}
        with patch.object(loop_puente, "llamar", llamar), patch.dict(loop_puente._CARGADOS, {"nct_loop": Modulo}):
            asyncio.run(lr.reanudar_todas(self.banco))
        self.assertEqual(lr.traducir({"grupo_id": "par-1"}), {"grupo_id": "par-2"})
        self.assertEqual(lr.traducir({"proceso_id": "gob-b"}), {"proceso_id": "gob-d"})

    def test_por_http_un_gobernar_real_queda_registrado(self):
        r = self.client.post("/plugins/nct_loop/call/gobernar", headers={"x-api-key": "api-ficticia"}, json={"objetivo": "Crear evidencia real"})
        self.assertEqual(r.status_code, 200)
        pid = r.json()["result"]["proceso_id"]
        self.assertIn("loop-" + pid, estado_tarea.pendientes(self.banco))
        self.client.post("/plugins/nct_loop/call/cancelar", headers={"x-api-key": "api-ficticia"}, json={"proceso_id": pid})
