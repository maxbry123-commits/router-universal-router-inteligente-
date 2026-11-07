class ECCEngine:
    def __init__(self):
        self.ecc_rules = {
            "optimizacion": {"keywords": ["optimizar", "refactorizar", "limpiar", "yagni"], "rules": ["ECC-RULE-1: Aplica YAGNI.", "ECC-RULE-2: Usa stdlib de Python."]},
            "debugging": {"keywords": ["error", "fallo", "traceback", "bug"], "rules": ["ECC-RULE-4: Lee Traceback de abajo hacia arriba.", "ECC-RULE-5: Imprime variables para verificar."]}
        }
    def load_skills_for_input(self, text: str) -> str:
        text = text.lower()
        active = []
        for spec, data in self.ecc_rules.items():
            if any(kw in text for kw in data["keywords"]):
                active.extend(data["rules"])
        return "\n".join(active) if active else "ECC-RULE-0: Código limpio."
