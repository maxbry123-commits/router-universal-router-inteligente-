"""Triggers Python ECC con 10 fases NCT y 7 subetapas CODA.

No reemplaza el LOOP, la cola o la memoria. Es un interceptor tipado,
que el motor NCT ya creado puede inyectar como 'ecc'.
"""
from __future__ import annotations
from dataclasses import dataclass,field
from typing import Callable
from .ecc_operational_rules import SOURCE_MAPPING, Verdict

# Entradas traducidas de documentación ECC inspeccionada; se exigen
# validadores Python/recibos reales, nunca solo la presencia de una skill.
EVENT_SOURCE_MAP = {
 'phase.0':('loop-design-check','agent-harness-construction'),
 'phase.1':('continuous-agent-loop','autonomous-agent-harness'),
 'phase.2':('ralphinho-rfc-pipeline','plan-orchestrate','eval-harness'),
 'phase.3':('context-and-decisions','context-budget'),
 'phase.4.pre':('tdd-workflow','agent-harness-construction'),
 'phase.4.receipt':('verification-loop','agent-harness-construction'),
 'phase.4.model':('agent-harness-construction',),
 'phase.5':('continuous-agent-loop','loop-design-check'),
 'phase.6':('verification-loop','module-regression','ai-regression-testing'),
 'phase.7':('context-and-decisions','eval-harness'),
 'phase.8':('loop-design-check','continuous-agent-loop'),
 'phase.9':('verification-loop','delivery-gate','eval-harness'),
 'code.changed':('tdd-workflow','plankton-code-quality','ai-regression-testing','security-review'),
 'ui.changed':('click-path-audit','accessibility','e2e-testing'),
 'api.changed':('module-regression','contract-first','security-review'),
}

# IDs funcionales: interfaz explicitada y verificada por test.
EVENT_OPERATIONAL_CHECKS={
 'preflight.loop':('loop.preflight',),
 'plan.units':('plan.decompose',),
 'code.red_green':('code.red_green',),
 'code.verify':('code.verify',),
 'code.regression':('code.regression',),
 'ui.changed':('ui.click_path','ui.accessibility'),
 'code.quality':('code.quality',),
 'eval.finish':('eval.suite',),
 'loop.progress':('loop.progress',),
}

@dataclass
class EventResult:
    event:str
    ok:bool
    sources:list[str]=field(default_factory=list)
    checks:list[dict]=field(default_factory=list)
    failures:list[str]=field(default_factory=list)
    def asdict(self):return vars(self)


def run_ecc_event(event:str, context:dict, *, require_known_event:bool=True)->EventResult:
    """Ejecuta únicamente reglas deterministas con argumentos acordados.

    La evidencia mutable la aporta un EJECUTOR/VERIFICADOR externo. No se
    autoaprueban eventos que no tienen reglas conectadas.
    """
    known=event in EVENT_SOURCE_MAP or event in EVENT_OPERATIONAL_CHECKS
    if require_known_event and not known:
        return EventResult(event,False,failures=['UNKNOWN_EVENT'])
    keys=EVENT_OPERATIONAL_CHECKS.get(event,())
    out=EventResult(event,True,sources=list(EVENT_SOURCE_MAP.get(event,())))
    if not isinstance(context,dict):return EventResult(event,False,failures=['BAD_CONTEXT'])
    if not keys:
        return out # eventos fase sirven de metadata; el ECCCodeRuntime existente impone gates
    for key in keys:
        if key not in SOURCE_MAPPING:
            out.ok=False;out.failures.append(f'MISSING_COMPILED_RULE:{key}');continue
        fn=SOURCE_MAPPING[key]
        data=context.get(key)
        if data is None:
            out.ok=False;out.failures.append(f'MISSING_RULE_INPUT:{key}');continue
        try:
            if isinstance(data,dict):v=fn(**data)
            else:v=fn(data)
        except (ValueError,TypeError,KeyError,AttributeError) as exc:
            out.ok=False;out.failures.append(f'BAD_RULE_DATA:{key}:{type(exc).__name__}');continue
        out.checks.append(v.asdict())
        if not v.ok:out.ok=False;out.failures.extend(v.failures)
    return out


class ECCEventInterceptor:
    """Decorador compatible con el puerto existente ECCCodeRuntime.

    Inyectar como ecc=ECCEventInterceptor(ECCCodeRuntime(...)); ningún cambio
    del motor legacy es necesario.
    """
    def __init__(self, old_ecc):self.old_ecc=old_ecc
    def emit(self,event:str,ctx:dict):
        from .ecc_runtime import Gate
        old=self.old_ecc.emit(event,ctx)
        # Solo evalúa controles nuevos cuando el host pasa entradas explícitas
        # ``ecc_operational``; no altera comportamiento de misiones previas.
        if 'ecc_operational' in ctx:
            newer=run_ecc_event(ctx.get('ecc_event',event),ctx['ecc_operational'])
            old.triggered.extend([{'ecc_source':x,'action':'CODE_GUARD','ok':newer.ok} for x in newer.sources])
            if not newer.ok:
                old.ok=False;old.failures+=newer.failures
        return old
    def evidence_gate(self,profile,events,evidence):
        return self.old_ecc.evidence_gate(profile,events,evidence)
