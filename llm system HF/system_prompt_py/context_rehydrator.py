# context_rehydrator.py
import json
from typing import Optional
from semantic_checkpoint import SemanticCheckpoint
from forensic_dlq import ForensicDLQ

class ContextRehydrator:
    """
    Reconstruye el contexto para una nueva llamada tras un fallo o corte.
    Genera un 'Resume Brief' compacto para que el LLM no empiece de cero.
    """
    def __init__(self, checkpoint: SemanticCheckpoint):
        self.checkpoint = checkpoint
        self.dlq = ForensicDLQ()

    def build_resume_brief(self, next_block: dict) -> str:
        """
        Arma el prompt con toda la info recuperada.
        Se inyecta al inicio de la llamada a Chat B.
        """
        state = self.checkpoint.state
        completed = state.get("completed_blocks", [])
        
        # 1. Resumen de bloques completados
        completed_summary = "\n".join(
            [f"  - {b['id']} (hash: {b['hash'][:12]}...)" for b in completed]
        ) or "  (ninguno todavía)"

        # 2. Último error forense del DLQ
        last_error = self._get_last_error()

        # 3. Huella de integridad del plan y entorno
        plan_fingerprint = state.get("plan_sha256", "UNKNOWN")[:16]
        env_fingerprint = state.get("environment_hash", "UNKNOWN")[:16]

        # 4. Armar el brief
        brief = f"""
[RESTAURACIÓN DE CONTEXTO — NO EMPEZAR DE CERO]

Huella del plan (SHA-256): {plan_fingerprint}...
Huella del entorno:        {env_fingerprint}...
Bloques ya completados:
{completed_summary}

Bloque actual a ejecutar: {next_block['id']}
Descripción: {next_block['description']}
Límite: {next_block['max_loc']} líneas

{last_error}

[INSTRUCCIÓN]
Continúa EXACTAMENTE desde el bloque actual. NO repitas los bloques ya completados.
NO cambies el plan (su huella está anclada arriba).
Si el error anterior se resolvió con una estrategia distinta, aplícala.
Devuelve JSON: {{\"status\": \"ok\", \"code\": \"...\", \"tests\": [...]}}
"""
        return brief.strip()

    def _get_last_error(self) -> str:
        """Recupera el último error del bloque fallido, si existe."""
        failures = self.dlq.replay_failures()
        if not failures:
            return "[SIN ERRORES PREVIOS]"
        last = failures[-1]
        return f"""
[ERROR PREVIO EN {last.get('provider', 'UNKNOWN')}]
Motivo: {last.get('error', 'desconocido')}
Este es el fallo que debes evitar en esta nueva llamada.
""".strip()
