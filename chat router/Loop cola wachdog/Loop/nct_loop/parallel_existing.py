"""Fan-out/fan-in OPCIONAL sobre jobs PREVIAMENTE CLAIMED por scheduler existente.
NO es scheduler/DAG, NO posee cola, NO inventa claims ni lock distribuido.
El host garantiza idempotencia, scopes y lease; concurrencia real opt-in.
"""
import asyncio
from .contracts import NCTError

async def fanout_claimed(existing_queue, claimed_jobs:list[dict], action_by_id:dict,
                         *, max_parallel:int=4)->list[dict]:
    if not isinstance(max_parallel,int) or not (1<=max_parallel<=100):
        raise NCTError('max_parallel debe ser 1..100')
    if len(claimed_jobs)>100:raise NCTError('lote excede 100 jobs')
    seen=set(); resources=set()
    for claim in claimed_jobs:
        if not isinstance(claim,dict) or claim.get('claim_status')!='CLAIMED':
            raise NCTError('sin claim del scheduler EXISTENTE')
        ident=claim.get('task_id')
        if not isinstance(ident,str) or ident not in action_by_id or ident in seen:
            raise NCTError('task_id ausente/no permitido/duplicado')
        if not isinstance(claim.get('lease_id'),str) or not claim['lease_id']:
            raise NCTError('lease del scheduler ausente')
        keys=claim.get('resource_keys',[])
        if not isinstance(keys,list) or any(not isinstance(k,str) or not k for k in keys):
            raise NCTError('resource_keys inválidas')
        if resources.intersection(keys):
            raise NCTError('colisión de recursos: no despachar en paralelo')
        resources.update(keys);seen.add(ident)
    sem=asyncio.Semaphore(max_parallel)
    async def execute(job):
        async with sem:
            return await existing_queue.submit_and_wait(job,action_by_id[job['task_id']])
    results=await asyncio.gather(*(execute(x) for x in claimed_jobs),return_exceptions=True)
    return [{'task_id':job['task_id'], 'ok':not isinstance(r,BaseException),
             'result':str(r)[:200] if isinstance(r,BaseException) else r}
            for job,r in zip(claimed_jobs,results)]
