# chat_ab_orchestrator.py
import os
import asyncio
from chat_a_architect import decompose_task
from llm_provider_adapter import generate_code
from semantic_checkpoint import SemanticCheckpoint
from output_formatter import EvidencePacket
from event_emitter import EMITTER
from context_rehydrator import ContextRehydrator
from mode_router_v2 import route as route_mode
from temp_cache import TempCache
from gap_resolution_loop import GapResolutionLoop
from web_search_tool import WebSearchTool

class ChatABOrchestrator:
    def __init__(self, plan_id: str, environment: dict, model_family: str = "qwen2.5"):
        self.plan_id = plan_id
        self.model_family = model_family
        self.environment = environment
        self.checkpoint = SemanticCheckpoint(plan_id, environment)
        self.rehydrator = ContextRehydrator(self.checkpoint)
        self.cache = TempCache(ttl_s=3600)
        self.web_search = WebSearchTool()
        self.gap_loop = GapResolutionLoop(search_tool=self.web_search, max_rounds=3)
        self.evidence = EvidencePacket(task_id=plan_id, chat_b_id="orchestrator")
        self.workspace = os.getenv("ORCHESTRATOR_WORKSPACE", "./workspace")
        os.makedirs(self.workspace, exist_ok=True)

    def _evaluate_code(self, code: str) -> int:
        score = 0
        if "def " in code: score += 10
        if "return" in code: score += 5
        if "pass" in code: score -= 10
        if len(code.splitlines()) <= 200: score += 5
        return score

    async def run(self, task_description: str) -> dict:
        EMITTER.emit("orchestrator_start", {"task": task_description})

        mode_config = route_mode(task_description, self.model_family)
        mode_name = mode_config.get("mode", "programacion")
        mode_prompt = mode_config.get("prompt", "MODO PROGRAMACIÓN.")
        EMITTER.emit("mode_selected", {"mode": mode_name})

        plan = decompose_task(task_description, max_loc=200)
        real_plan_id = plan["plan_sha256"]

        if real_plan_id != self.plan_id:
            EMITTER.emit("plan_id_reconciled", {"old": self.plan_id, "new": real_plan_id})
            self.plan_id = real_plan_id
            self.checkpoint = SemanticCheckpoint(real_plan_id, self.environment)
            self.rehydrator = ContextRehydrator(self.checkpoint)

        next_block = self.checkpoint.get_next(plan["blocks"])

        if not next_block and not self.checkpoint.state.get("completed_blocks"):
            EMITTER.emit("orchestrator_empty", {"reason": "plan vacío"})
            self.evidence.finalize("PARTIAL")
            self.evidence.save()
            return self.evidence.data

        while next_block:
            block_id = next_block["id"]
            EMITTER.emit("block_start", {"block_id": block_id})

            cached = self.cache.get(f"{self.plan_id}_{block_id}")
            if cached:
                EMITTER.emit("cache_hit", {"block_id": block_id})
                self._persist_code(block_id, cached)
                self.checkpoint.save_block(block_id, cached)
                next_block = self.checkpoint.get_next(plan["blocks"])
                continue

            resume_brief = self.rehydrator.build_resume_brief(next_block)

            prompt = f"""
{resume_brief}

[INSTRUCCIONES DEL MODO: {mode_name.upper()}]
{mode_prompt}

[TAREA DEL BLOQUE]
{next_block['description']}
LÍMITE: Máximo {next_block['max_loc']} líneas.
Si te falta información, escribe GAP_DETECTADO: <motivo>.
"""

            try:
                async def model_call(p):
                    return await generate_code(p, model_family=self.model_family)

                raw_output = await asyncio.to_thread(
                    self.gap_loop.run_with_loop,
                    model_call_fn=lambda p: asyncio.run(model_call(p)),
                    initial_prompt=prompt
                )
            except Exception as e:
                EMITTER.emit("block_fail", {"block_id": block_id, "error": str(e)})
                self.evidence.finalize("FAIL")
                self.evidence.save()
                raise RuntimeError(f"Fallo crítico en bloque {block_id}: {e}")

            self._persist_code(block_id, raw_output)
            self.cache.set(f"{self.plan_id}_{block_id}", raw_output)
            self.checkpoint.save_block(block_id, raw_output)
            self.evidence.add_code_block(
                block_id, f"{block_id}.py",
                lines=len(raw_output.split("\n"))
            )

            next_block = self.checkpoint.get_next(plan["blocks"])

        self.evidence.finalize("PASS")
        self.evidence.save()
        EMITTER.emit("orchestrator_done", {"status": "success"})
        return self.evidence.data

    def _persist_code(self, block_id: str, code: str):
        try:
            filepath = os.path.join(self.workspace, f"{block_id}.py")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(code)
            EMITTER.emit("code_persisted", {"block_id": block_id, "path": filepath})
        except Exception as e:
            EMITTER.emit("code_persist_fail", {"block_id": block_id, "error": str(e)})
            raise
