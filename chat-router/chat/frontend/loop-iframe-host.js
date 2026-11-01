// Chat 2: panel LOOP independiente, mismo origen, sin claves dentro del iframe.
const CHANNEL='yaiwes.loop.ui.v1';
const ALLOWED=new Set(['status','dsl_estado','dsl_config','dsl_control','mirror_listar']);
let selected=null;
export function loopNewUIEnabled(){try{return localStorage.getItem('yaiwes_loop_panel_v1')!=='off';}catch{return true;}}
function powerState(status){
  const button=document.querySelector('#btn-loop-power');if(!button)return;
  const s=String(status||'UNKNOWN').toUpperCase(),yes=s==='RUNNING',known=yes||['OFF','PAUSED','STOPPED','IDLE','DRAFT'].includes(s);
  button.textContent=known?'LOOP '+(yes?'ON':'OFF'):'LOOP ?';button.setAttribute('aria-pressed',String(yes));
  button.title=known?'Backend: '+s:'Estado real no confirmado';button.dataset.verified=known?'true':'false';
}
async function api(action,payload){
  if(typeof window.RIU_PLUGIN!=='function')throw Error('BACKEND_NO_DISPONIBLE');
  const r=await window.RIU_PLUGIN('nct_loop',action,payload);
  const d=r&&r.result&&typeof r.result==='object'?r.result:r;
  if(!d||d.error||d.ok===false)throw Error(String(d?.error||'BACKEND_RECHAZADO'));return d;
}
export function renderLoopIFrame(cuerpo){
  selected=null;powerState();
  const f=document.createElement('iframe');f.src='/chat/ui/loop-panel.html';
  f.title='LOOP YAIWES aislado';f.style.cssText='width:100%;height:min(78dvh,900px);min-height:480px;background:#1B1B1B;border:0;border-radius:12px;';
  const back=document.createElement('button');back.type='button';back.className='secondary';back.textContent='Volver a la interfaz LOOP anterior';back.onclick=()=>{localStorage.setItem('yaiwes_loop_panel_v1','off');location.reload();};
  cuerpo.replaceChildren(f,back);
  const listener=async(event)=>{
    const d=event.data;if(event.origin!==location.origin||event.source!==f.contentWindow||!d||d.channel!==CHANNEL||d.type!=='request')return;
    if(!/^r-[a-z0-9-]{1,100}$/i.test(String(d.id||'')))return;
    let size=Infinity;try{size=JSON.stringify(d).length}catch{}if(size>260000)return;
    const reply={channel:CHANNEL,type:'reply',id:d.id,ok:false};
    try{
      if(d.name==='plugin'){
        if(d.plugin!=='nct_loop'||!ALLOWED.has(d.action)||!d.payload||typeof d.payload!=='object'||Array.isArray(d.payload))throw Error('ACCION_NO_AUTORIZADA');
        reply.result=await api(d.action,d.payload);reply.ok=true;
      }else if(d.name==='selection'){
        const p=d.payload||{};
        if(!/^[\w-]{1,80}$/.test(p.project_id||'')||!/^[\w-]{1,80}$/.test(p.loop_id||''))throw Error('IDS_INVALIDOS');
        const k={project_id:p.project_id,loop_id:p.loop_id};
        const s=await api('dsl_estado',{op:'get',...k});
        if(!s.status||s.project_id!==k.project_id||s.loop_id!==k.loop_id)throw Error('SELECCION_NO_VERIFICADA');
        selected=k;powerState(s.status);reply.result={selected:true,status:s.status};reply.ok=true;
      }else if(d.name==='open_anchor'){
        const b=document.querySelector('#btn-ancla');if(!b)throw Error('ANCLA_NO_DISPONIBLE');b.click();reply.ok=true;reply.result={opened:true,anchored:false};
      }else throw Error('OPERACION_NO_AUTORIZADA');
    }catch(e){reply.error=String(e.message||e).slice(0,180)}
    if(f.isConnected&&f.contentWindow)f.contentWindow.postMessage(reply,location.origin);
  };
  window.addEventListener('message',listener);
  const watcher=new MutationObserver(()=>{if(!f.isConnected){watcher.disconnect();window.removeEventListener('message',listener);}});
  watcher.observe(document.body,{childList:true,subtree:true});
}
export function mountLoopPowerButton(){
  const bar=document.querySelector('#composer .composer-bar');if(!bar||document.querySelector('#btn-loop-power'))return;
  const button=document.createElement('button');button.id='btn-loop-power';button.type='button';button.className='secondary';button.style.minHeight='44px';
  bar.insertBefore(button,bar.querySelector('.action')||null);powerState();
  button.onclick=async()=>{
    if(!selected){button.title='Abre LOOP y vincula el proyecto primero';return}
    button.disabled=true;try{
      const old=await api('dsl_estado',{op:'get',...selected});
      if(!old.status||old.project_id!==selected.project_id||old.loop_id!==selected.loop_id)throw Error('ESTADO_NO_VERIFICADO');
      const op=String(old.status).toUpperCase()==='RUNNING'?'pause':'start';
      await api('dsl_control',{...selected,op,expected_revision:old.revision});
      const now=await api('dsl_estado',{op:'get',...selected});
      if(!now.status||now.project_id!==selected.project_id||now.loop_id!==selected.loop_id||op==='start'&&now.status!=='RUNNING'||op==='pause'&&now.status==='RUNNING')throw Error('CONTROL_NO_CONFIRMADO');
      powerState(now.status);
    }catch(e){powerState();button.title=String(e.message||e)}finally{button.disabled=false}
  };
}