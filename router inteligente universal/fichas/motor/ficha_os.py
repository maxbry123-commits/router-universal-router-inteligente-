"""1 FICHA = 1 TAREA = 1 MINI-SISTEMA INDEPENDIENTE.
Cada ficha lleva SU scheduler local (una instancia por tarea). Lo unico compartido: la Puerta (cola global, 4 puestos),
el registro de candados de rutas y el almacen fisico del harness. La memoria no se duplica: la ficha solo guarda su namespace."""
import hashlib
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request

from .api_engine import ErrorApi, Motor, Proveedor, tokens_est
from .locks import Candados, solapa
from .memoria import Memoria, ProveedorMock, conectar_harness
from .puerta import EsperaAgotada, Puerta


def _choque(n, o):
    if set(n.get('locks') or []) & set(o.get('locks') or []):
        return True
    for w in n.get('write_paths') or []:
        for x in (o.get('write_paths') or []) + (o.get('read_paths') or []):
            if solapa(w, x):
                return True
    for r in n.get('read_paths') or []:
        for x in o.get('write_paths') or []:
            if solapa(r, x):
                return True
    return False


def es_datos(n):
    return n.get('tipo') == 'goals' or n.get('ejecutar_api') is False


def evidencia_ok(ev):
    """PASS de codigo = evidencia real del Harness. Una respuesta de modelo, por si sola, NO es evidencia."""
    t = (ev or {}).get('tests') or {}
    return isinstance(ev, dict) and ev.get('exit_code') == 0 and bool(ev.get('receipt')) and isinstance(ev.get('files_changed'), list) and t.get('ran') is True and t.get('passed') is True


