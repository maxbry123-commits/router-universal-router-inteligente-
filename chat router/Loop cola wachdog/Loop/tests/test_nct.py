import asyncio,copy,json,tempfile,unittest
from pathlib import Path
from nct_loop.engine import NCTLoopEngine
from nct_loop.contracts import NCTError,WorkUnit,stable_hash
from nct_loop.planner import parse_tasks,to_existing_dag_payload
from nct_loop.ecc_runtime import ECCCodeRuntime
from nct_loop.monitor import Monitor
from nct_loop.classifier import classify,choose_route
from nct_loop.ports import DemoMemory,DemoModel,InlineQueueDemo
from nct_loop.ricardo_adapter import RicardoOpsDemo,FileCheckerDemo
from nct_loop.repair import decide_repair
from nct_loop.resource_registry import suggestions

ROOT=Path(__file__).resolve().parent.parent
OPS=set(json.loads((ROOT/'referencia_ricardo/allowed_ops.json').read_text())['allowed_ops'])

class NCTTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.mission=json.loads((ROOT/'examples/mission_smoke.json').read_text())
        self.proposal=json.loads((ROOT/'examples/mock_proposals.json').read_text())
        self.memory=DemoMemory()
        self.model=DemoModel(self.proposal)
        self.ecc=ECCCodeRuntime(ROOT/'config/ecc_rules.json')
        self.tools=RicardoOpsDemo(Path(self.tmp.name),ROOT/'referencia_ricardo/allowed_ops.json')
        self.eng=NCTLoopEngine(ecc=self.ecc,model=self.model,queue=InlineQueueDemo(),
           memory=self.memory,tools=self.tools,checker=FileCheckerDemo(Path(self.tmp.name)),
           resources_file=ROOT/'config/resources.json',known_blocks={'executor'},
           approved_ops=OPS,max_calls=60)
    async def asyncTearDown(self):self.tmp.cleanup()
    async def test_real_ricardo_op_engine(self):
        result=await self.eng.run(self.mission)
        self.assertEqual(result['status'],'DONE_VERIFICADO',result.get('error'))
        self.assertTrue((Path(self.tmp.name)/'evidencia/smoke.txt').is_file())
        self.assertEqual(len(self.model.calls),7)
        self.assertTrue(result['triple_gate']['per_task'][0]['checker']['three_layers']['cross_file_hash'])
    async def test_no_duplicate_after_checkpoint(self):
        await self.eng.run(self.mission)
        other=await self.eng.run(self.mission)
        self.assertEqual(other['status'],'ALREADY_COMPLETED')
        self.assertEqual(len(self.model.calls),7)
    async def test_real_ecc_events_fired(self):
        result=await self.eng.run(self.mission)
        events=[x['event'] for x in result['trace'] if 'event' in x]
        for key in ['phase.0','phase.1','phase.2','phase.3','phase.4.pre','phase.4.receipt',
                    'phase.5','phase.6','phase.7','phase.9']:
            self.assertIn(key,events,key)
    async def test_bad_operation_denied(self):
        self.proposal['S_UNIT']['ops'][2]['op']='exec'
        result=await self.eng.run(self.mission)
        self.assertEqual(result['status'],'BLOCKED')
        self.assertFalse((Path(self.tmp.name)/'evidencia/smoke.txt').exists())
    async def test_dag_cycle_rejected(self):
        self.mission['units']=[{'id':'A','goal':'A','block':'executor','depends_on':['B']},
                               {'id':'B','goal':'B','block':'executor','depends_on':['A']}]
        result=await self.eng.run(self.mission)
        self.assertEqual(result['status'],'BLOCKED')
        self.assertIn('ciclo',result['error'])
    async def test_unknown_block_rejected(self):
        self.mission['units'][0]['block']='missing_block'
        result=await self.eng.run(self.mission)
        self.assertIn('NO CONECTADO',result['error'])
    async def test_output_scope_escape_denied(self):
        self.proposal['S_UNIT']['ops'][2]['path']='../out.txt'
        result=await self.eng.run(self.mission)
        self.assertEqual(result['status'],'BLOCKED')
        self.assertFalse((Path(self.tmp.name).parent/'out.txt').exists())
    async def test_untrusted_acceptance_rejected(self):
        self.mission['units'][0]['acceptance']=[{'op':'approve_all'}]
        result=await self.eng.run(self.mission)
        self.assertEqual(result['status'],'BLOCKED')
    async def test_code_profile_requires_ecc_evidence(self):
        self.mission['profile']='code'
        self.mission['units'][0]['scope']=['code']
        result=await self.eng.run(self.mission)
        self.assertEqual(result['status'],'GAP')
        self.assertIn('ECC_ACTION_PORT_NOT_CONNECTED',result['error'])
    async def test_missing_acceptance_rejected_by_ecc(self):
        self.mission['acceptance']=[]
        result=await self.eng.run(self.mission)
        self.assertEqual(result['status'],'BLOCKED')
        self.assertIn('phase.0',result['error'])
    async def test_model_malformed_response_rejected(self):
        class Invalid:
            async def invoke(self,b,p):return 'DONE'
        self.eng.model=Invalid()
        result=await self.eng.run(self.mission)
        self.assertEqual(result['status'],'BLOCKED')
        self.assertFalse(result['receipts'])
    async def test_model_blocked_not_done(self):
        class Invalid:
            async def invoke(self,b,p):return {'status':'BLOCKED'}
        self.eng.model=Invalid()
        result=await self.eng.run(self.mission)
        self.assertEqual(result['status'],'BLOCKED')
    async def test_budget_limited(self):
        self.eng.max_calls=2
        result=await self.eng.run(self.mission)
        self.assertEqual(result['status'],'BLOCKED')
        self.assertIn('MAX_MODEL_CALLS',result['error'])
    async def test_dag_idempotency_key(self):
        unit=WorkUnit(id='T',goal='algo')
        a=to_existing_dag_payload(unit,'M','sha')
        b=to_existing_dag_payload(unit,'M','sha')
        self.assertEqual(a['idempotency_key'],b['idempotency_key'])
    async def test_no_retry_on_write(self):
        self.assertEqual(decide_repair(1,retryable=False,has_checkpoint=False)['action'],'BLOCK')
    async def test_retry_bounded(self):
        self.assertEqual(decide_repair(1,retryable=True,has_checkpoint=False)['action'],'RETRY_SAME')
        self.assertEqual(decide_repair(10,retryable=True,has_checkpoint=False)['action'],'ESCALATE')
    async def test_ecc_python_triggers_are_allowlisted(self):
        self.assertFalse(self.ecc.evidence_gate('frontend',['ui.changed'],{}).ok)
        self.assertFalse(self.ecc.emit('phase.2',{'units':[],'approved_ops':[]}).ok)
    async def test_resources_offline(self):
        results=suggestions(ROOT/'config/resources.json','frontend','React UI de componente')
        self.assertTrue(any(x['name']=='shadcn/ui' for x in results))
    async def test_no_change_existing_ricardo_policy(self):
        self.assertEqual(len(OPS),7)
        self.assertNotIn('exec',OPS)
    async def test_signatures_same_fixture(self):
        self.assertEqual(stable_hash(self.mission),stable_hash(copy.deepcopy(self.mission)))
    async def test_missing_dependency(self):
        self.mission['units'][0]['depends_on']=['NOPE']
        res=await self.eng.run(self.mission)
        self.assertEqual(res['status'],'BLOCKED')
    async def test_duplicate_ids(self):
        self.mission['units'].append(copy.deepcopy(self.mission['units'][0]))
        res=await self.eng.run(self.mission)
        self.assertEqual(res['status'],'BLOCKED')
    async def test_reconcile_resume_no_unsafe_reexecution(self):
        await self.memory.checkpoint(self.mission['mission_id'],{'mission_sha':stable_hash(self.mission),
            'phase':4,'receipts':[{'task_id':'S_UNIT','status':'PASS'}]})
        res=await self.eng.run(self.mission)
        self.assertEqual(res['status'],'GAP')
        self.assertEqual(len(self.model.calls),0)
    async def test_checker_tamper_detects(self):
        res=await self.eng.run(self.mission)
        receipt=res['receipts'][0]
        (Path(self.tmp.name)/'evidencia/smoke.txt').write_text('tamper',encoding='utf8')
        chk=await FileCheckerDemo(Path(self.tmp.name)).check(WorkUnit(**self.mission['units'][0]),[receipt])
        self.assertFalse(chk['ok'])
        self.assertIn('HASH_MISMATCH',chk['errors'])

