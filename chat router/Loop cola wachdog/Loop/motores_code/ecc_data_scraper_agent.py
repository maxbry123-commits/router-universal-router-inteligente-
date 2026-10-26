"""Motor code ECC: 'data-scraper-agent'.
Fuente ECC: data-scraper-agent (sha256 '662e884d58f4089bd8e090ef8d32042b85a5d9b4715906a89072002704451c0a').
Cada fase corre como funcion real: el host inyecta model_fn + receipt_fn
(patron Ricardo: la LLM produce, el recibo verifica). Sin host -> FAIL cerrado,
nunca PASS fingido. Ciclos: MAIN -> VERIFY -> RECOVERY (si falla);
CONTINUOUS se declara como trigger; META (guia) no ejecuta.
"""
from __future__ import annotations
import argparse, asyncio, hashlib, json, sys

MOTOR_ID = 'data-scraper-agent'
SOURCE_SHA256 = '662e884d58f4089bd8e090ef8d32042b85a5d9b4715906a89072002704451c0a'
FASES = [{'phase_id': 's001', 'title': 'When to Activate', 'ciclo': 'META'}, {'phase_id': 's002', 'title': 'Core Concepts', 'ciclo': 'META'}, {'phase_id': 's003', 'title': 'The Three Layers', 'ciclo': 'MAIN'}, {'phase_id': 's004', 'title': 'Free Stack', 'ciclo': 'MAIN'}, {'phase_id': 's005', 'title': 'AI Model Fallback Chain', 'ciclo': 'MAIN'}, {'phase_id': 's006', 'title': 'Batch API Calls for Efficiency', 'ciclo': 'MAIN'}, {'phase_id': 's007', 'title': 'Untrusted Scraped Data', 'ciclo': 'MAIN'}, {'phase_id': 's008', 'title': 'Workflow', 'ciclo': 'MAIN'}, {'phase_id': 's009', 'title': 'Step 1: Understand the Goal', 'ciclo': 'MAIN'}, {'phase_id': 's010', 'title': 'Step 2: Design the Collection Architecture', 'ciclo': 'MAIN'}, {'phase_id': 's011', 'title': 'Step 3: Build the Source Connector', 'ciclo': 'MAIN'}, {'phase_id': 's012', 'title': 'Step 4: Build the Gemini AI Client', 'ciclo': 'MAIN'}, {'phase_id': 's013', 'title': 'Step 5: Build the AI Pipeline (Batch)', 'ciclo': 'MAIN'}, {'phase_id': 's014', 'title': 'Step 6: Build the Feedback Learning System', 'ciclo': 'MAIN'}, {'phase_id': 's015', 'title': 'Step 7: Build Storage (Notion example)', 'ciclo': 'META'}, {'phase_id': 's016', 'title': 'Step 8: Orchestrate in main.py', 'ciclo': 'MAIN'}, {'phase_id': 's017', 'title': 'Step 9: GitHub Actions Workflow', 'ciclo': 'MAIN'}, {'phase_id': 's018', 'title': 'Step 10: config.yaml Template', 'ciclo': 'META'}, {'phase_id': 's019', 'title': 'Common Scraping Patterns', 'ciclo': 'MAIN'}, {'phase_id': 's020', 'title': 'Pattern 1: REST API (easiest)', 'ciclo': 'MAIN'}, {'phase_id': 's021', 'title': 'Pattern 2: HTML Scraping', 'ciclo': 'MAIN'}, {'phase_id': 's022', 'title': 'Pattern 3: RSS Feed', 'ciclo': 'MAIN'}, {'phase_id': 's023', 'title': 'Pattern 4: Paginated API', 'ciclo': 'MAIN'}, {'phase_id': 's024', 'title': 'Pattern 5: JS-Rendered Pages (Playwright)', 'ciclo': 'MAIN'}, {'phase_id': 's025', 'title': 'Anti-Patterns to Avoid', 'ciclo': 'META'}, {'phase_id': 's026', 'title': 'Free Tier Limits Reference', 'ciclo': 'META'}, {'phase_id': 's027', 'title': 'Requirements Template', 'ciclo': 'MAIN'}, {'phase_id': 's028', 'title': 'Quality Checklist', 'ciclo': 'VERIFY'}, {'phase_id': 's029', 'title': 'Real-World Examples', 'ciclo': 'META'}, {'phase_id': 's030', 'title': 'Reference Implementation', 'ciclo': 'META'}]


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
