"""REST Watchdog 10-2880 min; no rutas de cola ni del LOOP."""
from fastapi import APIRouter,Depends,HTTPException
from .core import WatchError

def router_for(store,verificar):
    r=APIRouter(prefix='/api/watchdogs',dependencies=[Depends(verificar)])
    def use(fn,*a,**k):
        try:return fn(*a,**k)
        except WatchError as e:raise HTTPException(status_code=e.status,detail=str(e)) from None
    @r.get('/health')
    def health():return {'status':'ok','service':'watchdog48','storage':'sqlite_persistent_required'}
    @r.post('')
    def created(body:dict):return use(store.create,body)
    @r.get('')
    def listed():return {'watches':store.list()}
    @r.get('/{wid}')
    def get(wid:str):return use(store.get,wid)
    @r.get('/{wid}/events')
    def events(wid:str,after:int=0):return {'events':use(store.events,wid,after)}
    @r.post('/{wid}/heartbeat')
    def heartbeat(wid:str,body:dict):return use(store.heartbeat,wid,body.get('progress_id'))
    @r.post('/{wid}/pause')
    def pause(wid:str):return use(store.control,wid,'pause')
    @r.post('/{wid}/resume')
    def resume(wid:str):return use(store.control,wid,'resume')
    @r.post('/{wid}/cancel')
    def cancel(wid:str):return use(store.control,wid,'cancel')
    return r
