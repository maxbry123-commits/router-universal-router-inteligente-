#!/usr/bin/env python3
"""FICHA ejecutable en Python (copia de las otras fichas; solo cambian modelos, goals y Ask Council).

Uso:  python3 FICHA.py --mensaje "tarea..." [--modelo ficha-qwen38max]
Env:  RIU_HARNESS_URL = puente del chat (POST {model, messages, max_tokens});  RIU_CLAVE = clave opcional
      FICHA_SIMULAR=1 = prueba sin llamar a ningun modelo
No toca el Router: solo llama al puente que ya existe.
"""
import argparse, json, os, re, subprocess, sys, tempfile, urllib.request

# ================= CONFIG (generado de la ficha; es lo unico que cambia entre fichas) =================
FICHA = {'ficha': 'ficha2-dag-codigo',
 'tipo': 'dag',
 'version': 2,
 'api': 'modelos-14',
 'readme': '../README-FICHAS.md',
 'memory': {'provider': 'harness',
            'namespace': '{TASK_ID}',
            'project_memory': 'YAIWES',
            'read_project_memory': True,
            'write_task_memory': True,
            'write_project_memory': False,
            'promover_con_pass': True},
 'cache': {'namespace': '{TASK_ID}'},
 'ledger': {'namespace': '{TASK_ID}'},
 'cola': {'pool': 'qwen-token-plan'},
 'dsl': {'tokens': {'task_budget': 10000000, 'max_output_tokens': 1500},
         'cache': {'enabled': True, 'reuse_context': True},
         'parallel': {'enabled': True, 'max_parallel': 4, 'mode': 'partial', 'overflow': 'queue'},
         'priority': 50,
         'retry': {'max_attempts': 3},
         'timeouts': {'queue_seconds': 600, 'api_seconds': 90},
         'on_finish': {'save_usage': True, 'save_cache': True, 'release_slot': True, 'start_next': True}},
 'modelos': {'ficha-dsv4pro': 'texto',
             'ficha-glm52': 'texto',
             'ficha-qwen37max': 'texto',
             'ficha-qwen38max': 'texto'},
 'motor': {'api_recuperacion': 4,
           'tareas_recuperacion': 5,
           'bloque_chars': 8500,
           'limite_llamada_chars': 60000,
           'mensajes_del_director': True},
 'verificacion_instrucciones': {'fuente': 'instrucciones fijas que el Director ancla en el chat; llegan '
                                          'dentro del mensaje entre [INSTRUCCIONES FIJAS] y [FIN '
                                          'INSTRUCCIONES FIJAS]',
                                'revisar': ['antes_de_leer_la_orden',
                                            'despues_de_leer_la_orden',
                                            'antes_de_escribir_la_salida'],
                                'si_no_cumple': {'corregir_y_reintentar': 1,
                                                 'despues': 'entregar con aviso GAP que nombra la '
                                                            'instruccion no cumplida'},
                                'solo_tipo': 'texto',
                                'no_aplica_a_tipos': ['imagen', 'texto-a-voz', 'voz-en-vivo', 'voz-a-texto'],
                                'sin_instrucciones': 'no se ejecuta ni gasta API',
                                'revisor_previo': 'N6',
                                'verificador_final': 'N7'}}
USA_GOALS = True
GOALS_ENTRADA = [{'id': 'G01', 'texto': 'PONER AQUI'},
 {'id': 'G02', 'texto': 'PONER AQUI'},
 {'id': 'G03', 'texto': 'PONER AQUI'},
 {'id': 'G04', 'texto': 'PONER AQUI'},
 {'id': 'G05', 'texto': 'PONER AQUI'},
 {'id': 'G06', 'texto': 'PONER AQUI'},
 {'id': 'G07', 'texto': 'PONER AQUI'},
 {'id': 'G08', 'texto': 'PONER AQUI'},
 {'id': 'G09', 'texto': 'PONER AQUI'},
 {'id': 'G10', 'texto': 'PONER AQUI'},
 {'id': 'G11', 'texto': 'PONER AQUI'},
 {'id': 'G12', 'texto': 'PONER AQUI'}]
