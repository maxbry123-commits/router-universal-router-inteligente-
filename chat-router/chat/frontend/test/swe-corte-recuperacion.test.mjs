import test from 'node:test';
import assert from 'node:assert/strict';
globalThis.window = globalThis;
globalThis.localStorage = { getItem: () => null };
const { enviarSwe, leerSSE } = await import('../swe-directo.js');
const enc = new TextEncoder();
const evento = (delta, finish_reason = null) => 'data: ' + JSON.stringify({choices:[{delta,finish_reason}]}) + '\n\n';
const base = {model:'groq/qwen/qwen3.8-27b',historial:[],mensaje:'hola',sesion:'test'};

test('DONE finaliza aunque el transporte quede abierto', async () => {
  let cancelled = false;
  const response = new Response(new ReadableStream({start(c) { c.enqueue(enc.encode(evento({content:'OK'}, 'stop') + 'data: [DONE]\n\n')); },cancel() {cancelled=true;}}));
  const r = await leerSSE(response, () => {});
  assert.equal(r.fin,true); assert.equal(cancelled,true);
});

test('corte tras texto conserva parcial y no duplica peticion', async () => {
  let calls=0, reads=0;
  const api = async () => { calls++; return {__sse:new Response(new ReadableStream({pull(c) { if(reads++===0)c.enqueue(enc.encode(evento({content:'parcial'}))); else c.error(new Error('network disconnected')); }}))}; };
  const r = await enviarSwe(api,base);
  assert.equal(calls,1); assert.equal(r.reply,'parcial'); assert.equal(r.finish_reason,'error'); assert.match(r.nota,/STREAM_CORTADO/);
});

test('error definitivo 413 llega como tal sin reintentar', async () => {
  let calls=0;
  const api=async()=>{ calls++; return {__sse:new Response(evento({},'error').replace('"choices":','"error":{"code":"PROVEEDOR_HTTP_413"},"choices":')+'data: [DONE]\n\n')}; };
  await assert.rejects(enviarSwe(api,base), /PROVEEDOR_HTTP_413/);
  assert.equal(calls,1);
});
