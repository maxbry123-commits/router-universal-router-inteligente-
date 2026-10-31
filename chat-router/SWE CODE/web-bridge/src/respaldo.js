// respaldo.js — si la web no responde: Groq -> NVIDIA -> HF local (S1..S3). Mismas claves del chat (GROQ_API_KEY, NVIDIA_API_KEY, *_1..N).
export const BASES = { groq: 'https://api.groq.com/openai/v1', nvidia: 'https://integrate.api.nvidia.com/v1' };
const MODELO = { groq: ['RIU_SWE_GROQ_MODELO', 'llama-3.3-70b-versatile'], nvidia: ['RIU_SWE_NVIDIA_MODELO', 'meta/llama-3.3-70b-instruct'] };
// descubrimiento de modelos (GET {base}/models): nada de ids inventados
const RE_GROQ = /qwen.*3[.-]?8/i;
const RE_NVIDIA_1 = /minimax|kimi|deepseek.?v4/i, RE_NVIDIA_2A = /muse|glimmer/i, RE_NVIDIA_2B = /nemotron.*3.*super|nemotron-3-super/i;
const PICK = {
  groq: (ids) => ids.find(i => RE_GROQ.test(i)),
  nvidia: (ids) => ids.find(i => RE_NVIDIA_1.test(i)) || ids.find(i => RE_NVIDIA_2A.test(i) && RE_NVIDIA_2B.test(i)),
};
const LOCALES = ['lfm2.5-350m', 'qwen2.5-coder-1.5b', 'qwen3.5-0.8b', 'qwen3-0.6b'];
export const TIMEOUT_DEFECTO_MS = 120000;
const TIMEOUT_MS = parseInt(process.env.BRIDGE_RESPALDO_MS || String(TIMEOUT_DEFECTO_MS), 10) || TIMEOUT_DEFECTO_MS;
const CONTINUAR = 'Continúa exactamente donde terminó, sin repetir';
const RED = { continuaciones: 8, cooldownMs: 60000, esperaMax: 2000, esperaDefecto: 500, descubrirMs: 10000, cacheMs: 30 * 60000, cacheFalloMs: 60000, cortePorTokens: 15000 };
// parametros inyectables en tests: opts = { timeoutMs, continuaciones, cooldownMs, esperaMax, esperar(ms), ahora(), descubrirMs, cacheMs }
const red = (o = {}) => ({ ...RED, timeoutMs: TIMEOUT_MS, esperar: (ms) => new Promise(r => setTimeout(r, ms)), ahora: Date.now, ...o });

// estado en memoria (nunca persiste ni se loguea): claves enfriadas por 429 y modelos descubiertos
const enfriadas = new Map();  // `${prov}\0${clave}` -> epoch ms hasta el que no se usa
const cacheModelos = new Map();  // `${prov}\0${base}` -> { id|null, hasta }
export function limpiarEstado() { enfriadas.clear(); cacheModelos.clear(); }


export const esLocal = (m) => LOCALES.includes(String(m || ''));
export const esExterno = (m) => /^(groq|nvidia)\/.+/.test(String(m || ''));

// ids que el selector de OpenClaw ve ademas de los web-*: externos y locales
export function idsRespaldo(env = process.env) {
  return [...['groq', 'nvidia'].map(p => `${p}/${env[MODELO[p][0]] || MODELO[p][1]}`), ...LOCALES];
}

// claves inyectadas por llamada (POST /v1/chat/completions): solo en memoria del proceso, nunca se loguean
const inyectadas = { groq: [], nvidia: [] };
export function setClaves(c) {
  const { groq, nvidia } = c && typeof c === 'object' ? c : {};
  for (const [prov, v] of [['groq', groq], ['nvidia', nvidia]]) {
    if (v === undefined) continue;  // proveedor ausente: no se toca
    const lista = Array.isArray(v) ? v : typeof v === 'string' ? [v] : [];
    inyectadas[prov] = lista.filter(k => typeof k === 'string').map(k => k.trim()).filter(Boolean).filter((k, i, a) => a.indexOf(k) === i).slice(0, 20);
  }
}

export function limpiarClaves() { inyectadas.groq = []; inyectadas.nvidia = []; }  // DELETE /v1/claves: solo las inyectadas; las del entorno no se tocan

