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


def tarea4_delegar(c, m, rid):
    nombre = f"chat_estado/delegado-{m}.txt"
    def comprobar():
        ok, d = c.herramienta("almacen", {"accion": "leer", "destino": "hf", "nombre": nombre})
        return ok and "42" in str(d.get("valor", "")), d
    con_tool(c, m, "tarea4 delegar a otro modelo + HF", f"Tarea de delegación: usa la herramienta llm para preguntar al modelo qwen3.8-flash «¿Cuánto es 6 por 7? Responde solo el número». Guarda su respuesta con almacen en destino hf como {nombre}. Confirma.", rid + "t4", comprobar)


def tarea5_notas(c, m, rid):
    def comprobar():
        oky, y = c.herramienta("yaiwes_md", {"accion": "leer"})
        okp, p = c.herramienta("pendientes", {"accion": "listar"})
        lista = {x["texto"]: x["hecho"] for x in p.get("pendientes", [])} if okp else {}
        bien = oky and y.get("texto") == f"proyecto-{m}" and f"tarea5-{m}-a" in lista and lista.get(f"tarea5-{m}-b") is True
        return bien, "yaiwes=%s | pendientes=%s" % (y.get("texto"), {k: v for k, v in lista.items() if k.startswith("tarea5-" + m)})
    con_tool(c, m, "tarea5 yaiwes.md + checklist", f"Con yaiwes_md escribe exactamente el texto proyecto-{m}. Con pendientes agrega los pendientes tarea5-{m}-a y tarea5-{m}-b, y marca como hecho solo el segundo (tarea5-{m}-b). Confirma.", rid + "t5", comprobar)


def tarea6_codigo(c, m, rid):
    ruta = f"Prueba/{m}/palabras.py"
    def comprobar():
        ok, d = c.herramienta("github_leer", {"repo": REPO, "ruta": ruta, "rama": "main"})
        txt = d.get("texto") if isinstance(d, dict) and "texto" in d else ""
        try:
            arbol = ast.parse(txt)
        except SyntaxError as exc:
            return False, "codigo no valido: %s" % exc
        if not all(isinstance(n, SOLO_FUNCIONES) or (isinstance(n, ast.Expr) and isinstance(getattr(n, "value", None), ast.Constant)) for n in arbol.body):
            return False, "el modulo tiene codigo suelto (no solo funciones)"
        ambito = {}
        exec(compile(arbol, "palabras.py", "exec"), ambito)  # noqa: S102 - solo definiciones de funciones
        f = ambito.get("contar_palabras")
        if not callable(f):
            return False, "palabras.py no define contar_palabras (%d caracteres leidos)" % len(txt)
        r = f("hola mundo cruel"), f("")
        return ok and r == (3, 0), "contar_palabras('hola mundo cruel'),('')=%s" % (r,)
    con_tool(c, m, "tarea6 codigo con funcion", f"Tarea de programación. Con github_escribir, en el repo {REPO}, rama main, crea {ruta} con una función Python contar_palabras(texto) que devuelva cuántas palabras tiene el texto (0 si está vacío), con docstring y sin código suelto fuera de la función. Luego léelo con github_leer y confirma.", rid + "t6", comprobar)


TAREAS = {"t1": tarea1_codigo, "t2": tarea2_hf, "t3": tarea3_combinada, "t4": tarea4_delegar, "t5": tarea5_notas, "t6": tarea6_codigo}


def tareas_modelo(c, m, pruebas=None):
    for clave in (pruebas or ["t1", "t2", "t3"]):
        TAREAS[clave](c, m, f"v-{m}-")
