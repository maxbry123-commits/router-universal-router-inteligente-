"""Escalado bajo demanda: umbral 85 %, maximo 3 destinos, cola, despertar lento, reintentos y resultado entre procesos (todo simulado: sin HF ni red)."""
import asyncio
import os
import time
import unittest
from unittest.mock import patch
from mvp import escalado, trabajos
from mvp.test_control import Base, servicio

A, B = "https://a.hf.space", "https://b.hf.space"
CAB = {"x-api-key": "api-ficticia"}


class Umbral(unittest.TestCase):
    def setUp(self):
        escalado._uso.clear(); escalado._caida.clear(); escalado._vuelo.clear()
        self.env = patch.dict(os.environ, {"RIU_SCALE_TARGETS": A + "," + B + ",https://c.hf.space," + A})
        self.env.start()

    def tearDown(self): self.env.stop()

    def elegir(self, cpu_local, cpus=None):
        async def sonda(url, clave): return (cpus or {}).get(url)
        with patch("mvp.escalado.cpu_local", return_value=cpu_local), patch("mvp.escalado.sonda", sonda):
            return asyncio.run(escalado.elegir("k"))

    def test_maximo_tres_servidores(self):
        self.assertEqual(escalado.remotos(), [A, B])  # local + 2 = 3; el cuarto y los duplicados se ignoran
        with patch.dict(os.environ, {"RIU_SCALE_TARGETS": "http://x, " + A}):
            self.assertEqual(escalado.remotos(), [A])  # solo https; ningun destino inventado

    def test_bajo_85_es_local_y_en_85_pasa_al_siguiente(self):
        self.assertEqual(self.elegir(84.9), "local")
        self.assertEqual(self.elegir(85.0), A)  # dormido: se despierta con el trabajo, sin sondearlo
        escalado._uso[A] = time.time()
        self.assertEqual(self.elegir(90, {A: 85.0}), B)  # A despierto y al 85 %: siguiente
        self.assertEqual(self.elegir(90, {A: 40.0}), A)

    def test_todos_ocupados_queda_en_cola(self):
        escalado._uso[A] = escalado._uso[B] = time.time()
        self.assertIsNone(self.elegir(99, {A: 99.0, B: 91.0}))
        escalado._caida[A] = time.time()  # servidor no disponible: se salta 30 s
        self.assertEqual(self.elegir(99, {B: 10.0}), B)

    def test_capacidad_por_servidor(self):
        for _ in range(escalado.capacidad()): escalado.entrar("local")
        self.assertEqual(self.elegir(1), A)
        escalado.salir("local"); self.assertEqual(self.elegir(1), "local")

    def test_despertar_lento_reintenta_con_el_mismo_cuerpo(self):
        intentos = []
        def http(url, clave, cuerpo=None, timeout=60):
            intentos.append(cuerpo)
            if len(intentos) < 3: raise OSError("despertando")
            return {"result": {"estado": "procesando", "proceso_id": "p-x"}}
        async def sin_pausa(_): return None
        with patch("mvp.escalado._http", http), patch("mvp.escalado.asyncio.sleep", sin_pausa):
            r = asyncio.run(escalado.enviar(A, "k", "chat_async", {"request_id": "x"}))
        self.assertEqual(r["proceso_id"], "p-x"); self.assertEqual(intentos, [{"request_id": "x"}] * 3)

    def test_destino_caido_da_error_y_se_marca(self):
        async def sin_pausa(_): return None
        with patch("mvp.escalado._http", side_effect=OSError("caido")), patch("mvp.escalado.asyncio.sleep", sin_pausa), patch("mvp.escalado.ESPERA_DESPERTAR", -1):
            with self.assertRaises(escalado.DestinoError): asyncio.run(escalado.enviar(A, "k", "chat_async", {}))
        self.assertIn(A, escalado._caida)


class Circuito(Base):
    def setUp(self):
        super().setUp()
        escalado._uso.clear(); escalado._caida.clear(); escalado._vuelo.clear(); servicio.TRABAJOS.clear(); servicio._PROPIOS.clear()
        self.env = patch.dict(os.environ, {"RIU_SCALE_TARGETS": A, "RIU_DEEPSEEK_HARNESS_URL": "http://127.0.0.1:1"}); self.env.start()
        self.banco.datos["RIU_API_KEY"] = "clave-harness"
        self.client.__enter__()  # un solo bucle de eventos: las tareas en segundo plano sobreviven entre peticiones

    def tearDown(self): self.client.__exit__(None, None, None); self.env.stop(); super().tearDown()

    def post(self, accion, cuerpo): return self.client.post("/plugins/puente_chat/call/" + accion, headers=CAB, json=cuerpo).json()["result"]

    def test_trabajo_va_al_siguiente_servidor_y_su_resultado_es_recuperable(self):
        llamadas = []
        def http(url, clave, cuerpo=None, timeout=60):
            llamadas.append((url, cuerpo))
            if url.endswith("/chat_async"): return {"result": {"estado": "procesando", "proceso_id": cuerpo["request_id"] and "p-" + cuerpo["request_id"]}}
            return {"result": {"estado": "completado", "proceso_id": "p-r1", "choices": [{"message": {"content": "desde A"}}], "finish_reason": "stop"}}
        with patch("mvp.escalado.cpu_local", return_value=99.0), patch("mvp.escalado._http", http):
            pid = self.post("chat_async", {"message": "hola", "request_id": "r1"})["proceso_id"]
            self.assertEqual(self.post("chat_async", {"message": "hola", "request_id": "r1"})["proceso_id"], pid)  # reintento: sin doble ejecucion
            for _ in range(10):
                r = self.post("resultado", {"proceso_id": pid, "espera": 1})
                if r["estado"] != "procesando": break
        self.assertEqual(r["estado"], "completado", (r, escalado._vuelo, escalado._caida))
        self.assertEqual(r["choices"][0]["message"]["content"], "desde A")
        self.assertEqual(sum(1 for u, _ in llamadas if u.endswith("/chat_async")), 1)
        servicio.TRABAJOS.clear()  # otro proceso: sin memoria local, lo recupera del almacen
        self.assertEqual(self.post("resultado", {"proceso_id": pid})["choices"][0]["message"]["content"], "desde A")
        self.assertEqual(self.client.post("/plugins/puente_chat/call/resultado", headers=CAB, json={"proceso_id": "p-nunca"}).status_code, 404)

    def test_sin_capacidad_el_trabajo_espera_en_cola_y_sigue_vivo(self):
        escalado._caida[A] = time.time()
        with patch("mvp.escalado.cpu_local", return_value=99.0):
            pid = self.post("chat_async", {"message": "hola", "request_id": "cola"})["proceso_id"]
            time.sleep(0.3)
            r = self.post("resultado", {"proceso_id": pid})
        self.assertEqual((r["estado"], r.get("subestado")), ("procesando", "en_cola"))

    def test_trabajo_local_interrumpido_se_reejecuta(self):
        trabajos.guardar(self.banco, "p-viejo", {"estado": "procesando", "proceso_id": "p-viejo", "creado": time.time() - 5000})
        self.assertFalse(asyncio.run(servicio._recuperar("p-viejo")))
