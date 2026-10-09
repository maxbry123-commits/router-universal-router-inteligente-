"""Sheriff — gate determinista de políticas (doc 23, nivel 3).

NO es una LLM: es código. Reglas:
- toda tarea debe tener criterio de aceptación
- las dependencias deben existir en el plan
- rutas prohibidas: absolutas, con '..', '.github/', 'router inteligente universal/'
"""
from __future__ import annotations

RUTAS_PROHIBIDAS = (".github/", "router inteligente universal/")


class Sheriff:
    """Valida reglas y permisos sobre un plan {'tasks': [...]}."""

    def validate(self, plan: dict) -> tuple[bool, str]:
        tasks = plan.get("tasks", [])
        if not tasks:
            return False, "plan sin tareas"

        ids = {t.get("id") for t in tasks}

        for task in tasks:
            if not task.get("acceptance"):
                return False, f"{task.get('id')} sin criterio de aceptación"

            for dep in task.get("dependencies", []):
                if dep not in ids:
                    return False, f"Dependencia inválida: {dep}"

            for path in task.get("allowed_paths", []):
                if path.startswith("/"):
                    return False, "Ruta absoluta no autorizada"
                if ".." in path:
                    return False, "Path traversal bloqueado"
                for prohibida in RUTAS_PROHIBIDAS:
                    if path.startswith(prohibida):
                        return False, f"Ruta prohibida: {prohibida}"

        return True, "PASS"
