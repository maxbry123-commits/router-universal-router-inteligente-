import os
from chat_a_architect import ChatAArchitect
from chat_b_implementer import ChatBImplementer
from semantic_checkpoint import SemanticCheckpoint
from context_rehydrator import ContextRehydrator
from evidence_packet import EvidencePacket
from temp_cache import TempCache
from event_emitter import EMITTER
from contracts import MissionContract

class ChatABOrchestrator:
    def __init__(self, plan_id: str, environment: dict):
        self.plan_id = plan_id
        self.checkpoint = SemanticCheckpoint(plan_id, environment)
        self.rehydrator = ContextRehydrator(self.checkpoint)
        self.chat_a = ChatAArchitect()
        self.chat_b = ChatBImplementer()
        self.cache = TempCache()
        self.workspace = os.getenv("ORCHESTRATOR_WORKSPACE", "./workspace")
        os.makedirs(self.workspace, exist_ok=True)

    async def run(self, task_description: str):
        council = self.chat_a.ask_council(task_description)
        contract = MissionContract(council["task"], ["Python"], ["Tests passing"])

        plan = self.chat_a.decompose(task_description)
        if plan["plan_sha256"] != self.plan_id:
            self.plan_id = plan["plan_sha256"]
            self.checkpoint = SemanticCheckpoint(self.plan_id, self.checkpoint.environment)
            self.rehydrator = ContextRehydrator(self.checkpoint)

        evidence = EvidencePacket(task_id=self.plan_id, chat_b_id="auto")
        next_block = self.checkpoint.get_next(plan["blocks"])

        while next_block:
            block_id = next_block["id"]
            contract.verify_goal_lock(council["task"])

            cached = await self.cache.get(f"{self.plan_id}_{block_id}")
            if cached:
                self.checkpoint.save_block(block_id, cached)
                evidence.add_code(block_id, f"{block_id}.py", len(cached.splitlines()))
                next_block = self.checkpoint.get_next(plan["blocks"])
                continue

            resume_brief = self.rehydrator.build_resume_brief(next_block)
            try:
                code = await self.chat_b.implement(next_block, resume_brief)
                filepath = os.path.join(self.workspace, f"{block_id}.py")
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(code)

                await self.cache.set(f"{self.plan_id}_{block_id}", code)
                self.checkpoint.save_block(block_id, code)
                evidence.add_code(block_id, filepath, len(code.splitlines()))
                EMITTER.emit("block_success", {"block_id": block_id})
            except Exception as e:
                EMITTER.emit("block_fail", {"block_id": block_id, "error": str(e)})
                evidence.finalize("FAIL")
                raise RuntimeError(f"Fallo en bloque {block_id}: {e}")

            next_block = self.checkpoint.get_next(plan["blocks"])

        evidence.finalize("PASS")
        return evidence.data
