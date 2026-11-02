// Chat2 / salida 9 · Vista C. Usa SOLO nct_loop, cola50 y watchdog48 existentes.
// Sin servicios nuevos, sin escribir archivos, sin estado inventado y sin timers LLM.
(() => {
'use strict';
const A=window.YAIWES_PANEL,$=id=>document.getElementById(id);
if(!A||!$('lp-resources')||!$('lr-refresh'))return;
const ui=Object.fromEntries(['refresh','link','revision','count','dag','dag-list','queue-status','queue-id','queue-tasks','watch-status','watch-id','watch-detail','native-canvas','open-cola','open-watchdog','open-anchor','open-exec','notice'].map(k=>[k,$('lr-'+k)]));
let scope=null,seq=0,loading=false;
const make=(tag,cls,txt)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(txt!==undefined)e.textContent=String(txt);return e};
const setNotice=(txt,err)=>{ui.notice.textContent=String(txt).slice(0,350);ui.notice.classList.toggle('error',!!err)};
const validID=v=>A.idSafe(v);
function reset(){
 ui.link.textContent='◌ Sin LOOP vinculado';ui.revision.textContent='Revisión —';
 ui.count.textContent='0 triggers confirmados';
 ui['queue-status'].textContent=ui['watch-status'].textContent='SIN VERIFICAR';
 ui['queue-status'].dataset.state=ui['watch-status'].dataset.state='unknown';
 ui['queue-id'].textContent='Ninguna cola asociada al LOOP.';
 ui['queue-tasks'].textContent='Sin tareas consultadas.';
 ui['watch-id'].textContent='No hay identificador confirmado.';
 ui['watch-detail'].textContent='No se ejecutan temporizadores en el navegador.';
 ui.dag.replaceChildren();
 ui['dag-list'].replaceChildren(make('p','','Sin datos del motor.'));
}
async function state(){
 if(!scope)throw Error('VINCULAR_LOOP_PRIMERO');
 const r=await A.send('nct_loop','dsl_estado',{op:'get',...scope});
 if(!r||r.ok!==true||r.status!=='PASS'||r.project_id!==scope.project_id||r.loop_id!==scope.loop_id||!Number.isInteger(r.revision)||!Array.isArray(r.contracts)||!r.triggers||Array.isArray(r.triggers))throw Error(r?.error||'DSL_ESTADO_NO_CONFIRMADO');
 return r;
}
function makeSVG(tag,attrs={},txt){
 const n=document.createElementNS('http://www.w3.org/2000/svg',tag);
 for(const [k,v]of Object.entries(attrs))n.setAttribute(k,String(v));
 if(txt!==undefined)n.textContent=String(txt);
 return n;
}
function diagram(r){
 const all=r.contracts.filter(c=>c&&validID(c.id)).slice(0,100);
 const list=ui['dag-list'];list.replaceChildren();
 if(!all.length){ui.dag.replaceChildren(makeSVG('text',{x:24,y:55,fill:'#bfbfbf'},'Sin contratos reales registrados.'));list.append(make('p','','Sin triggers registrados.'));return}
 const shown=all.slice(0,24),indexed=new Map(shown.map((c,i)=>[c.id,i]));
 const levels=new Map(),byId=new Map(shown.map(x=>[x.id,x]));
 const depth=(id,stack=new Set())=>{
  if(levels.has(id))return levels.get(id);
  if(stack.has(id))return 0;
  stack.add(id);const item=byId.get(id);
  const upstream=(item?.depends_on||[]).filter(x=>byId.has(x));
  const result=upstream.length?Math.min(8,1+Math.max(...upstream.map(d=>depth(d,stack)))):0;
  stack.delete(id);levels.set(id,result);return result;
 };
 shown.forEach(c=>depth(c.id));
 const columns=new Map();
 for(const c of shown){const d=levels.get(c.id)||0;columns.set(d,(columns.get(d)||0)+1)}
 const positions=new Map(),used=new Map();
 const totalCols=Math.max(0,...levels.values())+1;
 const W=Math.max(600,totalCols*238+40),H=Math.max(155,Math.max(...columns.values())*93+40);
 ui.dag.setAttribute('viewBox','0 0 '+W+' '+H);
 ui.dag.style.minWidth=Math.min(W,1800)+'px';
 ui.dag.replaceChildren();
 const defs=makeSVG('defs'),marker=makeSVG('marker',{id:'lr-arrow',markerWidth:9,markerHeight:9,refX:8,refY:4,orient:'auto'});
 marker.append(makeSVG('path',{d:'M0 0 L8 4 L0 8',stroke:'#779bc7','stroke-width':1.5,fill:'none'}));defs.append(marker);ui.dag.append(defs);
 for(const c of shown){
  const lvl=levels.get(c.id)||0,n=used.get(lvl)||0;used.set(lvl,n+1);
  positions.set(c.id,{x:25+lvl*238,y:25+n*93});
 }
 for(const c of shown){
  const to=positions.get(c.id);
  for(const dep of c.depends_on||[]){
   const from=positions.get(dep);if(!from||!to)continue;
   const x1=from.x+198,y1=from.y+26,x2=to.x,y2=to.y+26,m=(x1+x2)/2;
   ui.dag.append(makeSVG('path',{d:'M'+x1+' '+y1+' C'+m+' '+y1+' '+m+' '+y2+' '+x2+' '+y2,fill:'none',stroke:'#7090b3','stroke-width':1.7,'marker-end':'url(#lr-arrow)'}));
  }
 }
 for(const c of shown){
  const pos=positions.get(c.id),s=String(r.triggers[c.id]?.status||'UNKNOWN').toUpperCase();
  const stroke=s==='PASS'?'#348b61':s==='BLOCKED'||s==='FLAGGED'?'#bb6868':s==='RUNNING'?'#2f80ff':'#555';
  ui.dag.append(makeSVG('rect',{x:pos.x,y:pos.y,width:198,height:57,rx:11,fill:'#292929',stroke,'stroke-width':1.5}));
  ui.dag.append(makeSVG('text',{x:pos.x+10,y:pos.y+22,fill:'#ededed','font-size':12,'font-weight':650},String(c.name||c.id).slice(0,24)));
  ui.dag.append(makeSVG('text',{x:pos.x+10,y:pos.y+43,fill:'#bfbfbf','font-size':11},c.id+' · '+(c.enabled?'ON':'OFF')+' · '+s.slice(0,13)));
 }
 for(const c of all){
  const card=make('div','lr-step');card.dataset.state=String(r.triggers[c.id]?.status||'UNKNOWN').toUpperCase();
  card.append(make('strong','',String(c.name||c.id).slice(0,120)),make('small','',c.id+' · '+(c.enabled?'ON':'OFF')+' · '+card.dataset.state));
  if((c.depends_on||[]).length)card.append(make('small','','Depende: '+c.depends_on.join(', ').slice(0,130)));
  list.append(card);
 }
 if(all.length>shown.length)list.prepend(make('p','',shown.length+' nodos dibujados de '+all.length+'; el listado incluye todos.'));
}
async function refresh(){
 if(!scope||loading)return;
 const turn=++seq;loading=true;ui.refresh.disabled=true;
 try{
  const r=await state();
  if(turn!==seq)return;
  ui.link.textContent='● '+scope.project_id+' / '+scope.loop_id+' · backend confirmado';
  ui.revision.textContent='Revisión '+r.revision;
  ui.count.textContent=r.contracts.length+' triggers reales';
  diagram(r);
  const q=r.queue;
  ui['queue-status'].textContent=String(q?.status||'SIN COLA').toUpperCase();
  ui['queue-status'].dataset.state=String(q?.status||'unknown').toLowerCase();
  ui['queue-id'].textContent=q?.queue_id?'CIT-50 · '+String(q.queue_id).slice(0,80):'Sin cola del LOOP creada.';
  ui['queue-tasks'].textContent=Array.isArray(q?.tasks)?q.tasks.length+' tareas del backend · '+q.tasks.filter(x=>x.status==='succeeded').length+' completadas':'Sin tareas confirmadas.';
  if(!r.watchdog_id){
   ui['watch-status'].textContent='SIN WATCHDOG';ui['watch-status'].dataset.state='unknown';
   ui['watch-id'].textContent='El LOOP no informa un watchdog_id.';
   ui['watch-detail'].textContent='Ninguna conexión simulada.';
  }else{
   const wid=r.watchdog_id;
   ui['watch-id'].textContent='Watchdog48 · '+wid;
   ui['watch-status'].textContent='CONSULTANDO';ui['watch-status'].dataset.state='unknown';
   ui['watch-detail'].textContent='Esperando lectura del plugin.';
   try{
    const watch=await A.send('watchdog48','estado',{wid});
    if(turn!==seq)return;
    if(!watch||watch.id!==wid||watch.target_id!==q?.queue_id||typeof watch.status!=='string')throw Error('WATCHDOG_NO_CONFIRMADO');
    ui['watch-status'].textContent=watch.status.toUpperCase();ui['watch-status'].dataset.state=watch.status.toLowerCase();
    ui['watch-detail'].textContent='Objetivo '+watch.target_type+' · '+String(watch.target_id)+' · '+String(watch.checks??0)+' comprobaciones reales.';
   }catch(e){if(turn!==seq)return;ui['watch-status'].textContent='NO CONFIRMADO';ui['watch-detail'].textContent=String(e.message||e).slice(0,210)}
  }
  if(turn===seq)setNotice('Canvas de solo lectura y motores sincronizados con el backend · revisión '+r.revision);
 }catch(e){
  if(turn===seq){reset();setNotice('Estado sin verificar: '+String(e.message||e),true)}
 }finally{if(turn===seq){loading=false;ui.refresh.disabled=false}}
}
const native=async target=>{
 try{
  const out=await A.openNative(target);
  if(!(out?.opened||out?.requested))throw Error('NAVEGACION_NO_CONFIRMADA');
  setNotice(target==='canvas'?'Abierta navegación a Canvas existente. Su mapa tiene su propio botón.':'Ventana '+target+' abierta con los controles existentes.');
 }catch(e){setNotice('No se pudo abrir '+target+': '+String(e.message||e),true)}
};
ui.refresh.addEventListener('click',refresh);
ui['native-canvas'].addEventListener('click',()=>native('canvas'));
ui['open-cola'].addEventListener('click',()=>native('cola'));
ui['open-watchdog'].addEventListener('click',()=>native('watchdog'));
ui['open-anchor'].addEventListener('click',()=>A.openAnchor('general').catch(e=>setNotice(String(e.message||e),true)));
ui['open-exec'].addEventListener('click',()=>$('lp-tab-exec')?.click());
window.addEventListener('yaiwes:loop-verified',e=>{
 const p=e.detail?.project_id,l=e.detail?.loop_id;
 if(!validID(p)||!validID(l))return;
 seq++;scope={project_id:p,loop_id:l};reset();refresh();
});
window.addEventListener('yaiwes:loop-unverified',()=>{
 seq++;scope=null;reset();setNotice('Vincula primero un LOOP real. Las ventanas nativas siguen disponibles.');
});
window.addEventListener('yaiwes:resources-view-open',()=>{if(scope)refresh()});
window.addEventListener('yaiwes:exec-state-updated',()=>{if(scope)refresh()});
reset();
})();