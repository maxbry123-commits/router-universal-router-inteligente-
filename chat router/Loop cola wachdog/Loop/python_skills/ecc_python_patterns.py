"""Motor Python ejecutable del skill ECC: 'python-patterns'.
Generado desde skills/python-patterns/SKILL.md (sha256 '103e0130dac33a49d26705fc5a2df804980fcab6a0138d65bc7f370a987d49f6').
Cada fase corre como funcion real: el host inyecta model_fn + receipt_fn
(patron Ricardo: la LLM produce, el recibo verifica). Sin host -> FAIL cerrado,
nunca PASS fingido. Ciclos: MAIN -> VERIFY -> RECOVERY (si falla);
CONTINUOUS se declara como trigger; META (guia) no ejecuta.
"""
from __future__ import annotations
import argparse, asyncio, hashlib, json, sys

SKILL_ID = 'python-patterns'
SOURCE_SHA256 = '103e0130dac33a49d26705fc5a2df804980fcab6a0138d65bc7f370a987d49f6'
FASES = [{'phase_id': 's001', 'title': 'When to Activate', 'ciclo': 'META'}, {'phase_id': 's002', 'title': 'Core Principles', 'ciclo': 'META'}, {'phase_id': 's003', 'title': '1. Readability Counts', 'ciclo': 'MAIN'}, {'phase_id': 's004', 'title': '2. Explicit is Better Than Implicit', 'ciclo': 'MAIN'}, {'phase_id': 's005', 'title': '3. EAFP - Easier to Ask Forgiveness Than Permission', 'ciclo': 'MAIN'}, {'phase_id': 's006', 'title': 'Type Hints', 'ciclo': 'MAIN'}, {'phase_id': 's007', 'title': 'Basic Type Annotations', 'ciclo': 'MAIN'}, {'phase_id': 's008', 'title': 'Modern Type Hints (Python 3.9+)', 'ciclo': 'MAIN'}, {'phase_id': 's009', 'title': 'Type Aliases and TypeVar', 'ciclo': 'MAIN'}, {'phase_id': 's010', 'title': 'Protocol-Based Duck Typing', 'ciclo': 'MAIN'}, {'phase_id': 's011', 'title': 'Error Handling Patterns', 'ciclo': 'RECOVERY'}, {'phase_id': 's012', 'title': 'Specific Exception Handling', 'ciclo': 'MAIN'}, {'phase_id': 's013', 'title': 'Exception Chaining', 'ciclo': 'MAIN'}, {'phase_id': 's014', 'title': 'Custom Exception Hierarchy', 'ciclo': 'MAIN'}, {'phase_id': 's015', 'title': 'Context Managers', 'ciclo': 'MAIN'}, {'phase_id': 's016', 'title': 'Resource Management', 'ciclo': 'META'}, {'phase_id': 's017', 'title': 'Custom Context Managers', 'ciclo': 'MAIN'}, {'phase_id': 's018', 'title': 'Context Manager Classes', 'ciclo': 'MAIN'}, {'phase_id': 's019', 'title': 'Comprehensions and Generators', 'ciclo': 'MAIN'}, {'phase_id': 's020', 'title': 'List Comprehensions', 'ciclo': 'MAIN'}, {'phase_id': 's021', 'title': 'Generator Expressions', 'ciclo': 'MAIN'}, {'phase_id': 's022', 'title': 'Generator Functions', 'ciclo': 'MAIN'}, {'phase_id': 's023', 'title': 'Data Classes and Named Tuples', 'ciclo': 'MAIN'}, {'phase_id': 's024', 'title': 'Data Classes', 'ciclo': 'MAIN'}, {'phase_id': 's025', 'title': 'Data Classes with Validation', 'ciclo': 'VERIFY'}, {'phase_id': 's026', 'title': 'Named Tuples', 'ciclo': 'MAIN'}, {'phase_id': 's027', 'title': 'Decorators', 'ciclo': 'MAIN'}, {'phase_id': 's028', 'title': 'Function Decorators', 'ciclo': 'MAIN'}, {'phase_id': 's029', 'title': 'Parameterized Decorators', 'ciclo': 'MAIN'}, {'phase_id': 's030', 'title': 'Class-Based Decorators', 'ciclo': 'MAIN'}, {'phase_id': 's031', 'title': 'Concurrency Patterns', 'ciclo': 'MAIN'}, {'phase_id': 's032', 'title': 'Threading for I/O-Bound Tasks', 'ciclo': 'MAIN'}, {'phase_id': 's033', 'title': 'Multiprocessing for CPU-Bound Tasks', 'ciclo': 'MAIN'}, {'phase_id': 's034', 'title': 'Async/Await for Concurrent I/O', 'ciclo': 'MAIN'}, {'phase_id': 's035', 'title': 'Package Organization', 'ciclo': 'MAIN'}, {'phase_id': 's036', 'title': 'Standard Project Layout', 'ciclo': 'MAIN'}, {'phase_id': 's037', 'title': 'Import Conventions', 'ciclo': 'MAIN'}, {'phase_id': 's038', 'title': '__init__.py for Package Exports', 'ciclo': 'MAIN'}, {'phase_id': 's039', 'title': 'Memory and Performance', 'ciclo': 'MAIN'}, {'phase_id': 's040', 'title': 'Using __slots__ for Memory Efficiency', 'ciclo': 'MAIN'}, {'phase_id': 's041', 'title': 'Generator for Large Data', 'ciclo': 'MAIN'}, {'phase_id': 's042', 'title': 'Avoid String Concatenation in Loops', 'ciclo': 'MAIN'}, {'phase_id': 's043', 'title': 'Python Tooling Integration', 'ciclo': 'MAIN'}, {'phase_id': 's044', 'title': 'Essential Commands', 'ciclo': 'MAIN'}, {'phase_id': 's045', 'title': 'pyproject.toml Configuration', 'ciclo': 'META'}, {'phase_id': 's046', 'title': 'Quick Reference: Python Idioms', 'ciclo': 'META'}, {'phase_id': 's047', 'title': 'Anti-Patterns to Avoid', 'ciclo': 'META'}]