if __name__=='__main__':unittest.main(verbosity=2)

class ECCActionsTests(unittest.IsolatedAsyncioTestCase):
    async def test_ecc_code_actions_are_real_callable_operations(self):
        from nct_loop.ecc_actions import ECCActionDispatcher,EVENT_OPERATIONS
        class FakeHost:
            def __init__(self):self.requests=[]
            async def run_approved_action(self,request):
                self.requests.append(request)
                return {'request_id':request['request_id'],'status':'PASS','receipt_id':'tool-'+request['request_id']}
        h=FakeHost()
        allapproved={name for evt in EVENT_OPERATIONS.values() for _,name,_ in evt}
        dispatcher=ECCActionDispatcher(h,approved_actions=allapproved)
        result=await dispatcher.execute('T1',['code.changed','ui.changed'])
        self.assertEqual(len(result),10)
        self.assertEqual(len(h.requests),10)
    async def test_ecc_action_unapproved_denied(self):
        from nct_loop.ecc_actions import ECCActionDispatcher
        with self.assertRaises(NCTError):
            ECCActionDispatcher(None,approved_actions=set()).requests('T1',['code.changed'])
    async def test_ecc_action_unrecognized_denied(self):
        from nct_loop.ecc_actions import ECCActionDispatcher
        with self.assertRaises(NCTError):
            ECCActionDispatcher(None,approved_actions=set()).requests('T1',['do.shell'])
    async def test_ecc_action_fake_receipt_denied(self):
        from nct_loop.ecc_actions import ECCActionDispatcher
        class FakeHost:
            async def run_approved_action(self,request):return {'request_id':'wrong','status':'PASS','receipt_id':'x'}
        with self.assertRaises(NCTError):
            await ECCActionDispatcher(FakeHost(),approved_actions={'run_ui_e2e','trace_click_path','check_accessibility'}).execute('T1',['ui.changed'])

