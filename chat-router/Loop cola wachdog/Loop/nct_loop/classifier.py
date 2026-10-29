"""Fase 0: clasificación determinista (heurísticas locales, no modelo)."""

def classify(goal: str, tasks: list) -> dict:
    low=goal.lower()
    signals=('arquitectura','migraci','refactor','multi','integraci','sistema','backend','frontend','autentic')
    complexity=sum(w in low for w in signals)+len(tasks)
    intent='simple' if complexity < 3 else 'media' if complexity < 8 else 'compleja'
    task_type='batch' if len(tasks)>1 else 'simple' if intent=='simple' else 'complex'
    proj='frontend' if any(x in low for x in ('ui','frontend','react','botón')) else 'backend' if any(x in low for x in ('api','backend','python')) else 'general'
    return {'intent':intent,'task_type':task_type,'project_type':proj,'basis':'deterministic_heuristic'}

def choose_route(classified: dict) -> dict:
    route={'simple':'directa','batch':'batch','complex':'agentes_especializados'}[classified['task_type']]
    return {'route':route, 'mode':'continuous', 'agent_mode':'isolated_workers' if route!='directa' else 'direct',
            'ecc_loop_type':('rfc-dag' if route=='agentes_especializados' else 'sequential'),
            'max_parallel_requested': 1, 'effective_parallelism':'determined_by_existing_queue'}
