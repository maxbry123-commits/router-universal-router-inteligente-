# security_gates.py
import json
import hashlib
from enum import Enum

class Verdict(str, Enum):
    GO = "GO"
    NO_GO = "NO_GO"

class SheriffVerdict:
    def __init__(self, verdict: Verdict, reason: str = ""):
        self.verdict = verdict
        self.reason = reason

class Sheriff:
    """
    Extraído de execution_pipeline_dsl.py.
    Tiene 6 gates de validación.
    """
    def validate(self, output: dict, gate: str, state) -> SheriffVerdict:
        if gate == "completitud":
            if not isinstance(output, dict) or not output:
                return SheriffVerdict(Verdict.NO_GO, "Output vacío")
            if output.get("status") not in ("ok", "completed", "success"):
                return SheriffVerdict(Verdict.NO_GO, "status no válido")
            return SheriffVerdict(Verdict.GO, "completitud_ok")
        
        if gate == "coherencia":
            if "tasks" in output and not isinstance(output["tasks"], list):
                return SheriffVerdict(Verdict.NO_GO, "'tasks' debe ser lista")
            return SheriffVerdict(Verdict.GO, "coherencia_ok")
            
        return SheriffVerdict(Verdict.NO_GO, f"Gate '{gate}' no definido")

class OCRCHecker:
    def hash_doc(self, doc_path: str) -> str:
        try:
            with open(doc_path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return "UNREADABLE"

    def verify_completitud(self, start_hashes: dict, end_hashes: dict) -> dict:
        results = {}
        for doc in start_hashes:
            if start_hashes[doc] != end_hashes.get(doc):
                results[doc] = {"complete": False, "reason": "hash_mismatch"}
            else:
                results[doc] = {"complete": True}
        return results

class Judge:
    """
    Extraído de execution_pipeline_dsl.py.
    Hace 3 simulaciones antes de dar PASS.
    """
    def run_simulations(self, output: dict) -> dict:
        results = {
            "real": self._simulate_real(output),
            "adversarial": self._simulate_adversarial(output)
        }
        return results

    def _simulate_real(self, output: dict) -> dict:
        if "status" not in output or output["status"] not in ("ok", "success"):
            return {"verdict": "NO_GO", "reason": "fallo_real"}
        return {"verdict": "GO", "reason": "real_pasa"}

    def _simulate_adversarial(self, output: dict) -> dict:
        blob = json.dumps(output, default=str)
        for token in ("TODO", "FIXME", "UNREADABLE"):
            if token in blob:
                return {"verdict": "NO_GO", "reason": f"placeholder:{token}"}
        return {"verdict": "GO", "reason": "adversarial_pasa"}
