"""NCT LOOP + ECC CODE + CODA. NO scheduler, router, vault, memoria ni DAG secundarios.
10 fases en una pasada, con micro-LOOP controlado por unidad dentro de fase 4.
En producción se INYECTAN puertos existentes tras inspeccionar sus interfaces.
"""
from __future__ import annotations
import asyncio, json
from pathlib import Path
from .contracts import NCTError,Receipt,stable_hash,ID
from .classifier import classify,choose_route
from .planner import parse_tasks,to_existing_dag_payload,for_existing_dag_handoff
from .context_isolator import isolated_context
from .resource_registry import suggestions
from .monitor import Monitor
from .repair import decide_repair
from .consolidator import consolidate,deliver
from .ecc_actions import ECCActionDispatcher

PIPELINE=('INSPECT','RESEARCH','PLAN','TEST_RED','IMPLEMENT','TEST_GREEN','REVIEW')

class NCTLoopEngine:
    def __init__(self, *, ecc,model,queue,memory,tools,checker,resources_file:Path,
                 known_blocks:set[str],approved_ops:set[str],max_calls:int=60,
                 ecc_action_port=None,approved_ecc_actions:set[str]|None=None):
        self.ecc=ecc;self.model=model;self.queue=queue;self.memory=memory
        self.tools=tools;self.checker=checker;self.resources_file=resources_file
        self.known_blocks=set(known_blocks);self.approved_ops=set(approved_ops)
        self.max_calls=max_calls
        self.ecc_actions=(ECCActionDispatcher(ecc_action_port,approved_actions=approved_ecc_actions or set())
                          if ecc_action_port is not None else None)
    def _gate(self,event,ctx,trace):
        gate=self.ecc.emit(event,ctx).asdict()
        trace.append({'event':event,'gate':gate})
        if not gate['ok']:raise NCTError(f'ECC_GATE_FAIL {event}: {gate["failures"]}')
        return gate
    async def _call(self,block,payload,monitor):
        monitor.before_call()
        response=await self.model.invoke(block,payload)
        if not isinstance(response,dict) or response.get('status') not in ('READY','NEED_INPUT','BLOCKED'):
            raise NCTError('Modelo no devolvió JSON con status READY|NEED_INPUT|BLOCKED')
        if response['status']!='READY':raise NCTError('MODEL_'+response['status'])
        if set(response)-{'status','proposal','notes','evidence','next_actions','artifacts'}:
            raise NCTError('modelo envió campos sin contrato')
        return response
    async def _run_unit(self,unit, *, mission_id:str,context:dict,monitor:Monitor,trace:list,profile:str)->dict:
        """PIPELINE de 7 PASOS. La LLM propone JSON; SOLO tools port ejecuta acciones."""
        proposal=None
        for stage in PIPELINE:
            event_ctx={'worker_context':context,'max_context_chars':24000}
            self._gate('phase.4.pre',event_ctx,trace)
            call={'mission_id':mission_id,'task_id':unit.id,'stage':stage,'profile':profile,
                  'context':context,'format':'JSON_ONLY',
                  'response_contract':{'status':'READY|NEED_INPUT|BLOCKED',
                                       'proposal':'meta+ops solamente en IMPLEMENT'}}
            answer=await self._call(unit.block,call,monitor)
            trace.append({'event':'phase.4.model','task_id':unit.id,'stage':stage,
                          'response_status':answer['status']})
            if stage=='IMPLEMENT':
                proposal=answer.get('proposal')
                if not isinstance(proposal,dict):raise NCTError('Sin ops JSON en IMPLEMENT')
        ops=proposal.get('ops')
        if not isinstance(ops,list) or not ops:raise NCTError('ops vacía')
        names=[x.get('op') for x in ops if isinstance(x,dict)]
        if len(names)!=len(ops) or set(names)-set(unit.allowed_ops):
            raise NCTError('ops del modelo fuera de permiso de ficha')
        async def execute_once():return await self.tools.execute(proposal,unit.id)
        outcome=await self.queue.submit_and_wait(unit,execute_once)
        if not isinstance(outcome,dict) or not outcome.get('ok'):
            err=(outcome or {}).get('errors',['TOOL_ERROR']) if isinstance(outcome,dict) else ['WRONG_TOOL_RESPONSE']
            raise NCTError('REAL_TOOL_FAILED '+str(err)[:500])
        if outcome.get('executed_count')!=len(ops):raise NCTError('recibos incompletos')
        receipt=Receipt(id=stable_hash([mission_id,unit.id,outcome['plan_sha256']])[:24],
                        task_id=unit.id,status='PASS',evidence=outcome,source='existing_tool_port')
        self._gate('phase.4.receipt',{'receipt':receipt.asdict(),'task_id':unit.id},trace)
        return receipt.asdict()
    async def run(self,mission:dict)->dict:
        """Una misión por llamada. Se reanuda con la memoria EXISTENTE del proyecto."""
        trace=[];receipts=[];repaired=[];external_evidence={};monitor=Monitor(max_calls=self.max_calls)
        mission_id=str(mission.get('mission_id',''))
        if not ID.fullmatch(mission_id):raise NCTError('mission_id inválido')
        goal=mission.get('goal','')
        if not isinstance(goal,str) or not goal.strip():raise NCTError('goal inválido')
        profile=mission.get('profile','document')
        if profile not in ('document','code','frontend','api'):raise NCTError('perfil inválido')
        prior=await self.memory.load(mission_id) # puerto del storage YA EXISTENTE
        if prior and prior.get('final_status')=='DONE_VERIFICADO' and prior.get('mission_sha')==stable_hash(mission):
            return {'mission_id':mission_id,'status':'ALREADY_COMPLETED','previous':prior,'note':'No duplicó efectos'}
        if prior and prior.get('mission_sha') and prior['mission_sha']!=stable_hash(mission):
            raise NCTError('misión cambió tras checkpoint: nuevo ID o aprobación explícita')
        try:
            # FASE 0, 1
            classified=classify(goal,mission.get('units',[]))
            self._gate('phase.0',{'goal':goal,'acceptance':mission.get('acceptance'),
                                  'max_calls':self.max_calls},trace)
            route=choose_route(classified)
            self._gate('phase.1',{'route':route['route']},trace)
            trace.append({'phase':0,'classification':classified});trace.append({'phase':1,'route':route})
            # FASE 2 (equivalente DAG Ricardo + ECC RFC)
            units=for_existing_dag_handoff(parse_tasks(mission,known_blocks=self.known_blocks,known_ops=self.approved_ops))
            self._gate('phase.2',{'units':units,'approved_ops':list(self.approved_ops)},trace)
            resources=suggestions(self.resources_file,classified['project_type'],goal)
            dag_payload=[to_existing_dag_payload(x,mission_id,stable_hash(mission)) for x in units]
            trace.append({'phase':2,'task_count':len(units),'step_2_5_resources':resources,
                          'dag_contract_export':dag_payload})
            # FASE 3: aislamiento con memoria existente, nunca historial completo entre workers
            contexts={}
            for unit in units:
                contexts[unit.id]=isolated_context(mission_id=mission_id,unit=unit,
                    prior_receipts=receipts,memory=prior,
                    phase_rules=[{'rule':'ECC_DSL_DAG_CODA','phase':'WORKER_PIPELINE'}],resources=resources)
                self._gate('phase.3',{'worker_context':contexts[unit.id], 'task_id':unit.id,
                                      'mission_id':mission_id},trace)
            trace.append({'phase':3,'isolated_workers':len(contexts)})
            # FASE 4: los jobs pasan al puerto cola EXISTENTE. SIN crear otra cola/scheduler.
            # Demo en serie; en producción el scheduler existente gestiona depends_on y concurrencia.
            completed={r.get('task_id') for r in (prior or {}).get('receipts',[]) if r.get('status')=='PASS'}
            if completed:
                # RECONCILIACIÓN: independiente, usando el checker YA EXISTENTE.
                by_id={unit.id:unit for unit in units}
                recovered=(prior or {}).get('receipts',[])
                for old in recovered:
                    task=by_id.get(old.get('task_id'))
                    if task is None or old.get('status')!='PASS' or set(task.scope)&{'code','ui','api'}:
                        raise NCTError('CHECKPOINT_RECONCILIATION_REQUIRED: efectos/acciones ECC no confirmables')
                    check=await self.checker.check(task,[old])
                    if not check.get('ok') or not all(check.get('three_layers',{}).values()):
                        raise NCTError('CHECKPOINT_RECONCILIATION_REQUIRED: recibo no válido en workspace')
                    receipts.append(old)
                    trace.append({'event':'phase.4.recovered','task_id':task.id,'status':'RECONFIRMED'})
            for unit in units:
                if unit.id in completed:
                    continue
                if not set(unit.depends_on).issubset(completed):
                    raise NCTError('DEPENDENCY_WAITING: scheduler existente debe liberar nodo')
                # Handoff actualizado: el siguiente worker ve SOLO hashes de dependencias ya probadas.
                contexts[unit.id]=isolated_context(mission_id=mission_id,unit=unit,
                    prior_receipts=receipts,memory=prior,
                    phase_rules=[{'rule':'ECC_DSL_DAG_CODA','phase':'WORKER_PIPELINE'}],resources=resources)
                failures=0
                while True:
                    try:
                        receipt=await self._run_unit(unit,mission_id=mission_id,
                            context=contexts[unit.id],monitor=monitor,trace=trace,profile=profile)
                        receipts.append(receipt)
                        events=[ev for flag,ev in (('code','code.changed'),('ui','ui.changed'),('api','api.changed'))
                                if flag in unit.scope]
                        if events:
                            if self.ecc_actions is None:
                                raise NCTError('ECC_ACTION_PORT_NOT_CONNECTED: no se pueden ejecutar pruebas reales')
                            external_evidence[unit.id]=await self.ecc_actions.execute(unit.id,events)
                            trace.append({'event':'phase.4.ecc_actions','task_id':unit.id,
                                          'receipts':sorted(external_evidence[unit.id])})
                        completed.add(unit.id)
                        checked=monitor.observe(stable_hash(receipt),True)
                        self._gate('phase.5',{'stalls':monitor.stalls,'calls':monitor.calls,
                                              'max_calls':self.max_calls},trace)
                        if not checked['ok']:raise NCTError(checked['reason'])
                        await self.memory.checkpoint(mission_id,{'mission_sha':stable_hash(mission),
                            'phase':4,'receipts':receipts,'last_task':unit.id,
                            'summary':f'{len(receipts)} tareas con recibo; pendientes {len(units)-len(receipts)}'})
                        break
                    except (NCTError,ValueError,RuntimeError,KeyError) as exc:
                        failures+=1
                        monitor.observe(stable_hash(['error',unit.id,str(exc)]),False)
                        decision=decide_repair(failures,
                             retryable=not any(o in unit.allowed_ops for o in ('write_text','delete','deploy','install')),
                             has_checkpoint=bool(prior),authorized_fallback=False)
                        repaired.append({'task_id':unit.id,'error_type':type(exc).__name__,
                                         'reason':str(exc)[:300],'repair':decision})
                        self._gate('phase.8',{'failures':monitor.failures,'max_failures':monitor.max_failures},trace)
                        if decision['action']!='RETRY_SAME' or failures>unit.max_retries:
                            raise NCTError('REPAIR_STOP '+decision['action']+' '+str(exc)) from exc
            # FASE 5 métricas, FASE 6 tres comprobaciones con recibos del ejecutor
            stats=monitor.metrics();trace.append({'phase':5,'metrics':stats})
            allchecks=[]
            evidence_verified=True
            for unit in units:
                group=[r for r in receipts if r['task_id']==unit.id]
                checked=await self.checker.check(unit,group)
                events=[]
                if 'code' in unit.scope:events.append('code.changed')
                if 'ui' in unit.scope:events.append('ui.changed')
                if 'api' in unit.scope:events.append('api.changed')
                # Evidence from checker is external, not strings from model.
                tool_evidence={**external_evidence.get(unit.id,{}),**checked.get('evidence',{})}
                eg=self.ecc.evidence_gate(profile,events,tool_evidence).asdict()
                checks=checked.get('three_layers',{})
                three_ok=all(checks.get(k) is True for k in
                    ('adversarial_contract','cross_file_hash','maker_checker_acceptance'))
                ok=bool(checked.get('ok') and three_ok and eg['ok'])
                evidence_verified=evidence_verified and ok
                allchecks.append({'task_id':unit.id,'ok':ok,'checker':checked,'ecc_gate':eg})
            self._gate('phase.6',{'evidence_verified':evidence_verified},trace)
            # FASE 7 / 9: consolidar, cerrar SOLO si checks reales pasan.
            summary=consolidate(receipts,stats,verified=evidence_verified)
            self._gate('phase.7',{'receipts':receipts,'summary':summary},trace)
            self._gate('phase.9',{'evidence_verified':evidence_verified},trace)
            aggregate={'receipts':receipts,'summary':summary,
                       'triple_gate':{'ok':evidence_verified,'per_task':allchecks}}
            final=deliver(mission_id,aggregate,required_tasks={x.id for x in units})
            final.update({'trace':trace,'classification':classified,'routing':route,
                          'repairs':repaired,'phase_reached':9})
            await self.memory.checkpoint(mission_id,{'mission_sha':stable_hash(mission),
                'phase':9,'receipts':receipts,'final_status':final['status'],
                'summary':summary['tier1_digest']})
            return final
        except (NCTError,ValueError,RuntimeError,TypeError,KeyError) as exc:
            # Mantener receipts confiables en el puerto de memoria existente; no declarar DONE.
            status='GAP' if 'NOT_CONNECTED' in str(exc) or 'REQUIRED' in str(exc) else 'BLOCKED'
            return {'mission_id':mission_id,'status':status,'error':str(exc),
                    'phase_reached':max([x.get('phase',-1) for x in trace if 'phase' in x] or [-1]),
                    'receipts':receipts,'trace':trace,'repairs':repaired,
                    'metrics':monitor.metrics()}
