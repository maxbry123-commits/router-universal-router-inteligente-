"""Pruebas del delta ECC código/puente Ricardo, todo offline."""
import asyncio
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from nct_loop.ecc_phase_compiler import (compile_skill,compile_directory,make_python_wrappers,
                                         write_compiled_catalog,ECCCompilationError)
from nct_loop.ecc_compiled_executor import execute_compiled_motor,PhaseBlocked
from nct_loop.ecc_operational_rules import (
    loop_design,dag_rfc,tdd_red_green,verification_loop,module_regression,
    ui_path_audit,accessibility,quality_gate,benchmark_reliability,stall_guard)
from nct_loop.ricardo_missing_bridge import parse_planner_steps,ModelPlanError
from nct_loop.ecc_event_hooks import run_ecc_event,EVENT_SOURCE_MAP

SAMPLE='''---\nname: tdd-workflow\ndescription: example\n---\n# TDD\n## Identify tests\n## RED\n### Run failing tests\n## GREEN\n## Verify coverage\n'''

def receipt(name,**kwargs):
    return {'status':'PASS','receipt_id':'trusted-'+name,'evidence_source':'approved_tool',**kwargs}

def good_doc():
    return {'task_id':'job001','status':'READY','goal':'archivo verificado','steps':[
        {'id':'A','tool':'create_directory','args':{'path':'report'},'depends_on':[], 'checks':['exists']},
        {'id':'B','tool':'write_text','args':{'path':'report/a.txt','text':'ok'},'depends_on':['A'],'checks':['sha']},
        {'id':'C','tool':'verify_contains','args':{'path':'report/a.txt','text':'ok'},'depends_on':['B'],'checks':['pass']}],
        'inputs_missing':[],'expected_artifacts':['report/a.txt'],'evidence_required':['sha'],'constraints_respected':True}


class CompilerTests(unittest.TestCase):
    def test_compiles_real_sections_as_data(self):
        c=compile_skill('tdd-workflow',SAMPLE)
        self.assertEqual(len(c.phases),5)
        self.assertEqual(c.phases[0].title,'Identify tests')
        self.assertTrue(all(p.mode=='REQUIRES_APPROVED_HANDLER' for p in c.phases))
    def test_no_eval_from_source(self):
        src=SAMPLE+'\n```python\n__import__("os").system("false")\n```\n'
        c=compile_skill('tdd-workflow',src)
        self.assertEqual(len(c.phases),5)
    def test_invalid_name_rejected(self):
        with self.assertRaises(ECCCompilationError):compile_skill('../../escape',SAMPLE)
    def test_empty_source_rejected(self):
        with self.assertRaises(ECCCompilationError):compile_skill('valid-name','')
    def test_catalog_two_source_files_generate_two_python(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp);root=d/'ECC'
            for name in ('tdd-workflow','verification-loop'):
                p=root/'skills'/name/'SKILL.md';p.parent.mkdir(parents=True);p.write_text(SAMPLE)
            catalog=compile_directory(root)
            self.assertEqual(len(catalog),2)
            write_compiled_catalog(catalog,d/'compiled.json')
            self.assertEqual(make_python_wrappers(catalog,d/'generated'),2)
            self.assertEqual(len(list((d/'generated').glob('*.py'))),2)
            self.assertEqual(json.loads((d/'compiled.json').read_text())['total_source_documents'],2)
    def test_empty_checkout_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ECCCompilationError):compile_directory(Path(tmp))

class ExecutorTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        c=compile_skill('tdd-workflow',SAMPLE)
        self.catalog={'skills':{'tdd-workflow':c.asdict()}}
        self.source_sha=c.source_sha256
    def arguments(self,handlers,callback):
        return dict(catalog=self.catalog,skill_id='tdd-workflow',source_sha256=self.source_sha,
                    event='code.changed',task_id='T001',context={'goal':'test'},
                    approved_handlers=handlers,receipt_callback=callback)
    async def test_missing_handler_fail_closed(self):
        result=await execute_compiled_motor(**self.arguments({},None))
        self.assertFalse(result['ok']);self.assertEqual(result['status'],'NOT_IMPLEMENTED')
        self.assertEqual(result['executed'],0)
    async def test_valid_handlers_execute_all_phases(self):
        phases=self.catalog['skills']['tdd-workflow']['phases']
        async def action(req):return {'status':'PASS','data':'output'}
        async def trusted(req,result):
            return dict(request_id=req['request_id'],task_id=req['task_id'],skill_id=req['skill_id'],
                        phase_id=req['phase_id'],receipt_id='tool-'+req['request_id'],
                        status='PASS',evidence_source='approved_tool')
        handlers={x['action_id']:action for x in phases}
        res=await execute_compiled_motor(**self.arguments(handlers,trusted))
        self.assertTrue(res['ok']);self.assertEqual(res['executed'],len(phases))
    async def test_fake_receipt_rejected(self):
        phases=self.catalog['skills']['tdd-workflow']['phases']
        async def action(req):return {'status':'PASS'}
        handlers={x['action_id']:action for x in phases}
        res=await execute_compiled_motor(**self.arguments(handlers,lambda req,r:{'status':'PASS','receipt_id':'fake'}))
        self.assertEqual(res['status'],'BAD_RECEIPT')
    async def test_source_hash_mismatch_rejected(self):
        args=self.arguments({},None);args['source_sha256']='0'*64
        with self.assertRaises(PhaseBlocked):await execute_compiled_motor(**args)
    async def test_failure_does_not_continue(self):
        phases=self.catalog['skills']['tdd-workflow']['phases']
        async def action(req):return {'status':'FAIL'}
        handlers={x['action_id']:action for x in phases}
        res=await execute_compiled_motor(**self.arguments(handlers,lambda req,r:{}))
        self.assertEqual(res['status'],'FAILED')

class PolicyTests(unittest.TestCase):
    def test_loop_design_requires_authority(self):
        self.assertFalse(loop_design({'acceptance':['a']}).ok)
    def test_loop_design_valid(self):
        self.assertTrue(loop_design({'acceptance':['unit tests'],'negative_constraints':['no scope change'],
           'fallback':'STOP','max_rounds':3,'max_calls':21,'checker_actor':'B','executor_actor':'A'}).ok)
    def test_rfc_dag_missing_acceptance(self):
        self.assertFalse(dag_rfc([{'id':'X','depends_on':[]}]).ok)
    def test_rfc_dag_valid(self):
        units=[{'id':'A','depends_on':[],'acceptance_tests':['assert A'],'scope':['a'],
                'risk_level':'low','rollback_plan':'restore snapshot'},
               {'id':'B','depends_on':['A'],'acceptance_tests':['assert B'],'scope':['b'],
                'risk_level':'medium','rollback_plan':'revert diff'}]
        self.assertTrue(dag_rfc(units).ok)
        units[0]['depends_on']=['B'];self.assertFalse(dag_rfc(units).ok)
    def test_tdd_requires_true_red_failure(self):
        self.assertFalse(tdd_red_green({'red':receipt('red',observed_failure=False,sequence=1,test_id='t'),
                                         'green':receipt('green',observed_pass=True,sequence=2,test_id='t')}).ok)
    def test_tdd_valid(self):
        self.assertTrue(tdd_red_green({'red':receipt('red',observed_failure=True,sequence=1,test_id='t'),
                                         'green':receipt('green',observed_pass=True,sequence=2,test_id='t')}).ok)
    def test_verification_all_required(self):
        self.assertFalse(verification_loop({'tests':receipt('tests')}).ok)
        self.assertTrue(verification_loop({x:receipt(x) for x in ('build','types','lint','tests','security','diff')}).ok)
    def test_regression_downstream(self):
        self.assertFalse(module_regression(['api'],{'api':['ui']},{'api':receipt('api')}).ok)
        self.assertTrue(module_regression(['api'],{'api':['ui']},{'api':receipt('api'),'ui':receipt('ui')}).ok)
    def test_ui_path_race(self):
        self.assertFalse(ui_path_audit([{'name':'Save','calls_traced':True,'undo_state_detected':False,
                                        'race_condition_checked':False,'e2e':receipt('ui')}]).ok)
    def test_ui_path_valid(self):
        self.assertTrue(ui_path_audit([{'name':'Save','calls_traced':True,'undo_state_detected':False,
                                        'race_condition_checked':True,'e2e':receipt('ui')}]).ok)
    def test_accessibility_pour(self):
        self.assertFalse(accessibility({}).ok)
        self.assertTrue(accessibility({x:receipt(x) for x in ('perceivable','operable','understandable','robust')}).ok)
    def test_lint_untampered(self):
        self.assertTrue(quality_gate({x:receipt(x) for x in ('formatter','linter','configs_unchanged')}).ok)
    def test_eval_needs_judge(self):
        self.assertFalse(benchmark_reliability([{'baseline_sha':'123'}]).ok)
        self.assertTrue(benchmark_reliability([{'baseline_sha':'123','judge':receipt('judge')}]).ok)
    def test_stall_halt(self):
        self.assertFalse(stall_guard([{'error_fingerprint':'X'} for _ in range(3)]).ok)
        self.assertTrue(stall_guard([{'error_fingerprint':'X'}, {'error_fingerprint':'Y'}]).ok)
    def test_event_dispatch(self):
        event='loop.progress'
        self.assertTrue(run_ecc_event(event,{'loop.progress':{'events':[]}}).ok)
        self.assertFalse(run_ecc_event(event,{}).ok)
        self.assertFalse(run_ecc_event('shell.exec',{}).ok)
        self.assertIn('verification-loop',EVENT_SOURCE_MAP['phase.6'])

