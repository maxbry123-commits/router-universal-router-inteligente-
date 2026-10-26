"""Motor code ECC: 'tdd-workflow'.
Fuente ECC: tdd-workflow (sha256 '8887afa786ef30de834e7567115d3df71934b343c3d9d849714f8ea43f979ee0').
Cada fase corre como funcion real: el host inyecta model_fn + receipt_fn
(patron Ricardo: la LLM produce, el recibo verifica). Sin host -> FAIL cerrado,
nunca PASS fingido. Ciclos: MAIN -> VERIFY -> RECOVERY (si falla);
CONTINUOUS se declara como trigger; META (guia) no ejecuta.
"""
from __future__ import annotations
import argparse, asyncio, hashlib, json, sys

MOTOR_ID = 'tdd-workflow'
SOURCE_SHA256 = '8887afa786ef30de834e7567115d3df71934b343c3d9d849714f8ea43f979ee0'
FASES = [{'phase_id': 's001', 'title': 'When to Activate', 'ciclo': 'META'}, {'phase_id': 's002', 'title': 'Plan Handoff', 'ciclo': 'MAIN'}, {'phase_id': 's003', 'title': 'Core Principles', 'ciclo': 'META'}, {'phase_id': 's004', 'title': '1. Tests BEFORE Code', 'ciclo': 'VERIFY'}, {'phase_id': 's005', 'title': '2. Coverage Requirements', 'ciclo': 'MAIN'}, {'phase_id': 's006', 'title': '3. Test Types', 'ciclo': 'VERIFY'}, {'phase_id': 's007', 'title': '4. Git Checkpoints', 'ciclo': 'VERIFY'}, {'phase_id': 's008', 'title': 'TDD Workflow Steps', 'ciclo': 'MAIN'}, {'phase_id': 's009', 'title': 'Step 0: Detect the Test Runner', 'ciclo': 'VERIFY'}, {'phase_id': 's010', 'title': 'Step 1: Write User Journeys', 'ciclo': 'MAIN'}, {'phase_id': 's011', 'title': 'Step 2: Generate Test Cases', 'ciclo': 'VERIFY'}, {'phase_id': 's012', 'title': 'Step 3: Run Tests (They Should Fail)', 'ciclo': 'RECOVERY'}, {'phase_id': 's013', 'title': 'Step 4: Implement Code', 'ciclo': 'MAIN'}, {'phase_id': 's014', 'title': 'Step 5: Run Tests Again', 'ciclo': 'VERIFY'}, {'phase_id': 's015', 'title': 'Step 6: Refactor', 'ciclo': 'MAIN'}, {'phase_id': 's016', 'title': 'Step 7: Verify Coverage', 'ciclo': 'VERIFY'}, {'phase_id': 's017', 'title': 'Step 8: Write a TDD Evidence Report', 'ciclo': 'MAIN'}, {'phase_id': 's018', 'title': 'Testing Patterns', 'ciclo': 'VERIFY'}, {'phase_id': 's019', 'title': 'Unit Test Pattern (Jest/Vitest)', 'ciclo': 'VERIFY'}, {'phase_id': 's020', 'title': 'Bun Native Test Pattern (`bun:test`)', 'ciclo': 'VERIFY'}, {'phase_id': 's021', 'title': 'API Integration Test Pattern', 'ciclo': 'VERIFY'}, {'phase_id': 's022', 'title': 'E2E Test Pattern (Playwright)', 'ciclo': 'VERIFY'}, {'phase_id': 's023', 'title': 'Test File Organization', 'ciclo': 'VERIFY'}, {'phase_id': 's024', 'title': 'Mocking External Services', 'ciclo': 'MAIN'}, {'phase_id': 's025', 'title': 'Supabase Mock', 'ciclo': 'MAIN'}, {'phase_id': 's026', 'title': 'Redis Mock', 'ciclo': 'MAIN'}, {'phase_id': 's027', 'title': 'OpenAI Mock', 'ciclo': 'MAIN'}, {'phase_id': 's028', 'title': 'Test Coverage Verification', 'ciclo': 'VERIFY'}, {'phase_id': 's029', 'title': 'Run Coverage Report', 'ciclo': 'MAIN'}, {'phase_id': 's030', 'title': 'Coverage Thresholds', 'ciclo': 'MAIN'}, {'phase_id': 's031', 'title': 'Common Testing Mistakes to Avoid', 'ciclo': 'VERIFY'}, {'phase_id': 's032', 'title': 'FAIL: WRONG: Testing Implementation Details', 'ciclo': 'RECOVERY'}, {'phase_id': 's033', 'title': 'PASS: CORRECT: Test User-Visible Behavior', 'ciclo': 'VERIFY'}, {'phase_id': 's034', 'title': 'FAIL: WRONG: Brittle Selectors', 'ciclo': 'RECOVERY'}, {'phase_id': 's035', 'title': 'PASS: CORRECT: Semantic Selectors', 'ciclo': 'MAIN'}, {'phase_id': 's036', 'title': 'FAIL: WRONG: No Test Isolation', 'ciclo': 'RECOVERY'}, {'phase_id': 's037', 'title': 'PASS: CORRECT: Independent Tests', 'ciclo': 'VERIFY'}, {'phase_id': 's038', 'title': 'Continuous Testing', 'ciclo': 'CONTINUOUS'}, {'phase_id': 's039', 'title': 'Watch Mode During Development', 'ciclo': 'CONTINUOUS'}, {'phase_id': 's040', 'title': 'Pre-Commit Hook', 'ciclo': 'CONTINUOUS'}, {'phase_id': 's041', 'title': 'CI/CD Integration', 'ciclo': 'MAIN'}, {'phase_id': 's042', 'title': 'Best Practices', 'ciclo': 'MAIN'}, {'phase_id': 's043', 'title': 'Success Metrics', 'ciclo': 'MAIN'}]


