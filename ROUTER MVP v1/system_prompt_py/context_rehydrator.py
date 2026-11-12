from semantic_checkpoint import SemanticCheckpoint
from forensic_dlq import ForensicDLQ

class ContextRehydrator:
    def __init__(self, checkpoint: SemanticCheckpoint):
        self.checkpoint = checkpoint
        self.dlq = ForensicDLQ()

    def build_resume_brief(self, next_block: dict) -> str:
        state = self.checkpoint.state
        completed = state.get("completed_blocks", [])

        completed_summary = "\n".join(
            [f"  - {b['id']} (hash: {b['hash'][:12]}...)" for b in completed]
        ) or "  (ninguno)"

        failures = self.dlq.replay_failures()
        last_error = "Ninguno"
        if failures:
            last = failures[-1]
            last_error = f"{last.get('provider')} falló con: {last.get('error')}"

        return f"""[RESTAURACIÓN DE CONTEXTO]
Huella plan: {state.get('plan_sha256', '')[:16]}...
Bloques completados:
{completed_summary}

Último error: {last_error}
Bloque actual: {next_block['id']} - {next_block['desc']}
Límite: {next_block['max_loc']} líneas.
"""