GOALS_SALIDA = [{'id': 'S01', 'texto': 'PONER AQUI'},
 {'id': 'S02', 'texto': 'PONER AQUI'},
 {'id': 'S03', 'texto': 'PONER AQUI'},
 {'id': 'S04', 'texto': 'PONER AQUI'},
 {'id': 'S05', 'texto': 'PONER AQUI'},
 {'id': 'S06', 'texto': 'PONER AQUI'},
 {'id': 'S07', 'texto': 'PONER AQUI'},
 {'id': 'S08', 'texto': 'PONER AQUI'},
 {'id': 'S09', 'texto': 'PONER AQUI'},
 {'id': 'S10', 'texto': 'PONER AQUI'},
 {'id': 'S11', 'texto': 'PONER AQUI'},
 {'id': 'S12', 'texto': 'PONER AQUI'}]
USA_ASK_COUNCIL = True
CONSEJO = [('N1', 'ficha-dsv4pro', 'analiza la arquitectura y propone solucion'),
 ('N2', 'ficha-glm52', 'analiza la arquitectura y propone solucion'),
 ('N3', 'ficha-qwen37max', 'analiza la arquitectura y propone solucion')]
EJECUTOR = 'ficha-qwen38max'
SELECTOR = []
EJECUTOR_ROL = 'analiza los goals de N0 y las propuestas de N1, N2 y N3 y EJECUTA directamente la tarea de programacion de code (unico ejecutor). Una vez aprobada la ejecucion, continua hasta completarla: no emite salida intermedia, no pide confirmacion adicional y no aplaza el trabajo'
# ================= MOTOR (identico en las tres fichas) =================
VERIFICACIONES = (("VERIFICACION 1", "ficha-dsv4flash"), ("VERIFICACION 2", "ficha-qwen38flash"))
TIPOS_QUE_APLICAN = ("texto",)  # no aplica a modelos de imagen, voz, audio ni video
MODELOS = dict(FICHA["modelos"])
for _, _m in VERIFICACIONES:
    MODELOS.setdefault(_m, "texto")
PEDIDO = ("Escribe SOLO codigo Python (sin explicaciones) que defina arreglar(texto) -> str. "
          "Debe verificar que la tarea esta bien hecha y que no falta nada del INPUT BLOCK VERBATIM, "
          "refactorizar lo necesario y APLICAR los arreglos devolviendo el texto corregido. "
          "No escales: resuelve. Sin sobreingenieria. Verifica una por una las INSTRUCCIONES FIJAS (si hay) "
          "y corrige lo que no las cumpla.")


def aplica(modelo):
    return MODELOS.get(modelo, "texto") in TIPOS_QUE_APLICAN


def separar(mensaje):
    """Separa la tarea de las instrucciones fijas que el chat envuelve en el mensaje."""
    m = re.search(r"\[INSTRUCCIONES FIJAS[^\]]*\]\n(.*?)\n\[FIN INSTRUCCIONES FIJAS\]", mensaje, re.S)
    instr = m.group(1).strip() if m else ""
    tarea = re.sub(r"\[INSTRUCCIONES FIJAS.*?\[FIN INSTRUCCIONES FIJAS\]\s*", "", mensaje, flags=re.S)
    tarea = re.sub(r"\[ANTES DE RESPONDER:[^\]]*\]\s*$", "", tarea).strip()
    return tarea, instr


def llamar(modelo, prompt, max_tokens=1500):
    if os.environ.get("FICHA_SIMULAR"):
        if "arreglar" in prompt:
            return "```python\ndef arreglar(texto):\n    return texto\n```"
        return "[simulado %s] %s" % (modelo, prompt[-60:].replace("\n", " "))
    url = os.environ.get("RIU_HARNESS_URL")
    if not url:
        raise SystemExit("GAP: falta RIU_HARNESS_URL (puente del chat) o FICHA_SIMULAR=1")
    cab = {"Content-Type": "application/json"}
    if os.environ.get("RIU_CLAVE"):
        cab["X-API-Key"] = os.environ["RIU_CLAVE"]
    cuerpo = json.dumps({"model": modelo, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens}).encode()
    r = json.load(urllib.request.urlopen(urllib.request.Request(url, data=cuerpo, headers=cab), timeout=90))
    return r["choices"][0]["message"]["content"]


