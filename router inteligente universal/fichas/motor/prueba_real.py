"""Prueba REAL (gasta cupo): NVIDIA glm-5.3 y Groq qwen3.8-27b con la ficha y los 4 motores de recuperacion de tareas. Se lanza en el job de HF.
Claves por entorno: NVIDIA_API_KEY, GROQ_API_KEY."""
import json
import os
import signal
import subprocess
import sys
import tempfile
import time

from .api_engine import TIMEOUT, ErrorApi, Motor, Proveedor
from .tareas import Cola, MARCA_OK

RES = []
NV = 'https://integrate.api.nvidia.com/v1/chat/completions'
GQ = 'https://api.groq.com/openai/v1/chat/completions'
PROV = [
    {'nombre': 'malo', 'url': NV, 'modelo': 'z-ai/glm-5.3', 'key_env': 'CLAVE_MALA', 'perfil': 'nvidia'},
    {'nombre': 'nvidia-glm53', 'url': NV, 'modelo': 'z-ai/glm-5.3', 'key_env': 'NVIDIA_API_KEY', 'perfil': 'nvidia'},
    {'nombre': 'groq-qwen38', 'url': GQ, 'modelo': 'qwen/qwen3.8-27b', 'key_env': 'GROQ_API_KEY', 'perfil': 'groq_free'},
    {'nombre': 'groq-qwen38-b', 'url': GQ, 'modelo': 'qwen/qwen3.8-27b', 'key_env': 'GROQ_API_KEY_B', 'perfil': 'groq_free'},
    {'nombre': 'groq-qwen38-c', 'url': GQ, 'modelo': 'qwen/qwen3.8-27b', 'key_env': 'GROQ_API_KEY_C', 'perfil': 'groq_free'},
]


def chequeo(nombre, ok, detalle=''):
    RES.append(ok)
    print(('PASS ' if ok else 'FAIL ') + nombre + (' | ' + str(detalle)[:160] if detalle else ''), flush=True)


def prov(tmp, *nombres):
    return [Proveedor(d['nombre'], d['url'], d['modelo'], d['key_env'], d['perfil'], tmp) for d in PROV if d['nombre'] in nombres]


def api(tmp):
    msg = [{'role': 'user', 'content': 'Responde solo con la palabra OK.'}]
    chequeo('timeout de llamada real', TIMEOUT == 90, TIMEOUT)
    for n in ('nvidia-glm53', 'groq-qwen38'):
        try:
            t0 = time.time()
            r = Motor(prov(tmp, n)).llamar(msg, 200)
            chequeo('API real ' + n + ' responde', bool(r), str(round(time.time() - t0, 1)) + ' s')
        except ErrorApi as e:
            chequeo('API real ' + n + ' responde', False, e)
    m = Motor(prov(tmp, 'malo', 'nvidia-glm53', 'groq-qwen38', 'groq-qwen38-b', 'groq-qwen38-c'))
    try:
        r = m.llamar(msg, 200)
        chequeo('cambio de API: la mala falla y pasa a la buena', bool(r) and m.i >= 1, m.bitacora[:2])
    except ErrorApi as e:
        chequeo('cambio de API', False, e)
    m = Motor(prov(tmp, 'groq-qwen38'))
    largo = [{'role': 'user', 'content': 'Lee y al final responde solo OK. ' + 'dato ' * 3800}]
    try:
        r = m.llamar(largo, 1500)
        chequeo('bloques de 8500 con llamada real de 19000 caracteres', bool(r), len(largo[0]['content']))
    except ErrorApi as e:
        chequeo('bloques de 8500', False, e)


def recuperacion(tmp, modo):
    carpeta = os.path.join(tmp, modo)
    os.makedirs(carpeta)
    prov_json = os.path.join(carpeta, 'prov.json')
    json.dump([d for d in reversed(PROV) if d['nombre'] != 'malo'], open(prov_json, 'w'))
    c = Cola(os.path.join(carpeta, 'cola.db'))
    tid = c.agregar('Responde con una linea corta que diga listo y escribe la marca de cierre ' + MARCA_OK)
    e = dict(os.environ, FICHA_CARPETA=carpeta, FICHA_PROVEEDORES=prov_json, FICHA_LATIDO_MAX='40', PYTHONPATH=os.getcwd())
    if modo in ('salir', 'colgar'):
        e.update(FICHA_PRUEBA_FALLA=modo + ':1', FICHA_PRUEBA_MARCA=os.path.join(carpeta, 'marca'))
    t0 = time.time()
    if modo == 'huerfana':
        with c.c() as cx:
            cx.execute("update tareas set estado='en_curso',pid=999999 where id=?", (tid,))
        try:
            subprocess.run([sys.executable, '-m', 'motor', 'correr', '--una'], env=e, timeout=150)
        except subprocess.TimeoutExpired:
            pass
    else:
        p = subprocess.Popen([sys.executable, '-m', 'motor', 'supervisar', '--una'], env=e)
        if modo == 'matar':
            for _ in range(600):
                time.sleep(0.1)
                est = c.estado()[0]
                if est['pid'] and c.ultimo_paso(tid) >= 1:
                    os.kill(est['pid'], signal.SIGKILL)
                    break
        try:
            p.wait(timeout=150)
        except subprocess.TimeoutExpired:
            p.kill()
            subprocess.run(["pkill", "-f", "motor correr"])
    est = c.estado()[0]['estado']
    with c.c() as cx:
        pasos = [r[0] for r in cx.execute('select paso from pasos order by paso')]
    log = open(os.path.join(carpeta, 'inicios.log')).read().splitlines()
    ok = est == 'cerrada' and pasos == list(range(1, len(pasos) + 1)) and len(pasos) >= 2 and (len(log) >= 2 if modo != 'huerfana' else 'reactivadas=1' in log[0])
    chequeo('REAL reinicio ' + modo + ': el motor se activo y la tarea cerro', ok, (est, pasos, 'arranques=' + str(len(log)), round(time.time() - t0, 1)))


if __name__ == '__main__':
    tmp = tempfile.mkdtemp()
    api(tmp)
    for modo in ('salir', 'matar', 'colgar', 'huerfana'):
        recuperacion(tmp, modo)
    print('RESULTADO_REAL', sum(RES), '/', len(RES), flush=True)
    sys.exit(0 if all(RES) else 1)
