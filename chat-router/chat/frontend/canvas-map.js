(() => {
'use strict';
const CHANNEL='yaiwes.canvas.ui.v1', waiting=new Map();
const $=id=>document.getElementById(id);
const NS='http://www.w3.org/2000/svg';
const N=(tag,attrs={},val)=>{const e=document.createElementNS(NS,tag);for(const [k,v]of Object.entries(attrs))e.setAttribute(k,String(v));if(val!==undefined)e.textContent=String(val);return e;};
const SAMPLE={schema_id:'yaiwes.canvas.graph.v1',graph_id:'MAP-LOCAL-001',project_id:'P-001',loop_id:'LOOP-001',mode:'mindmap',title:'YAIWES · mapa de ejemplo LOCAL',note:'Ejemplo de diseño, SIN resultados remotos',nodes:[
{id:'objetivo',title:'Proyecto / objetivo',kind:'root',status:'UNKNOWN',x:90,y:270,note:'EJEMPLO LOCAL; sin fuente real',evidence_refs:[]},
{id:'arquitectura',title:'Arquitectura',kind:'group',status:'UNKNOWN',x:390,y:140,evidence_refs:[]},
{id:'frontend',title:'Frontend',kind:'component',status:'UNKNOWN',x:390,y:420,evidence_refs:[]},
{id:'checkpoint',title:'Checkpoint',kind:'check',status:'UNKNOWN',x:755,y:285,evidence_refs:[]}],edges:[
{id:'l1',source:'objetivo',target:'arquitectura'}, {id:'l2',source:'objetivo',target:'frontend'},
{id:'l3',source:'arquitectura',target:'checkpoint'}, {id:'l4',source:'frontend',target:'checkpoint'}]};
let graph=JSON.parse(JSON.stringify(SAMPLE)), selected=null,rev=0, remoteSaved=false,originLabel='EJEMPLO LOCAL';
let viewport={x:0,y:0,w:1300,h:760}, dragging=null, movingBg=false, startPoint=null;
const color={PASS:'#36D58A',FLAGGED:'#F9B65D',BLOCKED:'#FF5570',RUNNING:'#70A7F9',UNKNOWN:'#88909B',DRAFT:'#88909B',NOT_APPLICABLE:'#9d9da2',OFF:'#9d9da2'};
const toId=s=>/^[A-Za-z0-9_-]{1,80}$/.test(s||'');
function log(t){const l=$('log'),d=document.createElement('div');d.textContent=new Date().toLocaleTimeString('es')+' · '+String(t).slice(0,240);l.prepend(d);while(l.children.length>24)l.lastChild.remove();}
function markLocal(message){remoteSaved=false;$('local-state').textContent='NO GUARDADO EN SERVIDOR';$('metric-sha').textContent='SHA: pendiente';if(message)log(message);}
function banner(text,success=false){const s=$('server-state');s.textContent=text;s.className='status '+(success?'ok':'warning');log(text);}
function applyMeta(){for(const [k,id] of [['project_id','project-id'],['graph_id','graph-id'],['loop_id','loop-id'],['title','graph-title'],['mode','graph-mode']])graph[k]=$(id).value.trim();}
function syncMeta(){for(const [k,id] of [['project_id','project-id'],['graph_id','graph-id'],['loop_id','loop-id'],['title','graph-title'],['mode','graph-mode']])$(id).value=graph[k]||'';}
function checkLocal(g){if(!g||typeof g!=='object'||g.schema_id!=='yaiwes.canvas.graph.v1'||!toId(g.graph_id)||!toId(g.project_id))throw Error('CONTRATO_INVALIDO');
 if(!['mindmap','dag'].includes(g.mode)||!Array.isArray(g.nodes)||g.nodes.length<1||g.nodes.length>250||!Array.isArray(g.edges)||g.edges.length>500)throw Error('FORMATO_INVALIDO');
 let ids=new Set(),ei=new Set();for(const n of g.nodes){if(!toId(n.id)||ids.has(n.id)||typeof n.title!=='string'||n.title.length>120||!Number.isFinite(n.x)||!Number.isFinite(n.y))throw Error('NODO_INVALIDO');ids.add(n.id);if(n.status==='PASS'&&!(n.evidence_refs||[]).length)throw Error('PASS_SIN_EVIDENCIA');}
 for(const e of g.edges){if(!toId(e.id)||ei.has(e.id)||!ids.has(e.source)||!ids.has(e.target)||e.source===e.target)throw Error('ENLACE_INVALIDO');ei.add(e.id);}
 if(g.mode==='dag'){const next={};for(const n of g.nodes)next[n.id]=[];for(const e of g.edges)next[e.source].push(e.target);const stack=new Set(),done=new Set();function visit(x){if(stack.has(x))throw Error('DAG_CICLICO');if(done.has(x))return;stack.add(x);next[x].forEach(visit);stack.delete(x);done.add(x)}Object.keys(next).forEach(visit)}
 return true;
}
function trim(s,n){s=String(s||'');return s.length>n?s.slice(0,n-1)+'…':s;}
function mouseToGraph(ev){const svg=$('diagram'),r=svg.getBoundingClientRect();return {x:viewport.x+(ev.clientX-r.left)*viewport.w/r.width,y:viewport.y+(ev.clientY-r.top)*viewport.h/r.height};}
function view(){const v=viewport;$('diagram').setAttribute('viewBox',`${v.x} ${v.y} ${v.w} ${v.h}`);}
function render(){
 const edges=$('edge-layer'),nodes=$('node-layer');edges.replaceChildren();nodes.replaceChildren();
 const lookup=new Map(graph.nodes.map(n=>[n.id,n]));const q=$('filter').value.trim().toLowerCase();
 for(const edge of graph.edges){const a=lookup.get(edge.source),b=lookup.get(edge.target);if(!a||!b)continue;
  const ax=a.x+196,ay=a.y+39,bx=b.x,by=b.y+39;
  const mid=(ax+bx)/2;edges.append(N('path',{d:`M${ax},${ay} C${mid},${ay} ${mid},${by} ${bx},${by}`,class:'graph-edge'}));}
 for(const n of graph.nodes){const g=N('g',{transform:`translate(${n.x},${n.y})`,class:'graph-node'+(n.id===selected?' selected':''),'data-id':n.id,'aria-label':n.title});
  if(q&&!(`${n.id} ${n.title} ${n.kind||'task'}`).toLowerCase().includes(q))g.setAttribute('opacity','.24');
  g.append(N('rect',{width:196,height:78}),N('rect',{width:5,height:76,rx:3,fill:color[n.status]||color.UNKNOWN,stroke:'none'}));
  g.append(N('text',{x:16,y:26,fill:'#EDEDED','font-size':13,'font-weight':600},trim(n.title,25)));
  g.append(N('text',{x:16,y:46,fill:'#BFBFBF','font-size':10},trim((n.kind||'task')+' · '+(n.status||'UNKNOWN'),28)));
  g.append(N('text',{x:16,y:63,fill:'#8DA9CF','font-size':10},n.id));
  g.addEventListener('pointerdown',ev=>{ev.stopPropagation();selected=n.id;dragging={id:n.id,start:mouseToGraph(ev),x:n.x,y:n.y};$('diagram').setPointerCapture(ev.pointerId);render();inspector();});
  nodes.append(g);
 }
 $('metric-nodes').textContent=graph.nodes.length+' nodos';$('metric-edges').textContent=graph.edges.length+' relaciones';
 edgeOptions();sources();mobileList();view();
}
function mobileList(){const box=$('mobile-node-list');if(!box)return;box.replaceChildren();for(const n of graph.nodes){const b=document.createElement('button');b.type='button';b.textContent=n.title+' · '+(n.status||'UNKNOWN');b.setAttribute('aria-current',String(n.id===selected));b.onclick=()=>{selected=n.id;viewport.x=n.x-170;viewport.y=n.y-180;viewport.w=540;viewport.h=480;render();inspector();document.querySelector('.inspector')?.scrollIntoView({behavior:'smooth',block:'start'});};box.append(b);}}
function edgeOptions(){for(const id of ['edge-source','edge-target']){const inp=$(id),v=inp.value;inp.replaceChildren();for(const n of graph.nodes)inp.append(new Option(trim(n.title,24),n.id));if(graph.nodes.some(n=>n.id===v))inp.value=v;}}
function inspector(){const n=graph.nodes.find(x=>x.id===selected);$('selected-id').textContent=n?n.id:'Selecciona un nodo';
 for(const id of ['node-title','node-kind','node-status','node-note','node-source','node-checkpoint','node-evidence','btn-node-update'])$(id).disabled=!n;
 if(!n)return;
 $('node-title').value=n.title||'';$('node-kind').value=n.kind||'task';$('node-status').value=n.status||'UNKNOWN';
 $('node-note').value=n.note||'';$('node-source').value=n.source_ref||'';$('node-checkpoint').value=n.checkpoint_ref||'';$('node-evidence').value=(n.evidence_refs||[]).join('\n');
}
function sources(){const box=$('sources-list');box.replaceChildren();const src=graph.nodes.filter(n=>n.source_ref||n.checkpoint_ref||(n.evidence_refs||[]).length);if(!src.length){const d=document.createElement('div');d.textContent='Sin fuentes documentadas';box.append(d);return;}
 for(const n of src){const d=document.createElement('div');d.textContent=n.id+' · '+[n.source_ref,n.checkpoint_ref,...(n.evidence_refs||[])].filter(Boolean).join(' · ');box.append(d);}}
function installGraph(v,tag){checkLocal(v);graph=JSON.parse(JSON.stringify(v));selected=null;rev=0;originLabel=tag;syncMeta();inspector();markLocal('Importado '+tag);$('data-origin').textContent=tag;render();}
function blob(name,content,type){const a=document.createElement('a'),u=URL.createObjectURL(new Blob([content],{type}));a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);}
function downloadJSON(){try{applyMeta();checkLocal(graph);blob(graph.graph_id+'.json',JSON.stringify(graph,null,2),'application/json');log('Descarga JSON local completa')}catch(e){banner(e.message)}}
function downloadSVG(){try{applyMeta();checkLocal(graph);const svg=$('diagram').cloneNode(true);svg.setAttribute('xmlns',NS);svg.setAttribute('width','1500');svg.setAttribute('height','900');
  // Preserve the visible diagram, not arbitrary DOM from external HTML.
  blob(graph.graph_id+'.svg',new XMLSerializer().serializeToString(svg),'image/svg+xml');log('Descarga SVG local completa');}catch(e){banner(e.message)}}
function request(name,args={}){if(window.parent===window||location.protocol==='file:')return Promise.reject(Error('VISTA_LOCAL_SIN_BACKEND'));
 const id='c-'+(crypto.randomUUID?crypto.randomUUID().replace(/-/g,''):Math.random().toString(36).slice(2));
 return new Promise((resolve,reject)=>{const t=setTimeout(()=>{waiting.delete(id);reject(Error('PUENTE_SIN_RESPUESTA'));},12000);
  waiting.set(id,{resolve,reject,t});window.parent.postMessage({channel:CHANNEL,type:'request',id,name,...args},location.origin);});}
window.addEventListener('message',ev=>{if(ev.origin!==location.origin||ev.source!==window.parent)return;const d=ev.data;if(!d||d.channel!==CHANNEL||d.type!=='reply')return;const w=waiting.get(d.id);if(!w)return;clearTimeout(w.t);waiting.delete(d.id);d.ok?w.resolve(d.result):w.reject(Error(d.error||'BACKEND_REJECTED'));});
const plugin=(action,payload)=>request('plugin',{plugin:'nct_loop',action,payload});
async function remote(action){try{applyMeta();if(action==='canvas_load'){if(!toId(graph.project_id)||!toId(graph.graph_id))throw Error('IDENTIFICADOR_INVALIDO');}else checkLocal(graph);let r;
 if(action==='canvas_save'){r=await plugin(action,{project_id:graph.project_id,graph_id:graph.graph_id,graph,expected_revision:rev});
  if(r?.verified!==true)throw Error('SIN_READBACK');rev=r.revision;remoteSaved=true;$('local-state').textContent='GUARDADO EN SERVIDOR (READBACK)';$('metric-sha').textContent='SHA: '+String(r.sha256||'').slice(0,10);}
 else if(action==='canvas_load'){r=await plugin(action,{project_id:graph.project_id,graph_id:graph.graph_id});
  if(!r?.graph)throw Error('SIN_GRAFO');installGraph(r.graph,'SERVIDOR CONFIRMADO');rev=r.revision;remoteSaved=true;
  $('local-state').textContent='RECUPERADO DEL SERVIDOR';$('metric-sha').textContent='SHA: '+String(r.sha256||'').slice(0,10);}
 else r=await plugin('canvas_validate',{graph});
 if(!r||!r.ok)throw Error(r?.error||'BACKEND_REJECTED');banner('● '+action+' · confirmación real',true);
 $('validation-output').textContent='OK · '+JSON.stringify({revision:r.revision,sha256:r.sha256,stats:r.stats});
 }catch(e){banner('◌ '+action+' · '+e.message);$('validation-output').textContent=String(e.message);}}
function updateNode(){const n=graph.nodes.find(x=>x.id===selected);if(!n)return;
 const old=JSON.parse(JSON.stringify(n));n.title=$('node-title').value.trim()||n.id;
 n.kind=$('node-kind').value;n.status=$('node-status').value;n.note=$('node-note').value;
 n.source_ref=$('node-source').value;n.checkpoint_ref=$('node-checkpoint').value;
 n.evidence_refs=$('node-evidence').value.split(/\r?\n/).map(x=>x.trim()).filter(Boolean);
 try{checkLocal(graph);markLocal('Nodo '+n.id+' actualizado');render();}catch(e){Object.assign(n,old);banner('Nodo rechazado · '+e.message);inspector();}}
function wire(){
 for(const input of ['project-id','graph-id','loop-id','graph-title','graph-mode'])$(input).addEventListener('change',()=>{applyMeta();markLocal('Metadatos actualizados');});
 $('btn-import').onclick=()=>$('input-file').click();
 $('input-file').onchange=async ev=>{const f=ev.target.files?.[0];ev.target.value='';if(!f)return;if(f.size>1024*1024){banner('El archivo excede 1MB');return;}
  try{const data=JSON.parse(await f.text());installGraph(data,'ARCHIVO LOCAL: '+trim(f.name,45));}catch(e){banner('Archivo rechazado · '+e.message);}};
 for(const btn of ['btn-export','btn-download-copy'])$(btn).onclick=downloadJSON;
 for(const btn of ['btn-svg','btn-svg-copy'])$(btn).onclick=downloadSVG;
 $('btn-server-save').onclick=()=>remote('canvas_save');$('btn-server-load').onclick=()=>remote('canvas_load');$('btn-validate').onclick=()=>remote('canvas_validate');
 $('btn-node-update').onclick=updateNode;
 $('filter').oninput=render;
 $('btn-add-node').onclick=()=>{let i=graph.nodes.length+1,id='n'+i;while(graph.nodes.some(n=>n.id===id))id='n'+(++i);graph.nodes.push({id,title:'Nueva tarea',kind:'task',status:'UNKNOWN',x:Math.round(viewport.x+viewport.w/2),y:Math.round(viewport.y+viewport.h/2),note:'',evidence_refs:[]});selected=id;markLocal('Nodo '+id+' añadido');render();inspector();};
 $('btn-del-node').onclick=()=>{if(!selected)return;if(graph.nodes.length<=1){banner('Debes conservar al menos un nodo');return;}graph.nodes=graph.nodes.filter(n=>n.id!==selected);graph.edges=graph.edges.filter(e=>e.source!==selected&&e.target!==selected);markLocal('Nodo eliminado localmente');selected=null;render();inspector();};
 $('btn-add-edge').onclick=()=>{const src=$('edge-source').value,dst=$('edge-target').value;if(src===dst){banner('No puedes conectar un nodo consigo mismo');return;}let i=graph.edges.length+1,id='e'+i;while(graph.edges.some(e=>e.id===id))id='e'+(++i);const ed={id,source:src,target:dst};graph.edges.push(ed);
 try{checkLocal(graph);markLocal('Relación '+src+'→'+dst);render();}catch(e){graph.edges.pop();banner('Relación rechazada · '+e.message);}};
 $('btn-open-anchor').onclick=()=>request('open_anchor').then(()=>banner('Selector de anclajes abierto (no ancla automáticamente)',true)).catch(e=>banner(e.message));
 $('btn-zoom-in').onclick=()=>zoom(.80);$('btn-zoom-out').onclick=()=>zoom(1.25);
 $('btn-center').onclick=()=>{viewport={x:0,y:0,w:1300,h:760};view();};
 document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>{document.querySelectorAll('[data-tab]').forEach(x=>x.setAttribute('aria-selected',String(x===b)));document.querySelectorAll('[data-content]').forEach(x=>x.hidden=x.dataset.content!==b.dataset.tab);});
 $('diagram').addEventListener('pointerdown',ev=>{if(ev.target.closest('.graph-node'))return;movingBg=true;startPoint={x:ev.clientX,y:ev.clientY,ox:viewport.x,oy:viewport.y};$('diagram').setPointerCapture(ev.pointerId);});
 $('diagram').addEventListener('pointermove',ev=>{if(dragging){const curr=mouseToGraph(ev),n=graph.nodes.find(x=>x.id===dragging.id);if(n){n.x=Math.round(dragging.x+curr.x-dragging.start.x);n.y=Math.round(dragging.y+curr.y-dragging.start.y);render();}}else if(movingBg&&startPoint){const r=$('diagram').getBoundingClientRect();viewport.x=startPoint.ox-(ev.clientX-startPoint.x)*viewport.w/r.width;viewport.y=startPoint.oy-(ev.clientY-startPoint.y)*viewport.h/r.height;view();}});
 $('diagram').addEventListener('pointerup',()=>{if(dragging){markLocal('Nodo reposicionado');render();}dragging=null;movingBg=false;startPoint=null;});
 $('diagram').addEventListener('pointercancel',()=>{dragging=null;movingBg=false;startPoint=null;});
 $('diagram').addEventListener('wheel',ev=>{ev.preventDefault();zoom(ev.deltaY>0?1.12:.88);},{passive:false});
}
function zoom(f){const cx=viewport.x+viewport.w/2,cy=viewport.y+viewport.h/2;viewport.w=Math.min(6000,Math.max(240,viewport.w*f));viewport.h=Math.min(4000,Math.max(140,viewport.h*f));viewport.x=cx-viewport.w/2;viewport.y=cy-viewport.h/2;view();}
try{wire();syncMeta();render();inspector();log('Mapa EJEMPLO LOCAL · sin motor ni inferencia real');}catch(e){banner('INTERFAZ_ERROR: '+e.message);}
})();
