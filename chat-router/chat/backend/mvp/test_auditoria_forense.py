"""Auditoria forense (puntos 14-17, 19, 20): rotacion/cooldown de claves, redactor de claves, timeouts finitos, agentes y aprobador en YAIWES.
Servidores falsos en 127.0.0.1; claves inventadas; sin red real."""
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from fastapi.testclient import TestClient
from test_externos_nuevos import Entorno, ok, err, ID_GROQ, MSG
from mvp import app as servicio, compute, externos, harness_client as hc, hf_store

GSK = "gsk_" + "A1b2C3d4E5f6G7"  # 12+ alfanumericos: forma de clave de Groq, inventada
NVAPI = "nvapi-" + "Zz9_Yy8-Xx7_Ww6"  # forma de clave de NVIDIA, inventada


class TestRotacionYCooldown(Entorno):
    def setUp(self):
        super().setUp()
        externos.limpiar_enfriadas(); self.addCleanup(externos.limpiar_enfriadas)

    def test_402_rota_a_la_siguiente_clave(self):
        s = self.servidor("groq", lambda h, c: (err(402) if h.headers["Authorization"] == "Bearer gsk-ficticia" else ok("de la 2"))(h, c))
        with patch.dict(os.environ, {"GROQ_API_KEY_2": "gsk-ficticia-2"}):
            r = externos.llamar(MSG, ID_GROQ)
        self.assertEqual((r["texto"], [p["auth"] for p in s.peticiones]), ("de la 2", ["Bearer gsk-ficticia", "Bearer gsk-ficticia-2"]))

    def test_402_en_todas_las_claves_es_un_error_claro_sin_cambiar_de_modelo(self):
        self.servidor("groq", err(402))
        with patch.dict(os.environ, {"GROQ_API_KEY_2": "gsk-ficticia-2"}), self.assertRaisesRegex(RuntimeError, "ninguna de las 2 claves.*HTTP 402"):
            externos.llamar(MSG, ID_GROQ)

    def test_una_clave_con_429_se_enfria_entre_llamadas(self):
        s = self.servidor("groq", lambda h, c: (err(429, Retry_After="1") if h.headers["Authorization"] == "Bearer gsk-ficticia" else ok("de la 2"))(h, c))
        with patch.dict(os.environ, {"GROQ_API_KEY_2": "gsk-ficticia-2"}):
            externos.llamar(MSG, ID_GROQ)
            s.peticiones.clear()
            r = externos.llamar(MSG, ID_GROQ)
        self.assertEqual((r["texto"], [p["auth"] for p in s.peticiones]), ("de la 2", ["Bearer gsk-ficticia-2"]), "la clave enfriada no se vuelve a probar primero")

    def test_el_enfriamiento_caduca_y_la_clave_vuelve_a_su_sitio(self):
        s = self.servidor("groq", lambda h, c: (err(429) if h.headers["Authorization"] == "Bearer gsk-ficticia" else ok("de la 2"))(h, c))
        t = [1000.0]
        with patch.dict(os.environ, {"GROQ_API_KEY_2": "gsk-ficticia-2"}), patch.object(externos, "_reloj", lambda: t[0]):
            externos.llamar(MSG, ID_GROQ)
            t[0] += 61
            s.peticiones.clear(); s.guion[:] = [ok("de la 1")]
            r = externos.llamar(MSG, ID_GROQ)
        self.assertEqual((r["texto"], s.peticiones[0]["auth"]), ("de la 1", "Bearer gsk-ficticia"))

    def test_si_todas_estan_enfriadas_se_intenta_igual_y_el_estado_no_guarda_claves(self):
        s = self.servidor("groq", err(429), err(429), err(429), ok("ya paso"))
        with patch.object(externos, "_reloj", lambda: 5.0):
            with self.assertRaisesRegex(RuntimeError, "429"):
                externos.llamar(MSG, ID_GROQ)
            self.assertEqual(externos.llamar(MSG, ID_GROQ)["texto"], "ya paso")
        self.assertNotIn("gsk-ficticia", json.dumps([list(map(str, k)) for k in externos._ENFRIADAS]))

    def test_con_reintentos_nunca_devuelve_none(self):
        pol = externos._fusion(externos.POLITICA_DEFECTO, {"reintentos": {"max": 1}})
        payload = {"messages": [{"role": "user", "content": [{"type": "text", "text": "x"}, {"type": "image_url", "image_url": {"url": "data:,"}}]}]}
        def accion():
            raise externos.ErrorHTTP(400)
        with self.assertRaisesRegex(RuntimeError, "sin respuesta|HTTP 400"):
            externos._con_reintentos(accion, pol, payload, True)


