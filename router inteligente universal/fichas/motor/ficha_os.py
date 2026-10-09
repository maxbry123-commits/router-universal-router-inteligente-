"""1 FICHA = 1 TAREA = 1 MINI-SISTEMA INDEPENDIENTE.
Cada ficha lleva SU scheduler local (este modulo, una instancia por tarea). Lo unico compartido es la Puerta (cola global, 4 puestos).
La memoria no se duplica: la ficha solo guarda referencias (namespace) al almacen del harness."""
import hashlib
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request

from .api_engine import ErrorApi, Motor, Proveedor, tokens_est
from .memoria import Memoria, ProveedorMock, conectar_harness
from .puerta import EsperaAgotada, Puerta


def _solapa(a, b):
    a, b = a.rstrip('/') + '/', b.rstrip('/') + '/'
    return a.startswith(b) or b.startswith(a)


def _choque(n, o):
    if set(n.get('locks') or []) & set(o.get('locks') or []):
        return True
    for w in n.get('write_paths') or []:
        for x in (o.get('write_paths') or []) + (o.get('read_paths') or []):
            if _solapa(w, x):
                return True
    for r in n.get('read_paths') or []:
        for x in o.get('write_paths') or []:
            if _solapa(r, x):
                return True
    return False


class ProveedorDirecto(Proveedor):
    def __init__(self, nombre, url, modelo, clave, carpeta, perfil='libre'):
        super().__init__(nombre, url, modelo, '', perfil, carpeta)
        self._k = clave

    def key(self):
        return self._k


