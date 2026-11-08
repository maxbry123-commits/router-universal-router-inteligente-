import os
import uuid
from chat_a_architect import ChatAArchitect
from chat_b_implementer import ChatBImplementer
from semantic_checkpoint import SemanticCheckpoint
from context_rehydrator import ContextRehydrator
from evidence_packet import EvidencePacket
from temp_cache import TempCache
from event_emitter import EMITTER
from contracts import MissionContract
from mode_router_v2 import route as route_mode
from subprocess_bridge import execute_code_safely
from agent_skills_28 import AGENT_SKILLS
from rsi_engines import RSI_ENGINES

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

    def _evaluate_code(self, code: str) -> int:
        score = 0
        if "def " in code: score += 10
        if "return" in code: score += 5
        if "pass" in code: score -= 10
        return score

    async def run(self, task_description: str):
        mode_config = route_mode(task_description)
        session_id = str(uuid.uuid4())

        council = self.chat_a.ask_council(task_description)
        contract = MissionContract(council["task"], ["Python"], ["Compila sin errores"])

        plan = self.chat_a.decompose(task_description)
        if plan["plan_sha256"] != self.plan_id:
            self.plan_id = plan["plan_sha256"]
            self.checkpoint = SemanticCheckpoint(self.plan_id, self.checkpoint.environment)
            self.rehydrator = ContextRehydrator(self.checkpoint)

        evidence = EvidencePacket(task_id=self.plan_id, chat_b_id="auto")
        next_block = self.checkpoint.get_next(plan["blocks"])

        while next_block:
            block_id = next_block["id"]

            contract.verify_goal_lock(council["task"], ["Python"])

            cached = await self.cache.get(f"{self.plan_id}_{block_id}")
            if cached:
                self.checkpoint.save_block(block_id, cached)
                evidence.add_code(block_id, f"{block_id}.py", len(cached.splitlines()))
                next_block = self.checkpoint.get_next(plan["blocks"])
                continue

            resume_brief = self.rehydrator.build_resume_brief(next_block)
            enhanced_prompt = f"[MODO: {mode_config['mode']}]\nDataset: {mode_config['dataset']}\n{resume_brief}"

            try:
                code = await self.chat_b.implement(next_block, enhanced_prompt, session_id)

                rsi_name = mode_config.get("rsi", "simpletes")
                if rsi_name in RSI_ENGINES:
                    engine = RSI_ENGINES[rsi_name](self._evaluate_code)
                    code = engine.evolve(code)

                if "analyze_code" in AGENT_SKILLS:
                    AGENT_SKILLS["analyze_code"](code)

                filepath = os.path.join(self.workspace, f"{block_id}.py")
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(code)

                test_res = execute_code_safely(["python", "-m", "py_compile", filepath], self.workspace)

                if not test_res["ok"]:
                    evidence.add_test(block_id, "FAIL", test_res["logs"])
                    EMITTER.emit("block_test_fail", {"block_id": block_id, "logs": test_res["logs"]})
                    raise RuntimeError(f"El codigo generado no compila: {test_res['logs']}")

                evidence.add_test(block_id, "PASS", "py_compile OK")
                await self.cache.set(f"{self.plan_id}_{block_id}", code)
                self.checkpoint.save_block(block_id, code)
                evidence.add_code(block_id, filepath, len(code.splitlines()))
                EMITTER.emit("block_success", {"block_id": block_id})

            except Exception as e:
                evidence.finalize("FAIL")
                raise RuntimeError(f"Fallo en {block_id}: {e}")

            next_block = self.checkpoint.get_next(plan["blocks"])

        evidence.finalize("PASS")
        return evidence.data
