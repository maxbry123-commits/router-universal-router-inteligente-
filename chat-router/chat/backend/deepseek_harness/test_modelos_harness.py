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
        self.assertEqual(h._modelo_destino("swecode/nvidia/z-ai/glm-5.3"), ("mvp", "nvidia/z-ai/glm-5.3"))
        self.assertEqual(h._modelo_destino("swecode/lfm2.5-350m"), ("swe", "lfm2.5-350m"))
        self.assertEqual(h._modelo_destino("swecode/web-qwen38max"), ("swe", "web-qwen38max"))
        with self.assertRaises(HTTPException):
            h._modelo_destino("modelo-inexistente")

    def test_router_swe_usa_la_entrada_existente_sin_variable_url_nueva(self):
        # El Harness vive montado en el Router: ausencia de RIU_ROUTER_URL
        # NO equivale a Router caido ni bloquea los agentes por error.
        with patch.dict("os.environ", {"PORT": "7860"}, clear=True), \
             patch.object(h, "llamar", return_value={"agentes_on": True}) as cliente:
            h._exigir_agentes_on()
            cliente.assert_called_once_with("puente_chat", "tools_lock", {}, timeout=None)

    def test_router_swe_sigue_respetando_agentes_off(self):
        with patch.dict("os.environ", {"PORT": "7860"}, clear=True), \
             patch.object(h, "llamar", return_value={"agentes_on": False}):
            with self.assertRaisesRegex(ValueError, "AGENTES_APAGADOS"):
                h._exigir_agentes_on()

    def test_cómputo_mvp_usa_puerto_del_space_y_no_7861_fijo(self):
        with patch.dict("os.environ", {"PORT": "7860"}, clear=True):
            self.assertEqual(h._mvp_modelos_url(), "http://127.0.0.1:7860")
        with patch.dict("os.environ", {"PORT": "7861"}, clear=True):
            self.assertEqual(h._mvp_modelos_url(), "http://127.0.0.1:7861")
        with patch.dict("os.environ", {"PORT": "99999"}, clear=True):
            with self.assertRaises(HTTPException):
                h._mvp_modelos_url()

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