class MotorUso(Motor):
    """Motor con recuperacion + conteo del consumo REAL que devuelve la API."""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.uso = {'in': 0, 'out': 0, 'cached': 0}

    def _post(self, p, mensajes, max_tokens):
        cuerpo = json.dumps({'model': p.modelo, 'messages': mensajes, 'max_tokens': max_tokens}).encode()
        req = urllib.request.Request(p.url, cuerpo, {'Content-Type': 'application/json', 'User-Agent': 'ficha-motor/1.0', 'Authorization': 'Bearer ' + p.key()})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            d = json.loads(r.read())
        txt = (d['choices'][0]['message'].get('content') or '').strip()
        if not txt:
            raise urllib.error.URLError('respuesta vacia')
        u = d.get('usage') or {}
        self.uso['in'] += u.get('prompt_tokens', tokens_est(mensajes))
        self.uso['out'] += u.get('completion_tokens', len(txt) // 4)
        self.uso['cached'] += (u.get('prompt_tokens_details') or {}).get('cached_tokens', 0)
        return txt


class FichaOS:
    def __init__(self, ficha, task_id, texto, motor_factory, puerta, memoria, modelo=None, dormir=time.sleep):
        self.f, self.task, self.texto = ficha, task_id, texto
        self.mf, self.puerta, self.mem, self.dormir = motor_factory, puerta, memoria, dormir
        dsl = ficha.get('dsl', {})
        par = dsl.get('parallel', {})
        self.max_par, self.modo = par.get('max_parallel', 4), par.get('mode', 'partial')
        self.presupuesto = dsl.get('tokens', {}).get('budget', 12000)
        self.cache_cfg = dsl.get('cache', {'enabled': False})
        self.reintentos = dsl.get('retry', {}).get('max_attempts', 3)
        self.t_cola = dsl.get('timeouts', {}).get('queue_seconds', 600)
        self.prio = dsl.get('priority', 50)
        self.saltados = []
        self.nodos = self._expandir(ficha, modelo)
        self.estado = {n['id']: 'pendiente' for n in self.nodos}
        self.salida, self.ledger = {}, {}
        self.cv = threading.Condition()
        self.hilos = []
        self.fin = threading.Event()

    def _expandir(self, ficha, modelo):
        tipos = ficha.get('modelos', {})
        if ficha.get('tipo') == 'individual':
            return [{'id': 'N1', 'modelo': modelo, 'rol': 'responde la tarea', 'depende_de': [], 'read_paths': [], 'write_paths': ['salida/' + self.task + '/']}]
        out = []
        for n in ficha['nodos']:
            if n.get('tipo') != 'goals':
                out.append(dict(n))
                continue
            part = n.get('participan', 'todos')
            nombres = ficha.get('todos_los_modelos', []) if part in ('todos', 'todos_los_modelos') else part
            hijos = []
            for m in nombres:
                if tipos.get(m, 'texto') != 'texto':
                    self.saltados.append({'nodo': n['id'], 'modelo': m, 'motivo': 'tipo ' + tipos[m] + ' no participa en goals de texto'})
                    continue
                h = {'id': n['id'] + ':' + m, 'modelo': m, 'rol': 'participa en los goals de ' + n.get('nombre', n['id']) + ': evalua cada goal en una linea',
                     'depende_de': list(n.get('depende_de', [])), 'goals': n.get('goals', []), 'read_paths': [], 'write_paths': []}
                hijos.append(h['id'])
                out.append(h)
            out.append({'id': n['id'], 'tipo': 'join', 'depende_de': hijos, 'rol': 'une los aportes'})
        return out

    def _mensajes(self, n):
        nl = chr(10)
        sis = 'NODO ' + n['id'] + '. Rol: ' + n['rol'] + '. Responde corto y concreto.'
        usr = 'TAREA: ' + self.texto + nl
        for g in n.get('goals', []):
            usr += 'GOAL ' + str(g.get('id')) + ': ' + str(g.get('texto')) + nl
        for d in n.get('depende_de', []):
            if d in self.salida:
                usr += nl + '[' + d + '] ' + self.salida[d][:3000]
        return [{'role': 'system', 'content': sis}, {'role': 'user', 'content': usr[-14000:]}]

    # ---------- scheduler local ----------
    def _listos(self):
        res = []
        for n in self.nodos:
            if self.estado[n['id']] != 'pendiente':
                continue
            deps = n.get('depende_de', [])
            if any(self.estado[d] == 'gap' for d in deps):
                self.estado[n['id']] = 'gap'
                self.ledger[n['id']] = {'nodo': n['id'], 'estado': 'GAP', 'motivo': 'dependencia fallida'}
            elif all(self.estado[d] == 'ok' for d in deps):
                res.append(n)
        return res

    def _lote(self):
        activos = [n for n in self.nodos if self.estado[n['id']] == 'activo']
        if any(not a.get('parallel_safe', True) for a in activos):
            return []
        cupo, lote = self.max_par - len(activos), []
        for n in self._listos():
            if n.get('tipo') == 'join':
                self.estado[n['id']] = 'ok'
                self.salida[n['id']] = chr(10).join('[' + d + '] ' + self.salida.get(d, '')[:400] for d in n['depende_de'])
                continue
            if cupo <= 0:
                break
            seguro = n.get('parallel_safe', True)
            if not seguro and (activos or lote):
                continue
            if any(_choque(n, o) for o in activos + lote):
                continue
            lote.append(n)
            cupo -= 1
            if not seguro:
                break
        return lote

    def _lanzar(self, lote):
        for n in lote:
            self.estado[n['id']] = 'activo'
        if self.modo == 'group' and len(lote) > 1:
            hs = [threading.Thread(target=self._grupo, args=(lote,), daemon=True)]
        else:
            hs = [threading.Thread(target=self._individual, args=(n,), daemon=True) for n in lote]
        for h in hs:
            h.start()
            self.hilos.append(h)

    def _individual(self, n):  # modo partial: cada nodo pide su propio puesto
        try:
            permiso = self.puerta.pedir(self.task, n['id'], self.prio, 1, self.t_cola)
        except EsperaAgotada as e:
            return self._terminar(n, False, {'estado': 'GAP', 'motivo': 'COLA_AGOTADA ' + str(e)})
        try:
            self._correr(n, permiso)
        finally:
            self.puerta.liberar(permiso)

    def _grupo(self, lote):  # modo group: entran todos juntos o ninguno
        try:
            permiso = self.puerta.pedir(self.task, '+'.join(n['id'] for n in lote), self.prio, len(lote), self.t_cola)
        except EsperaAgotada as e:
            for n in lote:
                self._terminar(n, False, {'estado': 'GAP', 'motivo': 'COLA_AGOTADA ' + str(e)})
            return
        try:
            hs = [threading.Thread(target=self._correr, args=(n, permiso), daemon=True) for n in lote]
            for h in hs:
                h.start()
            for h in hs:
                h.join()
        finally:
            self.puerta.liberar(permiso)

    def _terminar(self, n, ok, reg, salida=''):
        reg['nodo'] = n['id']
        try:
            self.mem.guardar('ledger', n['id'], reg)
        except Exception as e:
            reg['memoria'] = 'ERROR ' + str(e)[:80]
        with self.cv:
            self.ledger[n['id']] = reg
            if ok:
                self.salida[n['id']] = salida
            self.estado[n['id']] = 'ok' if ok else 'gap'
            self.cv.notify_all()

    def _correr(self, n, permiso):
        try:
            self._ejecutar(n, permiso)
        except Exception as e:
            self._terminar(n, False, {'estado': 'GAP', 'motivo': 'ERROR ' + type(e).__name__ + ': ' + str(e)[:120]})

    # ---------- ejecutor + verificador ----------
    def _ejecutar(self, n, permiso):
        t0 = time.time()
        msgs = self._mensajes(n)
        tok = {'budget': self.presupuesto, 'input_used': 0, 'output_used': 0, 'cached_used': 0, 'total_used': 0}
        reg = {'modelo': n['modelo'], 'inicio': t0, 'tokens': tok}
        usa_cache = bool(self.cache_cfg.get('enabled')) and (n.get('cache') or {}).get('enabled', True)
        clave = (n.get('cache') or {}).get('key') or hashlib.sha256((n['modelo'] + json.dumps(msgs)).encode()).hexdigest()[:24]
        hit = self.mem.cargar('cache', clave) if usa_cache else []
        salida, err = None, ''
        if hit:
            salida = hit[-1]['salida']
            reg['cache'] = 'HIT'
            tok['cached_used'] = tokens_est(msgs)
        else:
            motor = self.mf(n['modelo'])
            motor.pulso = lambda: self.puerta.latir(permiso)
            for i in range(self.reintentos):
                try:
                    salida = motor.llamar(msgs, n.get('max_tokens', 1500))
                    break
                except ErrorApi as e:
                    err = str(e)[:150]
                    self.dormir(min(2 ** i, 5))
            tok['input_used'], tok['output_used'], tok['cached_used'] = motor.uso['in'], motor.uso['out'], motor.uso['cached']
        tok['total_used'] = tok['input_used'] + tok['output_used']
        reg['fin'] = time.time()
        if tok['total_used'] > self.presupuesto:
            reg.update(estado='GAP', motivo='PRESUPUESTO ' + str(tok['total_used']) + '>' + str(self.presupuesto))
            return self._terminar(n, False, reg)
        if not salida or len(salida.strip()) < n.get('valida_min_chars', 1):  # verificador: sin salida real no hay PASS
            reg.update(estado='GAP', motivo='SIN_SALIDA ' + err)
            return self._terminar(n, False, reg)
        if usa_cache and not hit:
            self.mem.guardar('cache', clave, {'salida': salida})
        reg['estado'] = 'PASS'
        self._terminar(n, True, reg, salida)

    # ---------- ciclo de vida ----------
    def _perro(self):  # watchdog de la ficha: libera puestos de fichas muertas o con lease vencido
        while not self.fin.wait(5):
            self.puerta.watchdog()

    def correr(self):
        self.puerta.watchdog()
        threading.Thread(target=self._perro, daemon=True).start()
        with self.cv:
            while not all(e in ('ok', 'gap') for e in self.estado.values()):
                antes = tuple(self.estado.values())
                lote = self._lote()
                if lote:
                    self._lanzar(lote)
                    continue
                if tuple(self.estado.values()) != antes:
                    continue
                self.cv.wait(timeout=0.2)
        for h in list(self.hilos):
            h.join()
        self.fin.set()
        return self._cerrar()

    def _cerrar(self):
        ok = all(e == 'ok' for e in self.estado.values())
        final = self.f.get('salida_final') or [n['id'] for n in self.nodos if n.get('tipo') != 'join'][-1]
        suma = {'input_used': 0, 'output_used': 0, 'cached_used': 0, 'total_used': 0}
        for r in self.ledger.values():
            for k in suma:
                suma[k] += (r.get('tokens') or {}).get(k, 0)
        res = {'task': self.task, 'ficha': self.f['ficha'], 'estado': 'PASS' if ok else 'GAP', 'salida': self.salida.get(final, ''),
               'tokens': suma, 'saltados': self.saltados, 'nodos': dict(self.estado)}
        self.mem.guardar('ledger', 'RESUMEN', res)
        if ok:
            self.mem.promover('resultado/' + self.task, {'salida': res['salida']}, True)
        return res


# ---------- carga y validacion de fichas ----------
def leer_texto(ruta):
    if os.path.exists(ruta):
        return open(ruta, encoding='utf-8').read()
    from .sellar import abrir_bytes
    return abrir_bytes(open(ruta + '.sello', 'rb').read()).decode('utf-8')


def cargar_ficha(ruta):
    return json.loads(leer_texto(ruta))


def validar_ficha(f, base):
    errs = []
    for k in ('ficha', 'tipo', 'api', 'memory', 'cache', 'ledger', 'dsl', 'cola_global', 'readme', 'modelos'):
        if k not in f:
            errs.append('falta ' + k)
    if f.get('readme') and not os.path.exists(os.path.join(base, f['readme'])):
        errs.append('README anclado no existe: ' + str(f.get('readme')))
    if f.get('tipo') == 'dag':
        ids = [n['id'] for n in f.get('nodos', [])]
        for n in f.get('nodos', []):
            if n.get('tipo') != 'goals' and n.get('modelo') not in f.get('modelos', {}):
                errs.append('modelo desconocido en ' + n['id'])
            for d in n.get('depende_de', []):
                if d not in ids:
                    errs.append('dependencia inexistente ' + d + ' en ' + n['id'])
    return errs


def proveedores_desde_yml(texto, carpeta):
    import yaml
    out = {}
    for nombre, p in yaml.safe_load(texto)[0]['config']['providers'].items():
        base = (p.get('baseURL') or '').rstrip('/')
        perfil = 'groq_free' if 'groq' in base else ('nvidia' if 'nvidia' in base else 'libre')
        out[nombre] = ProveedorDirecto(nombre, base + '/chat/completions', p['models'][0].get('id', ''), p.get('apiKey') or '', carpeta, perfil)
    return out


def fabrica_motores(provs, timeout=90):
    def mf(modelo):
        p = provs.get(modelo)
        if not p or not p._k or not p.url.startswith('http') or not p.modelo:
            raise ErrorApi('SIN_API: falta apiKey/baseURL/id de ' + modelo + ' en la ficha de modelos')
        return MotorUso([p], timeout=timeout)
    return mf


def main():
    a = sys.argv[1:]
    if len(a) < 5 or a[1] != '--tarea' or a[3] != '--texto':
        print('uso: python -m motor.ficha_os ficha.json --tarea T-001 --texto "..." [--modelo ficha-glm52]')
        return
    ruta, task, texto = a[0], a[2], a[4]
    modelo = a[a.index('--modelo') + 1] if '--modelo' in a else None
    base = os.path.dirname(os.path.abspath(ruta))
    f = cargar_ficha(ruta)
    errs = validar_ficha(f, base)
    if errs:
        sys.exit('ficha invalida: ' + '; '.join(errs))
    estado = os.environ.get('FICHA_ESTADO', os.path.join(base, '..', 'estado'))
    yml = os.environ.get('FICHA_API_YML', os.path.join(base, '..', 'modelos-14', 'harness-modelos-14.cordis.yml'))
    provs = proveedores_desde_yml(leer_texto(yml), estado)
    c = f['cola_global']
    puerta = Puerta(os.path.join(estado, 'puerta.db'), c.get('puestos', 4), c.get('espera_max_s', 600))
    prov_mem = ProveedorMock(estado) if os.environ.get('FICHA_MEMORIA') == 'mock' else conectar_harness()
    m = f['memory']
    mem = Memoria(prov_mem, task, m.get('project_memory', 'YAIWES'), m.get('read_project_memory', True), m.get('write_task_memory', True), m.get('write_project_memory', False))
    res = FichaOS(f, task, texto, fabrica_motores(provs, f['dsl'].get('timeouts', {}).get('api_seconds', 90)), puerta, mem, modelo).correr()
    print(json.dumps({k: res[k] for k in ('task', 'ficha', 'estado', 'tokens', 'nodos')}))


if __name__ == '__main__':
    main()
