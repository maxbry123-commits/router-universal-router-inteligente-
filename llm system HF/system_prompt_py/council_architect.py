# council_architect.py
import math

class AskCouncil:
    """
    Extraído de PROMPT_MAESTRO (Sección 5: ASK COUNCIL — 12 PUNTOS).
    Chat A evalúa 12 puntos antes de aprobar la arquitectura.
    """
    POINTS = [
        "OBJECTIVE", "SCOPE", "ARCHITECTURE", "EXISTING_CODE", "DEPENDENCIES", "CONTRACTS",
        "SECURITY", "DETERMINISM", "TESTABILITY", "INTEGRATION", "TRACEABILITY", "DEFINITION_OF_DONE"
    ]

    def evaluate(self, project_analysis: dict) -> dict:
        """Simula la evaluación de los 12 puntos."""
        results = {}
        for point in self.POINTS:
            # Si falta un punto, se marca para revisión
            results[point] = project_analysis.get(point, "PENDING")
        
        decision = "AUTHORIZE" if all(v != "PENDING" for v in results.values()) else "REPLAN"
        return {"decision": decision, "evaluation": results}

class TaskDecomposition:
    """
    Extraído de PROMPT_MAESTRO (Sección 18: CODE ESTIMATION).
    Calcula cuántos Chat B se necesitan (máximo 2000 LOC).
    """
    MAX_LOC = 2000
    
    def estimate_chat_b_count(self, total_estimated_loc: int) -> int:
        if total_estimated_loc <= 0:
            return 0
        return math.ceil(total_estimated_loc / self.MAX_LOC)

    def decompose(self, tasks: list, max_loc_per_task: int = 2000) -> list:
        valid_tasks = []
        for task in tasks:
            loc = task.get("estimated_loc", 0)
            if loc > max_loc_per_task:
                raise ValueError(f"La tarea {task.get('task_id')} excede el límite de {max_loc_per_task} LOC.")
            valid_tasks.append(task)
        return valid_tasks
