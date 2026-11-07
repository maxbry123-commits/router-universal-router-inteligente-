class AgentSkillsEngine:
    def __init__(self):
        self.phases = {
            "planificacion": ["Descomponer", "Requerimientos", "Arquitectura", "Definir tests"],
            "codificacion": ["Boilerplate", "Lógica", "Errores", "Refactor", "Optimizar"],
            "pruebas": ["Sandbox", "Traceback", "Auto-corregir", "Edge cases"]
        }
    def get_cascade_skills(self, phase: str = "codificacion") -> str:
        skills = self.phases.get(phase, [])
        return f"[FASE {phase.upper()}]: " + " | ".join(skills)
