#!/usr/bin/env python3
"""ADAPTACION YAIWES del patron R. Bertran (blender-json-scene-pipeline): JSON -> catalogo OPS -> recibos.

No es codigo de Ricardo. Reutiliza SIN TOCAR la clase Motor de motor_cli.py (referencia verbatim del Bloque 3)
y le anade solo lo que el contrato de los Bloques 2/4 exige y el motor aislado no tiene:
  - entrada como lista desnuda u objeto {meta, ops}   (igual que blender_cli.py original)
  - JSON estricto: Markdown alrededor = rechazo        (Bloque 1 [P08] / Bloque 4 seccion 08)
  - recibo por operacion con id + sha256 calculado por el ejecutor (Bloque 2 seccion 07)
  - checkpoint por plan (plan_sha256) + idempotencia: no repetir mutaciones ya verificadas (Bloque 4 seccion 04)
  - registro de recibos para que el Harness compruebe los receipt_ids que nombra el modelo (Bloque 2 seccion 06)
  - informe final con prefijo YAIWES_OP_REPORT; finish cierra el LOTE, nunca el objetivo global
Sin exec/eval/shell. Sin red. Solo biblioteca estandar.
"""
import hashlib
import json
import os
import re
import sys
import tempfile
import threading
from pathlib import Path

_DIR = Path(__file__).resolve().parent
if str(_DIR) not in sys.path:
    sys.path.insert(0, str(_DIR))
from motor_cli import Motor, MotorError  # noqa: E402  (referencia verbatim, no se edita)

POLITICA_DEFECTO = next((c for c in (_DIR.parent / 'fichas' / 'allowed_ops.json', _DIR / 'allowed_ops.json') if c.is_file()), _DIR / 'allowed_ops.json')  # >>> PARCHE_E2E <<< politica FUERA del control del modelo (el archivo real vive en motor_json/)
_MUTAN = ('create_directory', 'write_text')
_LOCK = threading.Lock()
_RECIBOS = {}  # receipt_id -> recibo (memoria del proceso; el disco guarda el resto en .receipts/)
_CAMPOS = {  # >>> PREFLIGHT_RB <<< esquema cerrado por operacion (GAP 02): campos obligatorios; cualquier otro campo = rechazo
    'inspect_workspace': (), 'create_directory': ('path',), 'write_text': ('path', 'text'), 'read_text': ('path',),
    'verify_exists': ('path',), 'verify_contains': ('path', 'text'), 'finish': (),
}
_BASE = ('id', 'op', 'depends_on')


