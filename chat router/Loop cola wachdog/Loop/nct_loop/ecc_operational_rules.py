"""Port Python auditado de las invariantes ECC para desarrollo de software.

Las funciones siguientes sí son lógica Python ejecutable. No declaran que
cumplan automáticamente instrucciones no programables de otros SKILL.md.
Requieren evidencia del host para pruebas, análisis UI y seguridad.
"""
from __future__ import annotations
import hashlib
import json
import re
from dataclasses import dataclass,asdict
from collections import defaultdict

class PolicyViolation(ValueError):pass

@dataclass(frozen=True)
class Verdict:
    ok:bool
    source:str
    rule:str
    failures:tuple[str,...]
    def asdict(self):return asdict(self)


def check(source, rule, failures):
    return Verdict(not failures, source,rule,tuple(failures))


def loop_design(ctx:dict) -> Verdict:
    """ECC loop-design-check: 4-condition gate + damping + límites."""
    errors=[]
    if not isinstance(ctx.get('acceptance'),list) or not ctx['acceptance']:errors.append('acceptance_missing')
    if not isinstance(ctx.get('negative_constraints'),list) or not ctx['negative_constraints']:
        errors.append('boundaries_missing')
    if not isinstance(ctx.get('fallback'),str) or ctx['fallback'] not in ('STOP','ESCALATE','REPLAN'):
        errors.append('fallback_missing')
    if not isinstance(ctx.get('max_rounds'),int) or not (1<=ctx['max_rounds']<=50):
        errors.append('unbounded_rounds')
    if not isinstance(ctx.get('max_calls'),int) or not (1<=ctx['max_calls']<=300):
        errors.append('unbounded_calls')
    if ctx.get('checker_actor')==ctx.get('executor_actor') or not ctx.get('checker_actor'):
        errors.append('non_independent_checker')
    return check('loop-design-check','decidable_bounded_loop',errors)


