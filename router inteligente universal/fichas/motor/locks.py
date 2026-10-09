import os
import sqlite3
import time

from .puerta import EsperaAgotada, _vivo


def solapa(a, b):
    a, b = a.rstrip('/') + '/', b.rstrip('/') + '/'
    return a.startswith(b) or b.startswith(a)


class Candados:
    """Registro GLOBAL de rutas en escritura. Solo evita que dos fichas escriban el mismo recurso a la vez.
    No decide el DAG ni administra tareas."""

    def __init__(self, ruta, lease=300, reloj=time.time, dormir=time.sleep):
        self.ruta, self.lease, self.reloj, self.dormir = ruta, lease, reloj, dormir
        os.makedirs(os.path.dirname(os.path.abspath(ruta)), exist_ok=True)
        con = self._c()
        con.executescript('create table if not exists candados(id integer primary key, ficha text, nodo text, ruta text, pid integer, lease real);')
        con.close()

    def _c(self):
        con = sqlite3.connect(self.ruta, timeout=30, isolation_level=None)
        con.execute('pragma journal_mode=wal')
        return con

    def _intentar(self, con, ficha, nodo, rutas):
        con.execute('begin immediate')
        try:
            ahora = self.reloj()
            for i, pid, lease in con.execute('select id,pid,lease from candados').fetchall():
                if lease < ahora or not _vivo(pid):  # watchdog: dueño muerto o lease vencido = se liberan sus rutas
                    con.execute('delete from candados where id=?', (i,))
            ocupadas = [r[0] for r in con.execute('select ruta from candados where ficha<>?', (ficha,)).fetchall()]
            if any(solapa(m, o) for m in rutas for o in ocupadas):
                con.execute('commit')
                return False
            for r in rutas:
                con.execute('insert into candados(ficha,nodo,ruta,pid,lease) values(?,?,?,?,?)', (ficha, nodo, r, os.getpid(), ahora + self.lease))
            con.execute('commit')
            return True
        except Exception:
            con.execute('rollback')
            raise

    def pedir(self, ficha, nodo, rutas, espera_max=600):
        """Pide TODAS las rutas juntas (o ninguna). Espera si otra ficha las tiene."""
        rutas = [r for r in rutas if r]
        if not rutas:
            return
        con = self._c()
        try:
            limite = self.reloj() + espera_max
            while not self._intentar(con, ficha, nodo, rutas):
                if self.reloj() > limite:
                    raise EsperaAgotada('rutas ocupadas por otra ficha: ' + ','.join(rutas))
                self.dormir(0.02)
        finally:
            con.close()

    def latir(self, ficha, nodo):
        con = self._c()
        try:
            con.execute('update candados set lease=? where ficha=? and nodo=?', (self.reloj() + self.lease, ficha, nodo))
        finally:
            con.close()

    def liberar(self, ficha, nodo):
        con = self._c()
        try:
            con.execute('delete from candados where ficha=? and nodo=?', (ficha, nodo))
        finally:
            con.close()
