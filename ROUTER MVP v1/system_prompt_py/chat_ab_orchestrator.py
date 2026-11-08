import uuid
import os
from chat_a_architect import decompose_task
from chat_b_implementer import implement_block
from semantic_checkpoint import SemanticCheckpoint
from context_rehydrator import ContextRehydrator
from temp_cache import TempCache
from event_emitter import EMITTER

class ChatABOrchestrator:
    def __init__(self, plan_id: str, environment: dict, model_family: str = "qwen2.5"):
        self.plan_id = plan_id
        self.model_family = model_family
        self.checkpoint = SemanticCheckpoint(plan_id, environment)
        self.rehydrator = ContextRehydrator(self.checkpoint)
        self.cache = TempCache()
        self.workspace = os.getenv("ORCHESTRATOR_WORKSPACE", "./workspace")
        os.makedirs(self.workspace, exist_ok=True)

    async def run(self, task_description: str):
        plan = decompose_task(task_description)
        if plan["plan_sha256"] != self.plan_id:
            self.plan_id = plan["plan_sha256"]
            self.checkpoint = SemanticCheckpoint(self.plan_id, self.checkpoint.environment)
            self.rehydrator = ContextRehydrator(self.checkpoint)

        next_block = self.checkpoint.get_next(plan["blocks"])

        while next_block:
            block_id = next_block["id"]
            cached = await self.cache.get(f"{self.plan_id}_{block_id}")
            if cached:
                self.checkpoint.save_block(block_id, cached)
                next_block = self.checkpoint.get_next(plan["blocks"])
                continue

            resume_brief = self.rehydrator.build_resume_brief(next_block)
            prompt = f"{resume_brief}\n\nINSTRUCCIONES: Escribe el código sin explicaciones."

            try:
                code = await implement_block(next_block, self.model_family)
                filepath = os.path.join(self.workspace, f"{block_id}.py")
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(code)

                await self.cache.set(f"{self.plan_id}_{block_id}", code)
                self.checkpoint.save_block(block_id, code)
                EMITTER.emit("block_success", {"block_id": block_id})
            except Exception as e:
                EMITTER.emit("block_fail", {"block_id": block_id, "error": str(e)})
                raise RuntimeError(f"Fallo en bloque {block_id}: {e}")

            next_block = self.checkpoint.get_next(plan["blocks"])

        return {"status": "PASS", "plan_id": self.plan_id}
