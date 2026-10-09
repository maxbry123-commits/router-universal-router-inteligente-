import os
import re
import signal
import sqlite3
import subprocess
import sys
import threading
import time

from .api_engine import ErrorApi, TIMEOUT

MARCA_OK = '[[TAREA_CERRADA]]'
MAX_PROMPT = 17000  # por debajo de los 18000 que reinician la llamada


def vivo(pid):
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


class Cola:
    """Sistema 1: todo el estado vive en SQLite (modo WAL), no en memoria."""

    def __init__(self, ruta):
        self.ruta = ruta
        os.makedirs(os.path.dirname(os.path.abspath(ruta)), exist_ok=True)
        with self.c() as c:
            c.executescript(
                'create table if not exists tareas(id integer primary key, texto text, estado text, resultado text,'
                ' pid integer, latido real, creada real);'
                'create table if not exists pasos(tarea integer, paso integer, salida text, primary key(tarea, paso));'
                'create table if not exists mensajes(id integer primary key, tarea integer, texto text, leido integer default 0, ts real);')

    def c(self):
        con = sqlite3.connect(self.ruta, timeout=30, isolation_level=None)
        con.row_factory = sqlite3.Row
        con.execute('pragma journal_mode=wal')
        return con

    def agregar(self, texto):
        with self.c() as c:
            return c.execute('insert into tareas(texto,estado,creada) values(?,?,?)', (texto, 'pendiente', time.time())).lastrowid

    def mensaje(self, texto, tarea=None):
        with self.c() as c:
            c.execute('insert into mensajes(tarea,texto,ts) values(?,?,?)', (tarea, texto, time.time()))

    def abiertas(self):
        with self.c() as c:
            return c.execute("select count(*) from tareas where estado in ('pendiente','en_curso')").fetchone()[0]

    def estado(self):
        with self.c() as c:
            return [dict(r) for r in c.execute('select id,estado,pid from tareas order by id')]

    def reactivar_huerfanas(self):  # sistema 5: al iniciar, lo que quedo en curso con trabajador muerto vuelve a la cola
        n = 0
        with self.c() as c:
            for r in c.execute("select id,pid from tareas where estado='en_curso'").fetchall():
                if r['pid'] != os.getpid() and not vivo(r['pid']):
                    c.execute("update tareas set estado='pendiente',pid=null where id=?", (r['id'],))
                    n += 1
        return n

    def tomar(self):
        c = self.c()
        try:
            c.execute('begin immediate')
            r = c.execute("select * from tareas where estado='pendiente' order by id limit 1").fetchone()
            if r:
                c.execute("update tareas set estado='en_curso',pid=?,latido=? where id=?", (os.getpid(), time.time(), r['id']))
            c.execute('commit')
            return dict(r) if r else None
        finally:
            c.close()

    def ultimo_paso(self, tid):  # sistema 2: punto de control por paso, se retoma donde quedo
        with self.c() as c:
            return c.execute('select coalesce(max(paso),0) from pasos where tarea=?', (tid,)).fetchone()[0]

    def notas(self, tid):
        with self.c() as c:
            return [(r['paso'], r['salida']) for r in c.execute('select paso,salida from pasos where tarea=? order by paso', (tid,))]

    def mensajes_nuevos(self, tid):
        with self.c() as c:
            return [(r['id'], r['texto']) for r in c.execute('select id,texto from mensajes where leido=0 and (tarea is null or tarea=?) order by id', (tid,))]

    def guardar_paso(self, tid, paso, salida, ids):
        with self.c() as c:
            c.execute('insert or replace into pasos values(?,?,?)', (tid, paso, salida))
            for i in ids:
                c.execute('update mensajes set leido=1 where id=?', (i,))
            c.execute('update tareas set latido=? where id=?', (time.time(), tid))

    def cerrar(self, tid, resultado, estado='cerrada'):
        with self.c() as c:
            c.execute('update tareas set estado=?,resultado=? where id=?', (estado, resultado, tid))


