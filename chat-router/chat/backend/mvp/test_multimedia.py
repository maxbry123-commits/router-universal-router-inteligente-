"""Los 23 modelos del plan Personal Standard y la generacion de imagen, voz, ASR y video (HTTP simulado)."""
import json
import os
import pathlib
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from fastapi.testclient import TestClient
from mvp import app as servicio, modelos, multimedia

CAB = {"x-api-key": "api-ficticia"}
B = "https://token-plan.test"


class TestCatalogo(unittest.TestCase):
    def test_los_22_modelos_del_plan(self):
        with patch.dict(os.environ, {"MVP_PLAN": "personal"}):
            cat = dict(modelos.catalogo())
        self.assertEqual(len(cat), 22)
        self.assertEqual(sorted(set(cat.values())), ["audio", "imagen", "texto", "video"])
        self.assertEqual([sum(1 for t in cat.values() if t == k) for k in ("texto", "imagen", "audio", "video")], [12, 3, 3, 4])
        self.assertNotIn("auto", cat)  # quitado a pedido de Antonio
        for m in ("qwen3.8-max", "glm-5.3", "deepseek-v4.1-flash-1017", "qwen-image-3.0-pro", "wan2.7-image-pro", "qwen-audio-3.0-tts-plus", "qwen-audio-3.0-realtime-plus", "qwen-audio-3.0-asr-flash", "wan3.0-video", "happyhorse-1.1-r2v"):
            self.assertIn(m, cat)


class TestGenerar(unittest.TestCase):
    def llamar(self, modelo, tipo, texto, respuestas):
        vistas = []
        def falso(url, clave, cuerpo=None, extra=None):
            vistas.append((url, cuerpo, extra)); return respuestas.pop(0)
        with patch("mvp.multimedia._http", falso), patch("mvp.multimedia.time.sleep"):
            return multimedia.generar(modelo, tipo, B + "/compatible-mode/v1", "k", texto), vistas

    def test_imagen(self):
        doc = {"output": {"choices": [{"message": {"content": [{"image": "https://img/x.png"}]}}]}}
        salida, v = self.llamar("wan2.7-image", "imagen", "un robot", [("application/json", json.dumps(doc).encode())])
        self.assertEqual(salida, "[[imagen:https://img/x.png]]")
        self.assertEqual((v[0][0], v[0][1]["model"]), (B + multimedia.RUTAS["imagen"], "wan2.7-image"))

    def test_video_asincrono_con_url_de_imagen(self):
        r = [("j", b'{"output":{"task_id":"t1"}}'), ("j", b'{"output":{"task_status":"RUNNING"}}'), ("j", b'{"output":{"task_status":"SUCCEEDED","video_url":"https://v/a.mp4"}}')]
        salida, v = self.llamar("happyhorse-1.1-i2v", "video", "camina https://i/r.png", r)
        self.assertEqual(salida, "[[video:https://v/a.mp4]]")
        self.assertEqual((v[0][2], v[0][1]["input"]["media"][0]["type"], v[0][1]["input"]["prompt"]), ({"X-DashScope-Async": "enable"}, "first_frame", "camina"))
        self.assertEqual(v[1][0], B + "/api/v1/tasks/t1")

    def test_video_fallido_y_modelos_que_piden_url(self):
        with self.assertRaisesRegex(RuntimeError, "FAILED"):
            self.llamar("wan3.0-video", "video", "x", [("j", b'{"output":{"task_id":"t"}}'), ("j", b'{"output":{"task_status":"FAILED","message":"mal"}}')])
        for m, t in (("happyhorse-1.1-r2v", "video"), ("qwen-audio-3.0-asr-flash", "audio")):
            with self.assertRaisesRegex(ValueError, "URL"):
                self.llamar(m, t, "sin enlace", [])

    def test_voz_binaria_y_asr_y_realtime(self):
        salida, _ = self.llamar("qwen-audio-3.0-tts-plus", "audio", "hola", [("audio/mpeg", b"ID3datos")])
        self.assertTrue(salida.startswith("[[audio:data:audio/mpeg;base64,"))
        doc = {"output": {"choices": [{"message": {"content": [{"text": "hola mundo"}]}}]}}
        self.assertEqual(self.llamar("qwen-audio-3.0-asr-flash", "audio", "https://a/x.wav", [("j", json.dumps(doc).encode())])[0], "hola mundo")
        with self.assertRaisesRegex(RuntimeError, "WebSocket"):
            self.llamar("qwen-audio-3.0-realtime-plus", "audio", "x", [])


class TestChat(unittest.TestCase):
    def test_chat_send_con_modelo_de_imagen_no_pasa_por_el_harness(self):
        from types import SimpleNamespace
        antes = getattr(servicio.app.state, "banco", None)
        servicio.app.state.banco = SimpleNamespace(leer=lambda k: "q" if k == "QWEN_API_KEY" else "h")
        try:
            with patch.dict(os.environ, {"RIU_API_KEY": "api-ficticia", "RIU_DEEPSEEK_HARNESS_URL": "http://127.0.0.1:1", "MVP_PLAN": "personal"}), \
                 patch("mvp.app.multimedia.generar", return_value="[[imagen:https://i/x.png]]") as gen, patch("mvp.app.harness_client.llm") as harness:
                r = TestClient(servicio.app).post("/chat/send", headers=CAB, json={"message": "un gato", "model": "qwen-image-3.0-pro"})
            self.assertEqual((r.status_code, r.json()["reply"]), (200, "[[imagen:https://i/x.png]]"))
            self.assertEqual((gen.call_args.args[0], gen.call_args.args[1]), ("qwen-image-3.0-pro", "imagen"))
            harness.assert_not_called()
        finally:
            servicio.app.state.banco = antes


if __name__ == "__main__":
    unittest.main(verbosity=2)
