"""Con el servidor arriba, la tarea no se corta: fallas pasajeras se reintentan, el contexto se ajusta al modelo, una herramienta mala no la mata."""
import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fastapi import HTTPException
from plugins.deepseek_harness import server as h
from mvp import app as servicio

FIN = {"result": {"texto": "listo", "tool_calls": [], "finish_reason": "stop", "herramientas_usadas": []}}
MSGS = [{"role": "user", "content": "x"}]


async def _rapido(_s):
    return None


def _chat(llm, **extra):
    async def correr():
        with patch.object(servicio.harness_client, "llm", llm), patch.object(servicio, "clave_harness", lambda: "k"), patch.object(servicio.asyncio, "sleep", _rapido):
            return await servicio.chat({"modelo": "qwen3.8-max", "mensajes": extra.get("mensajes", MSGS), "via": "harness"})
    return asyncio.run(correr())


import unittest


class Reintentos(unittest.TestCase):
    def test_falla_pasajera_del_harness_se_reintenta_hasta_que_vuelve(self):
        fallos = ["Harness no disponible", "Harness HTTP 503", "Harness no disponible"]
        def llm(*a, **k):
            if fallos: raise RuntimeError(fallos.pop(0))
            return FIN
        self.assertEqual(_chat(llm)["texto"], "listo")
        self.assertEqual(fallos, [])

    def test_proveedor_saturado_o_caido_se_reintenta(self):
        for motivo in ("Router HTTP 502: Qwen HTTP 429", "Router HTTP 502: Qwen HTTP 500", "Router HTTP 502: Qwen error de red"):
            intentos = []
            def llm(*a, **k):
                intentos.append(1)
                if len(intentos) < 3: return {"status": "error", "error": motivo}
                return FIN
            self.assertEqual(_chat(llm)["texto"], "listo", motivo)
            self.assertEqual(len(intentos), 3)

    def test_un_error_que_no_se_arregla_esperando_si_termina(self):
        def llm(*a, **k):
            return {"status": "error", "error": "Router HTTP 502: Qwen HTTP 401"}   # clave mala: reintentar no sirve
        with self.assertRaises(HTTPException) as e:
            _chat(llm)
        self.assertEqual(e.exception.status_code, 502)

    def test_si_el_modelo_no_admite_tanto_contexto_se_reduce_y_sigue(self):
        grande = [{"role": "user", "content": "a" * 400_000}]
        vistos = []
        def llm(clave, mensajes, modelo, opciones=None, controles=None):
            vistos.append((controles or {}).get("contexto_max"))
            if len(vistos) == 1: return {"status": "error", "error": "Router HTTP 502: Qwen HTTP 400"}
            return FIN
        self.assertEqual(_chat(llm, mensajes=grande)["texto"], "listo")
        self.assertIsNone(vistos[0])
        self.assertEqual(vistos[1], 200_000)     # la mitad de lo que llevaba

    def test_un_400_con_contexto_pequeno_es_un_error_real(self):
        def llm(*a, **k):
            return {"status": "error", "error": "Router HTTP 502: Qwen HTTP 400"}
        with self.assertRaises(HTTPException):
            _chat(llm)


class HerramientaMala(unittest.TestCase):
    def test_pedir_una_herramienta_no_autorizada_no_corta_la_tarea(self):
        cola = [{"texto": "", "finish_reason": "tool_calls", "tool_calls": [{"id": "c1", "function": {"name": "borrar_todo", "arguments": "{}"}}]},
                {"texto": "listo", "finish_reason": "stop", "tool_calls": []}]
        vistos = []
        def router(a, d):
            vistos.append(d["mensajes"]); return cola.pop(0)
        def llamar(plugin, accion, datos, timeout=None):
            return {"result": {"tools": [{"name": "almacen", "description": "d", "inputSchema": {"type": "object"}}]}}
        with patch.object(h, "llamar", llamar), patch.object(h, "_router", router), patch.object(h, "PAUSA_S", 3600):
            r = h.llm({"messages": MSGS, "modelo": "qwen3.8-max"})
        self.assertEqual(r["texto"], "listo")
        tool = [m for m in vistos[1] if m.get("role") == "tool"][0]
        self.assertIn("no autorizada", tool["content"])        # el modelo recibe el error y puede elegir otra
        self.assertEqual(tool["tool_call_id"], "c1")

    def test_escribir_en_otra_rama_tambien_devuelve_error_al_modelo(self):
        cola = [{"texto": "", "finish_reason": "tool_calls", "tool_calls": [{"id": "c1", "function": {"name": "github_escribir", "arguments": json.dumps({"repo": "r", "ruta": "a", "contenido": "x", "rama": "otra"})}}]},
                {"texto": "listo", "finish_reason": "stop", "tool_calls": []}]
        def llamar(plugin, accion, datos, timeout=None):
            return {"result": {"tools": [{"name": "github_escribir", "description": "d", "inputSchema": {"type": "object"}}]}}
        with patch.object(h, "llamar", llamar), patch.object(h, "_router", lambda a, d: cola.pop(0)), patch.object(h, "PAUSA_S", 3600):
            self.assertEqual(h.llm({"messages": MSGS, "modelo": "qwen3.8-max"})["texto"], "listo")


if __name__ == "__main__":
    unittest.main()
