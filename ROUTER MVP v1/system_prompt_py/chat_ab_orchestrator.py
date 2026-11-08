import os
import uuid
from chat_a_architect import ChatAArchitect
from chat_b_implementer import ChatBImplementer, IncompleteResponse
from semantic_checkpoint import SemanticCheckpoint
from context_rehydrator import ContextRehydrator
from evidence_packet import EvidencePacket
from event_emitter import EMITTER
from mode_router_v2 import route as route_mode
from subprocess_bridge import execute_code_safely
from agentic_loop_controller import AgenticLoopController
from deduplication_layer import DeduplicationLayer
from temp_cache import TempCache
from code_splitter import split_code, NodeTooLargeError
from loc_limits import MAX_BLOCK_LOC

MAX_ROUNDS = 3

class ChatABOrchestrator:
    def __init__(self, plan_id: str, environment: dict):
        self.plan_id = plan_id
        self.checkpoint = SemanticCheckpoint(plan_id, environment)
        self.rehydrator = ContextRehydrator(self.checkpoint)
        self.chat_a = ChatAArchitect()
        self.chat_b = ChatBImplementer()
        self.cache = TempCache()
        self.dedup = DeduplicationLayer(self.cache)
        self.workspace = os.path.abspath(os.getenv('ORCHESTRATOR_WORKSPACE', './workspace'))
        os.makedirs(self.workspace, exist_ok=True)

    def _write(self, name: str, text: str) -> str:
        path = os.path.abspath(os.path.join(self.workspace, f"{name}.py"))
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)
        return path

    def _materialize(self, block_id: str, code: str) -> tuple:
        split = split_code(code, MAX_BLOCK_LOC, block_id)
        names = []
        for name, text in split["parts"]:
            self._write(name, text)
            names.append(name)
        if split["aggregator"]:
            self._write(split["aggregator"][0], split["aggregator"][1])
            self.checkpoint.save_parts(block_id, names)
        return split, names

    def _record(self, evidence, block_id: str, split: dict):
        for name, text in split['parts']:
            evidence.add_code(block_id, os.path.join(self.workspace, f'{name}.py'), len(text.splitlines()))

    async def run(self, task_description: str):
        mode_config = route_mode(task_description)
        session_id = str(uuid.uuid4())

        council = self.chat_a.ask_council(task_description)
        EMITTER.emit('council_evaluated', council)

        plan = self.chat_a.decompose(task_description)
        self.checkpoint.verify_objective(task_description)
        self.checkpoint.lock_objective(task_description)

        evidence = EvidencePacket(task_id=self.plan_id, chat_b_id='auto')
        next_block = self.checkpoint.get_next(plan['blocks'])

        while next_block:
            block_id = next_block['id']
            self.checkpoint.verify_objective(task_description)
            source = f"{self.plan_id}:{block_id}"

            is_dup, cached_code = await self.dedup.check_and_store(task_description, source)
            if is_dup:
                self.checkpoint.save_block(block_id, cached_code)
                self._record(evidence, block_id, split_code(cached_code, MAX_BLOCK_LOC, block_id))
                EMITTER.emit('dedup_hit', {'block_id': block_id})
                next_block = self.checkpoint.get_next(plan['blocks'])
                continue

            resume_brief = self.rehydrator.build_resume_brief(next_block)
            enhanced_prompt = f"[MODO: {mode_config['mode']}]\n{resume_brief}"
            loop_ctrl = AgenticLoopController(max_rounds=MAX_ROUNDS)
            done = False

            try:
                while loop_ctrl.can_continue() and not done:
                    partial = self.checkpoint.get_partial(block_id)
                    try:
                        result = await self.chat_b.implement(next_block, enhanced_prompt, session_id, partial=partial)
                    except IncompleteResponse as ie:
                        self.checkpoint.save_partial(block_id, ie.partial)
                        raise RuntimeError(f"respuesta incompleta guardada como parcial ({len(ie.partial.splitlines())} lineas); se retomara al reintentar")
                    loop_ctrl.register_round()

                    if result['type'] == 'code':
                        code = result['code']
                        split, names = self._materialize(block_id, code)
                        testpath = self._write(f"test_{block_id}", f"from {block_id} import *\n\n{result.get('tests', '')}")
                        test_res = execute_code_safely(['python', '-m', 'pytest', testpath], self.workspace)
                        if not test_res['ok']:
                            evidence.add_test(block_id, 'FAIL', test_res['logs'])
                            raise RuntimeError(f"Fallo tests: {test_res['logs']}")
                        evidence.add_test(block_id, 'PASS', f'pytest OK ({len(names)} parte(s))')
                        self.checkpoint.save_block(block_id, code)
                        self.checkpoint.clear_partial(block_id)
                        await self.dedup.store_response(task_description, source, code)
                        self._record(evidence, block_id, split)
                        EMITTER.emit('block_success', {'block_id': block_id, 'partes': names})
                        done = True

                    elif result['type'] == 'tool_result':
                        tool_out = result['result']
                        if tool_out.get('status') == 'failed' or 'error' in tool_out:
                            raise RuntimeError(f"Herramienta {result['tool']} fallo: {tool_out.get('error', 'sin detalle')}")
                        if loop_ctrl.is_repeated_call(result['tool'], str(result['args'])):
                            raise RuntimeError(f"Llamada repetida a {result['tool']} con los mismos argumentos")
                        EMITTER.emit('tool_executed', {'block_id': block_id, 'tool': result['tool']})
                        enhanced_prompt += f"\n[RESULTADO HERRAMIENTA {result['tool']}]\n{tool_out}"

                    else:
                        raise RuntimeError(f"Tipo de resultado no soportado: {result['type']}")

                if not done:
                    raise RuntimeError(f"rondas agotadas sin codigo ({MAX_ROUNDS})")

            except (NodeTooLargeError, Exception) as e:
                evidence.finalize('FAIL')
                raise RuntimeError(f'Fallo en {block_id}: {e}')

            next_block = self.checkpoint.get_next(plan['blocks'])

        evidence.finalize('PASS')
        return evidence.data
