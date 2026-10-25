"""Ejemplo de INYECCIÓN, no ejecutable sin callbacks reales verificables.
NO crea router, scheduler ni memoria nuevos. Claude/Grok debe resolver interfaces.
"""
from nct_loop.ports import ExistingQueueHooks,ExistingMemoryHooks,ExistingModelHooks
from nct_loop.engine import NCTLoopEngine
from nct_loop.ecc_runtime import ECCCodeRuntime
from pathlib import Path

# Los callbacks son pseudofirmas que SE DEBEN adaptar al sistema real.
# async def existing_queue_submit_wait(work_unit, coro_factory): ...
# async def existing_memory_load(mission_id): ...
# async def existing_memory_save(mission_id, checkpoint): ...
# async def existing_model_call(block_id, stage_payload): ...
# async def existing_authorized_tools_run(meta_ops, task_id): ...
# async def existing_independent_checker(work_unit, receipts): ...

async def build_engine(callbacks, *, approved_ops, block_ids, root:Path):
    class ToolBridge:
        async def execute(self, validated_ops, task_id):
            return await callbacks['authorized_tools_run'](validated_ops,task_id)
    class CheckBridge:
        async def check(self, task, receipts):
            return await callbacks['independent_checker'](task,receipts)
    return NCTLoopEngine(
        ecc=ECCCodeRuntime(root/'config/ecc_rules.json'),
        model=ExistingModelHooks(callbacks['model_call']),
        queue=ExistingQueueHooks(callbacks['queue_submit_and_wait']),
        memory=ExistingMemoryHooks(callbacks['memory_load'],callbacks['memory_save']),
        tools=ToolBridge(),checker=CheckBridge(),
        resources_file=root/'config/resources.json',
        known_blocks=set(block_ids),approved_ops=set(approved_ops))
