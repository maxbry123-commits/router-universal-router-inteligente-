# output_formatter.py
import json
import time

class EvidencePacket:
    """
    Chat B debe generar este paquete para probar que cumplió.
    Extraído del PROMPT_MAESTRO (Sección 29: EVIDENCE_PACKET).
    """
    def __init__(self, task_id: str, chat_b_id: str):
        self.task_id = task_id
        self.chat_b_id = chat_b_id
        self.data = {
            "task_id": task_id,
            "chat_b_id": chat_b_id,
            "code": [],
            "tests": [],
            "contracts": [],
            "dependencies": [],
            "quality": [],
            "traceability": [],
            "acceptance": [],
            "final_status": "PENDING",
            "timestamp": time.time()
        }

    def add_code_block(self, root_id: str, filepath: str, lines: int):
        self.data["code"].append({"root_id": root_id, "file": filepath, "actual_loc": lines})

    def add_test_result(self, test_id: str, status: str, evidence: str):
        self.data["tests"].append({"test_id": test_id, "status": status, "evidence": evidence})

    def finalize(self, status: str):
        """PASS, PARTIAL o FAIL"""
        if status not in ("PASS", "PARTIAL", "FAIL"):
            raise ValueError("Estado inválido. Debe ser PASS, PARTIAL o FAIL.")
        self.data["final_status"] = status
        return self.data

    def save(self, filepath: str = "08_EVIDENCE_PACKET.json"):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)
        return filepath
