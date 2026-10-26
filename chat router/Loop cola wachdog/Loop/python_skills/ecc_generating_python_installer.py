"""Motor Python ejecutable del skill ECC: 'generating-python-installer'.
Generado desde skills/generating-python-installer/SKILL.md (sha256 '47e73ef601d900be3b5ccb5d1a1ba2371d3e46c67b5243c1810e51cd2d8f62f3').
Cada fase corre como funcion real: el host inyecta model_fn + receipt_fn
(patron Ricardo: la LLM produce, el recibo verifica). Sin host -> FAIL cerrado,
nunca PASS fingido. Ciclos: MAIN -> VERIFY -> RECOVERY (si falla);
CONTINUOUS se declara como trigger; META (guia) no ejecuta.
"""
from __future__ import annotations
import argparse, asyncio, hashlib, json, sys

SKILL_ID = 'generating-python-installer'
SOURCE_SHA256 = '47e73ef601d900be3b5ccb5d1a1ba2371d3e46c67b5243c1810e51cd2d8f62f3'
FASES = [{'phase_id': 's001', 'title': 'When to Activate', 'ciclo': 'META'}, {'phase_id': 's002', 'title': 'How It Works', 'ciclo': 'MAIN'}, {'phase_id': 's003', 'title': 'Examples', 'ciclo': 'META'}, {'phase_id': 's004', 'title': '核心理念', 'ciclo': 'MAIN'}, {'phase_id': 's005', 'title': '实战参考案例（生产级 PySide2 桌面应用，323 MB，含 OpenCV / Playwright）', 'ciclo': 'MAIN'}, {'phase_id': 's006', 'title': '项目概况', 'ciclo': 'MAIN'}, {'phase_id': 's007', 'title': '关键优化策略', 'ciclo': 'MAIN'}, {'phase_id': 's008', 'title': '体积分布', 'ciclo': 'MAIN'}, {'phase_id': 's009', 'title': '预期效果对比', 'ciclo': 'MAIN'}, {'phase_id': 's010', 'title': '核心工作流 (Workflow) - WARNING: 严格执行', 'ciclo': 'MAIN'}, {'phase_id': 's011', 'title': 'Nuitka 极限优化编译（基于 参考项目经验）', 'ciclo': 'MAIN'}, {'phase_id': 's012', 'title': '一、32 位 vs 64 位选择策略', 'ciclo': 'MAIN'}, {'phase_id': 's013', 'title': '二、模块排除清单（参考项目验证过的）', 'ciclo': 'MAIN'}, {'phase_id': 's014', 'title': '三、GUI 框架专用优化', 'ciclo': 'MAIN'}, {'phase_id': 's015', 'title': '四、一键编译脚本模板', 'ciclo': 'MAIN'}, {'phase_id': 's016', 'title': '五、dist 瘦身脚本（参考项目级别清理）', 'ciclo': 'MAIN'}, {'phase_id': 's017', 'title': '六、DLL 依赖分析工具', 'ciclo': 'MAIN'}, {'phase_id': 's018', 'title': '完整优化工作流', 'ciclo': 'MAIN'}, {'phase_id': 's019', 'title': '步骤 1：修改编译脚本配置', 'ciclo': 'MAIN'}, {'phase_id': 's020', 'title': '步骤 2：一键编译+瘦身', 'ciclo': 'MAIN'}, {'phase_id': 's021', 'title': '步骤 3：分析 DLL 依赖', 'ciclo': 'MAIN'}, {'phase_id': 's022', 'title': '步骤 4：根据分析结果优化', 'ciclo': 'MAIN'}, {'phase_id': 's023', 'title': 'VC++ 运行库处理方案', 'ciclo': 'MAIN'}, {'phase_id': 's024', 'title': '方案一：静态链接（推荐）', 'ciclo': 'MAIN'}, {'phase_id': 's025', 'title': '方案二：捆绑运行库安装（商业发布推荐）', 'ciclo': 'MAIN'}, {'phase_id': 's026', 'title': 'Inno Setup 脚本模板（商业终极版）', 'ciclo': 'META'}, {'phase_id': 's027', 'title': '占位符说明', 'ciclo': 'MAIN'}, {'phase_id': 's028', 'title': '常见问题 (FAQ)', 'ciclo': 'META'}, {'phase_id': 's029', 'title': 'Q1: 安装后双击程序无反应？', 'ciclo': 'MAIN'}, {'phase_id': 's030', 'title': 'Q2: 安装包体积过大？', 'ciclo': 'MAIN'}, {'phase_id': 's031', 'title': 'Q3: 杀毒软件误报？', 'ciclo': 'MAIN'}, {'phase_id': 's032', 'title': 'Q4: 安装时提示 Windows 已保护你的电脑？', 'ciclo': 'MAIN'}, {'phase_id': 's033', 'title': '实战问题处理记录（更新 2026-02-07）', 'ciclo': 'MAIN'}, {'phase_id': 's034', 'title': '优化效果预期', 'ciclo': 'MAIN'}]


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
