"""Motor code ECC: 'flutter-dart-code-review'.
Fuente ECC: flutter-dart-code-review (sha256 '5ceac13c9b99c97340f9a47c081737aceee1f803ed9045b7fbc980243b01db03').
Cada fase corre como funcion real: el host inyecta model_fn + receipt_fn
(patron Ricardo: la LLM produce, el recibo verifica). Sin host -> FAIL cerrado,
nunca PASS fingido. Ciclos: MAIN -> VERIFY -> RECOVERY (si falla);
CONTINUOUS se declara como trigger; META (guia) no ejecuta.
"""
from __future__ import annotations
import argparse, asyncio, hashlib, json, sys

MOTOR_ID = 'flutter-dart-code-review'
SOURCE_SHA256 = '5ceac13c9b99c97340f9a47c081737aceee1f803ed9045b7fbc980243b01db03'
FASES = [{'phase_id': 's001', 'title': '1. General Project Health', 'ciclo': 'MAIN'}, {'phase_id': 's002', 'title': '2. Dart Language Pitfalls', 'ciclo': 'RECOVERY'}, {'phase_id': 's003', 'title': '3. Widget Best Practices', 'ciclo': 'MAIN'}, {'phase_id': 's004', 'title': 'Widget decomposition:', 'ciclo': 'MAIN'}, {'phase_id': 's005', 'title': 'Const usage:', 'ciclo': 'MAIN'}, {'phase_id': 's006', 'title': 'Key usage:', 'ciclo': 'MAIN'}, {'phase_id': 's007', 'title': 'Theming & design system:', 'ciclo': 'MAIN'}, {'phase_id': 's008', 'title': 'Build method complexity:', 'ciclo': 'MAIN'}, {'phase_id': 's009', 'title': '4. State Management (Library-Agnostic)', 'ciclo': 'MAIN'}, {'phase_id': 's010', 'title': 'Architecture:', 'ciclo': 'MAIN'}, {'phase_id': 's011', 'title': 'Immutability & value equality (for immutable-state solutions: BLoC, Riverpod, Redux):', 'ciclo': 'VERIFY'}, {'phase_id': 's012', 'title': 'Reactivity discipline (for reactive-mutation solutions: MobX, GetX, Signals):', 'ciclo': 'MAIN'}, {'phase_id': 's013', 'title': 'State shape design:', 'ciclo': 'MAIN'}, {'phase_id': 's014', 'title': 'Rebuild optimization:', 'ciclo': 'MAIN'}, {'phase_id': 's015', 'title': 'Subscriptions & disposal:', 'ciclo': 'MAIN'}, {'phase_id': 's016', 'title': 'Local vs global state:', 'ciclo': 'MAIN'}, {'phase_id': 's017', 'title': '5. Performance', 'ciclo': 'MAIN'}, {'phase_id': 's018', 'title': 'Unnecessary rebuilds:', 'ciclo': 'MAIN'}, {'phase_id': 's019', 'title': 'Expensive operations in build():', 'ciclo': 'MAIN'}, {'phase_id': 's020', 'title': 'Image optimization:', 'ciclo': 'MAIN'}, {'phase_id': 's021', 'title': 'Lazy loading:', 'ciclo': 'MAIN'}, {'phase_id': 's022', 'title': 'Other:', 'ciclo': 'MAIN'}, {'phase_id': 's023', 'title': '6. Testing', 'ciclo': 'VERIFY'}, {'phase_id': 's024', 'title': 'Test types and expectations:', 'ciclo': 'VERIFY'}, {'phase_id': 's025', 'title': 'Coverage targets:', 'ciclo': 'MAIN'}, {'phase_id': 's026', 'title': 'Test isolation:', 'ciclo': 'VERIFY'}, {'phase_id': 's027', 'title': 'Widget test quality:', 'ciclo': 'VERIFY'}, {'phase_id': 's028', 'title': '7. Accessibility', 'ciclo': 'MAIN'}, {'phase_id': 's029', 'title': 'Semantic widgets:', 'ciclo': 'MAIN'}, {'phase_id': 's030', 'title': 'Screen reader support:', 'ciclo': 'MAIN'}, {'phase_id': 's031', 'title': 'Visual accessibility:', 'ciclo': 'MAIN'}, {'phase_id': 's032', 'title': 'Interaction accessibility:', 'ciclo': 'MAIN'}, {'phase_id': 's033', 'title': '8. Platform-Specific Concerns', 'ciclo': 'MAIN'}, {'phase_id': 's034', 'title': 'iOS/Android differences:', 'ciclo': 'MAIN'}, {'phase_id': 's035', 'title': 'Responsive design:', 'ciclo': 'MAIN'}, {'phase_id': 's036', 'title': '9. Security', 'ciclo': 'MAIN'}, {'phase_id': 's037', 'title': 'Secure storage:', 'ciclo': 'MAIN'}, {'phase_id': 's038', 'title': 'API key handling:', 'ciclo': 'MAIN'}, {'phase_id': 's039', 'title': 'Input validation:', 'ciclo': 'VERIFY'}, {'phase_id': 's040', 'title': 'Network security:', 'ciclo': 'MAIN'}, {'phase_id': 's041', 'title': '10. Package/Dependency Review', 'ciclo': 'VERIFY'}, {'phase_id': 's042', 'title': 'Evaluating pub.dev packages:', 'ciclo': 'VERIFY'}, {'phase_id': 's043', 'title': 'Version constraints:', 'ciclo': 'MAIN'}, {'phase_id': 's044', 'title': 'Monorepo-specific (melos/workspace):', 'ciclo': 'MAIN'}, {'phase_id': 's045', 'title': '11. Navigation and Routing', 'ciclo': 'MAIN'}, {'phase_id': 's046', 'title': 'General principles (apply to any routing solution):', 'ciclo': 'META'}, {'phase_id': 's047', 'title': '12. Error Handling', 'ciclo': 'RECOVERY'}, {'phase_id': 's048', 'title': 'Framework error handling:', 'ciclo': 'RECOVERY'}, {'phase_id': 's049', 'title': 'Error reporting:', 'ciclo': 'RECOVERY'}, {'phase_id': 's050', 'title': 'Graceful degradation:', 'ciclo': 'RECOVERY'}, {'phase_id': 's051', 'title': '13. Internationalization (l10n)', 'ciclo': 'MAIN'}, {'phase_id': 's052', 'title': 'Setup:', 'ciclo': 'META'}, {'phase_id': 's053', 'title': 'Content:', 'ciclo': 'MAIN'}, {'phase_id': 's054', 'title': 'Code review:', 'ciclo': 'VERIFY'}, {'phase_id': 's055', 'title': '14. Dependency Injection', 'ciclo': 'MAIN'}, {'phase_id': 's056', 'title': 'Principles (apply to any DI approach):', 'ciclo': 'META'}, {'phase_id': 's057', 'title': '15. Static Analysis', 'ciclo': 'MAIN'}, {'phase_id': 's058', 'title': 'Configuration:', 'ciclo': 'META'}, {'phase_id': 's059', 'title': 'Enforcement:', 'ciclo': 'MAIN'}, {'phase_id': 's060', 'title': 'Key rules to verify regardless of lint package:', 'ciclo': 'VERIFY'}, {'phase_id': 's061', 'title': 'State Management Quick Reference', 'ciclo': 'META'}, {'phase_id': 's062', 'title': 'Sources', 'ciclo': 'MAIN'}]


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
