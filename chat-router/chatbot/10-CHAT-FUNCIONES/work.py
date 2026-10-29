"""Estado de trabajos del chat."""
from __future__ import annotations
from dataclasses import dataclass,asdict
STATES={"RUNNING","PAUSED","CANCELLED","DONE"}
@dataclass
class Job:
    id:str; status:str="RUNNING"; progress:int=0
_JOBS:dict[str,Job]={}
def crear(job_id:str)->dict:
    if not job_id: raise ValueError("id requerido")
    _JOBS[job_id]=Job(job_id); return asdict(_JOBS[job_id])
def cambiar(job_id:str,status:str,progress:int|None=None)->dict:
    if status not in STATES: raise ValueError(status)
    job=_JOBS[job_id]; job.status=status
    if progress is not None: job.progress=max(0,min(100,int(progress)))
    return asdict(job)
def pausar(job_id:str)->dict:return cambiar(job_id,"PAUSED")
def cancelar(job_id:str)->dict:return cambiar(job_id,"CANCELLED")
def reintentar(job_id:str)->dict:return cambiar(job_id,"RUNNING")
def aprobar(job_id:str)->dict:return cambiar(job_id,"DONE",100)
def listar()->list[dict]:return [asdict(x) for x in _JOBS.values()]
