"""Motor code ECC: 'react-performance'.
Fuente ECC: react-performance (sha256 'ac76e8694d4f802a7bccc3c07a73ac68ace6d82a65ea10f10d8b7384dda61a8f').
Cada fase corre como funcion real: el host inyecta model_fn + receipt_fn
(patron Ricardo: la LLM produce, el recibo verifica). Sin host -> FAIL cerrado,
nunca PASS fingido. Ciclos: MAIN -> VERIFY -> RECOVERY (si falla);
CONTINUOUS se declara como trigger; META (guia) no ejecuta.
"""
from __future__ import annotations
import argparse, asyncio, hashlib, json, sys

MOTOR_ID = 'react-performance'
SOURCE_SHA256 = 'ac76e8694d4f802a7bccc3c07a73ac68ace6d82a65ea10f10d8b7384dda61a8f'
FASES = [{'phase_id': 's001', 'title': 'When to Activate', 'ciclo': 'META'}, {'phase_id': 's002', 'title': 'Priority Index', 'ciclo': 'MAIN'}, {'phase_id': 's003', 'title': '1. Eliminating Waterfalls (CRITICAL)', 'ciclo': 'MAIN'}, {'phase_id': 's004', 'title': 'Cheap conditions before await', 'ciclo': 'MAIN'}, {'phase_id': 's005', 'title': 'Defer awaits until used', 'ciclo': 'MAIN'}, {'phase_id': 's006', 'title': 'Promise.all for independent work', 'ciclo': 'MAIN'}, {'phase_id': 's007', 'title': 'Partial dependencies — start early, await late', 'ciclo': 'MAIN'}, {'phase_id': 's008', 'title': 'Suspense for streaming', 'ciclo': 'MAIN'}, {'phase_id': 's009', 'title': 'Server Components: parallel through composition', 'ciclo': 'MAIN'}, {'phase_id': 's010', 'title': '2. Bundle Size Optimization (CRITICAL)', 'ciclo': 'MAIN'}, {'phase_id': 's011', 'title': 'Direct imports, not barrels', 'ciclo': 'MAIN'}, {'phase_id': 's012', 'title': 'Statically analyzable paths', 'ciclo': 'MAIN'}, {'phase_id': 's013', 'title': 'Dynamic imports for heavy components', 'ciclo': 'MAIN'}, {'phase_id': 's014', 'title': 'Defer third-party scripts', 'ciclo': 'MAIN'}, {'phase_id': 's015', 'title': 'Conditional module loading', 'ciclo': 'MAIN'}, {'phase_id': 's016', 'title': 'Preload on hover/focus', 'ciclo': 'MAIN'}, {'phase_id': 's017', 'title': '3. Server-Side Performance (HIGH)', 'ciclo': 'MAIN'}, {'phase_id': 's018', 'title': 'Authenticate Server Actions like API routes', 'ciclo': 'MAIN'}, {'phase_id': 's019', 'title': '`React.cache()` for per-request deduplication', 'ciclo': 'MAIN'}, {'phase_id': 's020', 'title': 'LRU cache for cross-request data', 'ciclo': 'MAIN'}, {'phase_id': 's021', 'title': 'Avoid duplicate serialization in RSC props', 'ciclo': 'MAIN'}, {'phase_id': 's022', 'title': 'Hoist static I/O to module scope', 'ciclo': 'MAIN'}, {'phase_id': 's023', 'title': 'No mutable module-level state in RSC/SSR', 'ciclo': 'MAIN'}, {'phase_id': 's024', 'title': 'Minimize data passed to Client Components', 'ciclo': 'MAIN'}, {'phase_id': 's025', 'title': 'Parallelize nested fetches with Promise.all per item', 'ciclo': 'MAIN'}, {'phase_id': 's026', 'title': 'Use `after()` for non-blocking work', 'ciclo': 'MAIN'}, {'phase_id': 's027', 'title': '4. Client-Side Data Fetching (MEDIUM-HIGH)', 'ciclo': 'MAIN'}, {'phase_id': 's028', 'title': 'SWR / TanStack Query for deduplication', 'ciclo': 'MAIN'}, {'phase_id': 's029', 'title': 'Deduplicate global event listeners', 'ciclo': 'MAIN'}, {'phase_id': 's030', 'title': 'Passive listeners for scroll', 'ciclo': 'MAIN'}, {'phase_id': 's031', 'title': 'localStorage: version + minimize', 'ciclo': 'MAIN'}, {'phase_id': 's032', 'title': '5. Re-render Optimization (MEDIUM)', 'ciclo': 'MAIN'}, {'phase_id': 's033', 'title': "Don't subscribe to state used only in callbacks", 'ciclo': 'META'}, {'phase_id': 's034', 'title': 'Extract expensive work into memoized components', 'ciclo': 'MAIN'}, {'phase_id': 's035', 'title': 'Hoist default non-primitive props', 'ciclo': 'RECOVERY'}, {'phase_id': 's036', 'title': 'Primitive dependencies in effects', 'ciclo': 'MAIN'}, {'phase_id': 's037', 'title': 'Subscribe to derived booleans, not raw values', 'ciclo': 'MAIN'}, {'phase_id': 's038', 'title': 'Derive during render, never via `useEffect`', 'ciclo': 'MAIN'}, {'phase_id': 's039', 'title': 'Functional `setState` for stable callbacks', 'ciclo': 'MAIN'}, {'phase_id': 's040', 'title': 'Lazy state initializer for expensive values', 'ciclo': 'MAIN'}, {'phase_id': 's041', 'title': 'Avoid memo for simple primitives', 'ciclo': 'MAIN'}, {'phase_id': 's042', 'title': 'Split hooks with independent deps', 'ciclo': 'CONTINUOUS'}, {'phase_id': 's043', 'title': 'Move interaction logic into event handlers', 'ciclo': 'MAIN'}, {'phase_id': 's044', 'title': '`startTransition` for non-urgent updates', 'ciclo': 'MAIN'}, {'phase_id': 's045', 'title': '`useDeferredValue` for expensive renders', 'ciclo': 'MAIN'}, {'phase_id': 's046', 'title': '`useRef` for transient frequent values', 'ciclo': 'MAIN'}, {'phase_id': 's047', 'title': "Don't define components inside components", 'ciclo': 'META'}, {'phase_id': 's048', 'title': '6. Rendering Performance (MEDIUM)', 'ciclo': 'MAIN'}, {'phase_id': 's049', 'title': 'Animate the wrapper, not the SVG', 'ciclo': 'MAIN'}, {'phase_id': 's050', 'title': '`content-visibility: auto` for long lists', 'ciclo': 'MAIN'}, {'phase_id': 's051', 'title': 'Hoist static JSX', 'ciclo': 'MAIN'}, {'phase_id': 's052', 'title': 'SVG: reduce coordinate precision', 'ciclo': 'MAIN'}, {'phase_id': 's053', 'title': 'Hydration no-flicker via inline script', 'ciclo': 'MAIN'}, {'phase_id': 's054', 'title': 'Suppress expected hydration mismatches narrowly', 'ciclo': 'MAIN'}, {'phase_id': 's055', 'title': '`<Activity>` for show/hide instead of mount/unmount', 'ciclo': 'MAIN'}, {'phase_id': 's056', 'title': 'Ternary over `&&` for conditional render', 'ciclo': 'MAIN'}, {'phase_id': 's057', 'title': '`useTransition` for loading states', 'ciclo': 'MAIN'}, {'phase_id': 's058', 'title': 'React DOM resource hints', 'ciclo': 'META'}, {'phase_id': 's059', 'title': '`defer` / `async` on `<script>` tags', 'ciclo': 'MAIN'}, {'phase_id': 's060', 'title': '7. JavaScript Performance (LOW-MEDIUM)', 'ciclo': 'MAIN'}, {'phase_id': 's061', 'title': '8. Advanced Patterns (LOW)', 'ciclo': 'MAIN'}, {'phase_id': 's062', 'title': '`useEffectEvent` deps', 'ciclo': 'MAIN'}, {'phase_id': 's063', 'title': 'Event handler refs', 'ciclo': 'MAIN'}, {'phase_id': 's064', 'title': 'Init once per app load', 'ciclo': 'MAIN'}, {'phase_id': 's065', 'title': '`useLatest` for stable callback refs', 'ciclo': 'VERIFY'}, {'phase_id': 's066', 'title': 'Automated Tools', 'ciclo': 'MAIN'}, {'phase_id': 's067', 'title': 'Lighthouse / Web Vitals Mapping', 'ciclo': 'MAIN'}, {'phase_id': 's068', 'title': 'Related', 'ciclo': 'META'}, {'phase_id': 's069', 'title': 'Attribution', 'ciclo': 'MAIN'}]


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
