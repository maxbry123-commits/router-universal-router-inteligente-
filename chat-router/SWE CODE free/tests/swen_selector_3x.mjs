// node "chat-router/SWE CODE free/tests/swen_selector_3x.mjs"
// Pruebas DETERMINISTAS sin tráfico real: tres escenarios por cada modelo
// seleccionado y tres escenarios de Ask Cónsil (no certifican una suscripción web).
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const leer = (relative) => fs.readFileSync(new URL(relative, import.meta.url), 'utf8');
const memoria = new Map([['riu_swe_seleccion',JSON.stringify({
  modelo_responde:'web-qwen38max',modelo_tool:'web-qwen38max',
  agente_responde:'openclaw',agente_tool:'openclaw',modo_agentico:true,workflow:'individual',modo_trabajo:''
})]]);
const storage = {getItem:(key)=>memoria.get(key)||null,setItem:(key,val)=>memoria.set(key,String(val))};
const codigo = leer('../../chat/frontend/swe-directo.js').replace(/\bexport\s+/g,'');
const frontend = new Function('localStorage','window',codigo+
  '\nreturn {MODELOS_WEB,SWE_LISTAS,leerSeleccion,guardarSeleccion,armar,armarTarea};'
)(storage,{});
let hechos = 0;
for (const [id] of frontend.MODELOS_WEB) {
  const agente=['openclaw','openhands','codex'];
  for (let paso=0;paso<3;paso++) {
    const body=frontend.armar({
      model:id,mensaje:'SWE_TEST_'+paso, sesion:'prueba_nueva',
      contexto_de:'prueba_anterior',tools:paso===1,ejecutor_tools:'openclaw'
    });
    assert.equal(body.model,id,'el modelo solicitado nunca cambia silenciosamente');
    assert.equal(body.contexto_de,'prueba_anterior');
    assert.equal(body.ejecutor_tools,'openclaw');
    const modeloTool=id==='swecode-consulta'?'web-qwen38max':id;
    const tarea=frontend.armarTarea({sel:{
      ...frontend.leerSeleccion(),modelo_responde:id,modelo_tool:modeloTool,
      agente_tool:agente[paso],modo_agentico:true,workflow:'individual'
    },mensaje:'SWE_TEST_'+paso,sesion:'prueba_nueva',proyecto:'regresion'});
    assert.equal(tarea.modelo_tool,modeloTool);
    assert.equal(tarea.modelo_responde,id);
    assert.equal(tarea.agente_tool,agente[paso]);
    assert.equal(tarea.workflow,'individual');
    assert.equal(tarea.modelo_lector,id);
    assert.equal(tarea.modelo_revisor,id);
    assert.ok(!JSON.stringify(tarea).includes('hf/'),'SWE CODE free sin Liquid ni HF');
    hechos++;
    console.log('PASS SELECTOR',id,'caso',paso+1);
  }
}

const consola = leer('../../SWE CODE/web-bridge/src/consenso.js')
  .replace(/^import .*$/gm,'').replace(/\bexport\s+/g,'');
const mk=(web,claude)=>new Function('consultarWeb','consultarClaude','esCuotaClaude',
  consola+';return consenso;')(web,claude,x=>x==='CLAUDE_CUENTAS_AGOTADAS');
{
  const log=[];
  const r=await mk(async(m,p)=>{log.push(m);return m==='qwen38max'&&p.includes('Eres el arbitro')?'DICTAMEN_QWEN':'OPINION_'+m},
    async()=>({texto:'OPINION_CLAUDE'}))('tarea');
  assert.equal(r.final,'DICTAMEN_QWEN');assert.equal(Object.keys(r.por_modelo).length,4);
  assert.equal(log.filter(x=>x==='qwen38max').length,2);
  hechos++;console.log('PASS CONSIL cuatro opiniones, árbitro Qwen');
}
{
  const r=await mk(async(m,p)=>m==='qwen38max'&&p.includes('Eres el arbitro')?'DICTAMEN':'OPINION',
    async()=>{throw Object.assign(new Error('cuota'),{code:'CLAUDE_CUENTAS_AGOTADAS'})})('tarea');
  assert.equal(r.final,'DICTAMEN');assert.match(r.por_modelo['claude-sonnet'],/^🚩/);
  hechos++;console.log('PASS CONSIL continúa si Claude agotado');
}
{
  const c=mk(async(m,p)=>{if(m==='qwen38max'&&p.includes('Eres el arbitro'))throw new Error('caída');return 'OPINION'},
    async()=>({texto:'OPINION'}));
  await assert.rejects(()=>c('tarea'),e=>e.code==='CONSIL_ARBITRO_NO_DISPONIBLE');
  hechos++;console.log('PASS CONSIL no inventa árbitro');
}
console.log('PASS COMPLETOS: '+hechos+' / 18 (simulados; no pruebas reales en cuentas web)');
