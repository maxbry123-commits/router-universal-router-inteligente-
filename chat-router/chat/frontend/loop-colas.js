// Salida 6 · cola CIT-50 realmente existente. Selector único (+ Añadir cola).
// Scoped by project+LOOP via chat_id (NO significa que nct_loop la ejecute automáticamente).
(() => {
'use strict';
const A=window.YAIWES_PANEL, el=id=>document.getElementById(id);
if(!A||!el('lq-add')||!el('lq-list'))return;
const menu=el('lq-add'), form=el('lq-form'), input=el('lq-name'),task=el('lq-task'),
list=el('lq-list'),counter=el('lq-count'),status=el('lq-message');
let ids=null,scope=null,loading=false,queues=[],refreshQueued=false,version=0;
const msg=(s,err=false)=>{status.textContent=String(s).slice(0,260);status.classList.toggle('is-error',err)};
const btn=(label,fn)=>{const b=document.createElement('button');b.type='button';b.textContent=label;b.addEventListener('click',fn);return b};
const clean=()=>{
  version++;ids=null;scope=null;queues=[];refreshQueued=false;menu.value='';form.hidden=true;
  counter.textContent='0';list.replaceChildren();
  const p=document.createElement('p');p.className='help';p.textContent='Vincula el proyecto y LOOP para consultar colas reales.';list.append(p);
  msg('Ninguna cola visible sin verificación del backend.');
};
async function scopeFor(p,l){
  const str=new TextEncoder().encode(p+'\u0000'+l);
  if(!crypto.subtle)throw Error('HASH_SHA256_NO_DISPONIBLE');
  const buf=await crypto.subtle.digest('SHA-256',str);
  return 'loop_'+[...new Uint8Array(buf)].map(x=>x.toString(16).padStart(2,'0')).join('').slice(0,40);
}
async function cola(action,payload){
  const r=await A.send('cola50',action,payload);
  if(!r||r.error||r.ok===false)throw Error(String(r?.error||'COLA_NO_DISPONIBLE'));
  return r;
}
function render(){
  counter.textContent=String(queues.length);list.replaceChildren();
  if(!queues.length){
    const p=document.createElement('p');p.className='help';p.textContent='Sin colas creadas para este LOOP. Usa ＋ Añadir cola.';list.append(p);return;
  }
  for(const q of queues){
    const card=document.createElement('article');card.className='lq-card';
    const head=document.createElement('div');head.className='lq-card-head';
    const title=document.createElement('strong');title.textContent=String(q.title||q.id||q.queue_id).slice(0,150);
    const badge=document.createElement('span');badge.className='lq-badge';badge.textContent=String(q.state||q.status||'SIN VERIFICAR').toUpperCase();
    head.append(title,badge);
    const meta=document.createElement('small');meta.className='lq-meta';meta.textContent='CIT-50 · '+String(q.id||q.queue_id).slice(0,28)+' · solo backend';
    const actions=document.createElement('div');actions.className='lq-card-actions';
    actions.append(btn('Consultar estado',async()=>{
      const qid=q.id||q.queue_id;
      try{
        const r=await cola('estado',{qid});
        if(r.queue_id!==qid||r.chat_id!==scope)throw Error('COLA_FUERA_DEL_LOOP');
        badge.textContent=String(r.status||'UNKNOWN').toUpperCase();
        msg('Cola '+qid+' · estado real '+badge.textContent+' · '+(r.tasks?.length??'?')+' tareas');
      }catch(e){msg(e.message,true)}
    }));
    card.append(head,meta,actions);list.append(card);
  }
}
async function refresh(){
  if(!ids||!scope)return;
  if(loading){refreshQueued=true;return}
  const stamp=version,current=scope;
  loading=true;msg('Consultando colas del LOOP en CIT-50…');menu.disabled=true;
  try{
    const r=await cola('listar',{chat_id:scope});
    if(stamp!==version||current!==scope)return;
    if(!Array.isArray(r.queues))throw Error('RESPUESTA_COLAS_INVALIDA');
    // El backend filtra por chat_id, pero filtramos de nuevo para no mostrar colas ajenas.
    queues=r.queues.filter(x=>x&&x.chat_id===scope).slice(0,100);
    render();msg(queues.length+' cola(s) verificadas en CIT-50. No se crean colas automáticamente.');
  }catch(e){if(stamp===version){queues=[];render();msg('CIT-50 no confirmado: '+e.message,true)}}
  finally{
    loading=false;menu.disabled=false;
    if(refreshQueued&&scope){refreshQueued=false;refresh()}
  }
}
async function init(p,l){
  clean();
  try{
    const key=await scopeFor(p,l);
    if(el('project-id').value.trim()!==p||el('loop-id').value.trim()!==l)return;
    ids={p,l};scope=key;
    await refresh();
  }catch(e){msg(e.message,true)}
}
async function create(){
  if(!ids||!scope){msg('Primero verifica project_id y loop_id',true);return}
  const title=input.value.trim(),prompt=task.value.trim();
  if(!title||title.length>150||!prompt||prompt.length>24000){msg('Completa nombre y primera tarea para crear una cola real.',true);return}
  const button=el('lq-create');button.disabled=true;
  try{
    // El contrato CIT-50 requiere >=1 tarea. Solo esta tarea explícita, nunca 50 preestablecidas.
    const payload={chat_id:scope,title,mode:'sequential',tasks:[{id:'t1',title:title.slice(0,150),type:'model',prompt,depends_on:[],acceptance:{}}]};
    const made=await cola('crear',payload);
    if(!/^cit_[a-f0-9]{20}$/.test(made.queue_id||'')||made.chat_id!==scope||made.title!==title||!Array.isArray(made.tasks)||made.tasks.length!==1)throw Error('COLA_CREADA_SIN_RECIBO_VALIDO');
    const read=await cola('estado',{qid:made.queue_id});
    if(read.queue_id!==made.queue_id||read.chat_id!==scope||read.title!==title||read.status!=='draft'||!Array.isArray(read.tasks)||read.tasks.length!==1)throw Error('LECTURA_COLA_NO_CONFIRMADA');
    form.hidden=true;menu.value='';input.value='';task.value='';
    msg('Cola '+read.queue_id+' creada y verificada · borrador sin ejecutar.');
    await refresh();
  }catch(e){msg('No se confirmó la cola: '+e.message,true)}
  finally{button.disabled=false}
}
menu.addEventListener('change',()=>{
  const value=menu.value;
  if(value==='new'){form.hidden=false;input.focus();msg(ids?'Introduce los datos de una cola real.':'Verifica primero el LOOP.',!ids)}
  else if(value==='existing'){form.hidden=true;menu.value='';refresh()}
  else form.hidden=true;
});
el('lq-cancel').addEventListener('click',()=>{form.hidden=true;menu.value=''});
el('lq-create').addEventListener('click',create);
window.addEventListener('yaiwes:loop-verified',e=>{const p=e.detail?.project_id,l=e.detail?.loop_id;if(p&&l)init(p,l)});
window.addEventListener('yaiwes:loop-unverified',clean);
el('project-id').addEventListener('input',clean);
el('loop-id').addEventListener('input',clean);
clean();
})();
