"""Los conteos de claves del Router pasan por el Harness sin secretos."""
import unittest
from plugins.deepseek_harness import server as harness


class MetricasCredenciales(unittest.TestCase):
    def test_relay_solamente_valores_numericos_seguros(self):
        m = {"metricas":{"stream": True, "credenciales":{
            "configuradas": 3, "probadas": 2, "rotaciones": 1,
            "llamadas_http": 2, "retry_after_s": 120.0,
            "errores_http":{"429":1, "codigo_inventado":9},
            "clave": "gsk-no-debe-aparecer",
            "hash": "no-debe-aparecer",
            "token": "nunca"}}}
        out = harness._metricas(m)
        c = out["metricas"]["credenciales"]
        self.assertEqual(c["configuradas"],3)
        self.assertEqual(c["rotaciones"],1)
        self.assertEqual(c["errores_http"],{"429":1})
        self.assertNotIn("clave",str(out))
        self.assertNotIn("hash",str(out))
        self.assertNotIn("gsk-",str(out))

    def test_rechaza_texto_y_contadores_falsos(self):
        out = harness._metricas({"metricas":{"credenciales":{
            "configuradas":"secret", "rotaciones":-99, "probadas":True,
            "errores_http":{"429":"no","500":3}}}})
        c = out["metricas"]["credenciales"]
        self.assertNotIn("configuradas", c)
        self.assertNotIn("rotaciones", c)
        self.assertNotIn("probadas", c)
        self.assertEqual(c["errores_http"],{"500":3})


if __name__ == "__main__":
    unittest.main()