class RicardoBridgeTests(unittest.TestCase):
    def setUp(self):self.allowed={'inspect_workspace','create_directory','write_text','read_text','verify_exists','verify_contains','finish'}
    def test_valid_response_to_meta_ops(self):
        result=parse_planner_steps(good_doc(),task_id='job001',allowed_ops=self.allowed)
        self.assertEqual(len(result['ops']),3)
        self.assertEqual(result['ops'][1]['depends_on'],['A'])
    def test_task_id_swap_rejected(self):
        with self.assertRaises(ModelPlanError):parse_planner_steps(good_doc(),task_id='other',allowed_ops=self.allowed)
    def test_exec_denied(self):
        x=good_doc();x['steps'][1]['tool']='exec'
        with self.assertRaises(ModelPlanError):parse_planner_steps(x,task_id='job001',allowed_ops=self.allowed|{'exec'})
    def test_args_override_protected_rejected(self):
        x=good_doc();x['steps'][1]['args']['op']='exec'
        with self.assertRaises(ModelPlanError):parse_planner_steps(x,task_id='job001',allowed_ops=self.allowed)
    def test_missing_dependency(self):
        x=good_doc();x['steps'][0]['depends_on']=['Z']
        with self.assertRaises(ModelPlanError):parse_planner_steps(x,task_id='job001',allowed_ops=self.allowed)
    def test_cycle(self):
        x=good_doc();x['steps'][0]['depends_on']=['C']
        with self.assertRaises(ModelPlanError):parse_planner_steps(x,task_id='job001',allowed_ops=self.allowed)
    def test_need_input_is_not_executable(self):
        x=good_doc();x['status']='NEED_INPUT'
        with self.assertRaises(ModelPlanError):parse_planner_steps(x,task_id='job001',allowed_ops=self.allowed)
    def test_deny_unapproved(self):
        x=good_doc()
        with self.assertRaises(ModelPlanError):parse_planner_steps(x,task_id='job001',allowed_ops={'finish'})

