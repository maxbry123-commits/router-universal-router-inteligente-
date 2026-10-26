"""Sin tope de vueltas de herramientas: 20 vueltas seguidas, pausas del Harness y reanudacion del Router hasta 48 h."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from plugins.deepseek_harness import server as h
from mvp import app as servicio

CATALOGO = {"result": {"tools": [{"name": "almacen", "description": "d", "inputSchema": {"type": "object"}}]}}


def _vuelta(i):
    return {"texto": "", "finish_reason": "tool_calls", "tool_calls": [{"id": "c%d" % i, "function": {"name": "almacen", "arguments": '{"accion":"leer","nombre":"x"}'}}]}


class TrabajoLargo(unittest.TestCase):
    def _llm(self, vueltas, pausa):
        cola = [_vuelta(i) for i in range(vueltas)] + [{"texto": "listo", "finish_reason": "stop", "tool_calls": []}]
        def llamar(plugin, accion, datos, timeout=0):
            return CATALOGO if datos.get("method") == "tools/list" else {"result": {"content": [{"type": "text", "text": "ok"}]}}
        with patch.object(h, "PAUSA_S", pausa), patch.object(h, "llamar", llamar), patch.object(h, "_router", lambda a, d: cola.pop(0)):
            return h.llm({"messages": [{"role": "user", "content": "x"}], "modelo": "qwen3.8-max"}), cola

    def test_veinte_vueltas_ya_no_cortan_en_ocho(self):
        r, cola = self._llm(20, 3600)
        self.assertEqual(r["texto"], "listo")
        self.assertEqual(len(r["herramientas_usadas"]), 20)
        self.assertNotIn("continuar", r)

    def test_con_pausa_devuelve_continuar_y_la_conversacion(self):
        r, cola = self._llm(20, -1)  # pausa inmediata despues de la primera vuelta
        self.assertTrue(r["continuar"])
        self.assertEqual(r["finish_reason"], "pausa_herramientas")
        self.assertTrue(any(m.get("role") == "tool" for m in r["mensajes"]))
        self.assertEqual(len(r["herramientas_usadas"]), 1)

    def test_el_router_reanuda_hasta_el_final(self):
        pausa = {"continuar": True, "finish_reason": "pausa_herramientas", "texto": "", "tool_calls": [],
                 "mensajes": [{"role": "user", "content": "x"}, {"role": "tool", "content": "ok"}], "herramientas_usadas": ["almacen"]}
        fin = {"texto": "listo", "tool_calls": [], "finish_reason": "stop", "herramientas_usadas": ["almacen"]}
        salidas = [{"result": dict(pausa)}] * 3 + [{"result": fin}]
        llamadas = []
        def falso(clave, mensajes, modelo, opciones=None, controles=None):
            llamadas.append(list(mensajes))
            return salidas.pop(0)
        import asyncio
        with patch.object(servicio.harness_client, "llm", falso), patch.object(servicio, "clave_harness", lambda: "k"):
            r = asyncio.run(servicio.chat({"modelo": "qwen3.8-max", "mensajes": [{"role": "user", "content": "x"}], "via": "harness"}))
        self.assertEqual(r["texto"], "listo")
        self.assertEqual(len(llamadas), 4)
        self.assertEqual(r["herramientas_usadas"], ["almacen"] * 4)
        self.assertEqual(llamadas[1][-1]["role"], "tool")  # reanuda con lo que devolvio el Harness

    def test_el_limite_es_de_48_horas(self):
        pausa = {"continuar": True, "finish_reason": "pausa_herramientas", "texto": "", "tool_calls": [], "mensajes": [{"role": "user", "content": "x"}]}
        import asyncio, os
        from fastapi import HTTPException
        with patch.object(servicio.harness_client, "llm", lambda *a, **k: {"result": dict(pausa)}), patch.object(servicio, "clave_harness", lambda: "k"), patch.dict(os.environ, {"RIU_MAX_HORAS": "0"}):
            with self.assertRaises(HTTPException) as e:
                asyncio.run(servicio.chat({"modelo": "qwen3.8-max", "mensajes": [{"role": "user", "content": "x"}], "via": "harness"}))
        self.assertEqual(e.exception.status_code, 504)
        self.assertIn("48 h", e.exception.detail)


if __name__ == "__main__":
    unittest.main()


class ContextoAcotado(unittest.TestCase):
    def test_compactar_recorta_solo_herramientas_viejas_y_respeta_lo_demas(self):
        grande = "x" * 50_000
        msgs = [{"role": "system", "content": "regla"}, {"role": "user", "content": "objetivo"}]
        for i in range(10):
            msgs += [{"role": "assistant", "content": "", "tool_calls": []}, {"role": "tool", "tool_call_id": "c%d" % i, "content": grande}]
        out = h.compactar(msgs, tope=200_000)
        self.assertLessEqual(h._tam(out), 200_000)
        self.assertEqual(out[0]["content"], "regla")
        self.assertEqual(out[1]["content"], "objetivo")
        self.assertEqual(out[-1]["content"], grande)           # las ultimas vueltas quedan completas
        self.assertIn("recortado", out[3]["content"])          # las viejas quedan recortadas
        self.assertEqual(len(out), len(msgs))                  # no se pierde ningun mensaje (ids de tool_call intactos)

    def test_no_toca_nada_si_cabe(self):
        msgs = [{"role": "user", "content": "x"}, {"role": "tool", "content": "y" * 1000}]
        self.assertEqual(h.compactar(msgs, tope=10_000), msgs)

    def test_cuarenta_vueltas_de_50k_no_pasan_del_tope_en_la_peticion_al_modelo(self):
        vistos = []
        cola = [_vuelta(i) for i in range(40)] + [{"texto": "listo", "finish_reason": "stop", "tool_calls": []}]
        def router(a, d):
            vistos.append(h._tam(d["mensajes"]))
            return cola.pop(0)
        def llamar(plugin, accion, datos, timeout=0):
            return CATALOGO if datos.get("method") == "tools/list" else {"result": {"content": [{"type": "text", "text": "z" * 50_000}]}}
        with patch.object(h, "PAUSA_S", 3600), patch.object(h, "llamar", llamar), patch.object(h, "_router", router), patch.object(h, "CONTEXTO_MAX", 300_000):
            r = h.llm({"messages": [{"role": "user", "content": "x"}], "modelo": "qwen3.8-max"})
        self.assertEqual(r["texto"], "listo")
        self.assertLess(max(vistos), 600_000)   # sin compactar llegaria a ~2.000.000 y el Router daria 413
