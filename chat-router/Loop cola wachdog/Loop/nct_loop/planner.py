"""Fase 2: contrato de unidades y puentes al DAG existente, NO scheduler."""
from .contracts import WorkUnit, NCTError, stable_hash

def parse_tasks(document: dict, *, known_blocks: set[str], known_ops: set[str]) -> list[WorkUnit]:
    if not isinstance(document,dict) or not isinstance(document.get('units'),list): raise NCTError('falta units')
    if not 1 <= len(document['units']) <= 50: raise NCTError('1..50 unidades por misión')
    tasks=[]
    for x in document['units']:
        if not isinstance(x,dict): raise NCTError('unidad no es objeto')
        unit=WorkUnit(**x)
        unit.validate()
        if unit.block not in known_blocks: raise NCTError('bloque NO CONECTADO: '+unit.block)
        if set(unit.allowed_ops)-known_ops: raise NCTError('operaciones no permitidas')
        tasks.append(unit)
    ids=[t.id for t in tasks]
    if len(set(ids))!=len(ids): raise NCTError('id duplicado')
    edges={t.id:t.depends_on for t in tasks}
    if any(d not in edges for t in tasks for d in t.depends_on): raise NCTError('dependencia inexistente')
    visited, active=set(),set()
    def visit(node):
        if node in active: raise NCTError('ciclo DAG')
        if node in visited:return
        active.add(node)
        for dep in edges[node]:visit(dep)
        active.remove(node);visited.add(node)
    for t in tasks:visit(t.id)
    return tasks

def to_existing_dag_payload(task: WorkUnit, mission_id: str, plan_sha: str) -> dict:
    """Contrato de intercambio; conectar con el formato real del DAG antes de usar en producción."""
    return {'task_id':task.id,'mission_id':mission_id,'depends_on':task.depends_on,
            'priority':task.priority,'block':task.block,'idempotency_key':stable_hash([mission_id,plan_sha,task.id]),
            'goal':task.goal,'acceptance':task.acceptance,'allowed_ops':task.allowed_ops}


def for_existing_dag_handoff(tasks: list[WorkUnit]) -> list[WorkUnit]:
    """Orden estable SOLO para demo serial. NO reclama jobs ni asigna workers.
    El scheduler/DAG REAL es la autoridad en producción.
    """
    table={t.id:t for t in tasks};visited=set(); result=[]
    def append(t):
        if t.id in visited:return
        for dep in t.depends_on:append(table[dep])
        visited.add(t.id);result.append(t)
    for t in tasks:append(t)
    return result
