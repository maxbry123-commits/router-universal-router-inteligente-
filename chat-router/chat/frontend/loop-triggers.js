// Chat2 / salida 7: contratos DSL VERBATIM, revisión real y CAS.
// Reutiliza nct_loop. No genera triggers, permisos ni estados ficticios.
(() => {
'use strict';
const A=window.YAIWES_PANEL,$=id=>document.getElementById(id);
if(!A||!$('lt-pick')||!$('lt-register'))return;
const ui={pick:$('lt-pick'),file:$('lt-file'),review:$('lt-review'),heading:$('lt-heading'),summary:$('lt-summary'),validate:$('lt-validate'),register:$('lt-register'),clear:$('lt-clear'),pending:$('lt-pending-summary'),pendingBtn:$('lt-open-pending')};
let contract=null,scope=null,verifiedHash='',generation=0;
const safe=s=>A.idSafe(s);
const canonical=o=>JSON.stringify(o,(k,v)=>v&&typeof v==='object'&&!Array.isArray(v)?Object.fromEntries(Object.keys(v).sort().map(key=>[key,v[key]])):v);
async function hash(text){
 if(!crypto.subtle)throw Error('SHA256_NO_DISPONIBLE');
 const b=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text));
 return [...new Uint8Array(b)].map(x=>x.toString(16).padStart(2,'0')).join('');
}
const say=s=>{ui.summary.textContent=String(s).slice(0,1800)};
function clear(){contract=null;verifiedHash='';ui.register.disabled=true;ui.validate.disabled=false;ui.file.value='';ui.review.hidden=true}
async function read(){
 if(!scope)throw Error('VINCULAR_LOOP_PRIMERO');
 const r=await A.send('nct_loop','dsl_estado',{op:'get',...scope});
 if(!r||r.ok!==true||!Number.isInteger(r.revision)||!Array.isArray(r.contracts)||!r.triggers||r.project_id!==scope.project_id||r.loop_id!==scope.loop_id)throw Error(r?.error||'DSL_NO_CONFIRMADO');
 return r;
}
function pending(r){
 const states=Object.values(r?.triggers||{}),flags=states.filter(x=>Array.isArray(x?.flags)&&x.flags.length).length;
 const awaiting=states.filter(x=>!['PASS','OFF','NOT_APPLICABLE'].includes(x?.status)).length;
 ui.pending.textContent=(r?.contracts?.length||0)+' contratos · '+awaiting+' pendientes/bloqueados · '+flags+' con banderas (backend).';
}
async function choose(file){
 clear();
 if(!scope){ui.review.hidden=false;say('Vincula primero un proyecto y LOOP reales');return}
 if(!file||file.size>250000||!file.name.toLowerCase().endsWith('.json')){ui.review.hidden=false;say('Selecciona un JSON de máximo 250 KB');return}
 const serial=++generation,origin={...scope};
 try{
  const c=JSON.parse(await file.text());
  if(!c||Array.isArray(c)||typeof c!=='object'||c.schema!=='yaiwes.trigger.v1'||!safe(c.id)||c.loop_id!==origin.loop_id||typeof c.input_block_verbatim!=='string'||!c.input_block_verbatim||typeof c.source?.sha256!=='string'||!Array.isArray(c.steps)||!c.steps.length)throw Error('ESQUEMA_ID_LOOP_O_VERBATIM_INVALIDO');
  const sourceHash=await hash(c.input_block_verbatim);
  if(sourceHash!==c.source.sha256)throw Error('SHA256_DEL_INPUT_VERBATIM_NO_COINCIDE');
  if(serial!==generation||scope?.loop_id!==origin.loop_id||scope?.project_id!==origin.project_id)return;
  contract=c;ui.heading.textContent='Trigger '+c.id+' · '+String(c.name||'').slice(0,120);ui.review.hidden=false;
  say('Categoría: '+String(c.category)+'\nRol: '+String(c.role)+'\nSHA-256 input: '+sourceHash.slice(0,20)+'…\nArchivo local. NO registrado ni ejecutado.');
 }catch(e){ui.review.hidden=false;say('Archivo rechazado: '+String(e.message||e))}
}
async function validate(){
 if(!contract||!scope){say('Selecciona un JSON y verifica el LOOP');return}
 ui.validate.disabled=true;ui.register.disabled=true;verifiedHash='';
 const c=contract,sc={...scope};
 try{
  const r=await A.send('nct_loop','dsl_config',{op:'contract_validate',...sc,contract:c});
  if(r?.ok!==true||!(/^[a-f0-9]{64}$/).test(r.contract_sha256||''))throw Error(r?.error||'VALIDACION_SIN_SHA');
  const local=await hash(canonical(c));
  if(local!==r.contract_sha256)throw Error('HASH_CANONICO_NO_COINCIDE');
  if(scope?.project_id!==sc.project_id||scope?.loop_id!==sc.loop_id||contract!==c)return;
  verifiedHash=local;ui.register.disabled=false;
  say('✅ Validado por backend · SHA '+local.slice(0,20)+'…\nTodavía NO está guardado. No se ejecutó.');
 }catch(e){say('Validación no confirmada: '+String(e.message||e))}
 finally{ui.validate.disabled=false}
}
async function register(){
 if(!contract||!verifiedHash||!scope)return;
 const c=contract,sc={...scope},digest=verifiedHash;ui.register.disabled=true;
 try{
  const before=await read();
  if(scope?.project_id!==sc.project_id||scope?.loop_id!==sc.loop_id||contract!==c)return;
  const saved=await A.send('nct_loop','dsl_config',{op:'trigger_upsert',...sc,contract:c,expected_revision:before.revision});
  if(saved?.ok!==true||saved.revision!==before.revision+1)throw Error(saved?.error||'REVISION_NO_CONFIRMADA');
  const after=await read(),found=after.contracts.find(row=>row.id===c.id);
  if(after.revision!==saved.revision||!found)throw Error('READBACK_INCOMPLETO');
  if(await hash(canonical(found))!==digest||after.triggers?.[c.id]?.contract_sha256!==digest)throw Error('READBACK_SHA_DISTINTO');
  say('✅ Trigger '+c.id+' guardado y leído · revisión '+after.revision+' · sin ejecución.');
  pending(after);contract=null;verifiedHash='';
  window.dispatchEvent(new CustomEvent('yaiwes:trigger-saved',{detail:{trigger_id:c.id,revision:after.revision}}));
 }catch(e){say('Guardado NO confirmado: '+String(e.message||e))}
}
ui.pick.addEventListener('click',()=>{if(!scope){ui.review.hidden=false;say('Vincula primero el LOOP.');return}ui.file.click()});
ui.file.addEventListener('change',()=>choose(ui.file.files?.[0]));
ui.validate.addEventListener('click',validate);
ui.register.addEventListener('click',register);
ui.clear.addEventListener('click',clear);
ui.pendingBtn.addEventListener('click',()=>A.openPending().catch(e=>{ui.pending.textContent='Pendientes: '+String(e.message||e)}));
window.addEventListener('yaiwes:loop-verified',async e=>{
 const project_id=e.detail?.project_id,loop_id=e.detail?.loop_id;
 if(!safe(project_id)||!safe(loop_id))return;
 const stamp=++generation;scope={project_id,loop_id};clear();
 try{const r=await read();if(stamp===generation)pending(r)}
 catch(e){if(stamp===generation)ui.pending.textContent='Sin pendientes verificados: '+String(e.message||e)}
});
window.addEventListener('yaiwes:loop-unverified',()=>{++generation;scope=null;clear();ui.pending.textContent='Vincula el LOOP para consultar observaciones reales.'});
})();