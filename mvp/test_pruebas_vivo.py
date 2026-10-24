"""El ejecutor de pruebas reales debe seguir corriendo de punta a punta (con un Router simulado) y dejar su informe."""
import json
import os
import tempfile
import unittest
from unittest.mock import patch
from mvp.pruebas_vivo import correr, pruebas


class ClienteFalso:
    def __init__(self, base, clave): self.n = 0
    def health(self): return {"status": "ok", "commit": "x"}
    def mcp(self, metodo, params=None): return 200, {"result": {"tools": [{"name": "chat"}]}}
    def post(self, ruta, cuerpo, timeout=60): return 200, {}
    def herramienta(self, nombre, args): return True, {"pendientes": [], "texto": ""}
    def chat(self, modelo, mensaje=None, rid="x", vueltas=20, **extra):
        return {"estado": "completado", "choices": [{"message": {"content": "PONG-%s 391 42" % modelo}}]}


class Ejecutor(unittest.TestCase):
    def test_corre_completo_y_escribe_el_informe(self):
        pruebas.FILAS.clear()
        with tempfile.TemporaryDirectory() as d, patch("mvp.pruebas_vivo.correr.Cliente", ClienteFalso), patch.dict(os.environ, {"RIU_KEY": "k"}):
            antes = os.getcwd(); os.chdir(d)
            try:
                correr.main(["correr", "--solo", "glm-5.3"])
                informe = open("informe_sol.md", encoding="utf-8").read()
            finally:
                os.chdir(antes)
        self.assertIn("glm-5.3", informe)
        self.assertTrue(any(f["prueba"] == "eco" and f["estado"] == "PASS" for f in pruebas.FILAS))
        self.assertEqual(sum(1 for f in pruebas.FILAS if f["prueba"] == "tool github escribir"), 1)  # una sola vez


class RouterConEstado:
    """Router simulado con estado: el 'modelo' ejecuta lo que pide la tarea (o algo malo si malo=True) y las herramientas lo leen de vuelta."""
    def __init__(self, base=None, clave=None, malo=False):
        self.archivos, self.hf, self.pend, self.malo = {}, {}, [], malo
    def health(self): return {"status": "ok"}
    def mcp(self, metodo, params=None): return 200, {"result": {"tools": [{"name": "chat"}]}}
    def post(self, ruta, cuerpo, timeout=60): return 200, {}
    def chat(self, modelo, mensaje=None, rid="x", vueltas=20, **extra):
        if rid.endswith("t1"):
            self.archivos[f"Prueba/{modelo}/calculadora.py"] = "import os\nos.system('echo x')\n" if self.malo else '"""m"""\ndef suma(a, b):\n    """s"""\n    return a + b\n\n\ndef resta(a, b):\n    """r"""\n    return a - b\n'
        if rid.endswith("t2"):
            self.hf[f"chat_estado/prueba-{modelo}.json"] = json.dumps({"modelo": modelo, "tarea": "hf", "numeros": [1, 2, 3], "suma": 6})
        if rid.endswith("t3"):
            self.hf[f"chat_estado/resumen-{modelo}.txt"] = "El Router decide y guarda claves; el Harness ejecuta el trabajo con plugins y herramientas."
            self.pend.append({"id": "1", "texto": f"tarea3-{modelo}", "hecho": False})
        if rid.endswith("t4"):
            self.hf[f"chat_estado/delegado-{modelo}.txt"] = "42"
        if rid.endswith("t5"):
            self.yaiwes = f"proyecto-{modelo}"
            self.pend += [{"id": "a", "texto": f"tarea5-{modelo}-a", "hecho": False}, {"id": "b", "texto": f"tarea5-{modelo}-b", "hecho": True}]
        if rid.endswith("t6"):
            self.archivos[f"Prueba/{modelo}/palabras.py"] = '"""m"""\ndef contar_palabras(texto):\n    """c"""\n    return len(texto.split())\n'
        return {"estado": "completado", "choices": [{"message": {"content": "hecho"}}]}
    def herramienta(self, nombre, args):
        if nombre == "github_leer":
            return True, {"texto": self.archivos.get(args["ruta"], "")}
        if nombre == "almacen":
            return True, {"valor": self.hf.get(args["nombre"], "")}
        if nombre == "pendientes":
            return True, {"pendientes": self.pend}
        if nombre == "yaiwes_md":
            return True, {"texto": getattr(self, "yaiwes", "")}
        return True, {}


class TareasReales(unittest.TestCase):
    def correr(self, malo, lista=None):
        from mvp.pruebas_vivo import tareas
        pruebas.FILAS.clear()
        tareas.tareas_modelo(RouterConEstado(malo=malo), "glm-5.3", lista)
        return {f["prueba"]: f["estado"] for f in pruebas.FILAS}

    def test_tres_tareas_pasan_y_se_comprueban_leyendo_el_resultado(self):
        self.assertEqual(set(self.correr(False).values()), {"PASS"})

    def test_codigo_con_instrucciones_sueltas_no_se_ejecuta_y_falla(self):
        r = self.correr(True)
        self.assertEqual(r["tarea1 codigo en GitHub"], "FAIL")

    def test_las_seis_tareas_existen_y_pasan(self):
        r = self.correr(False, ["t1", "t2", "t3", "t4", "t5", "t6"])
        self.assertEqual((len(r), set(r.values())), (6, {"PASS"}))

    def test_funcion_con_otro_nombre_es_fail_y_la_corrida_sigue(self):  # antes: KeyError 'contar_palabras' cortaba todo
        from mvp.pruebas_vivo import tareas
        pruebas.FILAS.clear()
        r = RouterConEstado(malo=False)
        original = r.herramienta
        def herramienta(nombre, args):
            if nombre == "github_leer" and args.get("ruta", "").endswith("palabras.py"):
                return True, {"texto": "def contar(texto):\n    return len(texto.split())\n"}
            return original(nombre, args)
        r.herramienta = herramienta
        tareas.tareas_modelo(r, "glm-5.3", ["t6", "t5"])
        estados = {f["prueba"]: f["estado"] for f in pruebas.FILAS}
        self.assertEqual(estados["tarea6 codigo con funcion"], "FAIL"); self.assertIn("tarea5 yaiwes.md + checklist", estados)

