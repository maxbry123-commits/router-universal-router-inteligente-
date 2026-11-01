"""X-Ray 4: Harness, delegacion Tools ON/OFF, MCP y diario de efectos.
Sin conexiones reales; usa un Router MVP falso y nunca toca Hugging Face.
"""
import json
import unittest
from unittest.mock import patch
from plugins.deepseek_harness import server as h


def llamada(nombre, args, ident=None):
    return {"type": "function", **({"id": ident} if ident else {}),
            "function": {"name": nombre, "arguments": json.dumps(args)}}


CAT = {"result": {"tools": [
    {"name": n, "description": "prueba", "inputSchema": {"type": "object"}}
    for n in ("github_leer", "github_escribir", "almacen", "agente", "llm", "loop")
]}}


class TestPermisosHarness(unittest.TestCase):
    def test_delegacion_nunca_salta_tools_off_ni_flag_individual(self):
        off = {"tools": False, "agente_tool": True, "llm_tool": True}
        self.assertFalse(h._delegacion_permitida("agente", off))
        self.assertFalse(h._delegacion_permitida("llm", off))
        self.assertFalse(h._delegacion_permitida("loop", off))
        self.assertTrue(h._delegacion_permitida("almacen", off))  # MCP interno intacto
        self.assertTrue(h._delegacion_permitida("github_leer", off))
        self.assertFalse(h._delegacion_permitida("agente", {"tools": True, "agente_tool": False}))
        self.assertFalse(h._delegacion_permitida("llm", {"tools": True, "llm_tool": False}))
        self.assertTrue(h._delegacion_permitida("llm", {"tools": True, "llm_tool": True}))

    def test_harness_no_ofrece_delegacion_apagada_al_modelo(self):
        vistos = []
        def proveedor(accion, datos):
            self.assertEqual(accion, "chat")
            vistos.extend(t["function"]["name"] for t in datos["opciones"]["tools"])
            return {"texto": "ok", "tool_calls": [], "finish_reason": "stop"}
        with patch.object(h, "llamar", lambda *a, **k: CAT), patch.object(h, "_router", proveedor):
            out = h.llm({"messages": [{"role": "user", "content": "hola"}], "modelo": "x",
                         "tools": False, "agente_tool": False, "llm_tool": False})
        self.assertEqual(out["texto"], "ok")
        self.assertIn("almacen", vistos)
        self.assertIn("github_leer", vistos)
        self.assertNotIn("llm", vistos)
        self.assertNotIn("agente", vistos)
        self.assertNotIn("loop", vistos)

    def test_llamada_no_autorizada_no_toca_mcp_y_vuelve_con_error(self):
        turnos = iter([
            {"texto": "", "tool_calls": [llamada("llm", {"modelo": "x"}, "c1")], "finish_reason": "tool_calls"},
            {"texto": "listo", "tool_calls": [], "finish_reason": "stop"}])
        mensajes = []
        def router(accion, datos):
            mensajes.append(datos["mensajes"])
            return next(turnos)
        def catalogo(plugin, accion, data, timeout=None):
            self.assertEqual(data["method"], "tools/list", "una delegacion OFF jamas alcanza tools/call")
            return CAT
        with patch.object(h, "llamar", catalogo), patch.object(h, "_router", router), patch.object(h, "PAUSA_S", 1e9):
            r = h.llm({"messages": [{"role": "user", "content": "hola"}], "modelo": "x",
                       "tools": False, "llm_tool": False})
        self.assertEqual(r["texto"], "listo")
        self.assertIn("Herramienta no autorizada: llm", json.dumps(mensajes[-1]))


class TestRecibos(unittest.TestCase):
    def test_id_sintetico_y_conservacion_de_id_oficial(self):
        r = h._normalizar_tool_calls([llamada("almacen", {"accion": "leer"}),
                                      llamada("github_leer", {"repo": "o/r"}, "real-id")])
        self.assertTrue(r[0]["id"].startswith("call_"))
        self.assertEqual(r[1]["id"], "real-id")
        self.assertNotEqual(r[0]["id"], r[1]["id"])

    def test_ids_duplicados_rechazados_antes_de_ejecutar(self):
        with self.assertRaisesRegex(RuntimeError, "DUPLICADO"):
            h._normalizar_tool_calls([llamada("a", {}, "same"), llamada("b", {}, "same")])

    def test_efectos_protegidos_incluyen_mcp_externo_archivos_y_loop(self):
        for n, args in [
            ("mcp__12345678__enviar", {}), ("archivos", {"accion": "ejecutar"}),
            ("archivos", {}), ("loop", {"accion": "cancelar"}), ("loop", {"accion": "motor_ejecutar"}),
            ("github_escribir", {}), ("sala", {"accion": "contexto"})]:
            self.assertTrue(h.con_efectos(n, args), (n, args))
        for n, args in [("github_leer", {}), ("archivos", {"accion": "listar_raiz"}),
                        ("loop", {"accion": "status"}), ("sala", {"accion": "leer"})]:
            self.assertFalse(h.con_efectos(n, args), (n, args))

    def test_mcp_error_nunca_es_recibo_de_operacion_confirmada(self):
        self.assertTrue(h._respuesta_mcp_fallida({"error": {"code": -32000}}))
        self.assertTrue(h._respuesta_mcp_fallida({"result": {"isError": True}}))
        self.assertFalse(h._respuesta_mcp_fallida({"result": {"isError": False}}))

    def test_error_de_tool_efectiva_deja_diario_iniciada_y_para(self):
        diario, anotadas, llamadas = {}, [], []
        turnos = iter([{"texto": "", "tool_calls": [
            llamada("github_escribir", {"repo": "o/r", "ruta": "a", "contenido": "b"}, "c1")
        ], "finish_reason": "tool_calls"}])
        def router(accion, datos):
            self.assertEqual(accion, "chat")
            return next(turnos)
        def mcp(plugin, accion, datos, timeout=None):
            llamadas.append(datos["method"])
            return CAT if datos["method"] == "tools/list" else {"error": {"code": -32000, "message": "desconocido"}}
        with patch.object(h, "llamar", mcp), patch.object(h, "_router", router), \
             patch.object(h, "_diario", lambda tarea: diario), \
             patch.object(h, "_anotar", lambda tarea, d: anotadas.append(dict(d))), \
             patch.object(h, "PAUSA_S", 1e9):
            with self.assertRaisesRegex(RuntimeError, "OPERACION_SIN_CONFIRMAR"):
                h.llm({"messages": [{"role": "user", "content": "escribe"}], "modelo": "x", "tarea_id": "tarea-x"})
        self.assertEqual(llamadas, ["tools/list", "tools/call"])
        self.assertEqual(len(anotadas), 1)
        self.assertEqual(next(iter(diario.values()))["estado"], "INICIADA")


if __name__ == "__main__":
    unittest.main()
