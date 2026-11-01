"""X-Ray 3: streaming SSE/ID de tools y catalogo de modelos con varias claves.
Pruebas locales aisladas: nunca se contacta NVIDIA/Groq ni se usan claves reales.
"""
import json
import time
import unittest
from unittest.mock import patch

from mvp import compute, externos


def _delta(**campos):
    return "data: " + json.dumps({"choices": [{"delta": campos, "finish_reason": None}]})


class TestSSEHerramientas(unittest.TestCase):
    def test_id_omitido_se_genera_y_argumentos_vacios_se_normalizan(self):
        a = compute.AcumuladorSSE(herramientas=["leer", "guardar"])
        a.linea(_delta(tool_calls=[{"index": 0, "type": "function",
                                    "function": {"name": "leer", "arguments": ""}}]))
        a.linea(_delta(tool_calls=[{"index": 1, "type": "function",
                                    "function": {"name": "guardar", "arguments": '{"x":1}'}}]))
        r = a.resultado("nvidia/z-ai/glm-5.3")
        calls = r["tool_calls"]
        self.assertEqual([c["function"]["name"] for c in calls], ["leer", "guardar"])
        self.assertEqual([c["function"]["arguments"] for c in calls], ["{}", '{"x":1}'])
        self.assertTrue(all(c["id"].startswith("call_") for c in calls))
        self.assertEqual(len({c["id"] for c in calls}), 2)
        self.assertEqual(r["mensaje_asistente"]["tool_calls"], calls)
        self.assertEqual(r["tools_invalidas"], [])

    def test_id_oficial_no_se_modifica(self):
        a = compute.AcumuladorSSE()
        a.linea(_delta(tool_calls=[{"index": 0, "id": "provider-call-123",
                                    "function": {"name": "f", "arguments": '{"a":'}}]))
        a.linea(_delta(tool_calls=[{"index": 0, "function": {"arguments": "2}"}}]))
        r = a.resultado("m")
        self.assertEqual(r["tool_calls"][0]["id"], "provider-call-123")
        self.assertEqual(r["tool_calls"][0]["function"]["arguments"], '{"a":2}')

    def test_ids_sinteticos_son_distintos_entre_respuestas(self):
        def una():
            a = compute.AcumuladorSSE()
            a.linea(_delta(tool_calls=[{"index": 0, "function": {"name": "f", "arguments": "{}"}}]))
            return a.resultado("m")["tool_calls"][0]["id"]
        self.assertNotEqual(una(), una())


class TestSSEVacio(unittest.TestCase):
    def test_stream_fin_sin_texto_ni_tools_es_error(self):
        a = compute.AcumuladorSSE()
        mensaje = "data: " + json.dumps({"choices": [{"delta": {}, "finish_reason": "stop"}]})
        class Respuesta:
            status_code = 200
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def iter_lines(self): return iter((mensaje, "data: [DONE]"))
        class Cliente:
            def stream(self, *args, **kwargs): return Respuesta()
        if externos._httpx is None:
            self.skipTest("httpx no instalado, se prueba con el fallback de integracion")
        with patch.object(externos, "_cliente", lambda: Cliente()):
            with self.assertRaisesRegex(externos.ErrorRed, "sin contenido"):
                externos._solicitar_stream("https://example.invalid/chat/completions",
                                         {"model": "m", "messages": []}, "ficticia", 10, a)


class TestCatalogoVariasClaves(unittest.TestCase):
    def setUp(self):
        self.modelo = "nvidia/z-ai/glm-5.3"
        self.copia = dict(externos.CACHE)
        externos.CACHE.clear()
        externos.CACHE["nvidia"] = (time.time(), ["nvidia/otro-modelo"])
        self.addCleanup(lambda: (externos.CACHE.clear(), externos.CACHE.update(self.copia)))

    def test_modelo_ausente_en_catalogo_de_otra_clave_se_intenta(self):
        visto = []
        def fake(url, payload, clave, timeout):
            visto.append((payload["model"], clave))
            return {"model": payload["model"], "choices": [{"message": {"content": "ok"},
                                                               "finish_reason": "stop"}],
                    "usage": {"completion_tokens": 2}}
        with patch.object(externos, "claves", lambda prov, banco=None: ["k1", "k2"]), \
             patch.object(externos, "_solicitar", fake):
            r = externos.llamar([{"role": "user", "content": "hola"}], self.modelo)
        self.assertEqual(r["texto"], "ok")
        self.assertEqual(visto, [("z-ai/glm-5.3", "k1")])
        self.assertEqual(r["modelo_solicitado"], self.modelo)

    def test_una_clave_con_catalogo_negativo_es_error_explicito(self):
        with patch.object(externos, "claves", lambda prov, banco=None: ["k1"]), \
             patch.object(externos, "_solicitar", side_effect=AssertionError("no consultar")):
            with self.assertRaisesRegex(RuntimeError, "NO DISPONIBLE"):
                externos.llamar([{"role": "user", "content": "hola"}], self.modelo)


if __name__ == "__main__":
    unittest.main()
