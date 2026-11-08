import json
import hashlib

def decompose_task(task_description: str, max_loc: int = 200) -> dict:
    subtasks = [
        "Definir modelos de datos y esquema",
        "Crear rutas de API y validación",
        "Implementar lógica de controladores",
        "Escribir tests unitarios y de integración"
    ]
    blocks = [
        {"id": f"block_{i}", "desc": st, "max_loc": max_loc}
        for i, st in enumerate(subtasks, 1)
    ]
    plan_json = json.dumps({"task": task_description, "blocks": blocks}, sort_keys=True)
    return {
        "plan": plan_json,
        "plan_sha256": hashlib.sha256(plan_json.encode()).hexdigest(),
        "blocks": blocks
    }
