import json
import hashlib

class ChatAArchitect:
    def ask_council(self, task: str) -> dict:
        points = [
            "OBJECTIVE", "SCOPE", "ARCHITECTURE", "REUSE",
            "DEPENDENCIES", "CONTRACTS", "SECURITY", "DETERMINISM",
            "TESTABILITY", "INTEGRATION", "TRACEABILITY", "DONE"
        ]
        return {
            "decision": "AUTHORIZE",
            "task": task,
            "council_points": points
        }

    def decompose(self, task: str, max_loc: int = 200) -> dict:
        subtasks = [
            {"id": "block_1", "desc": f"Definir modelos para {task}", "max_loc": max_loc},
            {"id": "block_2", "desc": f"Crear rutas y controladores para {task}", "max_loc": max_loc},
            {"id": "block_3", "desc": f"Escribir tests para {task}", "max_loc": max_loc}
        ]
        plan_json = json.dumps(subtasks, sort_keys=True)
        return {
            "plan_sha256": hashlib.sha256(plan_json.encode()).hexdigest(),
            "blocks": subtasks
        }
