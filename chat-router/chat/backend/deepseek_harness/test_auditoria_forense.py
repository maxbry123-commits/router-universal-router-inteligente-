"""Auditoria forense en el Harness (puntos 1/_bridge_chat, 15, 18): redactor de claves, import de adaptadores tolerante y tarea_id explicito hacia el bridge.
Claves inventadas; servidores falsos en 127.0.0.1."""
import json, os, re, subprocess, sys, threading, unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from plugins.deepseek_harness import server as h

MSGS = [{"role": "user", "content": "hola"}]
GSK = "gsk_" + "A1b2C3d4E5f6G7"
NVAPI = "nvapi-" + "Zz9_Yy8-Xx7_Ww6"


class Redactor(unittest.TestCase):
    def test_secreto_cubre_groq_y_nvidia_ademas_de_las_formas_anteriores(self):
        for v in (GSK, NVAPI, "sk-" + "a" * 14, "ghp_" + "a" * 14, "hf_" + "a" * 22, "github_pat_" + "a" * 14):
            self.assertEqual(h._SECRETO.sub("[REDACTADO]", "x " + v + " y"), "x [REDACTADO] y", v)
        self.assertEqual(h._SECRETO.sub("[REDACTADO]", "gsk_corta nvapi-corta"), "gsk_corta nvapi-corta")

    def test_el_diario_de_la_tarea_no_guarda_claves_de_groq_ni_nvidia(self):
        guardado = {}
        with patch.object(h, "guardar", lambda a: guardado.update(a)):
            h._anotar("t1", {"k": "salida con " + GSK + " y " + NVAPI})
        self.assertNotIn(GSK, guardado["valor"]); self.assertNotIn(NVAPI, guardado["valor"]); self.assertIn("[REDACTADO]", guardado["valor"])


class ImportDeAdaptadores(unittest.TestCase):
    def test_sin_agentes_adaptadores_solo_faltan_los_swe_y_status_invoke_llm_siguen_vivos(self):
        codigo = (
            "import sys, json\n"
            "sys.modules['agentes.adaptadores'] = None  # ImportError al importar\n"
            "from plugins.deepseek_harness import server as h\n"
            "from fastapi.testclient import TestClient\n"
            "import os; os.environ['RIU_API_KEY'] = 'clave-de-prueba'\n"
            "c = TestClient(h.app); cab = {'x-api-key': 'clave-de-prueba'}\n"
            "st = c.post('/invoke', json={'action': 'status'}, headers=cab).json()\n"
            "malo = c.post('/invoke', json={'action': 'invoke', 'tool': 'swe_iniciar', 'args': {}}, headers=cab).json()\n"
            "print(json.dumps({'swe': sorted(k for k in h.HERRAMIENTAS if k.startswith('swe_')), 'base': sorted(k for k in h.HERRAMIENTAS if not k.startswith('swe_')), 'status': st, 'malo': malo}))\n"
        )
        entorno = {**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)}
        r = subprocess.run([sys.executable, "-c", codigo], capture_output=True, text=True, env=entorno, timeout=120)
        self.assertEqual(r.returncode, 0, r.stderr[-400:])
        d = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertEqual(d["swe"], []); self.assertEqual(d["base"], ["computar", "guardar", "leer"])
        self.assertEqual(d["status"]["status"], "ok"); self.assertEqual(d["status"]["result"]["servicio"], "deepseek_harness")
        self.assertEqual(d["malo"]["status"], "error"); self.assertEqual(d["malo"]["error"], "tool no permitida")

    def test_con_los_adaptadores_siguen_registrados_los_cinco_swe(self):
        self.assertEqual(sorted(k for k in h.HERRAMIENTAS if k.startswith("swe_")), ["swe_aprobar", "swe_avanzar", "swe_estado", "swe_iniciar", "swe_reanudar"])


def bridge():
    vistos = []
    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            vistos.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps({"choices": [{"message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"}]}).encode())
        def log_message(self, *a): pass
    s = HTTPServer(("127.0.0.1", 0), H); threading.Thread(target=s.serve_forever, daemon=True).start()
    return s, "http://127.0.0.1:%d" % s.server_port, vistos