def extraer(texto):
    m = re.search(r"```(?:python)?\n(.*?)```", texto, re.S)
    return (m.group(1) if m else texto).strip()


def correr_codigo(codigo, texto, espera=60):
    """Ejecuta el codigo Python de la verificacion (funcion arreglar) y devuelve el texto arreglado."""
    with tempfile.TemporaryDirectory() as d:
        ruta = os.path.join(d, "verif.py")
        pie = "\n\nif __name__ == '__main__':\n    import sys, json\n    print(json.dumps({'texto': arreglar(json.load(sys.stdin)['texto'])}))\n"
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(codigo + pie)
        p = subprocess.run([sys.executable, "-I", ruta], input=json.dumps({"texto": texto}), capture_output=True,
                           text=True, timeout=espera, cwd=d)
    if p.returncode != 0:
        raise RuntimeError(p.stderr[-300:])
    return json.loads(p.stdout.strip().splitlines()[-1])["texto"]


def verificar(titulo, modelo, tarea, instr, resultado):
    prompt = "%s\n\nINPUT BLOCK VERBATIM:\n%s\n\nINSTRUCCIONES FIJAS:\n%s\n\nRESULTADO A VERIFICAR:\n%s" % (
        PEDIDO, tarea, instr or "(ninguna)", resultado)
    try:
        return correr_codigo(extraer(llamar(modelo, prompt)), resultado), "ok"
    except Exception as e:  # no escala: devuelve lo que habia y avisa
        return resultado, "GAP %s: %s" % (titulo, e)


def ejecutar(mensaje, modelo=None):
    tarea, instr = separar(mensaje)
    bitacora = []
    contexto = tarea
    if USA_GOALS:
        contexto += "\n\nGOALS DE ENTRADA:\n" + "\n".join(g["texto"] for g in GOALS_ENTRADA if g["texto"] != "PONER AQUI")
    if USA_ASK_COUNCIL:
        for nid, mod, rol in CONSEJO:
            contexto += "\n\nPROPUESTA %s (%s):\n%s" % (nid, mod, llamar(mod, rol + "\n\n" + tarea))
            bitacora.append("%s %s ok" % (nid, mod))
    if EJECUTOR == "selector":
        ids = [s["id"] for s in SELECTOR]
        ejec = modelo or ids[0]
        if ejec not in ids:
            raise SystemExit("GAP: modelo fuera del selector: %s" % ejec)
    else:
        ejec = EJECUTOR
    if not aplica(ejec):
        raise SystemExit("No aplica a modelos de imagen, voz, audio ni video: %s" % ejec)
    resultado = llamar(ejec, EJECUTOR_ROL + "\n\n" + contexto)
    bitacora.append("EJECUTA %s ok" % ejec)
    tarea_v = tarea
    if USA_GOALS:
        tarea_v += "\n\nGOALS DE SALIDA:\n" + "\n".join(g["texto"] for g in GOALS_SALIDA if g["texto"] != "PONER AQUI")
    for titulo, mod in VERIFICACIONES:
        resultado, estado = verificar(titulo, mod, tarea_v, instr, resultado)
        bitacora.append("%s %s %s" % (titulo, mod, estado))
    return resultado, bitacora


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=FICHA["ficha"])
    ap.add_argument("--mensaje", help="tarea (con o sin instrucciones fijas)")
    ap.add_argument("--archivo", help="archivo con el mensaje")
    ap.add_argument("--modelo", help="modelo ejecutor (solo ficha con selector)")
    a = ap.parse_args()
    msg = a.mensaje if a.mensaje is not None else open(a.archivo, encoding="utf-8").read()
    salida, bit = ejecutar(msg, a.modelo)
    print(salida)
    print("\n".join(bit), file=sys.stderr)
