(() => {
'use strict';
const A=window.YAIWES_PANEL;
const cats=[
['Constitución / contexto',['Constitución','Input literal','Handoff anterior','Inventario del proyecto','Contexto de misión']],
['Auditoría inicial',['Archivos y SHA','Arquitectura real','Cableado existente','Dependencias','GAPS y bloqueos']],
['Investigación / software',['Buscar soluciones','Documentación oficial','Auditar componentes','REUSE/PATCH/ADAPT','Plan de incorporación']],
['Arquitectura',['MissionContract','Council y refutaciones','Goals y criterios','DAG por segmentos','Contratos y roots']],
['Backend',['Código Python','APIs existentes','Persistencia','Herramientas y MCP','Pruebas backend']],
['Frontend',['Dirección visual V07','UI aislada','Interacciones','Accesibilidad móvil','Cableado frontend']],
['Canvas',['Plan visual','Mapa mental','Flujos DAG','Dependencias gráficas','Revisión visual']],
['Testing / auditoría',['Pruebas unitarias','Contratos','Integración','Browser QA','X-Ray 4 pasadas']],
['Refactoría / revisión',['Sheriff','Guardián','Auditor independiente','Refactorización autorizada','Regresión final']],
['GitHub / continuidad',['Preparar diff','Aprobación N4','Publicación autorizada','Checkpoint SHA','Handoff próximo LOOP']]
];
const all=[];let chosen=null, catFilter=-1, idsConfirmed=false, connected=false;
const cap=100;
for(let i=0;i<50;i++)all.push({id:'T'+String(i).padStart(2,'0'),title:cats[Math.floor(i/5)][1][i%5],category:Math.floor(i/5),enabled:false,note:'',status:'UNKNOWN',flags:[],contract:null,filename:'',hash:null,serverConfirmed:false});
const roleIDs=[['arquitecto','Arquitectura'],['auditor','Auditoría'],['ejecutor_codigo','Ejecutor de código'],['frontend','Frontend'],['refactor_revision','Refactoría / revisión']];
const stateEl= A.el('notice');
function log(t){const box=A.el('events');const div=A.h('div','',new Date().toLocaleTimeString('es')+' · '+String(t).slice(0,380));box.prepend(div);while(box.children.length>16)box.lastChild.remove();}
function notice(t){stateEl.textContent=t;log(t);}
function pids(){const project_id=A.el('project-id').value.trim(),loop_id=A.el('loop-id').value.trim();if(!A.idSafe(project_id)||!A.idSafe(loop_id))throw Error('Introduce project_id y loop_id reales');return {project_id,loop_id};}
function updateCounts(){A.el('metric-total').textContent=String(all.length);A.el('metric-on').textContent=String(all.filter(x=>x.enabled).length);A.el('metric-pass').textContent=String(all.filter(x=>x.serverConfirmed&&x.status==='PASS').length);A.el('metric-flags').textContent=String(all.filter(x=>x.flags.length||x.status==='BLOCKED').length);}
function rolePanel(){let root=A.el('roles');root.replaceChildren();for(const [id,label] of roleIDs){const wrap=A.h('div','role-row');wrap.append(A.h('span','',label));for(const kind of ['model','agent']){const inp=A.h('select');inp.id='role-'+id+'-'+kind;inp.disabled=true;inp.setAttribute('aria-label',label+' '+kind);inp.append(new Option('Sin datos de backend',''));wrap.append(inp);}root.append(wrap);}}
async function loadRoleOptions(){try{const r=await A.send('nct_loop','mirror_listar',{sesion:'general'});if(!Array.isArray(r?.modelos)||!Array.isArray(r?.agentes))throw Error('CATALOGO_NO_DISPONIBLE');const map=[['model',r.modelos],['agent',r.agentes]];for(const [type,items] of map){for(const [id]of roleIDs){const sel=A.el('role-'+id+'-'+type);sel.replaceChildren(new Option('Seleccionar '+type+' disponible',''));for(const it of items){const key=String(it.id||it.model_id||'');if(!A.idSafe(key))continue;sel.append(new Option(String(it.nombre||it.label||key),key));}sel.disabled=sel.options.length<=1;}}notice('Catálogos reales modelo/agente obtenidos; selecciona ambos para cada rol');}catch(e){notice('Selectores deshabilitados hasta conectar catálogo real: '+e.message);}}
function categories(){const nav=A.el('categories');nav.replaceChildren();const vals=[['Todos los pasos',-1],...cats.map(([x],i)=>[x,i])];for(const [name,index] of vals){const b=A.h('button','railbtn'+(catFilter===index?' sel':''));b.type='button';b.setAttribute('aria-current',String(catFilter===index));b.append(A.h('span','',name),A.h('span','count',index<0?all.length:all.filter(t=>t.category===index).length));b.onclick=()=>{catFilter=index;categories();render();};nav.append(b);}}
function filter(t){const q=A.el('search').value.toLowerCase().trim(),f=A.el('show-filter').value;if(catFilter>=0&&t.category!==catFilter)return false;if(q&&!(''+t.id+' '+t.title+' '+cats[t.category][0]).toLowerCase().includes(q))return false;if(f==='enabled'&&!t.enabled)return false;if(f==='configured'&&!t.contract)return false;if(f==='flags'&&!(t.flags.length||t.status==='BLOCKED'))return false;return true;}
async function remote(action,payload){if(!idsConfirmed)throw Error('Primero vincula project_id y loop_id con el backend');return A.send('nct_loop',action,{...pids(),...payload});}
function mustNoFalsePass(t){if(t.status==='PASS'&&!t.serverConfirmed){t.status='UNKNOWN';} }
async function command(t,op,payload){
  t.serverConfirmed=false;
  try{
    const r=await remote('dsl_config',{op,trigger_id:t.id,...payload});
    if(!r||r?.error||r?.ok===false)throw Error(r?.error||'ESCRITURA_RECHAZADA');
    const check=await remote('dsl_estado',{op:'get'});
    if(!check||!Array.isArray(check.triggers)||!check.status)throw Error('READBACK_TRIGGERS_MISSING');
    const item=check.triggers.find(x=>x.id===t.id);
    if(op==='trigger_remove'){
      if(item)throw Error('ELIMINACION_NO_CONFIRMADA');
    }else{
      if(!item)throw Error('TRIGGER_NO_CONFIRMADO');
      if(op==='trigger_toggle'&&!!item.enabled!==!!payload.enabled)throw Error('TOGGLE_NO_CONFIRMADO');
      if(op==='note_update'&&item.note!==payload.note)throw Error('NOTA_NO_CONFIRMADA');
      if(op==='trigger_upsert'&&(!item.contract_sha||item.contract_sha!==t.hash))throw Error('CONTRATO_SHA_NO_CONFIRMADO');
      if(op==='anchor_bind'&&(!Array.isArray(item.anchor_refs)||!payload.anchor_refs.every(x=>item.anchor_refs.includes(x))))throw Error('ANCLA_NO_CONFIRMADA');
      t.enabled=!!item.enabled;
      t.note=typeof item.note==='string'?item.note:t.note;
      t.status=String(item.status||'UNKNOWN').toUpperCase();
      t.flags=Array.isArray(item.flags)?item.flags:[];
      t.serverConfirmed=true;
    }
    notice(t.id+' · '+op+' READBACK OK · revisión '+String(check.revision??'sin revisión'));
    render();
    return r;
  }catch(e){t.serverConfirmed=false;t.status='UNKNOWN';notice(t.id+' · NO CONFIRMADO: '+e.message);render();throw e;}
}
function detailOf(t){const div=A.h('div','detail');const grid=A.h('div','fieldgrid');const note=A.h('label','field');note.append(A.h('span','','Nota humana — propósito de este trigger'));const area=A.h('textarea');area.value=t.note;area.placeholder='Qué hará este paso, qué archivos revisa y cuándo NO aplica';area.oninput=()=>t.note=area.value;note.append(area);grid.append(note);
 const attach=A.h('div','stack');const read=A.h('span','small muted',t.contract?'Archivo local '+t.filename+' · '+(t.hash?'SHA '+t.hash.slice(0,12):'SHA no disponible'):'Sin archivo asignado • Solo plantilla visual');const f=A.h('input');f.type='file';f.accept='.json,.md,.markdown,application/json,text/markdown';f.setAttribute('aria-label','Adjuntar contrato '+t.id);f.onchange=async()=>{const file=f.files[0];if(!file)return;if(file.size>250000){notice('Archivo > 250KB: usa anclaje existente y backend por referencia');return;}const contents=await file.text();if(file.name.toLowerCase().endsWith('.json')){try{const data=JSON.parse(contents);if(!data||typeof data!=='object'||Array.isArray(data))throw Error();}catch{notice('JSON inválido: no se adjuntó');return;}}
 t.contract=contents;t.filename=file.name;t.hash=null;try{const bytes=new TextEncoder().encode(contents);if(crypto.subtle){const buf=await crypto.subtle.digest('SHA-256',bytes);t.hash=[...new Uint8Array(buf)].map(x=>x.toString(16).padStart(2,'0')).join('');}}catch{}
 t.serverConfirmed=false;notice(t.id+' · archivo leído en el navegador. NO está anclado al backend.');render();};
 attach.append(read,f);grid.append(attach);div.append(grid);
 const btns=A.h('div','row');const save=A.h('button','','Guardar nota');save.onclick=async()=>{if(!idsConfirmed){notice(t.id+' · Nota solo en la vista; falta backend');return;}try{await command(t,'note_update',{note:t.note});}catch{}};
 const validate=A.h('button','','Validar contrato');validate.onclick=async()=>{if(!t.contract){notice('Añade primero JSON');return;}if(!t.filename.toLowerCase().endsWith('.json')){notice('Contrato JSON requerido; Markdown se ancla por referencia');return;}try{const r=await remote('dsl_config',{op:'contract_validate',trigger_id:t.id,contract:JSON.parse(t.contract)});if(r?.error)throw Error(r.error);notice(t.id+' · validación remota '+JSON.stringify(r).slice(0,150));}catch(e){notice(e.message);}};
 const upload=A.h('button','','↥ Guardar JSON');upload.onclick=async()=>{if(!t.contract||!t.filename.toLowerCase().endsWith('.json')){notice('Selecciona un contrato JSON válido');return;}if(!idsConfirmed){notice('Primero vincular backend: archivo solo en memoria local');return;}try{await command(t,'trigger_upsert',{contract:JSON.parse(t.contract),note:t.note,enabled:t.enabled});}catch(e){notice(e.message);}};
 const attachBtn=A.h('button','','⚓ Abrir anclaje');attachBtn.onclick=()=>A.openAnchor().then(()=>notice('Selector del chat abierto. Aún no hay anclaje confirmado.')).catch(e=>notice(e.message));
 const anchorRef=A.h('input');anchorRef.placeholder='ancla:ID_EXISTENTE';anchorRef.setAttribute('aria-label','Referencia de anclaje existente '+t.id);anchorRef.value=t.anchorRef||'';anchorRef.oninput=()=>t.anchorRef=anchorRef.value.trim();div.append(anchorRef);
 const linkAnchor=A.h('button','','Vincular ref');linkAnchor.onclick=async()=>{if(!/^ancla:[A-Za-z0-9_-]{1,80}$/.test(t.anchorRef||'')){notice('Primero obtén el ID real del anclaje del chat');return;}try{await command(t,'anchor_bind',{anchor_refs:[t.anchorRef]});}catch{}};
 const remove=A.h('button','','🗑 Quitar archivo');remove.onclick=async()=>{if(!window.confirm('¿Quitar el contrato local de '+t.id+'?'))return;if(idsConfirmed){try{await command(t,'trigger_remove',{});}catch{return;}}t.contract=null;t.filename='';t.hash=null;t.enabled=false;t.serverConfirmed=false;t.status='UNKNOWN';notice(t.id+' · contrato quitado');render();};
 btns.append(save,validate,upload,attachBtn,linkAnchor,remove);div.append(btns,A.h('p','help','No usar input local como prueba de anclaje. El backend debe responder con revision, contract_sha y receipt_ref.'));return div;}
function render(){const list=A.el('trigger-list');list.replaceChildren();for(const t of all.filter(filter)){mustNoFalsePass(t);const shell=A.h('article','trigger'+(chosen===t.id?' selected':''));const head=A.h('div','trhead');const title=A.h('div','trinfo');title.append(A.h('div','trname',t.title),A.h('div','trdesc',cats[t.category][0]+' · '+(t.filename||'Sin contrato')));const badge=A.h('span','status',A.statusFlag(t.serverConfirmed?t.status:'UNKNOWN'));badge.dataset.status=t.serverConfirmed?t.status:'UNKNOWN';const sw=A.h('label','switch');const inp=A.h('input');inp.type='checkbox';inp.checked=t.enabled;inp.setAttribute('aria-label','Activar '+t.id);inp.onchange=async()=>{let desired=inp.checked;if(!idsConfirmed){t.enabled=desired;notice(t.id+' · '+(desired?'ON':'OFF')+' SOLO VISTA LOCAL. No se guardó');updateCounts();return;}inp.disabled=true;try{await command(t,'trigger_toggle',{enabled:desired});t.enabled=desired;}catch{inp.checked=t.enabled;}finally{inp.disabled=false;updateCounts();}};sw.append(inp,A.h('span','',t.enabled?'ON':'OFF'));inp.addEventListener('change',()=>{sw.lastChild.textContent=inp.checked?'ON':'OFF';});const edit=A.h('button','','Detalles');edit.onclick=()=>{chosen=chosen===t.id?null:t.id;render();};const act=A.h('div','trcontrols');act.append(badge,sw,edit);head.append(A.h('span','trid',t.id),title,act);shell.append(head,detailOf(t));list.append(shell);}updateCounts();}
async function verify(){try{const ids=pids();const r=await A.send('nct_loop','dsl_estado',{op:'get',...ids});if(r?.error||r?.ok===false||!r||typeof r!=='object'||!r.status||r.project_id!==ids.project_id||r.loop_id!==ids.loop_id)throw Error(r?.error||'LOOP_NO_CONFIRMADO');idsConfirmed=true;connected=true;await A.selection(ids.project_id,ids.loop_id);all.forEach(t=>{t.serverConfirmed=false;t.status='UNKNOWN';t.enabled=false;t.flags=[];});A.banner('● LOOP conectado','ok');notice('LOOP verificado: '+String(r.status));const tlist=Array.isArray(r.triggers)?r.triggers:[];for(const item of tlist){const t=all.find(z=>z.id===item.id);if(!t)continue;t.status=String(item.status||'UNKNOWN').toUpperCase();t.serverConfirmed=true;t.enabled=!!item.enabled;t.note=typeof item.note==='string'?item.note:t.note;t.flags=Array.isArray(item.flags)?item.flags:[];}A.el('go-run').disabled=false;A.el('go-pause').disabled=false;render();
window.dispatchEvent(new CustomEvent('yaiwes:loop-verified',{detail:{project_id:ids.project_id,loop_id:ids.loop_id,status:r.status}}));return r;}catch(e){idsConfirmed=false;connected=false;all.forEach(t=>{t.serverConfirmed=false;t.status='UNKNOWN';});A.el('go-run').disabled=true;A.el('go-pause').disabled=true;
window.dispatchEvent(new CustomEvent('yaiwes:loop-unverified'));
A.banner('◌ Sin backend confirmado');notice(e.message);render();throw e;}}
A.el('verify-ids').onclick=()=>verify().catch(()=>{});A.el('refresh').onclick=async()=>{try{await A.health('nct_loop');if(idsConfirmed)await verify();}catch(e){notice(e.message);}};
async function control(op){try{const ids=pids();if(!idsConfirmed)throw Error('LOOP no confirmado');const r=await A.send('nct_loop','dsl_estado',{op:'get',...ids});if(!r?.status)throw Error('ESTADO_NO_CONFIRMADO');const done=await A.send('nct_loop','dsl_control',{...ids,op,expected_revision:r.revision});if(done?.error)throw Error(done.error);const read=await verify();if(op==='start'&&String(read.status).toUpperCase()!=='RUNNING')throw Error('START_NO_CONFIRMADO');if(op==='pause'&&String(read.status).toUpperCase()==='RUNNING')throw Error('PAUSE_NO_CONFIRMADO');notice('Comando '+op+' · backend ahora '+read.status);}catch(e){notice('CONTROL NO CONFIRMADO: '+e.message);}}
A.el('go-run').onclick=()=>control('start');A.el('go-pause').onclick=()=>control('pause');
A.el('search').oninput=render;A.el('show-filter').onchange=render;
A.el('add-step').onclick=()=>{if(all.length>=cap){notice('Máximo de 100 pasos por LOOP');return;}const idx=all.length;all.push({id:'T'+String(idx).padStart(2,'0'),title:'Paso adicional '+(idx+1),category:Math.min(9,Math.floor(idx/10)),enabled:false,note:'',status:'UNKNOWN',flags:[],contract:null,filename:'',hash:null,serverConfirmed:false});categories();render();notice('T'+String(idx).padStart(2,'0')+' añadido en VISTA LOCAL; el servidor debe guardarlo.');};
A.el('save-roles').onclick=async()=>{if(!idsConfirmed){notice('Primero vincular LOOP real');return;}const roles={};for(const [id]of roleIDs){roles[id]={model_id:A.el('role-'+id+'-model').value.trim(),agent_id:A.el('role-'+id+'-agent').value.trim()};if(!roles[id].model_id||!roles[id].agent_id){notice('Completa ambos identificadores para '+id);return;}}try{const r=await remote('dsl_config',{op:'roles_save',roles});if(r?.error)throw Error(r.error);notice('Solicitud de roles enviada; falta lectura de verificación antes de marcar GUARDADO');}catch(e){notice(e.message);}};
for(const [btn,op]of [['load-flags','flags'],['load-checkpoint','checkpoint']])A.el(btn).onclick=async()=>{try{const r=await remote('dsl_estado',{op});log(op+' : '+JSON.stringify(r).slice(0,700));}catch(e){notice(e.message);}};
rolePanel();categories();render();A.health('nct_loop').then(()=>{notice('Backend responde; selecciona IDs reales');return loadRoleOptions();}).catch(()=>notice('Modo vista previa. Backend no verificado.'));
})();
