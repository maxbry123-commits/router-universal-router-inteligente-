import os
import json
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

class ChatABOrchestrator:
    def __init__(self, plan_id: str, environment: dict):
        self.plan_id = plan_id
        self.checkpoint = SemanticCheckpoint(plan_id, environment)
        self.rehydrator = ContextRehydrator(self.checkpoint)
        self.chat_a = ChatAArchitect()
        self.chat_b = ChatBImplementer()
        self.cache = TempCache()
        self.workspace = os.path.abspath(os.getenv("ORCHESTRATOR_WORKSPACE", "./workspace"))
        os.makedirs(self.workspace, exist_ok=True)

    @staticmethod
    def _payload(result: dict) -> str:
        if result["type"] == "code":
            return result["code"]
        return json.dumps(result, ensure_ascii=False)

    async def run(self, task_description: str):
        mode_config = route_mode(task_description)
        session_id = str(uuid.uuid4())

        self.checkpoint.verify_objective(task_description)
        plan = self.chat_a.decompose(task_description)
        self.checkpoint.lock_objective(task_description)

        council = self.chat_a.ask_council(task_description)
        EMITTER.emit("council_evaluated", council)
        contract = MissionContract(council["task"], plan["plan_sha256"], ["Python"], ["pytest OK"])

        evidence = EvidencePacket(task_id=self.plan_id, chat_b_id="auto")
        next_block = self.checkpoint.get_next(plan["blocks"])

        while next_block:
            block_id = next_block["id"]
            self.checkpoint.verify_objective(task_description)
            contract.verify_goal_lock(task_description, plan["plan_sha256"], ["Python"])

            cached = await self.cache.get(f"{self.plan_id}_{block_id}")
            if cached:
                self.checkpoint.save_block(block_id, self._payload(cached))
                evidence.add_code(block_id, f"{block_id}.py", len(cached["code"].splitlines()))
                next_block = self.checkpoint.get_next(plan["blocks"])
                continue

            resume_brief = self.rehydrator.build_resume_brief(next_block)
            enhanced_prompt = f"[MODO: {mode_config['mode']}]\nDataset: {mode_config['dataset']}\n{resume_brief}"

            try:
                result = await self.chat_b.implement(next_block, enhanced_prompt, session_id)

                if result["type"] == "code":
                    code = result["code"]
                    tests = result.get("tests", "")
                    filepath = os.path.abspath(os.path.join(self.workspace, f"{block_id}.py"))
                    testpath = os.path.abspath(os.path.join(self.workspace, f"test_{block_id}.py"))
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(code)
                    with open(testpath, "w", encoding="utf-8") as f:
                        f.write(f"from {block_id} import *\n\n{tests}")
                    test_res = execute_code_safely(["python", "-m", "pytest", testpath], self.workspace)
                    if not test_res["ok"]:
                        evidence.add_test(block_id, "FAIL", test_res["logs"])
                        raise RuntimeError(f"El codigo no pasa los tests: {test_res['logs']}")
                    evidence.add_test(block_id, "PASS", "pytest OK")
                    await self.cache.set(f"{self.plan_id}_{block_id}", result)
                    self.checkpoint.save_block(block_id, code)
                    evidence.add_code(block_id, filepath, len(code.splitlines()))
                    EMITTER.emit("block_success", {"block_id": block_id})

                elif result["type"] == "tool_result":
                    tool_out = result["result"]
                    if tool_out.get("status") == "failed" or "error" in tool_out:
                        evidence.add_test(block_id, "FAIL", json.dumps(tool_out, ensure_ascii=False)[:2000])
                        raise RuntimeError(f"Herramienta {result['tool']} fallo: {tool_out.get('error', 'sin detalle')}")
                    evidence.add_test(block_id, "PASS", f"tool {result['tool']} OK")
                    EMITTER.emit("tool_executed", {"block_id": block_id, "tool": result["tool"]})
                    self.checkpoint.save_block(block_id, self._payload(result))

                else:
                    raise RuntimeError(f"Tipo de resultado no soportado: {result['type']}")

            except Exception as e:
                evidence.finalize("FAIL")
                raise RuntimeError(f"Fallo en {block_id}: {e}")

            next_block = self.checkpoint.get_next(plan["blocks"])

        evidence.finalize("PASS")
        return evidence.data
