"""Repara orden crítico de CODA: RED -> IMPLEMENT -> GREEN/REVISION.

Es subclase OPT-IN de NCTLoopEngine; no modifica engine.py anterior.
Reusa cola, memoria, verificador y herramientas existentes mediante puertos.
"""
from __future__ import annotations
import json
from .engine import NCTLoopEngine
from .contracts import Receipt,NCTError,stable_hash
from .ecc_actions import ECCActionDispatcher

class StagedECCActions(ECCActionDispatcher):
    """Dedupe por tarea+acción dentro de la invocación (no sustituye cola durable)."""
    def __init__(self,executor_port,*,approved_actions):
        super().__init__(executor_port,approved_actions=approved_actions)
        self.finished={}

    async def execute_action(self,req:dict)->dict:
        key=(req['task_id'],req['operation'])
        if key in self.finished:return self.finished[key]
        if req['operation'] not in self.approved:raise NCTError('OP_NOT_APPROVED')
        result=await self.executor.run_approved_action(req)
        if not isinstance(result,dict) or result.get('request_id')!=req['request_id']:
            raise NCTError('ECC recibo sin correlación')
        if result.get('status')!='PASS' or not result.get('receipt_id'):
            raise NCTError('ECC_ACTION_FAILED '+req['operation'])
        if req['operation']=='run_approved_red_tests' and result.get('observed_failure') is not True:
            raise NCTError('TDD_RED_NOT_CONFIRMED')
        if req['operation']=='run_approved_green_tests' and result.get('observed_pass') is not True:
            raise NCTError('TDD_GREEN_NOT_CONFIRMED')
        ev={'status':'PASS','receipt_id':result['receipt_id'],'source_ecc':req['source_ecc'],
            'operation':req['operation'],'evidence_source':'approved_tool'}
        for field in ('observed_failure','observed_pass','sequence','test_id'):
            if field in result:ev[field]=result[field]
        self.finished[key]=ev
        return ev

    async def execute(self,task_id,events):
        answer={}
        for req in self.requests(task_id,events):
            answer[req['receipt_key']]=await self.execute_action(req)
        return answer

    async def tdd_red_before_implement(self,task_id,events):
        if 'code.changed' not in events:return None
        for req in self.requests(task_id,events):
            if req['operation']=='run_approved_red_tests':
                return await self.execute_action(req)
        raise NCTError('TDD_RED_ACTION_MISSING')


class NCTLoopCodaFixed(NCTLoopEngine):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        if self.ecc_actions is not None:
            self.ecc_actions=StagedECCActions(self.ecc_actions.executor,
                                              approved_actions=self.ecc_actions.approved)

    async def _run_unit(self,unit,*,mission_id,context,monitor,trace,profile):
        events=[ev for flag,ev in (('code','code.changed'),('ui','ui.changed'),('api','api.changed'))
                if flag in unit.scope]
        receipt_ecc={}
        if events and self.ecc_actions is None:
            raise NCTError('ECC_ACTION_PORT_NOT_CONNECTED')
        proposal=None;approved_context=dict(context)
        for stage in ('INSPECT','RESEARCH','PLAN','TEST_RED','IMPLEMENT'):
            self._gate('phase.4.pre',{'worker_context':context,'max_context_chars':24000},trace)
            if stage=='IMPLEMENT' and 'code.changed' in events:
                receipt_ecc['red']=await self.ecc_actions.tdd_red_before_implement(unit.id,events)
            response=await self._call(unit.block,{'mission_id':mission_id,'task_id':unit.id,
                'stage':stage,'profile':profile,'context':approved_context,'format':'JSON_ONLY',
                'response_contract':{'status':'READY|NEED_INPUT|BLOCKED'}},monitor)
            trace.append({'event':'phase.4.model','task_id':unit.id,'stage':stage,
                          'response_status':response['status']})
            if stage=='IMPLEMENT':proposal=response.get('proposal')
        if not isinstance(proposal,dict) or set(proposal)-{'meta','ops'}:
            raise NCTError('JSON_RICARDO_PLAN_REQUIRED')
        ops=proposal.get('ops')
        if not isinstance(ops,list) or not ops or any(not isinstance(x,dict) for x in ops):
            raise NCTError('INVALID_JSON_OPS')
        if set(x.get('op') for x in ops)-set(unit.allowed_ops):
            raise NCTError('OP_OUTSIDE_APPROVED_SCOPE')
        async def actual_execution():return await self.tools.execute(proposal,unit.id)
        outcome=await self.queue.submit_and_wait(unit,actual_execution)
        if not isinstance(outcome,dict) or outcome.get('ok') is not True:
            raise NCTError('REAL_TOOL_FAILED '+str((outcome or {}).get('errors',[]))[:300])
        if outcome.get('executed_count')!=len(ops):raise NCTError('INCOMPLETE_TOOL_RECEIPTS')
        rcpt=Receipt(id=stable_hash([mission_id,unit.id,outcome['plan_sha256']])[:24],
                     task_id=unit.id,status='PASS',evidence=outcome,source='existing_tool_port')
        self._gate('phase.4.receipt',{'receipt':rcpt.asdict(),'task_id':unit.id},trace)
        # GREEN/REGRESSION/SEGURIDAD tienen que ocurrir DESPUÉS de la acción real.
        if events:
            gates=await self.ecc_actions.execute(unit.id,events)
            receipt_ecc.update(gates)
            trace.append({'event':'phase.4.ecc_actions_before_model_review',
                          'task_id':unit.id,'receipts':sorted(gates)})
        context_post={**approved_context,'receipt_id':rcpt.id,
                      'ecc_evidence_ids':{k:v['receipt_id'] for k,v in receipt_ecc.items() if isinstance(v,dict) and v.get('receipt_id')}}
        for stage in ('TEST_GREEN','REVIEW'):
            self._gate('phase.4.pre',{'worker_context':context_post,'max_context_chars':24000},trace)
            response=await self._call(unit.block,{'mission_id':mission_id,'task_id':unit.id,
                'stage':stage,'profile':profile,'context':context_post,
                'format':'JSON_ONLY','response_contract':{'status':'READY|NEED_INPUT|BLOCKED'}},monitor)
            trace.append({'event':'phase.4.model','task_id':unit.id,'stage':stage,
                          'response_status':response['status']})
        return rcpt.asdict()