def dag_rfc(units:list[dict]) -> Verdict:
    """ECC ralphinho-rfc-pipeline: ids, dependencias, aceptación y rollback."""
    errors=[];table={}
    if not isinstance(units,list) or not units:errors.append('empty_units')
    else:
        for unit in units:
            if not isinstance(unit,dict):errors.append('unit_not_dict');continue
            uid=unit.get('id')
            if not isinstance(uid,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',uid):
                errors.append('invalid_id');continue
            if uid in table:errors.append('duplicate_id')
            table[uid]=unit
            if not unit.get('acceptance_tests'):errors.append(f'{uid}_acceptance_tests_missing')
            if unit.get('risk_level') not in ('low','medium','high'):
                errors.append(f'{uid}_risk_level_missing')
            if not unit.get('scope'):errors.append(f'{uid}_scope_missing')
            if not unit.get('rollback_plan'):errors.append(f'{uid}_rollback_missing')
        state={}
        def visit(k):
            if state.get(k)==1:
                errors.append('cycle');return
            if state.get(k)==2:return
            state[k]=1
            for dep in table[k].get('depends_on',[]):
                if dep not in table:errors.append(f'{k}_unknown_dependency');continue
                visit(dep)
            state[k]=2
        for key in table:visit(key)
    return check('ralphinho-rfc-pipeline','unit_dag',errors)


def _evidence(receipts:dict,name:str) -> bool:
    x=receipts.get(name)
    return isinstance(x,dict) and x.get('status')=='PASS' and bool(x.get('receipt_id')) \
        and x.get('evidence_source') in ('approved_tool','independent_checker')


def tdd_red_green(receipts:dict) -> Verdict:
    """ECC tdd-workflow: prueba RED observada ANTES que GREEN, por runner real."""
    errors=[]
    if not _evidence(receipts,'red'):errors.append('missing_red_tool_receipt')
    if not _evidence(receipts,'green'):errors.append('missing_green_tool_receipt')
    red=receipts.get('red',{});green=receipts.get('green',{})
    if red.get('observed_failure') is not True:errors.append('RED_did_not_fail_as_expected')
    if green.get('observed_pass') is not True:errors.append('GREEN_did_not_pass')
    if not isinstance(red.get('sequence'),int) or not isinstance(green.get('sequence'),int) or red.get('sequence',999999)>=green.get('sequence',-1):
        errors.append('RED_GREEN_order_invalid')
    if not red.get('test_id') or red.get('test_id')!=green.get('test_id'):
        errors.append('test_identity_mismatch')
    return check('tdd-workflow','red_green_receipts',errors)


def verification_loop(receipts:dict, *, required:tuple[str,...]=('build','types','lint','tests','security','diff')) -> Verdict:
    errors=[f'missing_{x}' for x in required if not _evidence(receipts,x)]
    return check('verification-loop','six_phase_verification',errors)


def module_regression(changed:list[str],affected:dict,receipts:dict) -> Verdict:
    """ECC module-regression: afectados downstream, sin aceptaciones omitidas."""
    errors=[]
    if not changed:errors.append('no_change_evidence')
    required=set(changed)
    for k in changed:
        linked=affected.get(k)
        if not isinstance(linked,list):errors.append(f'unverified_dependency_graph:{k}');continue
        required.update(linked)
    for module in sorted(required):
        if not _evidence(receipts,module):errors.append(f'NO_REGRESSION_RECEIPT:{module}')
    return check('module-regression','downstream_receipts',errors)


def ui_path_audit(handlers:list[dict]) -> Verdict:
    """ECC click-path-audit: rechaza rutas sin trazas, sin prueba de estado final."""
    errors=[]
    if not handlers:errors.append('no_interaction_handlers')
    for h in handlers:
        if not isinstance(h,dict):errors.append('bad_handler');continue
        name=h.get('name','unknown')
        if not h.get('calls_traced'):errors.append(f'{name}:missing_call_graph')
        if h.get('undo_state_detected') is not False:errors.append(f'{name}:state_undo_unresolved')
        if h.get('race_condition_checked') is not True:errors.append(f'{name}:race_unverified')
        if not _evidence(h,'e2e'):errors.append(f'{name}:e2e_unverified')
    return check('click-path-audit','ui_event_trace',errors)


def accessibility(receipts:dict) -> Verdict:
    """ECC accessibility: evidencia por atributos perceptibles y controles."""
    axes=('perceivable','operable','understandable','robust')
    return check('accessibility','p_o_u_r',[f'unverified_{x}' for x in axes if not _evidence(receipts,x)])


def quality_gate(receipts:dict) -> Verdict:
    """ECC plankton-code-quality: no afirmar código limpio sin tool receipts."""
    return check('plankton-code-quality','write_time_quality',
                 [f'no_{x}' for x in ('formatter','linter','configs_unchanged') if not _evidence(receipts,x)])


def benchmark_reliability(samples:list[dict], *, required_pass_rate:float=1.0) -> Verdict:
    """ECC eval-harness: evaluación reproducible, no un juicio verbal del modelo."""
    errors=[]
    if not samples:errors.append('no_samples')
    for i,x in enumerate(samples):
        if not x.get('baseline_sha'):errors.append(f'{i}:baseline_missing')
        if not _evidence(x,'judge'):errors.append(f'{i}:judge_missing')
    if samples and sum(_evidence(x,'judge') for x in samples)/len(samples)<required_pass_rate:
        errors.append('pass_rate_below_target')
    return check('eval-harness','deterministic_pass_rate',errors)


def stall_guard(events:list[dict], *, max_repeats:int=2,max_retries:int=3) -> Verdict:
    """ECC continuous-agent-loop: bloquea churn sin evidencia de avance."""
    errors=[];seen=defaultdict(int)
    for e in events:
        key=e.get('error_fingerprint')
        if key:seen[key]+=1
        if e.get('retries',0)>max_retries:errors.append('retry_budget_exceeded')
        if e.get('scope_extended') and not e.get('user_approved'):
            errors.append('scope_escalation_unapproved')
    if any(x>max_repeats for x in seen.values()):errors.append('repeated_same_root_cause')
    return check('continuous-agent-loop','progress_and_budget',errors)


SOURCE_MAPPING={
 'loop.preflight':loop_design,
 'plan.decompose':dag_rfc,
 'code.red_green':tdd_red_green,
 'code.verify':verification_loop,
 'code.regression':module_regression,
 'ui.click_path':ui_path_audit,
 'ui.accessibility':accessibility,
 'code.quality':quality_gate,
 'eval.suite':benchmark_reliability,
 'loop.progress':stall_guard,
}