if __name__=='__main__':unittest.main(verbosity=2)

class CodeOrderedLoopTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        from nct_loop.ports import DemoMemory,InlineQueueDemo
        from nct_loop.ricardo_adapter import RicardoOpsDemo,FileCheckerDemo
        from nct_loop.ecc_runtime import ECCCodeRuntime
        from nct_loop.engine_coda_fixed import NCTLoopCodaFixed
        self.temp=tempfile.TemporaryDirectory()
        self.work=Path(self.temp.name)
        self.project=Path(__file__).resolve().parents[1]
        self.policy=self.project/'referencia_ricardo/allowed_ops.json'
        self.resources=self.project/'config/resources.json'
        self.rules=self.project/'config/ecc_rules.json'
        self.mission=json.loads((self.project/'examples/mission_smoke.json').read_text())
        self.proposal=json.loads((self.project/'examples/mock_proposals.json').read_text())
        self.timeline=[]
        class Model:
            def __init__(s,outer):s.o=outer
            async def invoke(s,b,p):
                s.o.timeline.append('model:'+p['stage'])
                result={'status':'READY'}
                if p['stage']=='IMPLEMENT':result['proposal']=s.o.proposal[p['task_id']]
                return result
        class Tools:
            def __init__(s,outer):s.o=outer;s.base=RicardoOpsDemo(outer.work,outer.policy)
            async def execute(s,p,t):
                s.o.timeline.append('tool:execute')
                return await s.base.execute(p,t)
        class Actions:
            def __init__(s,outer):s.o=outer
            async def run_approved_action(s,req):
                op=req['operation']
                s.o.timeline.append('action:'+op)
                p=s.o.work/'evidencia/smoke.txt'
                if op=='run_approved_red_tests' and p.exists():raise RuntimeError('red_after_implementation')
                if op=='run_approved_green_tests' and not p.is_file():raise RuntimeError('green_before_implementation')
                result={'request_id':req['request_id'],'receipt_id':'host-'+req['request_id'],'status':'PASS'}
                if op=='run_approved_red_tests':result['observed_failure']=True
                if op=='run_approved_green_tests':result['observed_pass']=True
                return result
        actions=Actions(self)
        approved={'run_approved_red_tests','run_approved_green_tests','run_test_suite',
                  'run_lint','check_diff_scope','run_security_checks','run_regression_suite'}
        self.engine=NCTLoopCodaFixed(ecc=ECCCodeRuntime(self.rules),model=Model(self),
            queue=InlineQueueDemo(),memory=DemoMemory(),tools=Tools(self),
            checker=FileCheckerDemo(self.work),resources_file=self.resources,
            known_blocks={'executor'},approved_ops=set(json.loads(self.policy.read_text())['allowed_ops']),
            ecc_action_port=actions,approved_ecc_actions=approved)
    async def asyncTearDown(self):self.temp.cleanup()
    async def test_existing_doc_flow(self):
        result=await self.engine.run(self.mission)
        self.assertEqual(result['status'],'DONE_VERIFICADO',result.get('error'))
        self.assertLess(self.timeline.index('tool:execute'),self.timeline.index('model:TEST_GREEN'))
    async def test_real_red_implement_green_order(self):
        self.mission['profile']='code'
        self.mission['units'][0]['scope']=['code']
        result=await self.engine.run(self.mission)
        self.assertEqual(result['status'],'DONE_VERIFICADO',result.get('error'))
        self.assertLess(self.timeline.index('action:run_approved_red_tests'),self.timeline.index('tool:execute'))
        self.assertLess(self.timeline.index('tool:execute'),self.timeline.index('action:run_approved_green_tests'))
        self.assertLess(self.timeline.index('action:run_approved_green_tests'),self.timeline.index('model:TEST_GREEN'))
        self.assertEqual(self.timeline.count('action:run_approved_red_tests'),1)
        self.assertEqual(self.timeline.count('action:run_approved_green_tests'),1)
