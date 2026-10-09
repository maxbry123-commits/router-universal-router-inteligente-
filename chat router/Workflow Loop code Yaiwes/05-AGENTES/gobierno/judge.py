"""Judge — verificador final determinista (doc 23, nivel 8).

NO es una LLM: es código. Decide PASS / REVISE / BLOCK.
BLOCK si la evidencia trae unauthorized_change.
"""
from __future__ import annotations


class Judge:
    """Aplica reglas de cierre sobre tarea + evidencia + revisiones duales."""

    def decide(
        self,
        task: dict,
        evidence: dict,
        hermes_review: dict,
        openclaw_review: dict,
    ) -> str:
        if evidence and evidence.get("unauthorized_change"):
            return "BLOCK"

        if not evidence:
            return "REVISE"

        if evidence.get("status") != "PASS":
            return "REVISE"

        if not evidence.get("tests"):
            return "REVISE"

        if not hermes_review.get("approve"):
            return "REVISE"

        if not openclaw_review.get("approve"):
            return "REVISE"

        return "PASS"