export const claves = (var_, env) => [...[var_, ...Array.from({ length: 20 }, (_, i) => `${var_}_${i + 1}`)].map(n => env[n]), ...(inyectadas[var_.split('_')[0].toLowerCase()] || [])].filter((v, i, a) => v && a.indexOf(v) === i);

const libres = (prov, env, r) => claves(prov.toUpperCase() + '_API_KEY', env).filter(k => (enfriadas.get(`${prov}\0${k}`) || 0) <= r.ahora());
const limpiar = (msg, ks) => ks.reduce((m, k) => (k ? m.split(k).join('[clave]') : m), String(msg));  // ninguna clave sale en errores

const errHttp = (status, retryAfter) => Object.assign(new Error(`HTTP ${status}`), { status, retryAfterMs: parseRetryAfter(retryAfter) });
function parseRetryAfter(v) {
  if (v == null || v === '') return null;
  const n = Number(v); if (Number.isFinite(n)) return Math.max(0, n * 1000);
  const t = Date.parse(v); return Number.isFinite(t) ? Math.max(0, t - Date.now()) : null;
}

async function pedir(base, modelo, mensajes, clave, extra = {}, r = red()) {
  const resp = await fetch(`${base.replace(/\/$/, '')}/chat/completions`, {
    method: 'POST', signal: AbortSignal.timeout(r.timeoutMs),
    headers: { 'content-type': 'application/json', 'user-agent': 'riu-swe-code', ...(clave ? { authorization: `Bearer ${clave}` } : {}) },
    body: JSON.stringify({ model: modelo, messages: mensajes, ...(extra.tools && extra.tools.length ? { tools: extra.tools, tool_choice: extra.tool_choice || 'auto' } : {}) }),
  });
  if (!resp.ok) throw errHttp(resp.status, resp.headers.get('retry-after'));
  const j = await resp.json();
  const c = j?.choices?.[0];
  const t = c?.message?.content, tc = c?.message?.tool_calls;
  if ((!t || !String(t).trim()) && !(Array.isArray(tc) && tc.length)) throw new Error('vacio');
  const tools = Array.isArray(tc) ? tc : [];
  const cortada = !tools.length && (c.finish_reason === 'length' || (!c.finish_reason && Number(j?.usage?.completion_tokens) >= r.cortePorTokens));
  return { texto: t ? String(t) : '', tool_calls: tools, finish_reason: c.finish_reason || (tools.length ? 'tool_calls' : cortada ? 'length' : 'stop'), cortada };
}

// una peticion + continuacion automatica si la salida se corto por longitud (nunca con tool_calls)
async function completar(base, modelo, mensajes, clave, extra, r) {
  let ultimo = await pedir(base, modelo, mensajes, clave, extra, r);
  let texto = ultimo.texto;
  for (let i = 0; i < r.continuaciones && ultimo.cortada; i++) {
    let sig;
    try { sig = await pedir(base, modelo, [...mensajes, { role: 'assistant', content: texto }, { role: 'user', content: CONTINUAR }], clave, extra, r); } catch { break; }  // se conserva lo ya recibido
    texto += sig.texto; ultimo = sig;
  }
  return { texto, tool_calls: ultimo.tool_calls, finish_reason: ultimo.cortada && !ultimo.tool_calls.length ? 'length' : ultimo.finish_reason };
}

// GET {base}/models con la primera clave valida; cachea el id elegido (o su ausencia)
async function descubrir(prov, base, ks, r) {
  const k = `${prov}\0${base}`, hit = cacheModelos.get(k);
  if (hit && hit.hasta > r.ahora()) return hit.id;
  let ids = null;
  for (const clave of ks) {
    try {
      const resp = await fetch(`${base.replace(/\/$/, '')}/models`, { signal: AbortSignal.timeout(Math.min(r.descubrirMs, r.timeoutMs)), headers: { 'user-agent': 'riu-swe-code', authorization: `Bearer ${clave}` } });
      if (resp.status === 401 || resp.status === 403) continue;  // clave invalida: prueba la siguiente
      if (!resp.ok) break;
      const j = await resp.json(), lista = Array.isArray(j?.data) ? j.data : Array.isArray(j?.models) ? j.models : [];
      ids = lista.map(m => typeof m === 'string' ? m : m?.id).filter(i => typeof i === 'string' && i);
      break;
    } catch { break; }  // proveedor caido: no insistir con cada clave
  }
  const id = ids ? PICK[prov](ids) || null : null;
  cacheModelos.set(k, { id, hasta: r.ahora() + (ids ? r.cacheMs : r.cacheFalloMs) });
  return id;
}

