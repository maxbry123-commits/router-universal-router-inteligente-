"""Tareas reales de programacion por modelo: escribir codigo en GitHub, guardar datos en HF y combinar herramientas. Cada tarea se comprueba leyendo el resultado."""
import ast
import json
from mvp.pruebas_vivo.pruebas import REPO, con_tool

SOLO_FUNCIONES = (ast.FunctionDef, ast.Import, ast.ImportFrom)


def _codigo_ok(texto):
    """Ejecuta el codigo escrito por el modelo SOLO si el modulo contiene unicamente funciones (nada se ejecuta al importarlo)."""
    arbol = ast.parse(texto)
    cuerpo = [n for n in arbol.body if not (isinstance(n, ast.Expr) and isinstance(getattr(n, "value", None), ast.Constant))]
    if not all(isinstance(n, SOLO_FUNCIONES) for n in cuerpo):
        return False, "el modulo tiene codigo suelto (no solo funciones)"
    ambito = {}
    exec(compile(arbol, "calculadora.py", "exec"), ambito)  # noqa: S102 - solo definiciones de funciones
    return ambito["suma"](2, 3) == 5 and ambito["resta"](5, 2) == 3, "suma(2,3)=%s resta(5,2)=%s" % (ambito["suma"](2, 3), ambito["resta"](5, 2))


def tarea1_codigo(c, m, rid):
    ruta = f"Prueba/{m}/calculadora.py"
    def comprobar():
        ok, d = c.herramienta("github_leer", {"repo": REPO, "ruta": ruta, "rama": "main"})
        txt = d.get("texto") if isinstance(d, dict) and "texto" in d else (d if isinstance(d, str) else json.dumps(d))
        try:
            bien, detalle = _codigo_ok(txt if isinstance(txt, str) else "")
        except (SyntaxError, KeyError, TypeError, NameError) as exc:
            return False, "codigo no valido: %s" % exc
        return ok and bien, detalle
    con_tool(c, m, "tarea1 codigo en GitHub", f"Tarea de programación. Con github_escribir, en el repo {REPO}, rama main, crea el archivo {ruta} con dos funciones Python: suma(a, b) que devuelve a+b y resta(a, b) que devuelve a-b, ambas con docstring y sin código suelto fuera de las funciones. Luego léelo con github_leer y confirma.", rid + "t1", comprobar)


def tarea2_hf(c, m, rid):
    nombre = f"chat_estado/prueba-{m}.json"
    def comprobar():
        ok, d = c.herramienta("almacen", {"accion": "leer", "destino": "hf", "nombre": nombre})
        try:
            doc = json.loads(d.get("valor", ""))
        except (ValueError, TypeError):
            return False, "no hay JSON valido en HF: %s" % json.dumps(d)[:150]
        return ok and doc.get("modelo") == m and doc.get("suma") == 6 and doc.get("numeros") == [1, 2, 3], doc
    con_tool(c, m, "tarea2 datos en HF", f'Con la herramienta almacen guarda en destino hf el nombre {nombre} con este JSON válido exacto como valor: {{"modelo": "{m}", "tarea": "hf", "numeros": [1, 2, 3], "suma": 6}}. Luego léelo de vuelta y confirma.', rid + "t2", comprobar)


def tarea3_combinada(c, m, rid):
    nombre = f"chat_estado/resumen-{m}.txt"
    def comprobar():
        ok, d = c.herramienta("almacen", {"accion": "leer", "destino": "hf", "nombre": nombre})
        okp, p = c.herramienta("pendientes", {"accion": "listar"})
        resumen = str(d.get("valor", ""))
        return ok and okp and len(resumen) > 40 and ("Router" in resumen or "Harness" in resumen) and f"tarea3-{m}" in json.dumps(p), "resumen=%s | pendiente=%s" % (resumen[:100], f"tarea3-{m}" in json.dumps(p))
    con_tool(c, m, "tarea3 GitHub+HF+pendientes", f"Tarea combinada en 3 pasos: (1) con github_leer lee docs/ARQUITECTURA.md del repo {REPO} en la rama main; (2) resume en máximo 3 frases qué son los dos edificios y guarda ese resumen con almacen en destino hf como {nombre}; (3) con pendientes agrega el pendiente 'tarea3-{m}'. Confirma los tres pasos.", rid + "t3", comprobar)


def tareas_modelo(c, m):
    for tarea in (tarea1_codigo, tarea2_hf, tarea3_combinada):
        tarea(c, m, f"v-{m}-")
