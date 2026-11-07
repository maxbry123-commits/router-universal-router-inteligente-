# chat_ab_orchestrator.py
import json
from chat_a_architect import decompose_task
from llm_provider_adapter import generate_code
from semantic_checkpoint import SemanticCheckpoint
from event_emitter import EMITTER
from output_formatter import EvidencePacket

class ChatABOrchestrator:
    """
    Orquesta el flujo Chat A (Arquitecto) -> Chat B (Programador).
    Aplica el límite estricto de 200 LOC.
    """
    def __init__(self, plan_id: str, environment: dict):
        self.checkpoint = SemanticCheckpoint(plan_id, environment)
        self.evidence = EvidencePacket(task_id=plan_id, chat_b_id="orchestrator")

    def run(self, task_description: str, all_blocks: list):
        """
        Ejecuta la tarea completa dividiéndola en bloques.
        """
        EMITTER.emit("orchestrator_start", {"task": task_description})
        
        # 1. Chat A divide la tarea (Máximo 200 LOC por bloque)
        plan = decompose_task(task_description, max_loc=200)
        self.evidence.add_code_block("plan", "plan.json", lines=len(plan["plan"].split("\n")))
        
        # 2. Recuperar el bloque por el que vamos (Checkpoint)
        next_block = self.checkpoint.get_next(plan["blocks"])
        if not next_block:
            EMITTER.emit("orchestrator_done", {"reason": "all_blocks_completed"})
            self.evidence.finalize("PASS")
            return self.evidence.data

        # 3. Chat B implementa el bloque
        while next_block:
            block_id = next_block["id"]
            EMITTER.emit("block_start", {"block_id": block_id})
            
            prompt = f"""
            Eres Chat B. Escribe el código para la siguiente tarea.
            Tarea: {next_block['description']}
            LÍMITE ESTRICTO: Máximo {next_block['max_loc']} líneas de código.
            Devuelve ÚNICAMENTE un JSON con el formato:
            {{\"status\": \"ok\", \"code\": \"tu código aquí\", \"tests\": [\"test1\", \"test2\"]}}
            """
            
            try:
                # Llama al adaptador (que maneja fallos, limites y validacion)
                generated_code = generate_code(prompt)
                
                # Guardar Checkpoint con huella digital
                self.checkpoint.save_block(block_id, generated_code)
                self.evidence.add_code_block(block_id, f"{block_id}.py", lines=len(generated_code.split("\n")))
                EMITTER.emit("block_success", {"block_id": block_id})
                
            except Exception as e:
                EMITTER.emit("block_fail", {"block_id": block_id, "error": str(e)})
                # El orquestador se detiene aquí. El sistema de recuperación (Paso 1) ya guardó la DLQ.
                self.evidence.finalize("FAIL")
                raise RuntimeError(f"Fallo crítico en bloque {block_id}: {e}")
            
            # 4. Pasar al siguiente bloque
            next_block = self.checkpoint.get_next(plan["blocks"])
            
        self.evidence.finalize("PASS")
        EMITTER.emit("orchestrator_done", {"status": "success"})
        return self.evidence.data
