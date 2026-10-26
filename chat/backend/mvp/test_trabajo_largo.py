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