def _canon(v):
    return json.dumps(v, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def _sha(texto):
    return hashlib.sha256(texto.encode('utf-8')).hexdigest()


def base_workspaces():
    return Path(os.environ.get('RIU_MOTOR_WS') or os.path.join(tempfile.gettempdir(), 'riu_motor_ws')).resolve()


def parse_estricto(entrada):
    """JSON PARSE -> ACCEPT/REJECT. Nunca se envia Markdown al ejecutor (Bloque 1 [P08])."""
    if isinstance(entrada, (dict, list)):
        return entrada
    if not isinstance(entrada, str):
        raise MotorError('GAP_JSON_TIPO: se esperaba objeto JSON')
    t = entrada.strip()
    if t.startswith('```') or t.endswith('```'):
        raise MotorError('GAP_JSON_EN_MARKDOWN: devuelve JSON puro, sin bloque Markdown')
    try:
        doc = json.loads(t)
    except ValueError as x:
        raise MotorError('GAP_JSON_INVALIDO_O_TRUNCADO: ' + str(x)[:160])
    if not isinstance(doc, (dict, list)):
        raise MotorError('GAP_JSON_RAIZ: debe ser objeto {meta, ops} o lista de ops')
    return doc


def cargar_politica(ruta=None):
    p = json.loads(Path(ruta or POLITICA_DEFECTO).read_text(encoding='utf-8'))
    if not isinstance(p.get('allowed_ops'), list):
        raise MotorError('GAP_POLITICA: falta allowed_ops')
    bloqueadas = {'exec', 'eval', 'shell', 'python_code'} & set(p['allowed_ops'])
    if bloqueadas:  # Bloque 2 seccion 03: nunca abiertas al modelo, ni aunque alguien edite la politica
        raise MotorError('GAP_POLITICA_INSEGURA: ' + ', '.join(sorted(bloqueadas)))
    return p


class MotorYaiwes(Motor):
    """Motor (verbatim) + recibos reales + checkpoint idempotente. El orden DAG lo valida Motor.order."""

    def __init__(self, root, policy, job='plan'):
        super().__init__(root, policy)
        self.job = re.sub(r'[^A-Za-z0-9_-]', '-', str(job or 'plan'))[:48] or 'plan'

    def order(self, operations):  # >>> PREFLIGHT_RB <<< preflight completo ANTES de ejecutar nada (GAP 02/03/04)
        ordered = super().order(operations)  # DAG verbatim: ids, ops autorizadas, dependencias, ciclos
        for item in ordered:
            req = _CAMPOS.get(item['op'])
            if req is None:
                raise MotorError('GAP_OP_SIN_ESQUEMA: ' + str(item['op']))
            extra = sorted(set(item) - set(_BASE) - set(req))
            if extra:
                raise MotorError('GAP_CAMPO_DESCONOCIDO %s: %s' % (item['id'], ', '.join(extra)))
            for k in req:
                if not isinstance(item.get(k), str):
                    raise MotorError('GAP_CAMPO_TIPO %s.%s: se esperaba texto' % (item['id'], k))
            if 'path' in req:
                _p = self.path(item['path'])  # ruta vacia/absoluta/fuera del workspace: rechazo antes de mutar
                if _p == self.root / '.receipts' or (self.root / '.receipts') in _p.parents:  # >>> PARCHE_T1 <<< el modelo no escribe donde viven los recibos
                    raise MotorError('GAP_RUTA_RESERVADA %s: .receipts es del ejecutor' % item['id'])
            if item['op'] == 'write_text' and len(item['text']) > self.max_chars:
                raise MotorError('GAP_TEXTO_LARGO %s: %d > %d' % (item['id'], len(item['text']), self.max_chars))
            if item['op'] == 'verify_contains' and not item['text']:
                raise MotorError('GAP_VERIFICACION_VACIA ' + item['id'])
        fin = [o for o in ordered if o['op'] == 'finish']
        if len(fin) > 1:
            raise MotorError('GAP_FINISH_DUPLICADO')
        if fin:  # finish solo cierra el lote si depende (directa o indirectamente) de TODAS las demas operaciones
            tabla = {o['id']: o for o in ordered}
            anc, pila = set(), list(fin[0].get('depends_on', []))
            while pila:
                d = pila.pop()
                if d not in anc:
                    anc.add(d)
                    pila.extend(tabla[d].get('depends_on', []))
            sueltas = sorted(set(tabla) - anc - {fin[0]['id']})
            if sueltas:
                raise MotorError('GAP_FINISH_SIN_DEPENDENCIAS: finish no depende de ' + ', '.join(sueltas))
        return ordered

    def _sha_archivo(self, item):
        try:
            p = self.path(item.get('path'))
            return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else ''
        except Exception:  # noqa: BLE001
            return ''

    def _sigue_valido(self, item, previo):
        # idempotencia: una mutacion ya confirmada no se repite si su efecto real sigue en disco
        if item['op'] == 'create_directory':
            return self.path(item['path']).is_dir()
        if item['op'] == 'write_text':
            return bool(previo.get('artifact_sha256')) and self._sha_archivo(item) == previo.get('artifact_sha256')
        return False

    def run(self, doc):
        plan_sha = ''
        try:
            if isinstance(doc, list):  # blender_cli.py original acepta la lista desnuda de ops
                doc = {'meta': {'name': self.job}, 'ops': doc}
            if not isinstance(doc, dict):
                raise MotorError('JSON raíz debe ser un objeto')
            plan_sha = _sha(_canon(doc))
            ordered = self.order(doc['ops'])
            cp_dir = self.root / '.receipts'
            cp_dir.mkdir(exist_ok=True)
            cp = cp_dir / (self.job + '.json')
            _lk = _bloqueo_archivo(cp_dir / (self.job + '.lock'))  # >>> PREFLIGHT_RB <<< un solo proceso por plan (GAP 06)
            state = {'plan_sha256': plan_sha, 'done': {}}
            if cp.exists():
                state = json.loads(cp.read_text(encoding='utf-8'))
                if state.get('plan_sha256') != plan_sha:
                    raise MotorError('GAP_CHECKPOINT_OTRO_PLAN: cambia meta.name o pide aprobacion')
            for item in ordered:
                previo = (state.get('done') or {}).get(item['id'])
                if previo and item['op'] in _MUTAN and self._sigue_valido(item, previo):
                    rec = dict(previo, reutilizado=True)
                else:
                    result = self.handlers[item['op']](item)
                    rec = {'id': 'receipt-%s-%s-%s' % (self.job, item['id'], plan_sha[:8]), 'source': 'tool_executor',
                           'op_id': item['id'], 'op': item['op'], 'ok': True, 'result': result,
                           'artifact': item.get('path') or '', 'artifact_sha256': self._sha_archivo(item) if item.get('path') else '',
                           'plan_sha256': plan_sha}
                    rec['sha256'] = _sha(_canon({k: v for k, v in rec.items() if k != 'sha256'}))
                    state.setdefault('done', {})[item['id']] = rec
                    tmp = cp.with_suffix('.tmp')
                    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding='utf-8')
                    os.replace(tmp, cp)
                with _LOCK:
                    _RECIBOS[rec['id']] = rec
                self.receipts.append({'id': item['id'], 'op': item['op'], 'ok': True, 'result': rec['result'],
                                      'receipt_id': rec['id'], 'receipt_sha256': rec['sha256'],
                                      'reutilizado': bool(rec.get('reutilizado'))})
        except (MotorError, ValueError, TypeError, KeyError, OSError, UnicodeError) as exc:
            self.errors.append({'type': type(exc).__name__, 'message': str(exc)})
        finally:
            _soltar(locals().get('_lk'))  # >>> PREFLIGHT_RB <<<
        ops = doc.get('ops', []) if isinstance(doc, dict) else []
        return {'ok': not self.errors, 'job': self.job, 'plan_sha256': plan_sha, 'ops_total': len(ops) if isinstance(ops, list) else 0,
                'ops_executed': len(self.receipts), 'receipts': self.receipts, 'errors': self.errors,
                'batch_finished': bool(self.receipts) and self.receipts[-1]['op'] == 'finish' and not self.errors,
                'objective_audited': False}


