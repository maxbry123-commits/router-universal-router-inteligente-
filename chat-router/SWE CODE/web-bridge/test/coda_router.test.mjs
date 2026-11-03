import assert from 'node:assert/strict';
import {test} from 'node:test';
import {detectarCodigoLargo, servirCodaRouter} from '../src/coda_router.js';

// Pruebas con Router SIMULADO; no afirman inferencia de NVIDIA/Groq.
const ms = [{role:'user',content:'Escribe 500 lineas de codigo Python sin herramientas'}];
const mdl = 'nvidia/minimaxai/minimax-m3.1-flash';

test('detecta 500 lineas y respeta Tools ON', () => {
  assert.equal(detectarCodigoLargo(mdl,ms,false),500);
  assert.equal(detectarCodigoLargo(mdl,ms,true),null);
  assert.equal(detectarCodigoLargo(mdl,[{role:'user',content:'hola'}],false),null);
  assert.equal(detectarCodigoLargo('web-qwen38max',ms,false),null);
  assert.equal(detectarCodigoLargo(mdl,[{role:'user',content:'Escribe 500 lineas de codigo JavaScript'}],false),null);
});

test('OpenClaw/YAIWES llaman al MISMO chat_async + resultado; PASS solo tras 500 lineas', async () => {
  const calls = [];
  const codigo = 'def f(x): return x\n'.repeat(500);
  const fetchFn = async (url,opt) => {
    const body = JSON.parse(opt.body);
    calls.push({url,body});
    return {ok:true,json:async()=>({status:'ok',result:
      url.endsWith('chat_async')?{estado:'procesando',proceso_id:'p-demo'}:
      {estado:'completado',choices:[{message:{content:codigo}}],
       metricas:{lineas_verificadas:500}}})};
  };
  const req={body:{stream:false,tools:false}};
  const res={headersSent:false,statusCode:200,setHeader(){},status(x){this.statusCode=x;return this},json(x){this.data=x}};
  const sse={pide:false,signal:{aborted:false},parar(){}};
  assert.equal(await servirCodaRouter(req,res,sse,{modelo:mdl,mensajes:ms,sesion:'test-coda',
       propietario:'anonimo',fetchFn,env:{PORT:'7861',RIU_API_KEY:'test-clave'}}),true);
  assert.equal(res.statusCode,200);
  assert.equal(res.data.choices[0].message.content.trimEnd().split('\n').length,500);
  assert.ok(calls[0].url.endsWith('/plugins/puente_chat/call/chat_async'));
  assert.ok(calls[1].url.endsWith('/plugins/puente_chat/call/resultado'));
  assert.equal(calls[0].body.task_type,'code_largo');
  assert.equal(calls[0].body.tools,false);
});

test('respuesta 429/errores no se anuncian como PASS', async()=>{
  const fetchFn=async(url,opt)=>({ok:true,json:async()=>({status:'ok',result:
     url.endsWith('chat_async')?{estado:'procesando',proceso_id:'p-demo'}:
      {estado:'error',status_code:504,error:'PROVEEDOR_GROQ_HTTP_429'}})});
  const req={body:{stream:false,tools:false}};
  const res={headersSent:false,statusCode:200,setHeader(){},status(x){this.statusCode=x;return this},json(x){this.data=x}};
  const sse={pide:false,signal:{aborted:false},parar(){}};
  await servirCodaRouter(req,res,sse,{modelo:mdl,mensajes:ms,sesion:'test',
    fetchFn,env:{PORT:'7861',RIU_API_KEY:'test-clave'}});
  assert.equal(res.statusCode,202);
  assert.equal(res.data.error.code,'CODA_MODELO_GAP');
});