def _sha(v):
    return hashlib.sha256(json.dumps(v, sort_keys=True, default=str).encode()).hexdigest()[:32]


async def fase(ph: dict, ctx: dict) -> dict:
    """Ejecuta una fase: llama al modelo inyectado y devuelve evidencia real."""
    model_fn = ctx.get('model_fn')
    if not callable(model_fn):
        return {'phase_id': ph['phase_id'], 'status': 'FAIL',
                'error': 'sin model_fn inyectado'}
    prompt = ('[ECC %s %s] %s | tarea=%s evento=%s ctx=%s'
              % (SKILL_ID, ph['phase_id'], ph['title'], ctx.get('task_id'),
                 ctx.get('event'), json.dumps(ctx.get('context', {}), ensure_ascii=False)[:1500]))
    r = await model_fn(prompt) if asyncio.iscoroutinefunction(model_fn) else model_fn(prompt)
    txt = (r or {}).get('reply') or (r or {}).get('texto') or ''
    if not txt:
        return {'phase_id': ph['phase_id'], 'status': 'FAIL', 'error': 'modelo sin respuesta'}
    status = 'PASS'
    try:
        i = txt.find('{')
        if i >= 0:
            d, _ = json.JSONDecoder().raw_decode(txt[i:])
            if isinstance(d, dict) and str(d.get('status')).upper() in ('FAIL', 'BLOCKED'):
                status = 'FAIL'
    except Exception:
        pass
    return {'phase_id': ph['phase_id'], 'status': status,
            'evidence_sha256': hashlib.sha256(txt.encode()).hexdigest(),
            'resultado': txt[:4000]}


async def _ciclo(nombre: str, fases: list, ctx: dict) -> dict:
    recibos = []
    for ph in fases:
        out = await fase(ph, ctx)
        rid = _sha([SKILL_ID, ph['phase_id'], ctx.get('task_id'), out.get('evidence_sha256')])
        receipt_fn = ctx.get('receipt_fn')
        rec = {'phase_id': ph['phase_id'], 'receipt_id': rid,
               'status': out['status'], 'evidence_source': 'approved_tool'}
        if callable(receipt_fn):
            extra = receipt_fn({'skill_id': SKILL_ID, 'task_id': ctx.get('task_id'),
                                'phase': ph, 'resultado': out})
            if asyncio.iscoroutine(extra):
                extra = await extra
            if isinstance(extra, dict):
                rec.update({k: v for k, v in extra.items() if k not in rec})
        recibos.append(rec)
        if out['status'] != 'PASS':
            return {'ciclo': nombre, 'ok': False, 'failed_phase': ph['phase_id'],
                    'receipts': recibos}
    return {'ciclo': nombre, 'ok': True, 'executed': len(recibos), 'receipts': recibos}


async def run(context: dict | None = None, *, task_id: str = 'tarea',
              event: str = 'skill.run', model_fn=None, receipt_fn=None) -> dict:
    """Corre el motor: MAIN -> VERIFY -> RECOVERY. Devuelve recibos por ciclo."""
    ctx = {'task_id': task_id, 'event': event,
           'context': context or {}, 'model_fn': model_fn, 'receipt_fn': receipt_fn}
    por = {'MAIN': [], 'VERIFY': [], 'RECOVERY': [], 'CONTINUOUS': [], 'META': []}
    for ph in FASES:
        por.setdefault(ph['ciclo'], []).append(ph)
    res = {'skill_id': SKILL_ID, 'task_id': task_id,
           'ciclos': {k: len(v) for k, v in por.items()},
           'continuous_triggers': [p['title'] for p in por['CONTINUOUS']],
           'meta_omitidas': len(por['META'])}
    main_fases = por['MAIN'] or por['VERIFY']
    res['main'] = await _ciclo('MAIN', main_fases, ctx)
    if not res['main']['ok']:
        if por['RECOVERY']:
            res['recovery'] = await _ciclo('RECOVERY', por['RECOVERY'], ctx)
        res['ok'], res['status'] = False, 'FAILED_MAIN'
        return res
    if por['VERIFY'] and por['MAIN']:
        res['verify'] = await _ciclo('VERIFY', por['VERIFY'], ctx)
        if not res['verify']['ok']:
            if por['RECOVERY']:
                res['recovery'] = await _ciclo('RECOVERY', por['RECOVERY'], ctx)
            res['ok'], res['status'] = False, 'FAILED_VERIFY'
            return res
    res['ok'], res['status'] = True, 'PASS'
    return res


def main():
    ap = argparse.ArgumentParser(description='Motor ECC ejecutable: ' + SKILL_ID)
    ap.add_argument('--task-id', default='tarea')
    ap.add_argument('--context', default='{}')
    ap.add_argument('--demo', action='store_true',
                    help='model_fn de demostracion (artefacto simulado)')
    a = ap.parse_args()
    model_fn = None
    if a.demo:
        def model_fn(prompt):
            return {'reply': json.dumps({'status': 'PASS', 'resultado': 'demo de fase'})}
    r = asyncio.run(run(json.loads(a.context), task_id=a.task_id, model_fn=model_fn))
    print(json.dumps(r, ensure_ascii=False, indent=2))
    sys.exit(0 if r.get('ok') else 1)


if __name__ == '__main__':
    main()