class TareaIdHaciaElBridge(unittest.TestCase):
    def enviar(self, modelo, conv_id, mensajes=MSGS):
        s, url, vistos = bridge()
        with patch.dict(os.environ, {"RIU_SWE_BRIDGE_URL": url}):
            h._bridge_chat(mensajes, modelo, conv_id)
        s.shutdown()
        return vistos[0]

    def test_con_tarea_y_modelo_local_o_externo_manda_tarea_id_explicito_valido_y_estable(self):
        a = self.enviar("lfm2.5-350m", "p-rq-abc123"); b = self.enviar("lfm2.5-350m", "p-rq-abc123")
        self.assertEqual(a["conv_id"], "p-rq-abc123")
        self.assertRegex(a["tarea_id"], r"^[A-Za-z0-9_-]{1,64}$"); self.assertTrue(a["tarea_id"].startswith("p-rq-abc123-"))
        self.assertEqual(a["tarea_id"], b["tarea_id"], "el mismo envio reintentado = la misma tarea (reanuda)")
        c = self.enviar("lfm2.5-350m", "p-rq-abc123", [{"role": "user", "content": "otra vuelta"}])
        self.assertNotEqual(a["tarea_id"], c["tarea_id"], "otra vuelta de la misma tarea no choca (sin 409)")
        e = self.enviar("groq/qwen/qwen3.8-27b", "p-rq-abc123")
        self.assertNotEqual(a["tarea_id"], e["tarea_id"], "otro modelo, otra tarea")
        self.assertLessEqual(len(self.enviar("lfm2.5-350m", "x" * 64)["tarea_id"]), 64)

    def test_sin_tarea_o_con_modelo_web_no_se_manda_tarea_id(self):
        self.assertNotIn("tarea_id", self.enviar("lfm2.5-350m", ""))
        self.assertNotIn("tarea_id", self.enviar("web-qwen38max", "p-rq-abc123"))
        self.assertEqual(self.enviar("web-qwen38max", "p-rq-abc123")["conv_id"], "p-rq-abc123")


if __name__ == "__main__":
    unittest.main()


class DiarioSeguro(unittest.TestCase):
    def test_ausente_de_verdad_crea_diario_nuevo(self):
        with patch.object(h, "leer", side_effect=RuntimeError("fallo HF: no existe tareas/t1/diario.json")):
            self.assertEqual(h._diario("t1"), {})

    def test_caida_de_hf_no_permite_repetir_herramientas(self):
        with patch.object(h, "leer", side_effect=RuntimeError("fallo de lectura HF")):
            with self.assertRaisesRegex(RuntimeError, "DIARIO_NO_DISPONIBLE"):
                h._diario("t1")

    def test_diario_corrupto_no_reinicia_la_tarea(self):
        for valor in ('{invalido', '[]', 'null'):
            with self.subTest(valor=valor), patch.object(h, "leer", return_value={"valor": valor}):
                with self.assertRaisesRegex(RuntimeError, "DIARIO_CORRUPTO"):
                    h._diario("t1")

    def test_error_al_guardar_diario_es_fallo_obligatorio(self):
        with patch.object(h, "guardar", side_effect=RuntimeError("fallo de escritura HF")):
            with self.assertRaisesRegex(RuntimeError, "DIARIO_NO_PERSISTIDO"):
                h._anotar("t1", {"k": "v"})

    def test_registro_iniciada_se_guarda_antes_de_ejecutar_y_frena_reintento(self):
        # Contrato de seguridad para la rama de herramientas del llm.
        import inspect
        fuente = inspect.getsource(h.llm)
        self.assertLess(fuente.index('{"estado": "INICIADA", "herramienta": nombre}'),
                        fuente.index('resultado = llamar("router_mvp", "mcp"'),
                        "INICIADA debe persistirse antes de la llamada con efectos")
        self.assertIn('raise RuntimeError("OPERACION_SIN_CONFIRMAR")', fuente)
        self.assertIn('"estado": "CONFIRMADA"', fuente)