def _sha(v):
    return hashlib.sha256(json.dumps(v, sort_keys=True, default=str).encode()).hexdigest()[:32]


async def fase(ph: dict, ctx: dict) -> dict:
    """Ejecuta una fase: llama al modelo inyectado y devuelve evidencia real."""
    model_fn = ctx.get('model_fn')
    if not callable(model_fn):
        return {'phase_id': ph['phase_id'], 'status': 'FAIL',
                'error': 'sin model_fn inyectado'}
    prompt = ('[ECC %s %s] %s | tarea=%s evento=%s ctx=%s'
              % (MOTOR_ID, ph['phase_id'], ph['title'], ctx.get('task_id'),
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
        rid = _sha([MOTOR_ID, ph['phase_id'], ctx.get('task_id'), out.get('evidence_sha256')])
        receipt_fn = ctx.get('receipt_fn')
        rec = {'phase_id': ph['phase_id'], 'receipt_id': rid,
               'status': out['status'], 'evidence_source': 'approved_tool'}
        if callable(receipt_fn):
            extra = receipt_fn({'motor_id': MOTOR_ID, 'task_id': ctx.get('task_id'),
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
              event: str = 'motor.run', model_fn=None, receipt_fn=None) -> dict:
    """Corre el motor: MAIN -> VERIFY -> RECOVERY. Devuelve recibos por ciclo."""
    ctx = {'task_id': task_id, 'event': event,
           'context': context or {}, 'model_fn': model_fn, 'receipt_fn': receipt_fn}
    por = {'MAIN': [], 'VERIFY': [], 'RECOVERY': [], 'CONTINUOUS': [], 'META': []}
    for ph in FASES:
        por.setdefault(ph['ciclo'], []).append(ph)
    res = {'motor_id': MOTOR_ID, 'task_id': task_id,
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
    ap = argparse.ArgumentParser(description='Motor ECC ejecutable: ' + MOTOR_ID)
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
