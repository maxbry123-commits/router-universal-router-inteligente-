import test from 'node:test';
import assert from 'node:assert/strict';
import { SITES, MODELOS_WEB, elegirModelo, necesitaLogin, leerRespuesta, pasarAgeGate } from '../src/sites.js';

const locator = (texto, { visible=true, onClick=()=>{} }={}) => ({
  first() { return this; },
  async isVisible() { return visible; },
  async innerText() { return typeof texto==='function' ? texto() : texto; },
  async getAttribute() { return ''; },
  async click() { return onClick(); }
});
const page = (selected='') => ({
  locator: () => locator(selected),
  $$: async () => [],
  waitForTimeout: async () => {},
  keyboard: { press:async()=>{} }
});

test('Claude es navegador web con autenticación oficial, nunca API Anthropic', () => {
  assert.equal(SITES.claude.url, 'https://claude.ai/new');
  assert.equal(SITES.claude.manual_login, true);
  assert.equal(MODELOS_WEB['claude-sonnet'].site,'claude');
  assert.match(SITES.claude.input[0],/ProseMirror/);
  assert.ok(SITES.claude.respuesta.every(x=>!x.includes('user-message')));
});
test('Qwen requiere prueba POST selección del modelo', async () => {
  let selected='Qwen 3.7 Max', clicks=0;
  const p=page();
  p.locator=()=>locator(()=>selected);
  p.$$=async () => [locator('Qwen 3.8 Max',{onClick:()=>{selected='Qwen 3.8 Max';clicks++;}})];
  assert.equal(await elegirModelo(p,SITES.qwen,MODELOS_WEB.qwen38max.modelo_regex),true);
  assert.equal(clicks,1);
});
test('Qwen no acepta otra versión cuando no pudo seleccionarla', async () => {
  assert.equal(await elegirModelo(page('Qwen 3.7 Max'),SITES.qwen,MODELOS_WEB.qwen38max.modelo_regex),false);
});
test('DeepSeek no confirma V4 Flash si el sitio no enseña identidad', async () => {
  assert.equal(await elegirModelo(page('DeepSeek modelo desconocido'),SITES.deepseek,
    MODELOS_WEB['dsv4-flash'].modelo_regex),false);
});
test('DeepSeek confirma únicamente un indicador visible que coincide', async () => {
  assert.equal(await elegirModelo(page('DeepSeek V4 Flash'),SITES.deepseek,
    MODELOS_WEB['dsv4-flash'].modelo_regex),true);
});
test('Claude Sonnet debe verificarse en selector visible', async () => {
  assert.equal(await elegirModelo(page('Claude Sonnet 5.5'),SITES.claude,
    MODELOS_WEB['claude-sonnet'].modelo_regex),true);
  assert.equal(await elegirModelo(page('Claude Opus 5.5'),SITES.claude,
    MODELOS_WEB['claude-sonnet'].modelo_regex),false);
});
test('Claude solicita login oficial si está en /login', async () => {
  const p=page();p.url=()=> 'https://claude.ai/login';
  assert.equal(await necesitaLogin(p,SITES.claude),true);
});
test('Lectura no reutiliza el mensaje anterior', async () => {
  let n=0;
  const p={waitForTimeout:async()=>{}, evaluate:async()=>++n<2?'ANTERIOR':'RESPUESTA NUEVA'};
  const t=await leerRespuesta(p,{respuesta:['.assistant'],stop_gen:[]},{previo:'ANTERIOR',timeoutMs:40000});
  assert.equal(t,'RESPUESTA NUEVA');
});
test('Verificación de edad requiere mecanismo oficial', async () => {
  const p={getByText:()=>({first:()=>({isVisible:async()=>true})})};
  await assert.rejects(pasarAgeGate(p,SITES.claude),e=>e.code==='AGE_VERIFICATION_REQUIRED');
});