// id efectivo para un proveedor: NVIDIA = env > descubierto > defecto; Groq = descubierto (Qwen 3.8) > env > defecto
async function modeloDe(prov, env, r) {
  const [nombreEnv, defecto] = MODELO[prov];
  if (prov === 'nvidia' && env[nombreEnv]) return env[nombreEnv];
  const ks = libres(prov, env, r);
  const d = ks.length ? await descubrir(prov, BASES[prov], ks, r) : null;
  return d || env[nombreEnv] || defecto;
}

const esperaCorta = (e, r) => Math.min(e.retryAfterMs ?? r.esperaDefecto, r.esperaMax);

// modelo concreto groq/<id> o nvidia/<id>: va directo a su API; rota por todas las claves (429/402/408/5xx/timeout/red) y descarta las 401/403
export async function externo(id, mensajes, { env = process.env, extra = {}, opts } = {}) {
  const [prov, ...resto] = id.split('/'), modelo = resto.join('/'), r = red(opts);
  const todas = claves(prov.toUpperCase() + '_API_KEY', env), ks = libres(prov, env, r);
  let ultimo = new Error(todas.length ? 'claves enfriadas' : 'sin clave'), n = 0;
  for (const k of ks) {
    if (n++ >= 20) break;
    try {
      const x = await completar(BASES[prov], modelo, mensajes, k, extra, r);
      return { salida: x.texto, tool_calls: x.tool_calls, finish_reason: x.finish_reason, via: prov, usado: id };
    } catch (e) {
      ultimo = e;
      if (e.status === 429) { enfriadas.set(`${prov}\0${k}`, r.ahora() + Math.max(r.cooldownMs, Math.min(e.retryAfterMs || 0, 600000))); await r.esperar(esperaCorta(e, r)); continue; }
      if (e.status === 401 || e.status === 403) continue;  // clave descartada
      if (e.status >= 400 && e.status < 500 && e.status !== 402 && e.status !== 408) break;  // 400/404/422...: no depende de la clave
    }
  }
  throw Object.assign(new Error(limpiar(`EXTERNO_${prov.toUpperCase()}: ${ultimo.message}`, todas)), { code: 'EXTERNO_FALLO' });
}

// modelo local de la cola HF: entra por S1 y salta a S2/S3 si no responde
export async function local(id, mensajes, { env = process.env, extra = {}, opts } = {}) {
  const fallos = [], r = red(opts);
  for (const n of [1, 2, 3]) {
    const u = env[`SWECODE_URL_S${n}`]; if (!u) continue;
    try { const x = await completar(u, id, mensajes, null, extra, r); return { salida: x.texto, tool_calls: x.tool_calls, finish_reason: x.finish_reason, via: 'hf-local', usado: id }; } catch (e) { fallos.push(`S${n}: ${e.message}`); }
  }
  throw Object.assign(new Error('HF_LOCAL: ' + (fallos.join(' | ') || 'sin SWECODE_URL_S1..S3')), { code: 'HF_LOCAL_FALLO' });
}

export async function respaldo(mensajes, { env = process.env, extra = {}, opts } = {}) {
  const fallos = [], r = red(opts);
  for (const prov of ['groq', 'nvidia']) {
    const todas = claves(prov.toUpperCase() + '_API_KEY', env);
    if (!todas.length) { fallos.push(`${prov}: sin clave`); continue; }
    try { return await externo(`${prov}/${await modeloDe(prov, env, r)}`, mensajes, { env, extra, opts }); } catch (e) { fallos.push(limpiar(`${prov}: ${e.message}`, todas)); }
  }
  try { return await local(LOCALES[0], mensajes, { env, extra, opts }); } catch (e) { fallos.push(e.message); }
  throw Object.assign(new Error('RESPALDO_AGOTADO: ' + fallos.join(' | ')), { code: 'RESPALDO_AGOTADO' });
}

// que respaldos hay configurados (conteos, nunca valores): para /health y el auto-diagnostico
export function estadoRespaldo(env = process.env) {
  return { groq: claves('GROQ_API_KEY', env).length, nvidia: claves('NVIDIA_API_KEY', env).length, hf_local: [1, 2, 3].filter(n => env[`SWECODE_URL_S${n}`]).length };
}
