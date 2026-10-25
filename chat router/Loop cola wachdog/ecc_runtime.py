"""Interpretación EJECUTABLE y revisada de fases ECC, no ejecuta SKILL.md.
Cada trigger resuelve a una función Python registrada manualmente; JSON NO puede añadir código.
"""
from __future__ import annotations
from dataclasses import dataclass,field
import json
from pathlib import Path
from .contracts import NCTError,stable_hash

@dataclass
class Gate:
    ok:bool=True
    event:str=''
    triggered:list[dict]=field(default_factory=list)
    failures:list[str]=field(default_factory=list)
    required:list[str]=field(default_factory=list)
    def asdict(self):return vars(self)

class ECCCodeRuntime:
    def __init__(self, rules_path: Path):
        data=json.loads(Path(rules_path).read_text(encoding='utf8'))
        self.provenance=data.get('sources',{})
        self.rules=data['triggers']
        self.checks={
            'goal_is_decidable':self.goal_is_decidable,
            'dag_contract':self.dag_contract,
            'tools_are_typed':self.tools_are_typed,
            'context_budget':self.context_budget,
            'receipts_bound':self.receipts_bound,
            'progress_guard':self.progress_guard,
            'verify_evidence':self.verify_evidence,
            'retry_budget':self.retry_budget,
            'route_is_bounded':self.route_is_bounded,
            'context_is_isolated':self.context_is_isolated,
            'summary_is_grounded':self.summary_is_grounded,
        }
        if any(r['action'] not in self.checks for r in self.rules):
            raise NCTError('Trigger ECC intenta llamar función no registrada')
    def emit(self, event:str, ctx:dict) -> Gate:
        verdict=Gate(event=event)
        for r in self.rules:
            if r['event']!=event:continue
            profile=r.get('profile','all')
            if profile not in ('all',ctx.get('profile')):continue
            action=r['action'];result=self.checks[action](ctx)
            verdict.triggered.append({'ecc_source':r['ecc_source'],'action':action,
                                      'ok':result,'rule_id':r['id']})
            if not result:
                verdict.failures.append(r['id']); verdict.ok=False
        return verdict
    @staticmethod
    def goal_is_decidable(c):
        return bool(c.get('goal','').strip() and c.get('acceptance') and c.get('max_calls',0)>0)
    @staticmethod
    def dag_contract(c):
        tasks=c.get('units',[]);table={x.id for x in tasks}
        return bool(tasks) and len(table)==len(tasks) and all(set(x.depends_on)<=table for x in tasks)
    @staticmethod
    def tools_are_typed(c):
        return all(set(x.allowed_ops)<=set(c.get('approved_ops',[])) for x in c.get('units',[]))
    @staticmethod
    def context_budget(c):
        return len(json.dumps(c.get('worker_context',{}),ensure_ascii=False))<=c.get('max_context_chars',24000)
    @staticmethod
    def receipts_bound(c):
        r=c.get('receipt'); return isinstance(r,dict) and r.get('task_id')==c.get('task_id') and r.get('status')=='PASS' and bool(r.get('id')) and bool(r.get('evidence'))
    @staticmethod
    def progress_guard(c):
        return c.get('stalls',0)<=c.get('max_stalls',2) and c.get('calls',0)<=c.get('max_calls',60)
    @staticmethod
    def verify_evidence(c):
        return bool(c.get('evidence_verified'))
    @staticmethod
    def retry_budget(c):
        return c.get('failures',0)<=c.get('max_failures',3)
    @staticmethod
    def route_is_bounded(c):
        return c.get('route') in ('directa','batch','agentes_especializados')
    @staticmethod
    def context_is_isolated(c):
        w=c.get('worker_context',{})
        return bool(w and w.get('task_id')==c.get('task_id') and w.get('mission_id')==c.get('mission_id'))
    @staticmethod
    def summary_is_grounded(c):
        return len(c.get('receipts',[]))==len(c.get('summary',{}).get('tier3_receipts',[]))
    def evidence_requirements(self, profile:str, event:str) -> list[str]:
        base={
            'code.changed':['tdd_red','tdd_green','test_run','lint_run','diff_review','security_scan','regression_test'],
            'ui.changed':['click_path_audit','accessibility_audit','e2e_test'],
            'api.changed':['contract_test','regression_test','security_scan'],
            'phase.verify':['independent_checker','acceptance_results'],
        }
        result=list(base.get(event,[]))
        if profile=='frontend' and event=='code.changed':result+=base['ui.changed']
        return list(dict.fromkeys(result))
    def evidence_gate(self, profile:str, events:list[str], evidence:dict) -> Gate:
        """ECC traducido a invariantes de recibos reales; la LLM no puede falsificar ok."""
        needed=set()
        for event in events: needed.update(self.evidence_requirements(profile,event))
        missing=[]
        for key in sorted(needed):
            item=evidence.get(key)
            if not isinstance(item,dict) or item.get('status')!='PASS' or not item.get('receipt_id'):
                missing.append(key)
        return Gate(ok=not missing,event='ECC_EVIDENCE_GATE',failures=missing,required=sorted(needed),
                    triggered=[{'ecc_source':'ECC eval-harness / verification-loop / tdd-workflow / click-path-audit / accessibility',
                                'action':'require_tool_receipts','ok':not missing}])
