import json
import time

class EvidencePacket:
    def __init__(self, task_id: str, chat_b_id: str):
        self.data = {
            "task_id": task_id,
            "chat_b_id": chat_b_id,
            "code": [],
            "tests": [],
            "contracts": [],
            "dependencies": [],
            "quality": [],
            "traceability": [],
            "final_status": "PENDING",
            "timestamp": time.time()
        }

    def add_code(self, root_id: str, filepath: str, loc: int):
        if loc > 500:
            raise ValueError(f"CODE_BLOCK_LIMIT_EXCEEDED: {loc} > 500")
        self.data["code"].append({"root_id": root_id, "file": filepath, "loc": loc})

    def add_test(self, test_id: str, status: str, evidence: str):
        self.data["tests"].append({"test_id": test_id, "status": status, "evidence": evidence})

    def finalize(self, status: str):
        if status not in ("PASS", "PARTIAL", "FAIL"):
            raise ValueError("Estado invalido")
        self.data["final_status"] = status
        return self.data
