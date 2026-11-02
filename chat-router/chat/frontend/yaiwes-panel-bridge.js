// Vista frontend independiente. API únicamente mediante el host autenticado del chat.
(() => {
 'use strict';
 const CHANNEL='yaiwes.loop.ui.v1', pending=new Map();
 const embedded=window.parent!==window && /^https?:$/.test(location.protocol);
 const origin=location.origin;
 function request(name,data={}) {
   if (!embedded) return Promise.reject(new Error('VISTA_LOCAL_SIN_BACKEND'));
   const id='r-'+(crypto.randomUUID?crypto.randomUUID().replaceAll('-',''):Math.random().toString(36).slice(2));
   return new Promise((resolve,reject)=>{
     const timer=setTimeout(()=>{pending.delete(id);reject(new Error('PUENTE_SIN_RESPUESTA'));},12000);
     pending.set(id,{resolve,reject,timer});
     window.parent.postMessage({channel:CHANNEL,type:'request',id,name,...data},origin);
   });
 }
 window.addEventListener('message',(event)=>{
   if(event.source!==window.parent || event.origin!==origin)return;
   const d=event.data;
   if(!d || d.channel!==CHANNEL || d.type!=='reply' || typeof d.id!=='string')return;
   const p=pending.get(d.id);if(!p)return;
   clearTimeout(p.timer);pending.delete(d.id);
   if(d.ok) p.resolve(d.result);
   else p.reject(new Error(String(d.error||'BACKEND_REJECTED')));
 });
 const send=(plugin,action,payload={})=>request('plugin',{plugin,action,payload});
 const openAnchor=(kind='general')=>request('open_anchor',{payload:{kind}});
 const openPending=()=>request('open_pending');
 const selection=(project_id,loop_id)=>request('selection',{payload:{project_id,loop_id}});
 const state={connected:false};
 const el=(id)=>document.getElementById(id);
 function banner(message,kind='warning'){
   const b=el('connection-state');if(!b)return;
   b.textContent=message;
   b.className='pill '+(kind==='ok'?'ok':'offline');
 }
 async function health(plugin){
   try{
     const res=await send(plugin,'status',{}); // confirma plugin existente, no el contrato DSL
     if(res?.error || res?.ok===false) throw new Error(res.error||'BACKEND_REJECTED');
     state.connected=true;banner('● Plugin accesible · DSL por verificar');return res;
   }catch(e){state.connected=false;banner('◌ Vista local · '+e.message);throw e;}
 }
 function showError(e){const msg=String(e?.message||e);const n=el('notice');if(n)n.textContent=msg;}
 function txt(v){return String(v===undefined||v===null?'':v)}
 function h(t,clazz,value){const n=document.createElement(t);if(clazz)n.className=clazz;if(value!==undefined)n.textContent=txt(value);return n;}
 function idSafe(v){return /^[A-Za-z0-9_-]{1,80}$/.test(v||'');}
 function statusFlag(s){const k=String(s||'UNKNOWN').toUpperCase();return k==='PASS'?'✅ PASS':k==='NOT_APPLICABLE'?'🚧 NO APLICA':k==='BLOCKED'?'🛑 BLOQUEO':k==='RUNNING'?'🔵 EN CURSO':k==='FLAGGED'?'🚩 OBSERVACIÓN':k==='OFF'?'⚪ OFF':k==='PAUSED'?'⏸ PAUSA':k==='DRAFT'?'▫ BORRADOR':k==='UNKNOWN'?'◌ SIN VERIFICAR':k;}
 window.YAIWES_PANEL={request,send,openAnchor,openPending,selection,health,state,el,banner,showError,txt,h,idSafe,statusFlag};
})();
