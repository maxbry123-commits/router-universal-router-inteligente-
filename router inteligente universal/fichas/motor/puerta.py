import os
import sqlite3
import time


class EsperaAgotada(Exception):
    pass


def _vivo(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


class Puerta:
    """Lo UNICO compartido entre fichas: cola global + puestos de la API.
    No decide como se ejecuta ninguna tarea: solo presta puestos (maximo `puestos` activos a la vez)."""

    def __init__(self, ruta, puestos=4, espera_max=600, lease=300, reloj=time.time, dormir=time.sleep):
        self.ruta, self.puestos, self.espera_max, self.lease = ruta, puestos, espera_max, lease
        self.reloj, self.dormir = reloj, dormir
        os.makedirs(os.path.dirname(os.path.abspath(ruta)), exist_ok=True)
        con = self._c()
        con.executescript('create table if not exists cola(id integer primary key, ficha text, nodo text, prio integer, n integer,'
                          ' estado text, pid integer, lease real, ts real);')
        con.close()

    def _c(self):
        con = sqlite3.connect(self.ruta, timeout=30, isolation_level=None)
        con.execute('pragma journal_mode=wal')
        return con

    def _limpiar(self, con):  # watchdog: lease vencido o dueño muerto = se libera el puesto / se saca de la cola
        ahora = self.reloj()
        n = 0
        for i, estado, pid, lease in con.execute('select id,estado,pid,lease from cola').fetchall():
            if (estado == 'activo' and lease < ahora) or not _vivo(pid):
                con.execute('delete from cola where id=?', (i,))
                n += 1
        return n

    def watchdog(self):
        con = self._c()
        try:
            con.execute('begin immediate')
            n = self._limpiar(con)
            con.execute('commit')
            return n
        finally:
            con.close()

    def _intentar(self, con, mi_id):
        con.execute('begin immediate')
        try:
            self._limpiar(con)
            usados = con.execute("select coalesce(sum(n),0) from cola where estado='activo'").fetchone()[0]
            cab = con.execute("select id,n from cola where estado='espera' order by prio desc, id asc limit 1").fetchone()
            ok = bool(cab) and cab[0] == mi_id and usados + cab[1] <= self.puestos
            if ok:
                con.execute("update cola set estado='activo', lease=? where id=?", (self.reloj() + self.lease, mi_id))
            con.execute('commit')
            return ok
        except Exception:
            con.execute('rollback')
            raise

    def pedir(self, ficha, nodo, prio=50, n=1, espera_max=None):
        """Pide n puestos. Espera en cola (por prioridad y orden de llegada) hasta espera_max s; si no, EsperaAgotada."""
        con = self._c()
        try:
            mi_id = con.execute("insert into cola(ficha,nodo,prio,n,estado,pid,lease,ts) values(?,?,?,?,'espera',?,0,?)",
                                (ficha, nodo, prio, n, os.getpid(), self.reloj())).lastrowid
            limite = self.reloj() + (self.espera_max if espera_max is None else espera_max)
            while True:
                if self._intentar(con, mi_id):
                    return mi_id
                if self.reloj() > limite:
                    con.execute('delete from cola where id=?', (mi_id,))
                    raise EsperaAgotada('sin puesto tras ' + str(espera_max if espera_max is not None else self.espera_max) + ' s: ' + ficha + '/' + nodo)
                self.dormir(0.02)
        finally:
            con.close()

    def latir(self, permiso):
        con = self._c()
        try:
            con.execute('update cola set lease=? where id=?', (self.reloj() + self.lease, permiso))
        finally:
            con.close()

    def liberar(self, permiso):
        con = self._c()
        try:
            con.execute('delete from cola where id=?', (permiso,))
        finally:
            con.close()

    def estado(self):
        con = self._c()
        try:
            a = con.execute("select coalesce(sum(n),0) from cola where estado='activo'").fetchone()[0]
            e = con.execute("select count(*) from cola where estado='espera'").fetchone()[0]
            return {'activos': a, 'en_cola': e, 'puestos': self.puestos}
        finally:
            con.close()

    @classmethod
    def desde_config(cls, ruta_db, ruta_config):
        """UNICA fuente de verdad de la capacidad de la API (puestos y espera maxima). Las fichas solo apuntan al pool."""
        import json
        c = json.load(open(ruta_config))
        p = cls(ruta_db, c['puestos'], c['espera_max_s'])
        p.pool = c['pool']
        return p
