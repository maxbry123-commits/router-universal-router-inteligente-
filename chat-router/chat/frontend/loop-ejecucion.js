// YAIWES Vista D / Salida 8. Progreso por recibos reales; sin ejecución implícita.
(() => {
'use strict';
const A=window.YAIWES_PANEL,$=id=>document.getElementById(id);
if(!A||!$('lp-execution')||!$('lx-refresh'))return;
const ui=Object.fromEntries(['state','queue','revision','progress','bar','progress-desc','phase','phase-desc','check-select','check','check-result','start','pause','resume','cancel','one','checklist','done','flags','flags-refresh','refactor','refactor-open','close-check','close-result','message','refresh'].map(k=>[k,$('lx-'+k)]));
let scope=null,last=null,loading=false,acting=false,unknownAction=false,version=0,refreshQueued=false;
const states=['PASS','NOT_APPLICABLE','BLOCKED','FLAGGED','RUNNING','STARTED','QUEUED','OFF','UNKNOWN'];
const positive=new Set(['PASS','NOT_APPLICABLE']),queueDone=new Set(['completed']),canStop=new Set(['running','paused']);
const note=(s,error=false)=>{ui.message.textContent=String(s).slice(0,500);ui.message.classList.toggle('lx-error',error)};
const safe=s=>A.idSafe(s);
const phaseName=s=>String(s||'').slice(0,180);
const codeStatus=s=>String(s||'UNKNOWN').toUpperCase();
const queueStatus=r=>String(r?.queue?.status||'').toLowerCase();
const taskState=v=>{const c=String(v||'UNKNOWN').toUpperCase();return states.includes(c)?c:'UNKNOWN'};
const trState=(r,id)=>taskState(r?.triggers?.[id]?.status);
const make=(tag,cls,text)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=String(text);return e};
async function get(op='get',extra={}){
 if(!scope)throw Error('LOOP_NO_VINCULADO');
 const p={project_id:scope.project_id,loop_id:scope.loop_id,op,...extra};
 const r=await A.send('nct_loop','dsl_estado',p);
 if(r?.ok!==true||r.status!=='PASS'||(op!=='checkpoint'&&(r.project_id!==scope.project_id||r.loop_id!==scope.loop_id)))throw Error(r?.error||'DSL_ESTADO_NO_VERIFICADO');
 return r;
}
function valid(r){
 return !!r&&r.ok===true&&r.status==='PASS'&&Number.isInteger(r.revision)&&Array.isArray(r.contracts)&&
   r.triggers&&typeof r.triggers==='object'&&!Array.isArray(r.triggers);
}
function buttons(r=last){
 const verified=!!scope&&valid(r),q=queueStatus(r),started=!!r?.queue?.queue_id,any=!!r?.contracts?.some(c=>c.enabled===true);
 ui.start.disabled=!verified||started||!any||loading||acting||unknownAction;
 ui.pause.disabled=!verified||q!=='running'||loading||acting||unknownAction;
 ui.resume.disabled=!verified||q!=='paused'||loading||acting||unknownAction;
 ui.cancel.disabled=!verified||!canStop.has(q)||loading||acting||unknownAction;
 ui.one.disabled=!verified||q!=='running'||loading||acting||unknownAction;
 ui.check.disabled=!verified||!ui['check-select'].value||loading||acting;
 ui['close-check'].disabled=!verified||loading||acting;
}
function reset(){
 last=null;
 ui.state.textContent='◌ Sin verificar';ui.state.dataset.state='UNKNOWN';
 ui.queue.textContent='Sin cola del LOOP confirmada';
 ui.revision.textContent='Revisión —';ui.progress.textContent='—';ui.bar.hidden=true;
 ui['progress-desc'].textContent='Vincula el LOOP para consultar evidencias.';
 ui.phase.textContent='Sin datos';ui['phase-desc'].textContent='Las fases se leen de loop_meta.segments.';
 ui['check-select'].replaceChildren(new Option('Vincula el LOOP',''));
 ui['check-result'].textContent='Sin lectura.';
 ui.checklist.replaceChildren(make('p','', 'Sin ejecución confirmada.'));
 ui.done.textContent='—';ui.flags.textContent='Sin consulta.';
 ui.refactor.textContent='Sin contratos de refactoría consultados.';
 ui['close-result'].textContent='Sin revisión de cierre.';
 buttons(null);
}
function render(r){
 if(!valid(r))throw Error('RESPUESTA_INCOMPLETA');
 last=r;const q=queueStatus(r),qs=q||'SIN COLA',contracts=r.contracts,enabled=contracts.filter(c=>c.enabled===true),
 finished=enabled.filter(c=>positive.has(trState(r,c.id))),total=enabled.length;
 ui.state.textContent=q?'● '+qs.toUpperCase():'◌ Configurado · sin ejecución';
 ui.state.dataset.state=q||'draft';
 ui.queue.textContent=r.queue?.queue_id?'CIT-50 · '+String(r.queue.queue_id).slice(0,80):'Sin cola del LOOP creada';
 ui.revision.textContent='Revisión '+r.revision;
 ui.progress.textContent=total?finished.length+' / '+total:'0 / 0';
 ui.bar.hidden=!total;ui.bar.max=Math.max(1,total);ui.bar.value=finished.length;
 ui['progress-desc'].textContent=total?'Contratos habilitados con PASS / NO APLICA (respuesta del backend).':'Ningún contrato habilitado. Sin porcentaje de avance.';
 const segments=r.loop_meta?.segments;
 if(Array.isArray(segments)&&segments.length&&Number.isInteger(r.phase_index)&&r.phase_index>=0&&r.phase_index<=segments.length){
   const i=r.phase_index,at=segments[i];
   ui.phase.textContent=at?String(at.name||at.id||'Fase sin nombre').slice(0,100):'Fases finalizadas según backend';
   ui['phase-desc'].textContent=at?'Fase '+(i+1)+' de '+segments.length+' · '+String((at.trigger_ids||[]).length)+' triggers':'Índice final verificado en el backend ('+segments.length+'/'+segments.length+').';
 }else{ui.phase.textContent='Sin fases registradas';ui['phase-desc'].textContent='No se inventan segmentos cuando loop_meta no contiene fases.'}
 const selected=ui['check-select'].value;
 ui['check-select'].replaceChildren(new Option(contracts.length?'Seleccionar trigger':'Sin triggers', ''));
 for(const c of contracts){if(!safe(c.id))continue;ui['check-select'].append(new Option(String(c.name||c.id).slice(0,90),c.id))}
 if(contracts.some(c=>c.id===selected))ui['check-select'].value=selected;
 ui.checklist.replaceChildren();
 if(!contracts.length)ui.checklist.append(make('p','', 'Sin triggers guardados.'));
 for(const c of contracts.slice(0,100)){
   const s=trState(r,c.id),row=make('div','lx-step'),label=make('div','lx-step-label'),flag=make('span','lx-step-state',A.statusFlag(s));
   row.dataset.state=s;label.append(make('strong','',String(c.name||c.id).slice(0,110)),make('small','',c.id+' · '+(c.enabled?'ON':'OFF')));
   const hasProof=s==='PASS'&&!!r.triggers?.[c.id]?.contract_sha256;
   flag.title=hasProof?'Estado PASS del backend; revisar checkpoint para recibos':'Estado informado por el backend';
   row.append(label,flag);ui.checklist.append(row);
 }
 ui.done.textContent=finished.length+' completados / '+total+' ON';
 drawFlags(r);
 const refs=contracts.filter(c=>c.category==='refactoria'),needsN4=contracts.filter(c=>(c.steps||[]).some(s=>s.kind==='TOOL'&&['write_text','create_directory'].includes(s.tool)));
 ui.refactor.replaceChildren(make('p','',refs.length?refs.length+' trigger(s) de refactoría · '+refs.filter(c=>positive.has(trState(r,c.id))).length+' con cierre confirmado.':'No hay contratos de refactoría registrados.'));
 if(needsN4.length)ui.refactor.append(make('p','lx-warning','Aprobación de escritura N4 potencial en '+needsN4.length+' contrato(s). Requiere autorización real del director mediante backend; esta vista no aprueba acciones.'));
 buttons(r);
}
function drawFlags(r){
 ui.flags.replaceChildren();
 const flags=Array.isArray(r.flags)?r.flags:[];
 const blocked=(r.contracts||[]).filter(c=>['BLOCKED','FLAGGED'].includes(trState(r,c.id)));
 if(!flags.length&&!blocked.length){ui.flags.append(make('p','', 'Sin flags comunicadas por el backend; esto no garantiza ausencia de problemas.'));return}
 for(const c of blocked.slice(0,15))ui.flags.append(make('p','lx-warning',c.id+' · '+trState(r,c.id)));
 for(const f of flags.slice(0,15)){
  const t=typeof f==='string'?f:(f&&typeof f==='object'?String(f.reason||f.code||f.symbol||JSON.stringify(f)):'FLAG');
  ui.flags.append(make('p','lx-warning',t.slice(0,220)));
 }
}
async function refresh(){
 if(!scope)return;
 if(loading||acting){refreshQueued=true;return}
 const stamp=version;loading=true;buttons();
 try{
  const r=await get();
  if(stamp!==version)return;
  if(!valid(r))throw Error('CONTRATOS_NO_CONFIRMADOS');
  render(r);unknownAction=false;note('Estado leído del backend · revisión '+r.revision+(r.queue?' · cola '+queueStatus(r):' · sin cola'));
 }catch(e){if(stamp===version){last=null;note('Estado NO confirmado: '+String(e.message||e),true);reset()}}
 finally{
   loading=false;buttons();
   if(refreshQueued&&scope&&!acting){refreshQueued=false;refresh()}
 }
}
async function action(op){
 if(!scope||!last||acting||loading||unknownAction)return;
 const now=queueStatus(last);
 if(op==='start'&&last.queue)return;
 if(op==='pause'&&now!=='running')return;
 if(op==='resume'&&now!=='paused')return;
 if(op==='cancel'&&!canStop.has(now))return;
 if(op==='run_ready'&&now!=='running')return;
 if(op==='cancel'&&!window.confirm('¿Cancelar la cola real de este LOOP? La acción no se puede deshacer.'))return;
 acting=true;buttons();const stamp=version;
 try{
  const before=await get(),params={project_id:scope.project_id,loop_id:scope.loop_id,op};
  if(op==='start')params.expected_revision=before.revision;
  if(op==='run_ready')params.max_steps=1;
  const result=await A.send('nct_loop','dsl_control',params);
  if(result?.ok===false||result?.error)throw Error(result.error||'OPERACION_RECHAZADA');
  if(result?.ok!==true)throw Error('RECIBO_OPERACION_FALTANTE');
  if(stamp!==version)return;
  const after=await get();
  if(stamp!==version)return;
  if(!valid(after))throw Error('READBACK_NO_CONFIRMADO');
  const q=queueStatus(after);
  if(op==='start'&&(q!=='running'||!after.queue?.queue_id||after.revision!==before.revision+1))throw Error('START_READBACK_NO_CONFIRMADO');
  if(op==='pause'&&q!=='paused')throw Error('PAUSA_NO_CONFIRMADA');
  if(op==='resume'&&q!=='running')throw Error('REANUDACION_NO_CONFIRMADA');
  if(op==='cancel'&&q!=='cancelled')throw Error('CANCELACION_NO_CONFIRMADA');
  render(after);unknownAction=false;
  const processed=Array.isArray(result.processed)?result.processed.length:0;
  note(op==='run_ready'?'Solicitud de 1 trigger · backend '+String(result.status||'DESCONOCIDO')+' · '+processed+' resultado(s); verificación actualizada.':'Control '+op+' confirmado · cola '+q);
  window.dispatchEvent(new CustomEvent('yaiwes:exec-state-updated'));
 }catch(e){
  unknownAction=true;
  note('Operación con estado no confirmado ('+op+'): '+String(e.message||e)+'. Consulta el estado antes de cualquier reintento.',true);
 }finally{acting=false;buttons()}
}
async function checkpoint(){
 if(!last||!scope||acting)return;
 const tid=ui['check-select'].value;if(!safe(tid)||!last.contracts.some(c=>c.id===tid))return;
 ui.check.disabled=true;
 try{
  const result=await get('checkpoint',{trigger_id:tid});
  const cp=result.checkpoint;
  if(!cp||typeof cp!=='object'){ui['check-result'].textContent=tid+' · sin checkpoint registrado.';return}
  const refs=Array.isArray(cp.receipts)?cp.receipts.length:0;
  const proof=cp.status==='PASS'&&(!!cp.queue_receipt_ref||refs>0||Object.keys(cp.anchor_receipts||{}).length>0);
  ui['check-result'].textContent=tid+' · '+String(cp.status||'UNKNOWN')+' · '+refs+' recibos'+(proof?' · evidencia disponible':' · falta evidencia de cierre');
 }catch(e){ui['check-result'].textContent='Checkpoint no confirmado: '+String(e.message||e)}
 finally{buttons()}
}
async function flags(){
 if(!scope||loading||acting)return;
 try{const r=await get('flags');if(!valid(r))throw Error('FLAGS_INVALIDOS');drawFlags(r);note('Flags consultadas en backend.');}
 catch(e){ui.flags.textContent='Sin lectura de flags: '+String(e.message||e);note('Flags no verificadas',true)}
}
async function closeCheck(){
 if(!scope||!last||acting||loading)return;
 ui['close-check'].disabled=true;
 try{
  const current=await get();if(!valid(current))throw Error('READBACK_NO_CONFIRMADO');
  const active=current.contracts.filter(c=>c.enabled===true);
  const completed=active.filter(c=>positive.has(trState(current,c.id)));
  if(!active.length||completed.length!==active.length){ui['close-result'].textContent='🚩 Cierre bloqueado: '+completed.length+' de '+active.length+' triggers habilitados con estado terminal aceptado.';return}
  if(!queueDone.has(queueStatus(current))){ui['close-result'].textContent='🚩 Cierre bloqueado: la cola CIT-50 no informa completed.';return}
  const r=await A.send('nct_loop','dsl_control',{project_id:scope.project_id,loop_id:scope.loop_id,op:'next_loop'});
  if(r?.ok!==true||!Array.isArray(r.completed)||!Array.isArray(r.eligible)||r.dispatched!==false)throw Error(r?.error||'CONTINUIDAD_NO_VERIFICADA');
  if(active.some(c=>!r.completed.includes(c.id))){ui['close-result'].textContent='🚩 Cierre sin evidencia completa en next_loop. Pendiente de reconciliación.';return}
  ui['close-result'].textContent='✅ Criterios de cierre verificados por backend · '+r.completed.length+' recibos elegibles para continuidad. dispatched=false: NO se despachó otro LOOP.';
 }catch(e){ui['close-result'].textContent='🚩 Cierre no confirmado: '+String(e.message||e)}
 finally{buttons()}
}
ui.refresh.addEventListener('click',()=>{unknownAction=false;refresh()});
ui.start.addEventListener('click',()=>action('start'));
ui.pause.addEventListener('click',()=>action('pause'));
ui.resume.addEventListener('click',()=>action('resume'));
ui.cancel.addEventListener('click',()=>action('cancel'));
ui.one.addEventListener('click',()=>action('run_ready'));
ui.check.addEventListener('click',checkpoint);
ui['check-select'].addEventListener('change',()=>buttons());
ui['flags-refresh'].addEventListener('click',flags);
ui['close-check'].addEventListener('click',closeCheck);
ui['refactor-open'].addEventListener('click',()=>{$('lp-tab-work')?.click();$('categories')?.scrollIntoView({block:'nearest',behavior:'smooth'})});
window.addEventListener('yaiwes:loop-verified',e=>{
 const p=e.detail?.project_id,l=e.detail?.loop_id;
 if(!safe(p)||!safe(l))return;
 scope={project_id:p,loop_id:l};version++;reset();refresh();
});
window.addEventListener('yaiwes:loop-unverified',()=>{version++;scope=null;unknownAction=false;refreshQueued=false;reset();note('Vincula el LOOP para consultar su ejecución.')});
window.addEventListener('yaiwes:exec-refresh',()=>{unknownAction=false;refresh()});
window.addEventListener('yaiwes:exec-view-open',()=>{if(scope)refresh()});
window.addEventListener('yaiwes:exec-open',e=>{if(e.detail?.focus==='checkpoint')setTimeout(()=>ui['check-select'].focus(),0);else if(e.detail?.focus==='flags')setTimeout(()=>ui['flags-refresh'].focus(),0)});
reset();
})();