class TestRedactores(unittest.TestCase):
    def test_hf_store_rechaza_claves_de_groq_y_nvidia(self):
        for v in (GSK, NVAPI, "texto " + GSK + " fin"):
            with self.assertRaisesRegex(ValueError, "credenciales"):
                hf_store.guardar("hf-ficticio", "tareas/x/valor.json", v)
        self.assertIsNone(hf_store.PATRON_CLAVE.search("gsk_corta"))
        self.assertIsNone(hf_store.PATRON_CLAVE.search("nvapi-corta"))

    def test_los_patrones_siguen_cubriendo_las_formas_anteriores(self):
        for v in ("sk-" + "a" * 14, "github_pat_" + "a" * 14, "ghp_" + "a" * 14, "hf_" + "a" * 22):
            self.assertTrue(hf_store.PATRON_CLAVE.search(v), v)


class TestTimeoutsFinitos(unittest.TestCase):
    def capturar(self, modulo, fn):
        visto = {}
        class R:
            def __enter__(s): return s
            def __exit__(s, *a): return False
            def read(s): return b'{"status": "ok", "result": {}, "choices": [{"message": {"content": "x"}}]}'
        def falso(solicitud, timeout=...):
            visto["timeout"] = timeout; return R()
        with patch.object(modulo.request, "urlopen", falso):
            fn()
        return visto["timeout"]

    def test_compute_usa_timeout_180_y_no_none(self):
        t = self.capturar(compute, lambda: compute._solicitar("http://127.0.0.1:9/v1/chat/completions", {"model": "m", "messages": []}, "k"))
        self.assertEqual(t, 180)

    def test_harness_cliente_30_s_para_lo_corto_y_largo_configurable_para_avanzar(self):
        with patch.dict(os.environ, {"RIU_DEEPSEEK_HARNESS_URL": "http://127.0.0.1:9"}):
            os.environ.pop("RIU_SWE_AVANZAR_TIMEOUT_MS", None)
            self.assertEqual(self.capturar(hc, lambda: hc.status("k")), 30)
            self.assertEqual(self.capturar(hc, lambda: hc.swe_invoke("k", "swe_estado", {"task_id": "t"})), 30)
            self.assertEqual(self.capturar(hc, lambda: hc.swe_invoke("k", "swe_iniciar", {"task_id": "t"})), 30)
            self.assertEqual(self.capturar(hc, lambda: hc.swe_invoke("k", "swe_avanzar", {"task_id": "t"})), 1800)
            self.assertEqual(self.capturar(hc, lambda: hc.swe_invoke("k", "swe_reanudar", {"task_id": "t"})), 1800)
            os.environ["RIU_SWE_AVANZAR_TIMEOUT_MS"] = "900000"
            self.assertEqual(self.capturar(hc, lambda: hc.swe_invoke("k", "swe_avanzar", {"task_id": "t"})), 900)
            os.environ["RIU_SWE_AVANZAR_TIMEOUT_MS"] = "x"
            self.assertEqual(self.capturar(hc, lambda: hc.swe_invoke("k", "swe_reanudar", {"task_id": "t"})), 1800)

    def test_ninguna_llamada_del_cliente_queda_sin_limite(self):
        with patch.dict(os.environ, {"RIU_DEEPSEEK_HARNESS_URL": "http://127.0.0.1:9"}):
            for fn in (lambda: hc.guardar("k", "a", "b"), lambda: hc.leer("k", "a"), lambda: hc.llm("k", MSG, "m"), lambda: hc.computar("k", {})):
                t = self.capturar(hc, fn)
                self.assertTrue(isinstance(t, (int, float)) and t > 0)


