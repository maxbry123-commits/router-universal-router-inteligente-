"""Sin tope de vueltas de herramientas: 20 vueltas seguidas, pausas del Harness y reanudacion del Router hasta 48 h."""
import json
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

    def test_sin_limite_por_defecto_y_solo_corta_si_se_fija_RIU_MAX_HORAS(self):
        pausa = {"continuar": True, "finish_reason": "pausa_herramientas", "texto": "", "tool_calls": [], "mensajes": [{"role": "user", "content": "x"}]}
        import asyncio, os
        from fastapi import HTTPException
        with patch.object(servicio.harness_client, "llm", lambda *a, **k: {"result": dict(pausa)}), patch.object(servicio, "clave_harness", lambda: "k"), patch.dict(os.environ, {"RIU_MAX_HORAS": "0.00001"}):
            with self.assertRaises(HTTPException) as e:
                asyncio.run(servicio.chat({"modelo": "qwen3.8-max", "mensajes": [{"role": "user", "content": "x"}], "via": "harness"}))
        self.assertEqual(e.exception.status_code, 504)
        self.assertIn("tiempo maximo", e.exception.detail)


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


    def test_por_defecto_no_hay_limite_de_tiempo(self):
        import asyncio, os
        pausa = {"continuar": True, "finish_reason": "pausa_herramientas", "texto": "", "tool_calls": [], "mensajes": [{"role": "user", "content": "x"}]}
        salidas = [{"result": dict(pausa)}] * 5 + [{"result": {"texto": "listo", "tool_calls": [], "finish_reason": "stop"}}]
        env = {k: v for k, v in os.environ.items() if k != "RIU_MAX_HORAS"}
        with patch.object(servicio.harness_client, "llm", lambda *a, **k: salidas.pop(0)), patch.object(servicio, "clave_harness", lambda: "k"), patch.dict(os.environ, env, clear=True), patch.object(servicio.time, "time", lambda: 9e12):
            r = asyncio.run(servicio.chat({"modelo": "qwen3.8-max", "mensajes": [{"role": "user", "content": "x"}], "via": "harness"}))
        self.assertEqual(r["texto"], "listo")


class DiarioYRondas(unittest.TestCase):
    def _correr(self, tarea, ya_hechas=None, vueltas=None):
        """Una invocacion del Harness (como cada retoma). `ejecutadas` cuenta lo que realmente se ejecuta."""
        ejecutadas, diario = [], dict(ya_hechas or {})
        cola = list(vueltas)
        def llamar(plugin, accion, datos, timeout=None):
            if datos.get("method") == "tools/list":
                return {"result": {"tools": [{"name": n, "description": "d", "inputSchema": {"type": "object"}} for n in ("github_escribir", "github_leer")]}}
            ejecutadas.append((datos["params"]["name"], datos["params"]["arguments"]))
            return {"result": {"content": [{"type": "text", "text": "hecho"}]}}
        guardados = {}
        def leer(args):
            if args["nombre"] not in guardados and not diario:
                raise RuntimeError("no existe")
            return {"valor": json.dumps(diario)}
        def guardar(args):
            guardados[args["nombre"]] = args["valor"]; diario.update(json.loads(args["valor"]))
            return {"nombre": args["nombre"]}
        with patch.object(h, "llamar", llamar), patch.object(h, "_router", lambda a, d: cola.pop(0)), patch.object(h, "leer", leer), patch.object(h, "guardar", guardar), patch.object(h, "PAUSA_S", 3600):
            r = h.llm({"messages": [{"role": "user", "content": "x"}], "modelo": "qwen3.8-max", "tarea_id": tarea})
        return r, ejecutadas, diario

    @staticmethod
    def _tool(i, nombre, args):
        return {"texto": "", "finish_reason": "tool_calls", "tool_calls": [{"id": "c%d" % i, "function": {"name": nombre, "arguments": json.dumps(args)}}]}

    def test_una_escritura_ya_hecha_no_se_repite_al_retomar(self):
        fin = {"texto": "listo", "finish_reason": "stop", "tool_calls": []}
        args = {"repo": "r", "ruta": "a.txt", "contenido": "x"}
        r1, ej1, diario = self._correr("p-1", vueltas=[self._tool(1, "github_escribir", args), fin])
        self.assertEqual(len(ej1), 1)                       # primera vez: se ejecuta y queda en el diario
        self.assertTrue(diario)
        r2, ej2, _ = self._correr("p-1", ya_hechas=diario, vueltas=[self._tool(2, "github_escribir", args), fin])  # el modelo la vuelve a pedir tras el reinicio
        self.assertEqual(ej2, [])                           # NO se ejecuta otra vez
        self.assertEqual(r2["texto"], "listo")

    def test_las_lecturas_siempre_se_ejecutan_y_otra_escritura_distinta_tambien(self):
        fin = {"texto": "listo", "finish_reason": "stop", "tool_calls": []}
        _, ej, diario = self._correr("p-2", vueltas=[self._tool(1, "github_leer", {"repo": "r"}), self._tool(2, "github_leer", {"repo": "r"}), fin])
        self.assertEqual(len(ej), 2)
        _, ej, _ = self._correr("p-2", ya_hechas={"otra": "x"}, vueltas=[self._tool(3, "github_escribir", {"repo": "r", "ruta": "b", "contenido": "y"}), fin])
        self.assertEqual(len(ej), 1)

    def test_sin_tarea_id_no_hay_diario(self):
        fin = {"texto": "listo", "finish_reason": "stop", "tool_calls": []}
        args = {"repo": "r", "ruta": "a", "contenido": "x"}
        _, ej, diario = self._correr("", vueltas=[self._tool(1, "github_escribir", args), self._tool(2, "github_escribir", args), fin])
        self.assertEqual(len(ej), 2)
        self.assertFalse(diario)

    def test_el_diario_no_guarda_credenciales(self):
        self.assertNotIn("ghp_", h._SECRETO.sub("[REDACTADO]", "token ghp_ABCDEFGHIJKLMNOPQRSTUV fin"))

    def test_por_defecto_el_harness_devuelve_la_conversacion_tras_cada_ronda(self):
        cola = [self._tool(1, "github_leer", {"repo": "r"}), self._tool(2, "github_leer", {"repo": "r"}),
                {"texto": "listo", "finish_reason": "stop", "tool_calls": []}]
        def llamar(plugin, accion, datos, timeout=None):
            return ({"result": {"tools": [{"name": "github_leer", "description": "d", "inputSchema": {"type": "object"}}]}} if datos.get("method") == "tools/list"
                    else {"result": {"content": [{"type": "text", "text": "ok"}]}})
        with patch.object(h, "llamar", llamar), patch.object(h, "_router", lambda a, d: cola.pop(0)):
            r = h.llm({"messages": [{"role": "user", "content": "x"}], "modelo": "qwen3.8-max"})
        self.assertTrue(r["continuar"])                      # PAUSA_S=0: tras la primera ronda ya devuelve para que el Router guarde
        self.assertEqual(len(r["herramientas_usadas"]), 1)
