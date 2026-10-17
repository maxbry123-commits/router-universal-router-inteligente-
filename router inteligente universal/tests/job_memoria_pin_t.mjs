// api.js + /memoria con PIN: manda X-Memoria-Pin, pide el PIN una sola vez ante MEMORIA_PIN_REQUERIDO y reintenta 1 vez; otras rutas sin cabecera.
// Uso: node "router inteligente universal/tests/job_memoria_pin_t.mjs"
import assert from 'node:assert/strict';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';
const API = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../chat router/chat frontend/api.js');
const mem = new Map();
const store = { getItem: (k) => (mem.has(k) ? mem.get(k) : null), setItem: (k, v) => mem.set(k, String(v)), removeItem: (k) => mem.delete(k) };
globalThis.localStorage = store; globalThis.sessionStorage = { getItem: () => null, setItem() {}, removeItem() {} };
globalThis.location = { hostname: 'localhost', origin: 'http://localhost', search: '' };
globalThis.window = globalThis; globalThis.dispatchEvent = () => {}; globalThis.CustomEvent = class { constructor(t, o) { this.type = t; this.detail = o && o.detail; } };
window.RIU_CONFIG = { proxyDestino: 'https://comand-center-1-riu-router.hf.space', liveUrl: 'https://x.invalid/LIVE_URL.json', authHeader: 'X-API-Key' };
const PIN = '4821'; const llamadas = []; let prompts = 0, respuestaPrompt = PIN;
globalThis.prompt = () => { prompts++; return respuestaPrompt; };
globalThis.fetch = async (url, o = {}) => {
  if (String(url).includes('LIVE_URL')) return new Response(JSON.stringify({ LIVE_URL: 'https://comand-center-1-riu-router.hf.space' }), { status: 200 });
  const h = o.headers || {}; llamadas.push({ url: String(url), pin: h['X-Memoria-Pin'] });
  const json = (b, s) => new Response(JSON.stringify(b), { status: s, headers: { 'content-type': 'application/json' } });
  if (String(url).includes('/memoria/')) return h['X-Memoria-Pin'] === PIN ? json({ ok: true }, 200) : json({ detail: 'MEMORIA_PIN_REQUERIDO' }, 401);
  return json({ ok: true }, 200);
};
const { api } = await import(pathToFileURL(API).href);
// 1) sin PIN guardado: 401 -> prompt -> reintento OK, PIN guardado
assert.deepEqual(await api('/memoria/health'), { ok: true });
assert.equal(prompts, 1); assert.equal(mem.get('riu_memoria_pin'), PIN);
assert.equal(llamadas.at(-2).pin, undefined); assert.equal(llamadas.at(-1).pin, PIN);
// 2) con PIN guardado: va directo, sin prompt
await api('/memoria/load?scope=a&key=b'); assert.equal(prompts, 1); assert.equal(llamadas.at(-1).pin, PIN);
// 3) otras rutas no llevan el PIN
await api('/chat/conversations'); assert.equal(llamadas.at(-1).pin, undefined);
// 4) PIN cambiado en el Space: el prompt ya se uso en esta carga -> falla sin pedir otra vez (sin bucle)
mem.set('riu_memoria_pin', '0000');
await assert.rejects(api('/memoria/health'), /MEMORIA_PIN_REQUERIDO/); assert.equal(prompts, 1);
console.log('job_memoria_pin_t: 4/4 OK');
