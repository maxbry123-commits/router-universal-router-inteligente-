import test from 'node:test';
import assert from 'node:assert/strict';
import { estadoClaude, consultarClaude, esCuotaClaude, CLAUDE_MODEL } from '../src/claude_gateway.js';

// No sale a Internet, no toca cuentas, no ejecuta tools, no consume saldo.
test('Claude SWEN: contrato Gateway, Sonnet max y agotamiento sin fallback de modelo', async () => {
  const oldToken=process.env.OPENCLAW_GATEWAY_TOKEN;
  const oldUrl=process.env.RIU_OPENCLAW_URL;
  process.env.OPENCLAW_GATEWAY_TOKEN='dummy-for-test-only';
  process.env.RIU_OPENCLAW_URL='http://127.0.0.1:18789';
  try {
    const status=await estadoClaude({fetchFn: async()=>({
      ok:true,json: async()=>({data:[{id:'openclaw/swen-council'}]})})});
    assert.equal(status.disponible,true);
    assert.equal(status.modelo,'anthropic/claude-sonnet-5-5');
    let last=null;
    const ok=await consultarClaude('Consultar sólo',{convId:'ses_1',fetchFn: async(url,opts)=>{
      last={url,opts};
      return {ok:true,text:async()=>JSON.stringify({
        model:'openclaw/swen-council',choices:[{message:{content:'RESPUESTA_OK'}}]})};
    }});
    assert.equal(ok.texto,'RESPUESTA_OK');
    assert.equal(ok.modelo,CLAUDE_MODEL);
    assert.equal(last.opts.headers['x-openclaw-model'],CLAUDE_MODEL);
    const request=JSON.parse(last.opts.body);
    assert.equal(request.model,'openclaw/swen-council');
    assert.equal(request.user,'swen-sonnet-ses_1');
    assert.match(request.messages[0].content,/^\/think:max\n/);
    await assert.rejects(()=>consultarClaude('Hola',{fetchFn:async()=>({
      ok:false,status:500,text:async()=> 'No available auth profile: all profiles in cooldown'})}),
      e=>e.code==='CLAUDE_CUENTAS_AGOTADAS' && esCuotaClaude(e.code));
    await assert.rejects(()=>consultarClaude('Hola',{fetchFn:async()=>({
      ok:false,status:401,text:async()=> 'Gateway bearer rejected'})}),
      e=>e.code==='CLAUDE_GATEWAY_NO_AUTORIZADO' && !esCuotaClaude(e.code));
  } finally {
    if(oldToken===undefined)delete process.env.OPENCLAW_GATEWAY_TOKEN;
    else process.env.OPENCLAW_GATEWAY_TOKEN=oldToken;
    if(oldUrl===undefined)delete process.env.RIU_OPENCLAW_URL;
    else process.env.RIU_OPENCLAW_URL=oldUrl;
  }
});
