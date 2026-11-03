"""Rotacion de claves en memoria y Retry-After del motor CODA.
Estas pruebas no llaman APIs reales ni imprimen secretos.
"""
import unittest
from unittest.mock import patch
from mvp import externos


class RotacionGroqTest(unittest.TestCase):
    def _patch(self, solicitar, keys):
        return (
            patch.object(externos, "claves", return_value=keys),
            patch.object(externos, "_solicitar", side_effect=solicitar),
            patch.object(externos, "_dormir", side_effect=lambda _s: None),
            patch.object(externos, "_azar", return_value=0.0),
        )

    def test_segunda_clave_si_la_primera_da_429(self):
        vistos = []
        def solicitar(_url, payload, key, _timeout):
            vistos.append(key)
            if key == "gsk-clave-ficticia-uno":
                raise externos.ErrorHTTP(429, retry_after=120)
            return {"model":payload["model"],
                    "choices":[{"message":{"content":"GROQ_OK"},"finish_reason":"stop"}]}
        mocks = self._patch(solicitar, ["gsk-clave-ficticia-uno","gsk-clave-ficticia-dos"])
        with mocks[0], mocks[1], mocks[2], mocks[3]:
            externos.limpiar_enfriadas()
            out = externos.llamar([{"role":"user","content":"hola"}],
                                  "groq/qwen/qwen3.8-27b", opciones={"max_tokens":60})
        self.assertEqual(out["texto"], "GROQ_OK")
        self.assertEqual(vistos, ["gsk-clave-ficticia-uno","gsk-clave-ficticia-dos"])
        diag = out["metricas"]["credenciales"]
        self.assertEqual((diag["configuradas"],diag["probadas"],diag["rotaciones"]), (2,2,1))
        self.assertEqual(diag["errores_http"].get("429"), 1)
        self.assertEqual(diag["retry_after_s"], 120.0)
        self.assertNotIn("gsk-", str(diag))

    def test_una_sola_clave_no_simula_rotacion(self):
        def solicitar(_url, payload, _key, _timeout):
            return {"model":payload["model"],
                    "choices":[{"message":{"content":"ok"},"finish_reason":"stop"}]}
        mocks = self._patch(solicitar, ["gsk-clave-ficticia-unica"])
        with mocks[0], mocks[1], mocks[2], mocks[3]:
            out = externos.llamar([{"role":"user","content":"hola"}],
                                  "groq/qwen/qwen3.8-27b", opciones={"max_tokens":60})
        d = out["metricas"]["credenciales"]
        self.assertEqual((d["configuradas"],d["probadas"],d["rotaciones"]), (1,1,0))

    def test_todas_429_informa_conteos_sin_valores(self):
        def solicitar(_url, _payload, _key, _timeout):
            raise externos.ErrorHTTP(429, retry_after=120)
        mocks = self._patch(solicitar, ["gsk-clave-ficticia-uno","gsk-clave-ficticia-dos"])
        with mocks[0], mocks[1], mocks[2], mocks[3]:
            with self.assertRaises(externos.ErrorProveedor) as c:
                externos.llamar([{"role":"user","content":"hola"}],
                                "groq/qwen/qwen3.8-27b", opciones={"max_tokens":60})
        msg = str(c.exception)
        self.assertIn("credenciales_configuradas=2", msg)
        self.assertIn("credenciales_probadas=2", msg)
        self.assertIn("rotaciones=1", msg)
        self.assertIn("retry_after_s=120", msg)
        self.assertNotIn("gsk-", msg)


if __name__ == "__main__":
    unittest.main()
