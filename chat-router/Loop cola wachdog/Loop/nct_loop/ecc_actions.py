"""ECC SKILL.md -> código Python que dispara requests TIPADOS hacia tools EXISTENTES.
NO carga/ejecuta markdown, NO llama shell, NO inventa herramientas del backend.
Para activar una acción se requieren: fase, evento, autorización y recibo REAL.
"""
from dataclasses import dataclass
from .contracts import NCTError,stable_hash

# Tabla de COMPILACIÓN REVISADA A MANO desde patrones ECC. No son comandos de ECC.
EVENT_OPERATIONS={
 'code.changed':[
   ('tdd_red','run_approved_red_tests','tdd-workflow'),
   ('tdd_green','run_approved_green_tests','tdd-workflow'),
   ('test_run','run_test_suite','verification-loop'),
   ('lint_run','run_lint','plankton-code-quality'),
   ('diff_review','check_diff_scope','verification-loop'),
   ('security_scan','run_security_checks','security-review'),
   ('regression_test','run_regression_suite','ai-regression-testing')],
 'ui.changed':[
   ('click_path_audit','trace_click_path','click-path-audit'),
   ('accessibility_audit','check_accessibility','accessibility'),
   ('e2e_test','run_ui_e2e','e2e-testing')],
 'api.changed':[
   ('contract_test','run_api_contract_tests','agent-harness-construction'),
   ('regression_test','run_regression_suite','module-regression'),
   ('security_scan','run_security_checks','security-review')],
}

class ECCActionDispatcher:
    def __init__(self, executor_port, *, approved_actions:set[str]):
        self.executor=executor_port
        self.approved=set(approved_actions)
    def requests(self, task_id:str, events:list[str]) -> list[dict]:
        unique={}
        for event in events:
            if event not in EVENT_OPERATIONS:raise NCTError('ECC_EVENT_UNKNOWN '+event)
            for receipt_key,op,source in EVENT_OPERATIONS[event]:
                if op not in self.approved:raise NCTError('ECC_OP_NOT_APPROVED '+op)
                unique[receipt_key]={'task_id':task_id,'operation':op,'source_ecc':source,
                   'receipt_key':receipt_key,'request_id':stable_hash([task_id,op])[:24]}
        return list(unique.values())
    async def execute(self, task_id:str, events:list[str]) -> dict:
        observed={}
        for req in self.requests(task_id,events):
            # SOLO el tool ya autorizado ejecuta el nombre definido. Ningún código externo.
            result=await self.executor.run_approved_action(req)
            if not isinstance(result,dict) or result.get('request_id')!=req['request_id']:
                raise NCTError('ECC receipt sin correlación')
            if result.get('status')!='PASS' or not result.get('receipt_id'):
                raise NCTError('ECC_ACTION_FAILED '+req['operation'])
            observed[req['receipt_key']]={'status':'PASS','receipt_id':result['receipt_id'],
                                           'source_ecc':req['source_ecc'],'operation':req['operation']}
        return observed
