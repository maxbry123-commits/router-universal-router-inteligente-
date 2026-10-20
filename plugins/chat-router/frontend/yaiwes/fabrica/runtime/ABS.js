
(function(g){
  const h=new Map(); const log=[];
  function emit(id, payload){
    const rec={at:Date.now(),id,ok:false,reason:null};
    const fn=h.get(id);
    const msg={type:'FROMTED_ABS', id, payload:payload||{}, windowId:(g.FROMTED_LOCK&&g.FROMTED_LOCK.id)||null};
    if(!fn){ rec.reason='SIN_HANDLER'; log.push(rec); g.parent&&g.parent.postMessage(msg,'*'); return rec; }
    try{ const r=fn(payload||{}); rec.ok=true; rec.result=r; }
    catch(e){ rec.reason=String(e&&e.message||e); }
    log.push(rec);
    g.parent&&g.parent.postMessage(msg,'*');
    g.dispatchEvent(new CustomEvent('FROMTED_'+id,{detail:payload||{}}));
    return rec;
  }
  g.ABS={register(id,fn){h.set(id,fn);}, dispatch:emit, list(){return[...h.keys()]}, log(){return log.slice(-20)}};
})(window);
