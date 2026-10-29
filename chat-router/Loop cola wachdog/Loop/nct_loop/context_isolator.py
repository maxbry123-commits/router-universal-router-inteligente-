"""Fase 3: contexto mínimo, pertenencia a task_id y lista permitida."""
from .contracts import NCTError, stable_hash

def isolated_context(*, mission_id: str, unit, prior_receipts: list[dict], memory: dict|None,
                     phase_rules: list[dict], resources: list[dict]) -> dict:
    own=[{'task_id':r.get('task_id'),'id':r.get('id'),'status':r.get('status'),
          'sha':stable_hash(r.get('evidence',{}))} for r in prior_receipts if r.get('task_id') in unit.depends_on]
    context={'mission_id':mission_id,'task_id':unit.id,'goal':unit.goal,'scope':unit.scope,
             'allowed_ops':unit.allowed_ops,'acceptance':unit.acceptance,'dependency_receipts':own,
             'phase_invariants':phase_rules,'suggested_resources':resources,
             'memory_excerpt': (memory or {}).get('summary','')[:2000]}
    if len(str(context))>24000:raise NCTError('presupuesto de contexto excedido')
    return context
