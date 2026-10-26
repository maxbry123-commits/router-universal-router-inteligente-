"""Tarea larga + reinicio del Space: el historial se guarda en el almacen permanente y la tarea se retoma sola."""
import asyncio
import json
from unittest.mock import patch
from mvp import estado_tarea
from mvp.test_control import Base, servicio

PAUSA = {"continuar": True, "finish_reason": "pausa_herramientas", "texto": "", "tool_calls": [], "herramientas_usadas": ["almacen"],
         "mensajes": [{"role": "user", "content": "hazlo"}, {"role": "tool", "content": "resultado de herramienta"}]}
FIN = {"texto": "listo", "tool_calls": [], "finish_reason": "stop", "herramientas_usadas": []}


class Reanudar(Base):
    def correr(self, coro):
        with patch.object(servicio, "clave_harness", lambda: "k"):
            return asyncio.run(coro)

    def test_guardar_y_leer_un_estado_de_varios_megas_sin_credenciales(self):
        grande = [{"role": "tool", "content": ("dato %d " % i) * 3000 + "ghp_ABCDEFGHIJKLMNOPQRSTUV"} for i in range(40)]
        import os
        # texto casi incompresible para forzar varios pedazos
        grande.append({"role": "tool", "content": os.urandom(900_000).hex()})
        self.assertTrue(estado_tarea.guardar(self.banco, "p-x", {"mensajes": grande, "acumulado": "a"}))
        pedazos = [k for k in self.nube if k.startswith("tareas/p-x/") and k != "tareas/p-x/meta.json"]
        self.assertGreater(len(pedazos), 1)
        self.assertTrue(all(len(self.nube[k]) <= 600_000 for k in pedazos))
        est = estado_tarea.leer(self.banco, "p-x")
        self.assertEqual(len(est["mensajes"]), 41)
        self.assertNotIn("ghp_", json.dumps(est))
        self.assertIn("[REDACTADO]", est["mensajes"][0]["content"])

    def test_cada_pausa_guarda_el_historial_y_al_terminar_se_limpia_el_indice(self):
        salidas = [{"result": dict(PAUSA)}, {"result": dict(PAUSA)}, {"result": dict(FIN)}]
        vistos = []
        def llm(clave, mensajes, modelo, opciones=None, controles=None):
            vistos.append(estado_tarea.pendientes(self.banco))
            return salidas.pop(0)
        async def tarea():
            servicio._PID.set("p-largo")
            return await servicio.chat({"modelo": "qwen3.8-max", "mensajes": [{"role": "user", "content": "hazlo"}], "via": "harness"})
        with patch.object(servicio.harness_client, "llm", llm):
            r = self.correr(tarea())
        self.assertEqual(r["texto"], "listo")
        self.assertEqual(vistos, [{"p-largo": 1}] * 3)               # durante toda la tarea estaba marcada como pendiente
        self.assertEqual(estado_tarea.pendientes(self.banco), {})    # terminada: nada que retomar
        self.assertEqual(estado_tarea.leer(self.banco, "p-largo")["mensajes"][-1]["content"], "resultado de herramienta")

    def test_tras_un_reinicio_la_tarea_se_retoma_con_el_historial_guardado(self):
        estado_tarea.guardar(self.banco, "p-caida", {"mensajes": PAUSA["mensajes"], "acumulado": "", "usadas": ["almacen"], "modelo": "qwen3.8-max",
                                                      "opciones": None, "controles": {}, "limite": 9e12})
        estado_tarea.marcar(self.banco, "p-caida", True)
        servicio.TRABAJOS.pop("p-caida", None)          # el proceso nuevo no sabe nada de ella
        recibidos = []
        def llm(clave, mensajes, modelo, opciones=None, controles=None):
            recibidos.append(list(mensajes))
            return {"result": dict(FIN)}
        with patch.object(servicio.harness_client, "llm", llm):
            self.correr(servicio._reanudar_todas()); self.correr(servicio._reanudar("p-caida"))
        t = servicio.TRABAJOS["p-caida"]
        self.assertEqual(t["estado"], "completado")
        self.assertTrue(t["reanudado"])
        self.assertEqual(t["choices"][0]["message"]["content"], "listo")
        self.assertEqual(recibidos[0][-1]["content"], "resultado de herramienta")   # retomo con lo ya hecho, no desde cero
        self.assertEqual(estado_tarea.pendientes(self.banco), {})
        servicio.TRABAJOS.pop("p-caida", None)

    def test_una_tarea_que_termina_en_error_no_se_retoma(self):
        def llm(clave, mensajes, modelo, opciones=None, controles=None):
            raise RuntimeError("Harness no disponible")
        async def tarea():
            servicio._PID.set("p-mala")
            with self.assertRaises(servicio.HTTPException):
                await servicio.chat({"modelo": "qwen3.8-max", "mensajes": [{"role": "user", "content": "x"}], "via": "harness"})
        with patch.object(servicio.harness_client, "llm", llm):
            self.correr(tarea())
        self.assertEqual(estado_tarea.pendientes(self.banco), {})

    def test_sin_estado_guardado_se_descarta_del_indice(self):
        estado_tarea.marcar(self.banco, "p-fantasma", True)
        self.correr(servicio._reanudar("p-fantasma"))
        self.assertEqual(estado_tarea.pendientes(self.banco), {})
        self.assertNotIn("p-fantasma", servicio.TRABAJOS)

    def test_el_arranque_del_servidor_retoma_las_pendientes(self):  # lifespan real: lo que pasa tras un reinicio del Space
        import time
        estado_tarea.guardar(self.banco, "p-arranque", {"mensajes": PAUSA["mensajes"], "acumulado": "", "usadas": [], "modelo": "qwen3.8-max",
                                                         "opciones": None, "controles": {}, "limite": 9e12})
        estado_tarea.marcar(self.banco, "p-arranque", True)
        servicio.TRABAJOS.pop("p-arranque", None)
        self.client.close()
        from fastapi.testclient import TestClient
        with patch.object(servicio.harness_client, "llm", lambda *a, **k: {"result": dict(FIN)}), patch.object(servicio, "clave_harness", lambda: "k"):
            with TestClient(servicio.app):
                for _ in range(50):
                    if servicio.TRABAJOS.get("p-arranque", {}).get("estado") == "completado":
                        break
                    time.sleep(0.1)
        self.assertEqual(servicio.TRABAJOS["p-arranque"]["estado"], "completado")
        servicio.TRABAJOS.pop("p-arranque", None)
        self.client = TestClient(servicio.app)
