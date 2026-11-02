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

    def test_mvp_heartbeat_no_duplica_modelo(self):
        import asyncio
        from unittest.mock import patch

        async def simulacion(_req, _headers, modelo):
            await asyncio.sleep(0.035)
            return h._mensaje_openai(modelo, [], {"texto": "una respuesta", "finish_reason": "stop"}, via="mvp")

        async def ejecutar():
            with patch.object(h, "_mvp_modelo_compat", side_effect=simulacion) as f:
                items = [x async for x in h._sse_mvp_con_latidos({}, {}, "nvidia/meta/muse-glimmer-30b", latido_s=0.005)]
                self.assertEqual(f.await_count, 1)
                return items
        items = asyncio.run(ejecutar())
        self.assertGreaterEqual(items.count(": keepalive\n\n"), 1)
        self.assertEqual(sum('"content": "una respuesta"' in x for x in items), 1)
        self.assertEqual(items.count("data: [DONE]\n\n"), 1)

    def test_mvp_heartbeat_error_es_terminal(self):
        import asyncio
        from unittest.mock import patch

        async def error(_req, _headers, _modelo):
            raise HTTPException(status_code=502, detail="ROUTER_MVP_HTTP_502 · PROVEEDOR_HTTP_410")

        async def ejecutar():
            with patch.object(h, "_mvp_modelo_compat", side_effect=error):
                return [x async for x in h._sse_mvp_con_latidos({}, {}, "nvidia/z-ai/glm-5.3", latido_s=0.005)]
        datos = asyncio.run(ejecutar())
        self.assertTrue(any('PROVEEDOR_HTTP_410' in x and 'error' in x for x in datos))
        self.assertEqual(datos.count("data: [DONE]\n\n"), 1)

    def test_sse_un_mensaje_y_un_done(self):
        resp = h._mensaje_openai("nvidia/z-ai/glm-5.3", [], {"texto": "Hola", "finish_reason": "stop"}, via="mvp")
        datos = list(h._openai_sse(resp))
        self.assertEqual(len([x for x in datos if "[DONE]" in x]), 1)
        self.assertIn("Hola", "".join(datos))
        self.assertEqual(resp["via_router"], "mvp")


if __name__ == "__main__":
    unittest.main()
