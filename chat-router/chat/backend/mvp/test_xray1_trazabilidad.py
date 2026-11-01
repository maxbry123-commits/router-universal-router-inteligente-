"""X-Ray 1: sin atribuciones de proveedor falsas y sin inventar metricas del bridge."""
import unittest
from mvp import app as router
from plugins.deepseek_harness import server as harness


class TestTrazabilidadXray1(unittest.TestCase):
    def test_proveedor_real_en_identidad(self):
        self.assertIn("NVIDIA", router._identidad_modelo("nvidia/z-ai/glm-5.3")["content"])
        self.assertIn("Groq", router._identidad_modelo("groq/qwen/qwen3.8-27b")["content"])
        self.assertNotIn("QwenCloud", router._identidad_modelo("nvidia/z-ai/glm-5.3")["content"])
        self.assertIn("QwenCloud Token Plan", router._identidad_modelo("qwen3.8-max")["content"])

    def test_metricas_bridge_unidades_y_ausencia(self):
        self.assertEqual(harness._metricas_bridge(None), {})
        self.assertEqual(harness._metricas_bridge({}), {})
        self.assertEqual(harness._metricas_bridge({
            "stream": True, "ttft_ms": 900, "total_ms": 3100,
            "tokens_s": 45.5, "tokens": 120, "tokens_estimado": False,
            "origen_tokens": "proveedor",
        }), {
            "stream": True, "ttft_s": 0.9, "duracion_s": 3.1,
            "tokens_por_s": 45.5, "tokens": 120, "tokens_estimados": False,
            "origen_tokens": "proveedor",
        })
        self.assertNotIn("ttft_s", harness._metricas_bridge({"ttft_ms": None}))
        self.assertNotIn("tokens", harness._metricas_bridge({"tokens": -1}))


if __name__ == "__main__":
    unittest.main()
