// Ejecutar dentro del Space con credenciales de entorno ya autorizadas.
// Test REAL extremo a extremo, 3 por selector (15). No imprime ni guarda secretos.
// node "chat-router/SWE CODE free/tests/swen_live_3x.mjs"
// SWEN_TEST_URL es opcional y admite sólo localhost (Harness o bridge).
const URL_TEST=process.env.SWEN_TEST_URL ||
 'http://127.0.0.1:7861/plugins/deepseek_harness/modelos/v1/chat/completions';
const SECRET=process.env.RIU_API_KEY||process.env.BRIDGE_TOKEN||'';
const IDS=['web-qwen38max','web-claude-sonnet','web-qwen37max','web-dsv4-flash','swecode-consulta'];
const EFECTIVO={
  'web-qwen38max':'qwen38max',
  'web-claude-sonnet':'anthropic/claude-sonnet-5-5',
  'web-qwen37max':'qwen37max',
  'web-dsv4-flash':'dsv4-flash',
  'swecode-consulta':'qwen38max'
};
const target=new URL(URL_TEST);
if(target.protocol!=='http:'||!['localhost','127.0.0.1','::1'].includes(target.hostname)||
  !/\/(?:modelos\/v1\/chat\/completions|v1\/chat\/completions)$/.test(target.pathname))
  throw Error('PRUEBA_URL_INVALIDA: solo Harness/bridge localhost');
if(!SECRET)throw Error('PRUEBA_SIN_CLAVE: RIU_API_KEY o BRIDGE_TOKEN en servidor');
let passed=0,failed=0;
const idRun=Date.now().toString(36);
for(const modelo of IDS){
  for(let n=1;n<=3;n++){
    const start=Date.now();
    const r={modelo,n,estado:'ERROR',http:0,usado:'',motivo:'',ms:0};
    const conv_id='swen_test_'+idRun+'_'+IDS.indexOf(modelo)+'_'+n;
    try{
      const timeout=modelo==='swecode-consulta'?430000:
        modelo==='web-claude-sonnet'?340000:230000;
      const res=await fetch(target,{method:'POST',redirect:'error',
        signal:AbortSignal.timeout(timeout),
        headers:{'content-type':'application/json',Authorization:'Bearer '+SECRET},
        body:JSON.stringify({model:modelo,conv_id,stream:false,tools:false,
          messages:[{role:'user',content:'Diagnostico. Responde una linea: TEST_OK '+modelo+' numero '+n}]})});
      r.http=res.status;
      const raw=await res.text();
      if(raw.length>2000000)throw Error('RESPUESTA_GRANDE');
      let x;try{x=JSON.parse(raw)}catch{throw Error('JSON_INVALIDO')}
      r.usado=String(x.modelo_usado||x.model||'');
      if(!res.ok)r.motivo=String(x.error?.code||x.detail||'HTTP_ERROR').slice(0,90);
      else if(!String(x.choices?.[0]?.message?.content||'').trim())r.motivo='RESPUESTA_VACIA';
      else if(r.usado!==EFECTIVO[modelo])r.motivo='MODELO_SUSTITUIDO';
      else if(x.via_respaldo)r.motivo='FALLBACK_NO_AUTORIZADO';
      else if(modelo==='swecode-consulta'&&x.consenso_detalle?.arbitro!=='qwen38max')
        r.motivo='ARBITRO_SIN_CONFIRMAR';
      else {r.estado='PASS';passed++}
    }catch(e){r.motivo=String(e?.name==='TimeoutError'?'TIMEOUT':e?.message||e).slice(0,90)}
    r.ms=Date.now()-start;
    if(r.estado!=='PASS')failed++;
    console.log(JSON.stringify(r)); // no registra correos, respuestas ni credenciales
  }
}
console.log(JSON.stringify({total:15,pass:passed,fail:failed,modo:'REAL'}));
if(failed)process.exitCode=1;
