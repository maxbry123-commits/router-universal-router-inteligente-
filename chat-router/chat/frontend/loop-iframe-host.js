import { abrirAnclajeUniversal } from "./anclaje-puente-universal.js";
// Chat 2: panel LOOP independiente, mismo origen, sin claves dentro del iframe.
const CHANNEL='yaiwes.loop.ui.v1';
const ALLOWED=new Set(['status','dsl_estado','dsl_config','dsl_control','mirror_listar']);
const COLA_ACTIONS=new Set(['listar','estado','crear']);
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
        if(!d.payload||typeof d.payload!=='object'||Array.isArray(d.payload))throw Error('PAYLOAD_INVALIDO');
        if(d.plugin==='nct_loop'&&ALLOWED.has(d.action))reply.result=await api(d.action,d.payload);
        else if(d.plugin==='cola50'&&COLA_ACTIONS.has(d.action)){
          if(!selected)throw Error('VERIFICA_LOOP_PRIMERO');
          const p=d.payload;
          if(d.action==='listar'&&!/^loop_[a-f0-9]{40}$/.test(String(p.chat_id||'')))throw Error('SCOPE_COLA_INVALIDO');
          if(d.action==='estado'&&!/^cit_[a-f0-9]{20}$/.test(String(p.qid||'')))throw Error('QID_COLA_INVALIDO');
          if(d.action==='crear'){
            if(!/^loop_[a-f0-9]{40}$/.test(String(p.chat_id||''))||p.mode!=='sequential'||typeof p.title!=='string'||!p.title.trim()||p.title.length>150||!Array.isArray(p.tasks)||p.tasks.length!==1||p.tasks[0]?.type!=='model'||p.tasks[0]?.id!=='t1'||typeof p.tasks[0]?.prompt!=='string'||!p.tasks[0].prompt.trim()||p.tasks[0].prompt.length>24000)throw Error('CONTRATO_CREACION_COLA_INVALIDO');
          }
          if(typeof window.RIU_PLUGIN!=='function')throw Error('BACKEND_NO_DISPONIBLE');
          const r=await window.RIU_PLUGIN('cola50',d.action,p);
          const result=r&&r.result&&typeof r.result==='object'?r.result:r;
          if(!result||result.error||result.ok===false)throw Error(String(result?.error||'COLA_RECHAZADA'));
          reply.result=result;
        }else if(d.plugin==='watchdog48'&&d.action==='estado'){
          if(!selected)throw Error('VERIFICA_LOOP_PRIMERO');
          const state=await api('dsl_estado',{op:'get',...selected});
          const wid=String(d.payload.wid||'');
          if(!/^wd_[0-9a-f]{20}$/.test(wid)||state.watchdog_id!==wid)throw Error('WATCHDOG_FUERA_DEL_LOOP');
          if(typeof window.RIU_PLUGIN!=='function')throw Error('BACKEND_NO_DISPONIBLE');
          const raw=await window.RIU_PLUGIN('watchdog48','estado',{wid});
          const result=raw?.result&&typeof raw.result==='object'?raw.result:raw;
          if(!result||result.error||result.id!==wid||result.target_id!==state.queue?.queue_id)throw Error(String(result?.error||'WATCHDOG_NO_CONFIRMADO'));
          reply.result=result;
        }else throw Error('ACCION_NO_AUTORIZADA');
        reply.ok=true;
      }else if(d.name==='selection'){
        const p=d.payload||{};
        if(!/^[\w-]{1,80}$/.test(p.project_id||'')||!/^[\w-]{1,80}$/.test(p.loop_id||''))throw Error('IDS_INVALIDOS');
        const k={project_id:p.project_id,loop_id:p.loop_id};
        const s=await api('dsl_estado',{op:'get',...k});
        if(!s.status||s.project_id!==k.project_id||s.loop_id!==k.loop_id)throw Error('SELECCION_NO_VERIFICADA');
        selected=k;powerState(s.status);reply.result={selected:true,status:s.status};reply.ok=true;
      }else if(d.name==='open_native'){
        const target=String(d.payload?.target||'');
        if(!['canvas','cola','watchdog'].includes(target))throw Error('VENTANA_NO_AUTORIZADA');
        const loop=document.querySelector('#ventana-loop');
        if(!loop)throw Error('LOOP_WINDOW_MISSING');
        const wasOpen=!loop.hidden;
        if(target==='canvas'){
          const nav=document.querySelector('[data-view="canvas"]');
          if(!nav)throw Error('CANVAS_TAB_MISSING');
          if(wasOpen)loop.hidden=true;
          try{
            nav.click();
            if(nav.getAttribute('aria-current')!=='page')throw Error('CANVAS_NAV_NO_CONFIRMADA');
            reply.ok=true;reply.result={requested:true,target:'canvas',native:true,note:'Canvas del chat; abre el mapa mental con su botón existente'};
          }catch(e){if(wasOpen&&loop.isConnected)loop.hidden=false;throw e}
        }else{
          const panel=document.querySelector('#ventana-'+target);
          const button=document.querySelector('#btn-'+target);
          if(!panel||!button)throw Error('VENTANA_NATIVA_NO_DISPONIBLE');
          if(wasOpen)loop.hidden=true;
          try{
            if(panel.hidden)button.click();
            if(panel.hidden)throw Error('VENTANA_NATIVA_NO_ABIERTA');
            if(wasOpen){
              const observer=new MutationObserver(()=>{if(panel.hidden){observer.disconnect();if(loop.isConnected)loop.hidden=false}});
              observer.observe(panel,{attributes:true,attributeFilter:['hidden']});
            }
            reply.ok=true;reply.result={opened:true,native:true,target};
          }catch(e){if(wasOpen&&loop.isConnected)loop.hidden=false;throw e}
        }
      }else if(d.name==='open_pending'){
        const pending=document.querySelector('#ventana-pendientes');
        const btn=document.querySelector('#btn-pendientes');
        const loop=document.querySelector('#ventana-loop');
        if(!pending||!btn||!loop)throw Error('PENDIENTES_NO_DISPONIBLES');
        const restore=!loop.hidden;
        if(restore)loop.hidden=true;
        try{
          if(pending.hidden)btn.click();
          if(pending.hidden)throw Error('PENDIENTES_NO_ABIERTOS');
          if(restore){const obs=new MutationObserver(()=>{if(pending.hidden){obs.disconnect();if(loop.isConnected)loop.hidden=false}});obs.observe(pending,{attributes:true,attributeFilter:['hidden']})}
          reply.ok=true;reply.result={opened:true,native:true};
        }catch(e){if(restore&&loop.isConnected)loop.hidden=false;throw e}
      }else if(d.name==='open_anchor'){
        const kind=String(d.payload?.kind||'general');
        if(!['general','handoff','files','notes','constitution'].includes(kind))throw Error('ANCLA_SECCION_INVALIDA');
        const result=abrirAnclajeUniversal('loop',kind==='constitution'?'constitucion':'chat');
        const target=kind==='handoff'?'#ancla-handoffs':kind==='files'?'#anc-lista':kind==='notes'?'.anc3-list':null;
        if(kind==='handoff'){
          const h=document.querySelector('#ancla-handoffs');if(h)h.open=true;
        }
        if(target)document.querySelector(target)?.scrollIntoView({block:'nearest',behavior:'smooth'});
        reply.ok=true;reply.result={...result,section:kind,anchored:false};
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