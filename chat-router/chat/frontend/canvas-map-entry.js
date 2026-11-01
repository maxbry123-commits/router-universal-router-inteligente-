// CHAT 3 — candidato de integración del Canvas EXISTENTE. NO MONTA UNA NUEVA PESTAÑA.
// Uso propuesto en panel-canvas.js, tras montarCanvas(root,{tell}) REAL.
const CHANNEL='yaiwes.canvas.ui.v1';
const OPS=new Set(['canvas_validate','canvas_from_dag','canvas_save','canvas_load']);
export function attachCanvasMapEntry(root){
  const app=root.querySelector('.cv-app');
  if(!app||app.querySelector('#btn-canvas-map'))return;
  const b=document.createElement('button');b.id='btn-canvas-map';b.type='button';
  b.className='mini';b.textContent='◇ Mapa mental / DAG';b.title='Abrir visualizador independiente sin cerrar el visor de medios';
  const dlg=document.createElement('dialog');dlg.setAttribute('aria-label','Canvas · mapa mental');
  dlg.style.cssText='padding:0;border:1px solid #484848;border-radius:14px;background:#1B1B1B;width:min(98vw,1580px);max-width:98vw;height:min(94dvh,1050px);max-height:94dvh';
  const h=document.createElement('header');h.style.cssText='display:flex;justify-content:space-between;align-items:center;gap:10px;padding:7px 14px;background:#202020;color:#EDEDED';
  const title=document.createElement('strong');title.textContent='YAIWES · Mapa mental';
  const close=document.createElement('button');close.type='button';close.textContent='Cerrar ✕';close.style.cssText='min-height:44px';close.onclick=()=>dlg.close();h.append(title,close);
  const frame=document.createElement('iframe');frame.title='Mapa mental YAIWES';frame.src='/chat/ui/canvas-map.html';frame.style.cssText='display:block;border:0;width:100%;height:calc(100% - 54px)';
  dlg.append(h,frame);app.prepend(b);document.body.append(dlg);b.onclick=()=>dlg.showModal();
  dlg.addEventListener('close',()=>b.focus());
  // No pasar secretos por postMessage. El backend se llama desde el chat autorizado.
  const handler=async event=>{
    const m=event.data;
    if(event.origin!==location.origin||event.source!==frame.contentWindow||!m||m.channel!==CHANNEL||m.type!=='request')return;
    if(!/^c-[A-Za-z0-9_-]{1,64}$/.test(String(m.id||''))||JSON.stringify(m).length>1000000)return;
    const r={channel:CHANNEL,type:'reply',id:m.id,ok:false};
    try{
      if(m.name==='plugin'&&m.plugin==='nct_loop'&&OPS.has(m.action)){
        if(typeof window.RIU_PLUGIN!=='function')throw Error('BACKEND_NOT_CONNECTED');
        if(!m.payload||typeof m.payload!=='object'||Array.isArray(m.payload))throw Error('PAYLOAD_INVALID');
        const raw=await window.RIU_PLUGIN('nct_loop',m.action,m.payload);const v=raw?.result||raw;
        if(v?.error||v?.ok===false)throw Error(String(v.error||'BACKEND_REJECTED').slice(0,160));
        r.ok=true;r.result=v;
      } else if(m.name==='open_anchor'){
        const a=document.querySelector('#btn-ancla');if(!a)throw Error('ANCHOR_UI_MISSING');
        a.click();r.ok=true;r.result={opened:true,anchored:false};
      } else throw Error('ACTION_DENIED');
    }catch(e){r.error=String(e.message||e).slice(0,160)}
    if(frame.contentWindow)frame.contentWindow.postMessage(r,location.origin);
  };
  window.addEventListener('message',handler);
  // shell.js calls mount() cleanup when changing panels; avoid listeners/dialogs leaking.
  return () => { window.removeEventListener('message',handler); dlg.close(); dlg.remove(); b.remove(); };
}
