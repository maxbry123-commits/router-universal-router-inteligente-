import json
import hashlib

def decompose_task(task_description: str, max_loc: int = 200) -> dict:
    """
    Chat A: Divide la tarea en bloques lógicos de máximo 200 LOC.
    Regla estricta del sistema.
    """
    subtasks = [
        "Definir modelos de datos y esquema (<= 200 LOC)",
        "Crear rutas de API y validación (<= 200 LOC)",
        "Implementar lógica de controladores (<= 200 LOC)",
        "Escribir tests unitarios y de integración (<= 200 LOC)"
    ]
    
    blocks = [{"id": f"block_{i}", "description": st, "max_loc": max_loc} for i, st in enumerate(subtasks, 1)]
        
    plan = {"task": task_description, "blocks": blocks}
    plan_json = json.dumps(plan, sort_keys=True)
    
    return {
        "plan": plan,
        "plan_sha256": hashlib.sha256(plan_json.encode()).hexdigest(),
        "blocks": blocks
    }
