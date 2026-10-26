"""REST de la cola exclusivamente. Los modelos se conectan por callback externo.
Los endpoints requieren el MISMO verificador de autenticación del Router existente.
"""
from fastapi import APIRouter,Depends,HTTPException
from .core import QueueError

def router_for(store,verificar):
    r=APIRouter(prefix='/api/cit50',dependencies=[Depends(verificar)])
    def use(fn,*a,**k):
        try:return fn(*a,**k)
        except QueueError as e:raise HTTPException(status_code=e.status,detail=str(e)) from None
    @r.get('/health')
    def health():return {'status':'ok','service':'cit50','storage':'sqlite_persistent_required'}
    @r.get('')
    def listed(chat_id:str|None=None):return {'queues':use(store.list,chat_id)}
    @r.post('')
    def created(body:dict):return use(store.create,body)
    @r.get('/{qid}')
    def get(qid:str):return use(store.get,qid)
    @r.get('/{qid}/events')
    def events(qid:str,after:int=0):return {'events':use(store.events,qid,after)}
    @r.put('/{qid}/draft')
    def replace(qid:str,body:dict):return use(store.replace_draft,qid,body,body.get('revision'))
    @r.put('/{qid}/order')
    def reorder(qid:str,body:dict):return use(store.reorder,qid,body.get('order'),body.get('revision'))
    @r.post('/{qid}/tasks')
    def add(qid:str,body:dict):return use(store.add_task,qid,body.get('task'),body.get('revision'))
    @r.patch('/{qid}/tasks/{tid}')
    def edit(qid:str,tid:str,body:dict):return use(store.edit_task,qid,tid,body.get('changes'),body.get('revision'))
    @r.delete('/{qid}/tasks/{tid}')
    def remove(qid:str,tid:str,revision:int):return use(store.remove_task,qid,tid,revision)
    @r.post('/{qid}/start')
    def start(qid:str,body:dict):return use(store.start,qid,body.get('seconds',3600))
    @r.post('/{qid}/pause')
    def pause(qid:str):return use(store.control,qid,'pause')
    @r.post('/{qid}/resume')
    def resume(qid:str):return use(store.control,qid,'resume')
    @r.post('/{qid}/cancel')
    def cancel(qid:str):return use(store.control,qid,'cancel')
    @r.post('/{qid}/tasks/{tid}/approve')
    def approve(qid:str,tid:str):return use(store.approve,qid,tid)
    return r