class TestSweAgentesYAprobador(unittest.TestCase):
    """swe_avanzar/swe_reanudar/swe_aprobar pasan por el permiso «agente» del servidor; swe_aprobar exige RIU_SWE_APROBADOR_TOKEN si esta definido."""
    CLAVE = "acceso-test"
    CAB = {"x-api-key": CLAVE}

    def setUp(self):
        self.llamadas = []
        def invoke(clave, operacion, datos):
            self.llamadas.append(operacion); return {"status": "ok", "result": {"ok": True}}
        self.parches = [patch.dict(os.environ, {"RIU_API_KEY": self.CLAVE, "RIU_DEEPSEEK_HARNESS_URL": "http://127.0.0.1:9", "MVP_PLAN": "personal"}),
                        patch("mvp.app.harness_client.swe_invoke", invoke), patch("mvp.app.clave_harness", lambda: "harness-ficticia")]
        for p in self.parches: p.start()
        os.environ.pop("RIU_SWE_APROBADOR_TOKEN", None)
        self.banco = getattr(servicio.app.state, "banco", None)
        servicio.app.state.banco = SimpleNamespace(leer=lambda n: None)
        self.agentes_on = servicio.CONTROL.d["agentes_on"]
        self.cliente = TestClient(servicio.app)

    def tearDown(self):
        self.cliente.close(); servicio.CONTROL.d["agentes_on"] = self.agentes_on; servicio.app.state.banco = self.banco
        for p in self.parches: p.stop()

    def post(self, op, cuerpo=None, headers=None):
        return self.cliente.post("/chat/swe/" + op, json=cuerpo or {"task_id": "t-1", **({"op_id": "op-1"} if op == "aprobar" else {})}, headers=headers or self.CAB)

    def test_avanzar_reanudar_y_aprobar_exigen_agentes_on_igual_que_iniciar_agentico(self):
        servicio.CONTROL.d["agentes_on"] = False
        for op in ("avanzar", "reanudar", "aprobar"):
            r = self.post(op)
            self.assertEqual(r.status_code, 403, op + r.text); self.assertIn("agentes=false", r.json()["detail"])
        self.assertEqual(self.llamadas, [], "el Harness no se toca con Agentes OFF")
        servicio.CONTROL.d["agentes_on"] = True
        for op in ("avanzar", "reanudar", "aprobar"):
            self.assertEqual(self.post(op).status_code, 200, op)
        self.assertEqual(self.llamadas, ["swe_avanzar", "swe_reanudar", "swe_aprobar"])
        servicio.CONTROL.d["agentes_on"] = False
        self.assertEqual(self.post("estado").status_code, 200, "estado es solo lectura: no pide agentes")

    def test_aprobar_con_token_de_aprobador_definido_exige_la_cabecera(self):
        servicio.CONTROL.d["agentes_on"] = True
        with patch.dict(os.environ, {"RIU_SWE_APROBADOR_TOKEN": "token-aprobador-de-prueba"}):
            self.assertEqual(self.post("aprobar").status_code, 401)
            self.assertEqual(self.post("aprobar", headers={**self.CAB, "x-operator-token": "otro"}).status_code, 401)
            self.assertEqual(self.llamadas, [])
            self.assertEqual(self.post("aprobar", headers={**self.CAB, "x-operator-token": "token-aprobador-de-prueba"}).status_code, 200)
            for op in ("avanzar", "reanudar", "estado"):
                self.assertEqual(self.post(op).status_code, 200, op + ": el token solo afecta a aprobar")
        self.assertEqual(self.post("aprobar").status_code, 200, "sin la variable definida no se pide")

    def test_un_token_de_aprobador_igual_a_la_clave_de_acceso_es_503(self):
        servicio.CONTROL.d["agentes_on"] = True
        with patch.dict(os.environ, {"RIU_SWE_APROBADOR_TOKEN": self.CLAVE}):
            r = self.post("aprobar", headers={**self.CAB, "x-operator-token": self.CLAVE})
        self.assertEqual(r.status_code, 503); self.assertEqual(self.llamadas, []); self.assertNotIn(self.CLAVE, r.text.replace("x-api-key", ""))


class TestCableadoPythonpath(unittest.TestCase):
    def test_cableado_fija_su_pythonpath_y_no_falla_con_no_module_named_mvp(self):
        ruta = pathlib.Path(__file__).resolve().parents[2] / "auditoria" / "cableado.py"
        entorno = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
        r = subprocess.run([sys.executable, str(ruta)], capture_output=True, text=True, env=entorno, timeout=120)
        self.assertNotIn("No module named", r.stdout + r.stderr)
        self.assertNotIn("FAIL: BE import", r.stdout)


if __name__ == "__main__":
    unittest.main()
