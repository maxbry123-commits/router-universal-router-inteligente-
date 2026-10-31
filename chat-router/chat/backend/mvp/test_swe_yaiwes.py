"""Rutas autenticadas de YAIWES para las tareas SWE (/chat/swe/*): contrato -> swe_invoke -> Harness (HTTP real, servidor falso local).
Sin claves reales: las credenciales de prueba son cadenas inventadas; ninguna sale en una respuesta."""
import json
import os
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fastapi.testclient import TestClient
from mvp import app as servicio, harness_client as hc

CLAVE_HARNESS = "harness-clave-de-prueba-xyz"
CLAVE_CHAT = "acceso-test"
CAB = {"x-api-key": CLAVE_CHAT}
CAMPOS = ["task_id", "origen", "mensaje", "workflow", "modelo_responde", "modelo_lector", "modelo_tool", "modelo_revisor", "agente_responde",
          "agente_tool", "agente_verificador", "modo_agentico", "aprobacion", "sesion", "proyecto"]
TAREA = {"task_id": "yaiwes-001", "origen": "yaiwes", "workflow": "swe_code", "mensaje": "Revisar proyecto", "modelo_responde": "hf/lfm2.5-350m",
         "modelo_lector": "hf/lfm2.5-350m", "modelo_tool": "hf/qwen2.5-coder-1.5b", "modelo_revisor": "hf/qwen3.5-0.8b", "agente_responde": "openclaw",
         "agente_tool": "swe-agent", "agente_verificador": "openhands", "modo_agentico": False, "aprobacion": False, "sesion": "chat-001", "proyecto": "yaiwes"}


class Falso(BaseHTTPRequestHandler):
    cola, recibidas = [], []

    def do_POST(self):
        cuerpo = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        type(self).recibidas.append((self.path, cuerpo, self.headers.get("X-API-Key")))
        codigo, respuesta = self.cola.pop(0) if self.cola else (200, {"status": "ok", "result": {"ok": True, "task_id": cuerpo.get("args", {}).get("task_id"), "estado": "PENDIENTE"}})
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(respuesta).encode())

    def log_message(self, *args):
        pass


