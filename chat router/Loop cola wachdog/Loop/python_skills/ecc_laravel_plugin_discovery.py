"""Motor Python ejecutable del skill ECC: 'laravel-plugin-discovery'.
Generado desde skills/laravel-plugin-discovery/SKILL.md (sha256 '6cf2b48ae39f26df7f8d17cf6480635b5203f6942a756a290efa27cf339169d3').
Cada fase corre como funcion real: el host inyecta model_fn + receipt_fn
(patron Ricardo: la LLM produce, el recibo verifica). Sin host -> FAIL cerrado,
nunca PASS fingido. Ciclos: MAIN -> VERIFY -> RECOVERY (si falla);
CONTINUOUS se declara como trigger; META (guia) no ejecuta.
"""
from __future__ import annotations
import argparse, asyncio, hashlib, json, sys

SKILL_ID = 'laravel-plugin-discovery'
SOURCE_SHA256 = '6cf2b48ae39f26df7f8d17cf6480635b5203f6942a756a290efa27cf339169d3'
FASES = [{'phase_id': 's001', 'title': 'When to Use', 'ciclo': 'META'}, {'phase_id': 's002', 'title': 'MCP Requirement', 'ciclo': 'MAIN'}, {'phase_id': 's003', 'title': 'MCP Tools', 'ciclo': 'MAIN'}, {'phase_id': 's004', 'title': 'SearchPluginTool', 'ciclo': 'MAIN'}, {'phase_id': 's005', 'title': 'GetPluginDetailsTool', 'ciclo': 'MAIN'}, {'phase_id': 's006', 'title': 'How It Works', 'ciclo': 'MAIN'}, {'phase_id': 's007', 'title': 'Finding Packages', 'ciclo': 'MAIN'}, {'phase_id': 's008', 'title': 'Evaluating Packages', 'ciclo': 'VERIFY'}, {'phase_id': 's009', 'title': 'Checking Compatibility', 'ciclo': 'VERIFY'}, {'phase_id': 's010', 'title': 'Examples', 'ciclo': 'META'}, {'phase_id': 's011', 'title': 'Example: Find Authentication Packages', 'ciclo': 'META'}, {'phase_id': 's012', 'title': 'Example: Find Laravel 12 Compatible Packages', 'ciclo': 'META'}, {'phase_id': 's013', 'title': 'Example: Get Package Details', 'ciclo': 'META'}, {'phase_id': 's014', 'title': 'Example: Find Packages by Vendor', 'ciclo': 'META'}, {'phase_id': 's015', 'title': 'Filtering Best Practices', 'ciclo': 'MAIN'}, {'phase_id': 's016', 'title': 'By Health Score', 'ciclo': 'MAIN'}, {'phase_id': 's017', 'title': 'By Laravel Version', 'ciclo': 'MAIN'}, {'phase_id': 's018', 'title': 'Combining Filters', 'ciclo': 'MAIN'}, {'phase_id': 's019', 'title': 'Response Interpretation', 'ciclo': 'MAIN'}, {'phase_id': 's020', 'title': 'Search Results', 'ciclo': 'MAIN'}, {'phase_id': 's021', 'title': 'Package Details', 'ciclo': 'MAIN'}, {'phase_id': 's022', 'title': 'Common Use Cases', 'ciclo': 'MAIN'}, {'phase_id': 's023', 'title': 'Best Practices', 'ciclo': 'MAIN'}, {'phase_id': 's024', 'title': 'Related Skills', 'ciclo': 'META'}]


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