def _bloqueo_archivo(ruta):  # >>> PREFLIGHT_RB <<< fcntl.flock exclusivo no bloqueante; en Windows/sin fcntl no bloquea (sin cambio)
    try:
        import fcntl  # noqa: PLC0415
    except ImportError:
        return None
    f = open(ruta, 'a+', encoding='utf-8')  # noqa: SIM115
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        f.close()
        raise MotorError('GAP_PLAN_EN_EJECUCION: otro proceso ejecuta este mismo plan')
    return f


def _soltar(f):
    if f is not None:
        try:
            f.close()
        except OSError:
            pass


def ejecutar(plan, workspace='default', politica=None):
    """Punto unico para el Harness: parse estricto -> politica -> workspace confinado -> informe con recibos."""
    try:
        doc = parse_estricto(plan)
        pol = cargar_politica(politica)
        ws = re.sub(r'[^A-Za-z0-9_-]', '-', str(workspace or 'default'))[:64] or 'default'
        job = (doc.get('meta') or {}).get('name') if isinstance(doc, dict) else None
        return MotorYaiwes(base_workspaces() / ws, pol, job or 'plan').run(doc)
    except (MotorError, ValueError, OSError) as x:
        return {'ok': False, 'ops_total': 0, 'ops_executed': 0, 'receipts': [], 'objective_audited': False,
                'errors': [{'type': type(x).__name__, 'message': str(x)[:300]}]}


def es_mutante(plan):
    try:
        doc = parse_estricto(plan)
        ops = doc.get('ops') if isinstance(doc, dict) else doc
        return any(isinstance(o, dict) and o.get('op') in _MUTAN for o in (ops or []))
    except Exception:  # noqa: BLE001
        return False


def _recibo_integro(rec):  # >>> PARCHE_T1 <<< lo emitio el ejecutor y nadie lo toco (sha256 sobre el contenido)
    try:
        if not isinstance(rec, dict) or rec.get('source') != 'tool_executor':
            return False
        return rec.get('sha256') == _sha(_canon({k: v for k, v in rec.items() if k not in ('sha256', 'reutilizado')}))
    except Exception:  # noqa: BLE001
        return False


def recibo_existe(rid):
    """El modelo puede NOMBRAR recibos; aqui se comprueba que los emitio el ejecutor (Bloque 2 seccion 06)."""
    rid = str(rid or '')
    if not rid.startswith('receipt-'):
        return False
    with _LOCK:
        if rid in _RECIBOS and _recibo_integro(_RECIBOS[rid]):
            return True
    try:
        for cp in base_workspaces().glob('*/.receipts/*.json'):
            done = (json.loads(cp.read_text(encoding='utf-8')).get('done') or {})
            for rec in done.values():
                if rec.get('id') == rid and _recibo_integro(rec):
                    with _LOCK:
                        _RECIBOS[rid] = rec
                    return True
    except Exception:  # noqa: BLE001
        pass
    return False


def main():
    import argparse  # noqa: PLC0415
    ap = argparse.ArgumentParser()
    ap.add_argument('plan')
    ap.add_argument('--policy', default=str(POLITICA_DEFECTO))
    ap.add_argument('--root', required=True)
    a = ap.parse_args()
    doc = parse_estricto(Path(a.plan).read_text(encoding='utf-8'))
    job = (doc.get('meta') or {}).get('name') if isinstance(doc, dict) else None
    rep = MotorYaiwes(a.root, cargar_politica(a.policy), job or 'plan').run(doc)
    print('YAIWES_OP_REPORT ' + json.dumps(rep, ensure_ascii=False))
    return 0 if rep['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
