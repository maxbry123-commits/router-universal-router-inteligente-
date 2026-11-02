"""Invariantes de la puerta única del Harness; no usa secretos ni red."""
import unittest
from unittest.mock import patch
from fastapi import HTTPException
from plugins.deepseek_harness import server as h


class ModeloGateTests(unittest.TestCase):
    def test_dos_rutas_unicas_sin_fallback(self):
        self.assertEqual(h._modelo_destino("groq/qwen/qwen3.8-27b"), ("mvp", "groq/qwen/qwen3.8-27b"))
        self.assertEqual(h._modelo_destino("nvidia/z-ai/glm-5.3"), ("mvp", "nvidia/z-ai/glm-5.3"))
        self.assertEqual(h._modelo_destino("deepseek/deepseek-v4-pro"), ("mvp", "deepseek/deepseek-v4-pro"))
        self.assertEqual(h._modelo_destino("hf/lfm2.5-350m"), ("swe", "lfm2.5-350m"))
        self.assertEqual(h._modelo_destino("web-qwen38max"), ("swe", "web-qwen38max"))
        with self.assertRaises(HTTPException):
            h._modelo_destino("modelo-inexistente")

    def test_la_clave_de_proveedor_no_es_clave_harness(self):
        with patch.dict("os.environ", {"RIU_API_KEY": "PRUEBA-INTERNA"}, clear=True):
            h._autorizar_chat_modelos("PRUEBA-INTERNA", None)
            with self.assertRaises(HTTPException):
                h._autorizar_chat_modelos("PRUEBA-EXTERNA", None)

    def test_sse_un_mensaje_y_un_done(self):
        resp = h._mensaje_openai("nvidia/z-ai/glm-5.3", [], {"texto": "Hola", "finish_reason": "stop"}, via="mvp")
        datos = list(h._openai_sse(resp))
        self.assertEqual(len([x for x in datos if "[DONE]" in x]), 1)
        self.assertIn("Hola", "".join(datos))
        self.assertEqual(resp["via_router"], "mvp")


if __name__ == "__main__":
    unittest.main()
