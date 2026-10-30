"""Detener en el chat: el frontend manda POST /cancelar {proceso_id}. El Router corta la tarea, la saca de pendientes y no la retoma al reiniciar."""
import asyncio, json, os, threading, time, unittest
from unittest.mock import patch
from test_control import Base, CAB
from mvp import app as servicio, estado_tarea


class TestCancelar(Base):
    def lanzar(self, pid):
        liberar = threading.Event()
        def lento(*a, **k):
            liberar.wait(20)
            return {"status": "ok", "result": {"texto": "tarde", "tool_calls": [], "finish_reason": "stop"}}
        self.addCleanup(liberar.set)
        return lento

    def test_cancelar_corta_la_tarea_y_la_saca_de_pendientes(self):
        lento = self.lanzar("x")
        with patch.dict(os.environ, {"RIU_DEEPSEEK_HARNESS_URL": "http://127.0.0.1:1"}), patch("mvp.app.harness_client.llm", lento):
            self.banco.datos["RIU_API_KEY"] = "clave-harness"
            r = self.client.post("/plugins/puente_chat/call/chat_async", headers=CAB, json={"ficha_qwen": "1", "message": "tarea larga", "request_id": "cancelar-0001", "modelo": "qwen3.8-max"}).json()["result"]
            pid = r["proceso_id"]; time.sleep(0.5)
            self.assertEqual(self.client.post("/plugins/puente_chat/call/resultado", headers=CAB, json={"proceso_id": pid}).json()["result"]["estado"], "procesando")
            c = self.client.post("/plugins/puente_chat/call/cancelar", headers=CAB, json={"proceso_id": pid})
            self.assertEqual(c.status_code, 200, c.text); self.assertTrue(c.json()["result"]["cancelado"])
            res = self.client.post("/plugins/puente_chat/call/resultado", headers=CAB, json={"proceso_id": pid}).json()["result"]
        self.assertEqual(res["estado"], "error"); self.assertEqual(res["error"], "PROCESO_DETENIDO")
        self.assertNotIn(pid, estado_tarea.pendientes(self.banco))

    def test_cancelar_algo_que_no_existe_no_falla(self):
        c = self.client.post("/plugins/puente_chat/call/cancelar", headers=CAB, json={"proceso_id": "p-nada"})
        self.assertEqual(c.status_code, 200); self.assertFalse(c.json()["result"]["cancelado"])

    def test_cancelar_exige_la_clave(self):
        self.assertIn(self.client.post("/plugins/puente_chat/call/cancelar", json={"proceso_id": "p-x"}).status_code, (401, 403))


if __name__ == "__main__":
    unittest.main()