class ModesTests(unittest.TestCase):
    def test_explicit_activation(self):
        from nct_loop.modes import validate_mode
        with self.assertRaises(NCTError):validate_mode('nct_continuous',explicit_user_choice=False)
        self.assertEqual(validate_mode('nct_continuous',explicit_user_choice=True),'nct_continuous')
    def test_manual_default_is_allowed(self):
        from nct_loop.modes import validate_mode
        self.assertEqual(validate_mode('manual',explicit_user_choice=False),'manual')

class ExistingParallelAdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_two_claimed_jobs(self):
        from nct_loop.parallel_existing import fanout_claimed
        class Q:
            async def submit_and_wait(self,job,perform):return await perform()
        jobs=[{'task_id':'A','claim_status':'CLAIMED','lease_id':'lease-A','resource_keys':['file-a']},
              {'task_id':'B','claim_status':'CLAIMED','lease_id':'lease-B','resource_keys':['file-b']}]
        async def run_a():return {'ok':True,'task_id':'A'}
        async def run_b():return {'ok':True,'task_id':'B'}
        result=await fanout_claimed(Q(),jobs,{'A':run_a,'B':run_b},max_parallel=2)
        self.assertEqual(len(result),2)
        self.assertTrue(all(x['ok'] for x in result))
    async def test_resource_collision_denied(self):
        from nct_loop.parallel_existing import fanout_claimed
        jobs=[{'task_id':x,'claim_status':'CLAIMED','lease_id':x,'resource_keys':['same-file']} for x in 'AB']
        with self.assertRaises(NCTError):await fanout_claimed(None,jobs,{'A':lambda:None,'B':lambda:None})
    async def test_not_claimed_denied(self):
        from nct_loop.parallel_existing import fanout_claimed
        with self.assertRaises(NCTError):await fanout_claimed(None,[{'task_id':'X','claim_status':'PENDING'}],{'X':lambda:None})

class CheckpointRecoveryTests(unittest.IsolatedAsyncioTestCase):
    async def test_verified_resume_skips_completed_mutation(self):
        from nct_loop.contracts import Receipt
        mission=json.loads((ROOT/'examples/mission_coda_2tasks.json').read_text())
        proposals=json.loads((ROOT/'examples/mock_proposals_2tasks.json').read_text())
        tmp=tempfile.TemporaryDirectory()
        try:
            memory=DemoMemory();model=DemoModel(proposals)
            tools=RicardoOpsDemo(Path(tmp.name),ROOT/'referencia_ricardo/allowed_ops.json')
            first=await tools.execute(proposals['S_UNIT'],'S_UNIT')
            self.assertTrue(first['ok'])
            receipt=Receipt(id=stable_hash([mission['mission_id'],'S_UNIT',first['plan_sha256']])[:24],
                            task_id='S_UNIT',status='PASS',evidence=first).asdict()
            await memory.checkpoint(mission['mission_id'],{
                'mission_sha':stable_hash(mission),'phase':4,'receipts':[receipt]})
            engine=NCTLoopEngine(ecc=ECCCodeRuntime(ROOT/'config/ecc_rules.json'),
                model=model,queue=InlineQueueDemo(),memory=memory,tools=tools,
                checker=FileCheckerDemo(Path(tmp.name)),resources_file=ROOT/'config/resources.json',
                known_blocks={'executor'},approved_ops=OPS,max_calls=60)
            result=await engine.run(mission)
            self.assertEqual(result['status'],'DONE_VERIFICADO',result.get('error'))
            self.assertEqual(len(model.calls),7)
            self.assertEqual({r['task_id'] for r in result['receipts']},{'S_UNIT','V_UNIT'})
            self.assertIn('phase.4.recovered',[t['event'] for t in result['trace'] if 'event' in t])
        finally:tmp.cleanup()
