"""Motor code ECC: 'openclaw-persona-forge'.
Fuente ECC: openclaw-persona-forge (sha256 '3498442cf72ee7efbc4cc56553b48dbbb1a26d1d95eca4037aede69e164a9875').
Cada fase corre como funcion real: el host inyecta model_fn + receipt_fn
(patron Ricardo: la LLM produce, el recibo verifica). Sin host -> FAIL cerrado,
nunca PASS fingido. Ciclos: MAIN -> VERIFY -> RECOVERY (si falla);
CONTINUOUS se declara como trigger; META (guia) no ejecuta.
"""
from __future__ import annotations
import argparse, asyncio, hashlib, json, sys

MOTOR_ID = 'openclaw-persona-forge'
SOURCE_SHA256 = '3498442cf72ee7efbc4cc56553b48dbbb1a26d1d95eca4037aede69e164a9875'
FASES = [{'phase_id': 's001', 'title': 'When to Use', 'ciclo': 'META'}, {'phase_id': 's002', 'title': 'Avoid when', 'ciclo': 'MAIN'}, {'phase_id': 's003', 'title': '前置条件', 'ciclo': 'MAIN'}, {'phase_id': 's004', 'title': 'Skill 目录约定', 'ciclo': 'MAIN'}, {'phase_id': 's005', 'title': '内置工具', 'ciclo': 'MAIN'}, {'phase_id': 's006', 'title': '抽卡引擎（gacha.py）', 'ciclo': 'MAIN'}, {'phase_id': 's007', 'title': '可选依赖', 'ciclo': 'MAIN'}, {'phase_id': 's008', 'title': '头像自动生图：可选生图 skill', 'ciclo': 'MAIN'}, {'phase_id': 's009', 'title': '核心理念', 'ciclo': 'MAIN'}, {'phase_id': 's010', 'title': 'How It Works', 'ciclo': 'MAIN'}, {'phase_id': 's011', 'title': '触发判断', 'ciclo': 'MAIN'}, {'phase_id': 's012', 'title': 'Step 1：选方向（引导模式）', 'ciclo': 'MAIN'}, {'phase_id': 's013', 'title': 'Step 1-B：抽卡模式', 'ciclo': 'MAIN'}, {'phase_id': 's014', 'title': 'Step 2：锻造身份张力', 'ciclo': 'MAIN'}, {'phase_id': 's015', 'title': 'Step 3：推导底线规则', 'ciclo': 'MAIN'}, {'phase_id': 's016', 'title': 'Step 4：锻造名字', 'ciclo': 'MAIN'}, {'phase_id': 's017', 'title': 'Step 5：生成头像', 'ciclo': 'MAIN'}, {'phase_id': 's018', 'title': '流程', 'ciclo': 'MAIN'}, {'phase_id': 's019', 'title': 'Step 6：输出完整方案 & 生成文件', 'ciclo': 'MAIN'}, {'phase_id': 's020', 'title': '对话语气指南', 'ciclo': 'MAIN'}, {'phase_id': 's021', 'title': '原则', 'ciclo': 'MAIN'}, {'phase_id': 's022', 'title': '各步骤的语气参考（不要照抄，每次变化）', 'ciclo': 'MAIN'}, {'phase_id': 's023', 'title': 'Examples', 'ciclo': 'META'}, {'phase_id': 's024', 'title': '错误处理', 'ciclo': 'MAIN'}, {'phase_id': 's025', 'title': '注意事项', 'ciclo': 'MAIN'}, {'phase_id': 's026', 'title': '好灵魂的检验标准', 'ciclo': 'MAIN'}, {'phase_id': 's027', 'title': '避坑', 'ciclo': 'MAIN'}, {'phase_id': 's028', 'title': '何时重新调整灵魂', 'ciclo': 'MAIN'}, {'phase_id': 's029', 'title': '兼容性', 'ciclo': 'MAIN'}]


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