class HarnessEjecutor:
    """Adaptador al DeepSeek Harness EXISTENTE (mismo contrato que plugins/deepseek_harness del Router: POST RIU_DEEPSEEK_HARNESS_URL + /invoke).
    Sin URL configurada devuelve None y la ficha queda en GAP_HARNESS_EXECUTOR (no se finge ejecucion)."""

    def __call__(self, nodo, salida_modelo, ctx):
        base = (os.getenv('RIU_DEEPSEEK_HARNESS_URL') or '').strip().rstrip('/')
        if not base:
            return None
        headers = {'Content-Type': 'application/json'}
        if os.getenv('RIU_DEEPSEEK_HARNESS_API_KEY'):
            headers['Authorization'] = 'Bearer ' + os.environ['RIU_DEEPSEEK_HARNESS_API_KEY']
        cuerpo = {'action': 'invoke', 'task_id': ctx['task'], 'nodo': nodo['id'], 'modelo': nodo['modelo'], 'plan': salida_modelo, 'write_paths': ctx.get('paths')}
        req = urllib.request.Request(base + (os.getenv('RIU_DEEPSEEK_HARNESS_PATH') or '/invoke'), json.dumps(cuerpo).encode(), headers, method='POST')
        try:
            with urllib.request.urlopen(req, timeout=900) as r:
                d = json.loads(r.read())
            return d.get('evidence', d) if isinstance(d, dict) else None
        except Exception:
            return None


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
    def __init__(self, ficha, task_id, texto, motor_factory, puerta, memoria, modelo=None, dormir=time.sleep, candados=None, harness=None):
        self.f, self.task, self.texto = ficha, task_id, texto
        self.mf, self.puerta, self.mem, self.dormir = motor_factory, puerta, memoria, dormir
        self.candados, self.harness = candados, harness
        dsl = ficha.get('dsl', {})
        par = dsl.get('parallel', {})
        self.max_par = par.get('max_parallel', 4) if par.get('enabled', True) else 1
        self.modo = par.get('mode', 'partial')
        tok = dsl.get('tokens', {})
        self.task_budget = tok.get('task_budget', 12000)  # presupuesto de la FICHA completa
        self.max_out = tok.get('max_output_tokens', 1500)  # tope por nodo/llamada
        self.consumido, self.reservado, self.tlock = 0, 0, threading.Lock()
        self.cache_cfg = dsl.get('cache', {'enabled': False})
        self.reintentos = dsl.get('retry', {}).get('max_attempts', 3)
        self.t_cola = dsl.get('timeouts', {}).get('queue_seconds', 600)
        self.prio = dsl.get('priority', 50)
        self.nodos = self._expandir(ficha, modelo)
        self.estado = {n['id']: 'pendiente' for n in self.nodos}
        self.salida, self.ledger = {}, {}
        self.cv = threading.Condition()
        self.hilos = []
        self.fin = threading.Event()

    def _expandir(self, ficha, modelo):
        if ficha.get('tipo') == 'individual':  # ficha 1: UN modelo elegido con el selector, una sola llamada
            return [{'id': 'N1', 'modelo': modelo, 'rol': 'responde la tarea', 'depende_de': [], 'read_paths': [], 'write_paths': ['salida/' + self.task + '/']}]
        return [dict(n) for n in ficha['nodos']]

    def _texto_datos(self, n):
        nl = chr(10)
        return 'CRITERIOS ' + n.get('nombre', n['id']) + ':' + nl + nl.join(str(g.get('id')) + ': ' + str(g.get('texto')) for g in n.get('goals', []))

    def _mensajes(self, n):
        nl = chr(10)
        sis = 'NODO ' + n['id'] + '. Rol: ' + n['rol'] + '. Responde corto y concreto.'
        usr = 'TAREA: ' + self.texto + nl
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
            if es_datos(n):  # goals = datos deterministas: 0 API, 0 tokens, 0 puesto de cola
                self.estado[n['id']] = 'ok'
                self.salida[n['id']] = self._texto_datos(n)
                self.ledger[n['id']] = {'nodo': n['id'], 'estado': 'PASS', 'api': 0}
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

    def _rutas(self, n):
        return list(n.get('write_paths') or []) + list(n.get('locks') or [])

    def _individual(self, n):  # modo partial: cada nodo pide sus rutas (candados) y su propio puesto
        lk = n['id']
        try:
            if self.candados:
                self.candados.pedir(self.task, lk, self._rutas(n), self.t_cola)
            try:
                permiso = self.puerta.pedir(self.task, n['id'], self.prio, 1, self.t_cola)
            except EsperaAgotada as e:
                return self._terminar(n, False, {'estado': 'GAP', 'motivo': 'COLA_AGOTADA ' + str(e)})
            try:
                self._correr(n, permiso, lk)
            finally:
                self.puerta.liberar(permiso)
        except EsperaAgotada as e:
            self._terminar(n, False, {'estado': 'GAP', 'motivo': 'LOCK_AGOTADO ' + str(e)})
        finally:
            if self.candados:
                self.candados.liberar(self.task, lk)

    def _grupo(self, lote):  # modo group: entran todos juntos o ninguno
        lk = '+'.join(n['id'] for n in lote)
        try:
            if self.candados:
                self.candados.pedir(self.task, lk, [r for n in lote for r in self._rutas(n)], self.t_cola)
            permiso = self.puerta.pedir(self.task, lk, self.prio, len(lote), self.t_cola)
            try:
                hs = [threading.Thread(target=self._correr, args=(n, permiso, lk), daemon=True) for n in lote]
                for h in hs:
                    h.start()
                for h in hs:
                    h.join()
            finally:
                self.puerta.liberar(permiso)
        except EsperaAgotada as e:
            for n in lote:
                self._terminar(n, False, {'estado': 'GAP', 'motivo': 'COLA_AGOTADA ' + str(e)})
        finally:
            if self.candados:
                self.candados.liberar(self.task, lk)

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

    def _correr(self, n, permiso, lock_nodo):
        try:
            self._ejecutar(n, permiso, lock_nodo)
        except Exception as e:
            self._terminar(n, False, {'estado': 'GAP', 'motivo': 'ERROR ' + type(e).__name__ + ': ' + str(e)[:120]})

    # ---------- ejecutor + verificador ----------
    def _ejecutar(self, n, permiso, lock_nodo):
        t0 = time.time()
        msgs = self._mensajes(n)
        tok = {'input_tokens': 0, 'output_tokens': 0, 'api_cached_input_tokens': 0, 'total_api_tokens': 0, 'local_cache_hit': False, 'estimated_tokens_avoided': 0}
        reg = {'modelo': n['modelo'], 'inicio': t0, 'tokens': tok}
        if self.f.get('modelos', {}).get(n['modelo'], 'texto') != 'texto':
            reg.update(estado='GAP', motivo='GAP_ENDPOINT_NO_CHAT: ' + n['modelo'] + ' no se llama por chat/completions')
            return self._terminar(n, False, reg)
        necesita_ev = bool(n.get('requiere_evidencia'))
        usa_cache = bool(self.cache_cfg.get('enabled')) and (n.get('cache') or {}).get('enabled', True) and not necesita_ev
        clave = (n.get('cache') or {}).get('key') or hashlib.sha256((n['modelo'] + json.dumps(msgs)).encode()).hexdigest()[:24]
        hit = self.mem.cargar('cache', clave) if usa_cache else []
        salida, err = None, ''
        if hit:
            salida = hit[-1]['salida']
            tok['local_cache_hit'] = True  # cache LOCAL: no cuenta como cached_tokens de la API
            tok['estimated_tokens_avoided'] = tokens_est(msgs)
        else:
            max_out = n.get('max_output_tokens', self.max_out)
            reserva = tokens_est(msgs) + max_out
            with self.tlock:
                sobra = self.consumido + self.reservado + reserva > self.task_budget
                if not sobra:
                    self.reservado += reserva
            if sobra:
                reg.update(estado='GAP', motivo='GAP_BUDGET: ' + str(self.consumido) + ' usados + ' + str(reserva) + ' > ' + str(self.task_budget) + ' de la ficha')
                return self._terminar(n, False, reg)
            motor = self.mf(n['modelo'])
            motor.pulso = lambda: (self.puerta.latir(permiso), self.candados.latir(self.task, lock_nodo) if self.candados else None)
            try:
                for i in range(self.reintentos):
                    try:
                        salida = motor.llamar(msgs, max_out)
                        break
                    except ErrorApi as e:
                        err = str(e)[:150]
                        self.dormir(min(2 ** i, 5))
            finally:
                with self.tlock:
                    self.reservado -= reserva
                    self.consumido += motor.uso['in'] + motor.uso['out']
            tok['input_tokens'], tok['output_tokens'], tok['api_cached_input_tokens'] = motor.uso['in'], motor.uso['out'], motor.uso['cached']
        tok['total_api_tokens'] = tok['input_tokens'] + tok['output_tokens']
        reg['fin'] = time.time()
        if not salida or len(salida.strip()) < n.get('valida_min_chars', 1):
            reg.update(estado='GAP', motivo='SIN_SALIDA ' + err)
            return self._terminar(n, False, reg)
        if necesita_ev:  # RESPUESTA DE MODELO != PASS. PASS = evidencia real del Harness (ejecucion, archivos, tests, receipt)
            ev = self.harness(n, salida, {'task': self.task, 'paths': n.get('write_paths')}) if self.harness else None
            reg['evidencia'] = ev
            if ev is None:
                reg.update(estado='GAP', motivo='GAP_HARNESS_EXECUTOR: sin Harness/tools reales no se declara ejecucion de codigo')
                return self._terminar(n, False, reg)
            if not evidencia_ok(ev):
                reg.update(estado='GAP', motivo='EVIDENCIA_INCOMPLETA: se exige exit_code 0, files_changed, tests ejecutados y pasados, receipt')
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
        final = self.f.get('salida_final') or [n['id'] for n in self.nodos if not es_datos(n)][-1]
        suma = {'input_tokens': 0, 'output_tokens': 0, 'api_cached_input_tokens': 0, 'total_api_tokens': 0, 'local_cache_hits': 0, 'estimated_tokens_avoided': 0}
        for r in self.ledger.values():
            t = r.get('tokens') or {}
            for k in ('input_tokens', 'output_tokens', 'api_cached_input_tokens', 'total_api_tokens', 'estimated_tokens_avoided'):
                suma[k] += t.get(k, 0)
            suma['local_cache_hits'] += 1 if t.get('local_cache_hit') else 0
        motivos = {k: v.get('motivo') for k, v in self.ledger.items() if v.get('estado') == 'GAP'}
        res = {'task': self.task, 'ficha': self.f['ficha'], 'estado': 'PASS' if ok else 'GAP', 'salida': self.salida.get(final, ''),
               'tokens': suma, 'task_budget': self.task_budget, 'nodos': dict(self.estado), 'gaps': motivos}
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


