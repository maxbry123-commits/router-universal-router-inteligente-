import { test, after } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const dir=fs.mkdtempSync(path.join(os.tmpdir(),'swen-autorepair-'));
process.env.BRIDGE_STATE_DIR=dir;
const {clasificarGap,registrarGap,listarGaps,gapPorId,investigarConOpenClaw}
  =await import('../src/autoreparacion.js');
after(()=>fs.rmSync(dir,{recursive:true,force:true}));

test('bloqueos de autenticación/edad/cuota no se saltan ni repiten',()=>{
  for(const code of ['SESSION_EXPIRED','AGE_VERIFICATION_REQUIRED','CF_CHALLENGE',
    'CLAUDE_CUENTAS_AGOTADAS','CLAUDE_PROVEEDOR_SIN_CREDENCIALES','NO_AUTORIZADO']){
    const x=clasificarGap(code);
    assert.equal(x.reintentar,false);
    assert.match(x.estado,/REQUIERE_OPERADOR/);
  }
});
test('sólo navegación anterior al envío permite 1 reintento seguro',()=>{
  assert.equal(clasificarGap('WEB_SITIO_NO_RESPONDE').reintentar,true);
  for(const code of ['WEB_SALIDA_PARCIAL','UPSTREAM_TIMEOUT',
    'MODELO_SELECTOR_NO_VERIFICADO','SELECTOR_BROKEN']){
    assert.equal(clasificarGap(code).reintentar,false);
  }
});
test('registro duradero redacciona errores e idempotencia por modelo/codigo',()=>{
  const g=registrarGap({modelo:'web-qwen38max',code:'SESSION_EXPIRED',convId:'sesion-privada'});
  assert.match(g.id,/^gap_[0-9a-f]{24}$/);
  assert.equal(g.nuevo,true);
  const repetido=registrarGap({modelo:'web-qwen38max',code:'SESSION_EXPIRED'});
  assert.equal(repetido.id,g.id);
  assert.equal(repetido.nuevo,false);
  assert.equal(listarGaps().length,1);
  assert.equal(gapPorId(g.id).id,g.id);
  assert.equal(gapPorId('gap_../../secreto'),null);
  const texto=fs.readFileSync(path.join(dir,'swen-gaps.json'),'utf8');
  assert.equal(texto.includes('sesion-privada'),false);
});
test('OpenClaw no investiga ni ejecuta en errores de autenticacion',async()=>{
  const g=listarGaps()[0];
  const r=await investigarConOpenClaw(g.id,{fetchFn:()=>{throw Error('NO DEBE LLAMAR')}});
  assert.equal(r.code,'REQUIERE_OPERADOR');
});
test('investiga sólo mediante agente aislado con respuesta, sin aplicar parche',async()=>{
  const g=registrarGap({modelo:'web-qwen37max',code:'SELECTOR_BROKEN'});
  const prev={enabled:process.env.OPENCLAW_ENABLE,token:process.env.OPENCLAW_GATEWAY_TOKEN};
  process.env.OPENCLAW_ENABLE='1';process.env.OPENCLAW_GATEWAY_TOKEN='TOKEN_SIMULADO';
  let requests=0;
  try{
    const r=await investigarConOpenClaw(g.id,{fetchFn:async(url,opts)=>{
      requests++;
      assert.ok(url.includes('127.0.0.1:'));
      const body=JSON.parse(opts.body);
      assert.equal(body.model,'openclaw/swen-repair');
      assert.ok(body.messages[0].content.includes('SOLO LECTURA'));
      assert.ok(!body.messages[0].content.includes('TOKEN_SIMULADO'));
      return {ok:true,json:async()=>({choices:[{message:{content:'Revisar el DOM; proponer parche en PR, no ejecutar.'}}]})};
    }});
    assert.equal(r.ok,true);assert.equal(requests,1);
    assert.equal(gapPorId(g.id).investigado,true);
    const again=await investigarConOpenClaw(g.id,{fetchFn:()=>{throw Error('NO LLAMAR DOS VECES')}});
    assert.equal(again.code,'YA_INVESTIGADO');assert.equal(requests,1);
  }finally{
    if(prev.enabled===undefined)delete process.env.OPENCLAW_ENABLE;
    else process.env.OPENCLAW_ENABLE=prev.enabled;
    if(prev.token===undefined)delete process.env.OPENCLAW_GATEWAY_TOKEN;
    else process.env.OPENCLAW_GATEWAY_TOKEN=prev.token;
  }
});
test('sin agente o token no inventa PASS',async()=>{
  const g=registrarGap({modelo:'web-dsv4-flash',code:'CLAUDE_GATEWAY_NO_CONECTADO'});
  const save=process.env.OPENCLAW_ENABLE;process.env.OPENCLAW_ENABLE='0';
  try{
    const r=await investigarConOpenClaw(g.id);
    assert.equal(r.ok,false);assert.equal(r.code,'OPENCLAW_NO_DISPONIBLE');
  }finally{
    if(save===undefined)delete process.env.OPENCLAW_ENABLE;
    else process.env.OPENCLAW_ENABLE=save;
  }
});

test('Claude 401 proveedor distinto de error de acceso al Gateway',async()=>{
  const {consultarClaude}=await import('../src/claude_gateway.js');
  const anterior=process.env.OPENCLAW_GATEWAY_TOKEN;
  process.env.OPENCLAW_GATEWAY_TOKEN='TOKEN_DE_PRUEBA_NO_REAL';
  try{
    const simular=(code)=>async()=>({ok:false,status:401,
      text:async()=>JSON.stringify({error:{type:'authentication_error',code}})});
    await assert.rejects(
      ()=>consultarClaude('Prueba',{fetchFn:simular('missing-provider-auth')}),
      e=>e.code==='CLAUDE_PROVEEDOR_SIN_CREDENCIALES');
    await assert.rejects(
      ()=>consultarClaude('Prueba',{fetchFn:simular('invalid-token')}),
      e=>e.code==='CLAUDE_GATEWAY_NO_AUTORIZADO');
  }finally{
    if(anterior===undefined)delete process.env.OPENCLAW_GATEWAY_TOKEN;
    else process.env.OPENCLAW_GATEWAY_TOKEN=anterior;
  }
});
