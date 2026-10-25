"""Contrato 1 a 1 con el input block del SDK QwenCloud (mvp/sdk_qwen.py): mismo catalogo, mismas rutas y mismos cuerpos."""
import unittest
from unittest.mock import patch
from mvp import modelos, multimedia, sdk_qwen

CLAVE = "sk-sp-prueba"


def capturar():
    visto = []
    def http(url, clave, cuerpo=None, extra=None):
        visto.append((url, cuerpo, extra))
        return "application/json", b'{"output":{"task_id":"t1","task_status":"SUCCEEDED","video_url":"https://v","audio":{"url":"https://a"},"choices":[{"message":{"content":[{"image":"https://i","text":"ok"}]}}]}}'
    return visto, http


class Contrato(unittest.TestCase):
    def test_catalogo_igual_al_bloque(self):
        d = modelos.cargar()
        ids = lambda k: [m["id"] for m in d[k] if m["p"]]
        b = sdk_qwen.QWEN_TOKEN_PLAN
        self.assertEqual(sorted(ids("texto")), sorted(b["text_models"]))
        self.assertEqual(sorted(ids("imagen")), sorted(b["image_models"]))
        self.assertEqual(sorted(ids("audio")), sorted(b["audio_models"]))
        self.assertEqual(sorted(ids("video")), sorted(b["video_models"]))
        self.assertNotIn("auto", b["text_models"])

    def test_urls_base(self):
        d = modelos.cargar()
        self.assertEqual(d["base_url_alterna_qwencloud"], sdk_qwen.QWEN_TOKEN_PLAN["base_url"])  # la del bloque
        self.assertEqual(d["base_url"], sdk_qwen.BASE_URL_OFICIAL + "/compatible-mode/v1")  # la del repo oficial
        self.assertEqual(modelos.bases(), [d["base_url"], d["base_url_alterna_qwencloud"]])

    def test_cuerpos_de_medios_son_los_del_bloque(self):
        visto, http = capturar()
        raiz = sdk_qwen.BASE_URL
        with patch("mvp.multimedia._http", http), patch("mvp.multimedia.time.sleep"):
            multimedia.imagen(raiz, CLAVE, "wan2.7-image", "una ciudad")
            multimedia.voz(raiz, CLAVE, "Hola")
            multimedia.asr(raiz, CLAVE, "https://x/a.wav")
            multimedia.video(raiz, CLAVE, "happyhorse-1.1-r2v", "camina", "https://x/r.png")
            multimedia.video(raiz, CLAVE, "happyhorse-1.1-i2v", "empieza", "https://x/r.png")
            multimedia.video(raiz, CLAVE, "wan3.0-video", "auto")
        esperado = [(raiz + sdk_qwen.RUTAS["imagen"], sdk_qwen.cuerpo_imagen("wan2.7-image", "una ciudad")),
                    (raiz + sdk_qwen.RUTAS["voz"], sdk_qwen.cuerpo_voz("Hola")),
                    (raiz + sdk_qwen.RUTAS["asr"], sdk_qwen.cuerpo_asr("https://x/a.wav")),
                    (raiz + sdk_qwen.RUTAS["video"], sdk_qwen.cuerpo_video("happyhorse-1.1-r2v", "camina", [{"type": "reference_image", "url": "https://x/r.png"}])),
                    (raiz + sdk_qwen.RUTAS["video"], sdk_qwen.cuerpo_video("happyhorse-1.1-i2v", "empieza", [{"type": "first_frame", "url": "https://x/r.png"}])),
                    (raiz + sdk_qwen.RUTAS["video"], sdk_qwen.cuerpo_video("wan3.0-video", "auto"))]
        enviados = [(u, c) for u, c, e in visto if c is not None]
        self.assertEqual(enviados, esperado)

    def test_funciones_del_bloque_envian_lo_mismo_con_user_agent(self):
        class R:
            def raise_for_status(self): pass
            def json(self): return {}
            content = b"x"
        with patch("requests.post", return_value=R()) as post:
            sdk_qwen.generar_imagen("qwen-image-3.0-pro", "Un robot futurista", CLAVE)
            sdk_qwen.generar_video("happyhorse-1.1-i2v", "x", CLAVE, media=[{"type": "first_frame", "url": "https://x/r.png"}])
        (a, ka), (b, kb) = post.call_args_list[0], post.call_args_list[1]
        self.assertEqual(ka["json"]["parameters"], {"size": "1024*1024", "n": 1})
        self.assertEqual(ka["headers"], {"Authorization": "Bearer " + CLAVE, "Content-Type": "application/json", "User-Agent": "qwencloud-skills"})
        self.assertEqual(kb["headers"]["X-DashScope-Async"], "enable")
        self.assertEqual(kb["json"]["parameters"], {"resolution": "720P", "duration": 5})


class TextoUnoAUno(unittest.TestCase):
    def test_mensaje_simple_igual_a_llamar_modelo_del_bloque(self):
        """Un solo mensaje de usuario, sin historial ni herramientas: misma ruta y mismo cuerpo que client.chat.completions.create."""
        from mvp import compute
        visto = []
        def sol(url, payload, clave):
            visto.append((url, payload)); return {"choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}], "model": "deepseek-v4-pro"}
        with patch("mvp.compute._solicitar", sol):
            compute.llamar([{"role": "user", "content": "Hola"}], "deepseek-v4-pro", sdk_qwen.QWEN_TOKEN_PLAN["base_url"], CLAVE)
        self.assertEqual(visto, [(sdk_qwen.BASE_URL + "/compatible-mode/v1/chat/completions",
                                  {"model": "deepseek-v4-pro", "messages": [{"role": "user", "content": "Hola"}]})])

    def test_razonamiento_explicito_igual_al_bloque(self):
        from mvp import compute
        visto = []
        def sol(url, payload, clave):
            visto.append(payload); return {"choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}]}
        with patch("mvp.compute._solicitar", sol):
            compute.llamar([{"role": "user", "content": "Analiza este código Python."}], "qwen3.8-max", sdk_qwen.BASE_URL + "/compatible-mode/v1", CLAVE, {"enable_thinking": True})
        self.assertEqual(visto[0]["enable_thinking"], True)  # extra_body={"enable_thinking": True} del bloque