class Trabajador:
    def __init__(self, cola, motor, plantilla, mejoras='', max_pasos=12, latido_max=600, archivo_latido=None, dormir=time.sleep):
        self.cola, self.motor, self.plantilla, self.mejoras = cola, motor, plantilla, mejoras
        self.max_pasos, self.latido_max, self.archivo_latido, self.dormir = max_pasos, latido_max, archivo_latido, dormir
        self.ultimo = time.time()
        motor.pulso = self.pulso

    def pulso(self):
        self.ultimo = time.time()
        if self.archivo_latido:
            try:
                with open(self.archivo_latido, 'w') as f:
                    f.write(str(self.ultimo))
            except OSError:
                pass

    def _perro(self):  # sistema 3: perro guardian interno, si el trabajo se cuelga mata el proceso y el supervisor lo relanza
        while True:
            time.sleep(min(2.0, self.latido_max / 3))
            if time.time() - self.ultimo > self.latido_max:
                os._exit(75)

    def armar(self, t, notas, msgs, paso):
        sis = self.plantilla
        sis = re.sub(r'(<user_query mode="verbatim">).*?(</user_query>)', lambda m: m.group(1) + chr(10) + t['texto'] + chr(10) + m.group(2), sis, count=1, flags=re.S)
        sis = sis + chr(10) + self.mejoras
        usr = 'paso=' + str(paso) + ' tarea=' + str(t['id']) + chr(10)
        if msgs:
            usr += 'MENSAJES_DEL_DIRECTOR (atender sin detener la tarea):' + chr(10) + chr(10).join('- ' + m[1] for m in msgs) + chr(10)
        historial = ''
        for n, s in reversed(notas):
            bloque = 'PASO ' + str(n) + ': ' + s[:1500] + chr(10)
            if len(sis) + len(usr) + len(historial) + len(bloque) > MAX_PROMPT:
                break
            historial = bloque + historial
        usr += historial + 'Continua. Si terminaste TODO escribe ' + MARCA_OK
        return [{'role': 'system', 'content': sis}, {'role': 'user', 'content': usr}]

    def _falla_de_prueba(self, paso):
        cfg = os.environ.get('FICHA_PRUEBA_FALLA', '')
        marca = os.environ.get('FICHA_PRUEBA_MARCA', '')
        if not cfg or not marca or os.path.exists(marca):
            return
        modo, n = cfg.split(':')
        if paso != int(n):
            return
        open(marca, 'w').close()
        if modo == 'salir':
            os._exit(1)
        if modo == 'matar':
            os.kill(os.getpid(), signal.SIGKILL)
        if modo == 'colgar':
            time.sleep(10 ** 6)

    def procesar(self, t):
        paso = self.cola.ultimo_paso(t['id'])
        fallos = 0
        while paso < self.max_pasos:
            paso += 1
            msgs = self.cola.mensajes_nuevos(t['id'])
            ms = self.armar(t, self.cola.notas(t['id']), msgs, paso)
            while True:
                try:
                    self.pulso()
                    salida = self.motor.llamar(ms, 1500)
                    break
                except ErrorApi:
                    fallos += 1
                    self.motor.dormir(min(600, 10 * 2 ** min(fallos, 6)))  # el loop no se detiene: espera y reintenta
            self.cola.guardar_paso(t['id'], paso, salida, [m[0] for m in msgs])
            self.pulso()
            self._falla_de_prueba(paso)
            if MARCA_OK in salida:  # solo una salida terminada cierra la tarea
                self.cola.cerrar(t['id'], salida)
                return
        self.cola.cerrar(t['id'], 'GAP: sin cierre tras ' + str(self.max_pasos) + ' pasos', 'bloqueada')

    def correr(self, una_pasada=False):
        n = self.cola.reactivar_huerfanas()
        self.pulso()
        try:
            with open(os.path.join(os.path.dirname(os.path.abspath(self.cola.ruta)), 'inicios.log'), 'a') as f:
                f.write(str(os.getpid()) + ' reactivadas=' + str(n) + chr(10))
        except OSError:
            pass
        threading.Thread(target=self._perro, daemon=True).start()
        while True:
            self.cola.reactivar_huerfanas()  # sistema 5 tambien en cada inicio de tarea
            t = self.cola.tomar()
            if not t:
                if una_pasada:
                    return
                self.dormir(2)
                self.pulso()
                continue
            self.procesar(t)


def supervisar(cmd, cola, archivo_latido, latido_max=600, cada=1.0, salir_vacio=True, env=None):
    """Sistema 4: proceso aparte que vigila al trabajador y lo relanza si muere o deja de latir."""
    proc, reinicios = None, -1
    while True:
        if proc is None or proc.poll() is not None:
            if salir_vacio and cola.abiertas() == 0:
                return reinicios
            with open(archivo_latido, 'w') as f:
                f.write(str(time.time()))
            proc = subprocess.Popen(cmd, env=env)
            reinicios += 1
        else:
            try:
                viejo = time.time() - float(open(archivo_latido).read())
            except Exception:
                viejo = 0
            if viejo > latido_max:
                proc.send_signal(signal.SIGKILL)
                proc.wait()
        time.sleep(cada)