class SweYaiwes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.http = ThreadingHTTPServer(("127.0.0.1", 0), Falso)
        cls.hilo = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.hilo.start()
        cls.url = "http://127.0.0.1:%d" % cls.http.server_port
        cls.cliente = TestClient(servicio.app)

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown(); cls.http.server_close(); cls.hilo.join(timeout=2); cls.cliente.close()

    def setUp(self):
        Falso.cola, Falso.recibidas = [], []
        self.env = patch.dict(os.environ, {"RIU_API_KEY": CLAVE_CHAT, "RIU_DEEPSEEK_HARNESS_URL": self.url, "MVP_PLAN": "personal"})
        self.env.start()
        self.banco = getattr(servicio.app.state, "banco", None)
        servicio.app.state.banco = SimpleNamespace(leer=lambda nombre: CLAVE_HARNESS if nombre == "RIU_API_KEY" else None)
        self.agentes_on = servicio.CONTROL.d["agentes_on"]
        servicio.CONTROL.d["agentes_on"] = False

    def tearDown(self):
        servicio.CONTROL.d["agentes_on"] = self.agentes_on
        servicio.app.state.banco = self.banco
        self.env.stop()

    def post(self, op, cuerpo, headers=CAB):
        return self.cliente.post("/chat/swe/" + op, json=cuerpo, headers=headers)

    # ---- harness_client.swe_invoke ----
    def test_swe_invoke_solo_las_cinco_operaciones_del_harness(self):
        for op in ("swe_iniciar", "swe_avanzar", "swe_estado", "swe_aprobar", "swe_reanudar"):
            hc.swe_invoke(CLAVE_HARNESS, op, {"task_id": "t-1"})
        self.assertEqual([r[1]["tool"] for r in Falso.recibidas], ["swe_iniciar", "swe_avanzar", "swe_estado", "swe_aprobar", "swe_reanudar"])
        self.assertTrue(all(r[0] == "/invoke" and r[1]["action"] == "invoke" and r[1]["args"] == {"task_id": "t-1"} and r[2] == CLAVE_HARNESS for r in Falso.recibidas))
        Falso.recibidas = []
        for malo in ("guardar", "leer", "computar", "llm", "swe_otra", "", None, "SWE_INICIAR", "swe_iniciar ", ["swe_iniciar"]):
            with self.assertRaisesRegex(ValueError, "OPERACION_SWE_NO_AUTORIZADA"):
                hc.swe_invoke(CLAVE_HARNESS, malo, {})
        with self.assertRaisesRegex(ValueError, "DATOS_SWE_INVALIDOS"):
            hc.swe_invoke(CLAVE_HARNESS, "swe_estado", "no-es-dict")
        self.assertEqual(Falso.recibidas, [], "ninguna llamada no autorizada llega al Harness")

    # ---- autenticacion ----
    def test_sin_clave_de_acceso_401_y_nada_llega_al_harness(self):
        for op in ("iniciar", "avanzar", "estado", "aprobar", "reanudar"):
            self.assertEqual(self.post(op, TAREA, headers={}).status_code, 401, op)
            self.assertEqual(self.post(op, TAREA, headers={"x-api-key": "otra"}).status_code, 401, op)
        self.assertEqual(self.cliente.get("/chat/swe/capacidades").status_code, 401)
        self.assertEqual(Falso.recibidas, [])

    def test_operacion_desconocida_no_autorizada(self):
        for op in ("guardar", "swe_iniciar", "llm", "x"):
            r = self.post(op, TAREA)
            self.assertIn(r.status_code, (404, 400), op)
        self.assertEqual(Falso.recibidas, [])

    # ---- iniciar ----
    def test_iniciar_reenvia_el_contrato_exacto_a_swe_iniciar_y_devuelve_task_id_y_estado(self):
        r = self.post("iniciar", TAREA)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json(), {"ok": True, "resultado": {"ok": True, "task_id": "yaiwes-001", "estado": "PENDIENTE"}})
        ruta, cuerpo, clave = Falso.recibidas[-1]
        self.assertEqual((ruta, cuerpo["action"], cuerpo["tool"], clave), ("/invoke", "invoke", "swe_iniciar", CLAVE_HARNESS))
        self.assertEqual(sorted(cuerpo["args"]), sorted(CAMPOS)); self.assertEqual(cuerpo["args"], TAREA)

    def test_la_clave_del_harness_nunca_sale_al_frontend(self):
        for op, cuerpo in (("iniciar", TAREA), ("estado", {"task_id": "yaiwes-001"})):
            r = self.post(op, cuerpo)
            self.assertNotIn(CLAVE_HARNESS, r.text); self.assertNotIn(CLAVE_HARNESS, json.dumps(dict(r.headers)))
        Falso.cola = [(401, {})]
        r = self.post("estado", {"task_id": "yaiwes-001"})
        self.assertEqual(r.status_code, 502); self.assertNotIn(CLAVE_HARNESS, r.text); self.assertNotIn(self.url, r.text)

    def test_origen_siempre_yaiwes_el_campo_aprobacion_del_cliente_no_cuenta_y_no_pasan_campos_ajenos(self):
        self.assertEqual(self.post("iniciar", {**TAREA, "origen": "openclaw"}).status_code, 400)
        self.assertEqual(self.post("iniciar", {**TAREA, "estado": "DONE"}).status_code, 400)
        self.assertEqual(self.post("iniciar", {**TAREA, "tool": "guardar"}).status_code, 400)
        self.assertEqual(Falso.recibidas, [])
        falta = {k: v for k, v in TAREA.items() if k != "agente_tool"}
        self.assertEqual(self.post("iniciar", falta).status_code, 400)
        r = self.post("iniciar", {**TAREA, "aprobacion": True})
        self.assertEqual(r.status_code, 200); self.assertIs(Falso.recibidas[-1][1]["args"]["aprobacion"], False)

    def test_task_id_y_tipos_validados_antes_de_llamar_al_harness(self):
        for malo in ("", "a b", "../x", "x" * 65, "ñ", None, 5):
            self.assertEqual(self.post("iniciar", {**TAREA, "task_id": malo}).status_code, 400, repr(malo))
            self.assertEqual(self.post("estado", {"task_id": malo}).status_code, 400, repr(malo))
        self.assertEqual(self.post("iniciar", {**TAREA, "mensaje": ""}).status_code, 400)
        self.assertEqual(self.post("iniciar", {**TAREA, "modo_agentico": "true"}).status_code, 400)
        self.assertEqual(self.post("iniciar", {**TAREA, "workflow": ["swe_code"]}).status_code, 400)
        self.assertEqual(self.post("iniciar", {**TAREA, "mensaje": "x" * 200_001}).status_code, 400)
        self.assertEqual(self.cliente.post("/chat/swe/iniciar", content=b"no-json", headers={**CAB, "content-type": "application/json"}).status_code, 422)
        self.assertEqual(Falso.recibidas, [])

    def test_modo_agentico_exige_agentes_encendidos_en_el_servidor(self):
        r = self.post("iniciar", {**TAREA, "modo_agentico": True})
        self.assertEqual(r.status_code, 403); self.assertIn("agentes=false", r.text)
        self.assertEqual(Falso.recibidas, [])
        servicio.CONTROL.d["agentes_on"] = True
        r = self.post("iniciar", {**TAREA, "modo_agentico": True})
        self.assertEqual(r.status_code, 200, r.text); self.assertIs(Falso.recibidas[-1][1]["args"]["modo_agentico"], True)
        servicio.CONTROL.d["agentes_on"] = False
        self.assertEqual(self.post("iniciar", {**TAREA, "modo_agentico": False}).status_code, 200, "con modo agentico OFF no se pide permiso de agentes")

    # ---- avanzar / estado / reanudar / aprobar ----
    def test_avanzar_estado_reanudar_solo_pasan_las_claves_permitidas(self):
        ref = {"task_id": "yaiwes-001", "origen": "yaiwes", "sesion": "chat-001", "proyecto": "yaiwes"}
        sucio = {**ref, "aprobacion": True, "operador": "intruso", "op_id": "x", "reconciliacion": {"resultado": "confirmada"}, "tool": "guardar", "estado": "DONE", "max_pasos": 99}
        for op, tool in (("avanzar", "swe_avanzar"), ("estado", "swe_estado"), ("reanudar", "swe_reanudar")):
            r = self.post(op, sucio)
            self.assertEqual(r.status_code, 200, (op, r.text))
            self.assertEqual(Falso.recibidas[-1][1]["tool"], tool)
            self.assertEqual(Falso.recibidas[-1][1]["args"], ref, op)
        self.assertEqual(self.post("estado", {**ref, "origen": "openclaw"}).status_code, 400)

    def test_aprobar_lo_identifica_el_servidor_no_el_cuerpo_ni_el_modelo(self):
        ref = {"task_id": "yaiwes-001", "origen": "yaiwes", "sesion": "chat-001", "proyecto": "yaiwes", "op_id": "op-abc123"}
        with patch.dict(os.environ, {"RIU_SWE_OPERADOR": "antonio.director"}):
            r = self.post("aprobar", {**ref, "aprobacion": True, "operador": "intruso", "aprobado_por": "intruso", "estado": "CONTINUAR"})
        self.assertEqual(r.status_code, 200, r.text)
        args = Falso.recibidas[-1][1]["args"]
        self.assertEqual(Falso.recibidas[-1][1]["tool"], "swe_aprobar")
        self.assertEqual(args, {**ref, "operador": "antonio.director"})
        self.assertNotIn("aprobacion", args)
        self.post("aprobar", ref)
        self.assertEqual(Falso.recibidas[-1][1]["args"]["operador"], "director", "sin variable el operador por defecto es 'director'")
        Falso.recibidas.clear()
        self.assertEqual(self.post("aprobar", {k: v for k, v in ref.items() if k != "op_id"}).status_code, 400, "sin op_id no se aprueba nada a ciegas")
        self.assertEqual(self.post("aprobar", {**ref, "op_id": "mal id!"}).status_code, 400)
        with patch.dict(os.environ, {"RIU_SWE_OPERADOR": "mal operador!"}):
            self.assertEqual(self.post("aprobar", ref).status_code, 503)
        self.assertEqual(Falso.recibidas, [])

    # ---- errores del Harness ----
    def test_errores_del_harness_se_traducen_sin_filtrar_detalles(self):
        Falso.cola = [(200, {"status": "error", "error": "TASK_ID_INVALIDO"})]
        r = self.post("estado", {"task_id": "yaiwes-001"})
        self.assertEqual(r.status_code, 400); self.assertIn("TASK_ID_INVALIDO", r.text)
        Falso.cola = [(200, {"status": "error", "error": "TAREA_NO_ENCONTRADA"})]
        self.assertEqual(self.post("estado", {"task_id": "yaiwes-001"}).status_code, 404)
        Falso.cola = [(200, {"status": "error", "error": "OPERADOR_NO_AUTORIZADO"})]
        self.assertEqual(self.post("aprobar", {"task_id": "yaiwes-001", "op_id": "op-1"}).status_code, 403)
        Falso.cola = [(200, {"status": "error", "error": "Traceback: token=" + CLAVE_HARNESS + " en /srv/x.py"})]
        r = self.post("estado", {"task_id": "yaiwes-001"})
        self.assertEqual(r.status_code, 502); self.assertIn("SWE_HARNESS_ERROR", r.text); self.assertNotIn(CLAVE_HARNESS, r.text); self.assertNotIn("Traceback", r.text)
        Falso.cola = [(200, {"status": "ok"})]
        self.assertEqual(self.post("estado", {"task_id": "yaiwes-001"}).status_code, 502, "ok sin result no es un exito")

    def test_harness_caido_o_sin_configurar_502_503(self):
        with patch.dict(os.environ, {"RIU_DEEPSEEK_HARNESS_URL": "http://127.0.0.1:9"}):
            r = self.post("estado", {"task_id": "yaiwes-001"})
        self.assertEqual(r.status_code, 502); self.assertIn("SWE_HARNESS_ERROR", r.text); self.assertNotIn("127.0.0.1:9", r.text)
        servicio.app.state.banco = SimpleNamespace(leer=lambda nombre: None)
        r = self.post("estado", {"task_id": "yaiwes-001"})
        self.assertEqual(r.status_code, 503); self.assertNotIn(CLAVE_HARNESS, r.text)

    # ---- capacidades (lo que el Harness reporta conectado) ----
    def test_capacidades_solo_lo_que_reporta_el_harness_y_saneado(self):
        Falso.cola = [(200, {"status": "ok", "result": {"servicio": "deepseek_harness", "swe": {"agentes": {"codex": {"disponible": True, "modelos": ["hf/qwen2.5-coder-1.5b", 5], "token": "no-debe-salir", "motivo": "ok"},
                                                                                                         "openhands": {"disponible": False, "motivo": "SDK no instalado " + "x" * 400}, "../raro": {"disponible": True}},
                                                                                   "workflows": {"liquid_mirror": {"disponible": True}}, "modelos": {"groq/qwen/qwen3.8-27b": {"disponible": False, "motivo": "no figura en GET /models"}}}}})]
        r = self.cliente.get("/chat/swe/capacidades", headers=CAB)
        self.assertEqual(r.status_code, 200); j = r.json()
        self.assertEqual(j["harness"], "ok")
        self.assertEqual(j["agentes"]["codex"], {"disponible": True, "modelos": ["hf/qwen2.5-coder-1.5b"], "motivo": "ok"})
        self.assertIs(j["agentes"]["openhands"]["disponible"], False); self.assertLessEqual(len(j["agentes"]["openhands"]["motivo"]), 200)
        self.assertNotIn("../raro", j["agentes"]); self.assertNotIn("no-debe-salir", r.text)
        self.assertEqual(j["workflows"], {"liquid_mirror": {"disponible": True}}); self.assertIs(j["modelos"]["groq/qwen/qwen3.8-27b"]["disponible"], False)
        self.assertEqual(Falso.recibidas[-1][1]["action"], "status")
        self.assertNotIn(CLAVE_HARNESS, r.text)

    def test_capacidades_sin_informe_del_harness_no_inventa_nada(self):
        r = self.cliente.get("/chat/swe/capacidades", headers=CAB)  # el status por defecto del servidor falso no trae `swe`
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {"harness": "ok", "agentes": {}, "workflows": {}, "modelos": {}})
        with patch.dict(os.environ, {"RIU_DEEPSEEK_HARNESS_URL": "http://127.0.0.1:9"}):
            r = self.cliente.get("/chat/swe/capacidades", headers=CAB)
        self.assertEqual(r.status_code, 200); self.assertEqual(r.json()["harness"], "no_disponible"); self.assertEqual(r.json()["agentes"], {})
        with patch.dict(os.environ, {"RIU_DEEPSEEK_HARNESS_URL": ""}):
            self.assertEqual(self.cliente.get("/chat/swe/capacidades", headers=CAB).json()["harness"], "no_configurado")
        servicio.app.state.banco = SimpleNamespace(leer=lambda nombre: None)
        self.assertEqual(self.cliente.get("/chat/swe/capacidades", headers=CAB).json()["harness"], "sin_credencial")


if __name__ == "__main__":
    unittest.main()