def validar_ficha(f, base, config_puerta=None):
    errs = []
    for k in ('ficha', 'tipo', 'api', 'memory', 'cache', 'ledger', 'dsl', 'cola', 'readme', 'modelos'):
        if k not in f:
            errs.append('falta ' + k)
    for k in ('cola_global', 'todos_los_modelos'):
        if k in f:
            errs.append('campo prohibido (fuente unica del pool / sin Council de 14): ' + k)
    if f.get('readme') and not os.path.exists(os.path.join(base, f['readme'])):
        errs.append('README anclado no existe: ' + str(f.get('readme')))
    if config_puerta and f.get('cola', {}).get('pool') != config_puerta.get('pool'):
        errs.append('la ficha no apunta al pool de la API: ' + str(f.get('cola')))
    if f.get('tipo') == 'dag':
        ids = [n['id'] for n in f.get('nodos', [])]
        for n in f.get('nodos', []):
            if 'participan' in n:
                errs.append('goals no pueden "participar" con modelos: ' + n['id'])
            if n.get('tipo') == 'goals' and n.get('ejecutar_api') is not False:
                errs.append('goals debe llevar ejecutar_api:false en ' + n['id'])
            if not es_datos(n) and n.get('modelo') not in f.get('modelos', {}):
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
        out[nombre] = ProveedorDirecto(nombre, base + '/chat/completions', p['models'][0].get('id', ''), p.get('apiKey') or '', carpeta, 'libre')
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
    aqui = os.path.dirname(os.path.abspath(__file__))
    cfg = json.load(open(os.path.join(aqui, 'puerta.config.json')))
    f = cargar_ficha(ruta)
    errs = validar_ficha(f, base, cfg)
    if errs:
        sys.exit('ficha invalida: ' + '; '.join(errs))
    estado = os.environ.get('FICHA_ESTADO', os.path.join(base, '..', 'estado'))
    yml = os.environ.get('FICHA_API_YML', os.path.join(base, '..', 'modelos-14', 'harness-modelos-14.cordis.yml'))
    provs = proveedores_desde_yml(leer_texto(yml), estado)
    puerta = Puerta.desde_config(os.path.join(estado, 'puerta.db'), os.path.join(aqui, 'puerta.config.json'))
    candados = Candados(os.path.join(estado, 'candados.db'))
    prov_mem = ProveedorMock(estado) if os.environ.get('FICHA_MEMORIA') == 'mock' else conectar_harness()
    m = f['memory']
    mem = Memoria(prov_mem, task, m.get('project_memory', 'YAIWES'), m.get('read_project_memory', True), m.get('write_task_memory', True), m.get('write_project_memory', False))
    res = FichaOS(f, task, texto, fabrica_motores(provs, f['dsl'].get('timeouts', {}).get('api_seconds', 90)), puerta, mem, modelo, candados=candados, harness=HarnessEjecutor()).correr()
    print(json.dumps({k: res[k] for k in ('task', 'ficha', 'estado', 'tokens', 'nodos', 'gaps')}))


if __name__ == '__main__':
    main()
