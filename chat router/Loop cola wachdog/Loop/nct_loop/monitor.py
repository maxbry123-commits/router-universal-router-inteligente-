"""Fase 5: métricas OBSERVABLES; PAD emocional/KL sin distribuciones no son medibles."""
from dataclasses import dataclass, field
import time

@dataclass
class Monitor:
    max_calls:int=60
    max_stalls:int=2
    max_failures:int=3
    started:float=field(default_factory=time.monotonic)
    calls:int=0
    stalls:int=0
    failures:int=0
    fingerprints:set[str]=field(default_factory=set)
    def before_call(self):
        if self.calls>=self.max_calls:raise RuntimeError('MAX_MODEL_CALLS')
        self.calls+=1
    def observe(self, fingerprint:str, success:bool):
        if success:
            self.stalls=0 if fingerprint not in self.fingerprints else self.stalls+1
            self.fingerprints.add(fingerprint)
        else:self.failures+=1
        return self.check()
    def check(self):
        if self.stalls>self.max_stalls:return {'ok':False,'reason':'STALLED'}
        if self.failures>self.max_failures:return {'ok':False,'reason':'CIRCUIT_OPEN'}
        return {'ok':True,'reason':'CONTINUE'}
    def metrics(self):
        return {'model_calls':self.calls,'stalls':self.stalls,'failures':self.failures,
                'elapsed_s':round(time.monotonic()-self.started,3),
                'drift_proxy':'not_calculated_without_plan_actual_distributions',
                'PAD_proxy':'disabled_no_valid_emotion_measurement'}
