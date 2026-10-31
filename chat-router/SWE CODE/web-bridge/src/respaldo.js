// respaldo.js — si la web no responde: Groq -> NVIDIA -> HF local (S1..S3). Mismas claves del chat (GROQ_API_KEY, NVIDIA_API_KEY, *_1..N).
export const BASES = { groq: 'https://api.groq.com/openai/v1', nvidia: 'https://integrate.api.nvidia.com/v1' };
const MODELO = { groq: ['RIU_SWE_GROQ_MODELO', 'llama-3.3-70b-versatile'], nvidia: ['RIU_SWE_NVIDIA_MODELO', 'meta/llama-3.3-70b-instruct'] };
const LOCALES = ['lfm2.5-350m', 'qwen2.5-coder-1.5b', 'qwen3.5-0.8b', 'qwen3-0.6b'];
const TIMEOUT_MS = parseInt(process.env.BRIDGE_RESPALDO_MS || '60000', 10);

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

async function pedir(base, modelo, mensajes, clave, extra = {}) {
  const r = await fetch(`${base.replace(/\/$/, '')}/chat/completions`, {
    method: 'POST', signal: AbortSignal.timeout(TIMEOUT_MS),
    headers: { 'content-type': 'application/json', 'user-agent': 'riu-swe-code', ...(clave ? { authorization: `Bearer ${clave}` } : {}) },
    body: JSON.stringify({ model: modelo, messages: mensajes, ...(extra.tools && extra.tools.length ? { tools: extra.tools, tool_choice: extra.tool_choice || 'auto' } : {}) }),
  });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  const c = (await r.json())?.choices?.[0];
  const t = c?.message?.content, tc = c?.message?.tool_calls;
  if ((!t || !String(t).trim()) && !(Array.isArray(tc) && tc.length)) throw new Error('vacio');
  return { texto: t ? String(t) : '', tool_calls: Array.isArray(tc) ? tc : [], finish_reason: c.finish_reason || (tc && tc.length ? 'tool_calls' : 'stop') };
}

// modelo concreto groq/<id> o nvidia/<id>: va directo a su API (con sus claves)
export async function externo(id, mensajes, { env = process.env, extra = {} } = {}) {
  const [prov, ...resto] = id.split('/');
  let ultimo = new Error('sin clave');
  for (const k of claves(prov.toUpperCase() + '_API_KEY', env)) {
    try { const r = await pedir(BASES[prov], resto.join('/'), mensajes, k, extra); return { salida: r.texto, tool_calls: r.tool_calls, finish_reason: r.finish_reason, via: prov, usado: id }; } catch (e) { ultimo = e; }
  }
  throw Object.assign(new Error(`EXTERNO_${prov.toUpperCase()}: ${ultimo.message}`), { code: 'EXTERNO_FALLO' });
}

// modelo local de la cola HF: entra por S1 y salta a S2/S3 si no responde
export async function local(id, mensajes, { env = process.env, extra = {} } = {}) {
  const fallos = [];
  for (const n of [1, 2, 3]) {
    const u = env[`SWECODE_URL_S${n}`]; if (!u) continue;
    try { const r = await pedir(u, id, mensajes, null, extra); return { salida: r.texto, tool_calls: r.tool_calls, finish_reason: r.finish_reason, via: 'hf-local', usado: id }; } catch (e) { fallos.push(`S${n}: ${e.message}`); }
  }
  throw Object.assign(new Error('HF_LOCAL: ' + (fallos.join(' | ') || 'sin SWECODE_URL_S1..S3')), { code: 'HF_LOCAL_FALLO' });
}

export async function respaldo(mensajes, { env = process.env, extra = {} } = {}) {
  const fallos = [];
  for (const prov of ['groq', 'nvidia']) {
    const id = `${prov}/${env[MODELO[prov][0]] || MODELO[prov][1]}`;
    if (!claves(prov.toUpperCase() + '_API_KEY', env).length) { fallos.push(`${prov}: sin clave`); continue; }
    try { return await externo(id, mensajes, { env, extra }); } catch (e) { fallos.push(`${prov}: ${e.message}`); }
  }
  try { return await local(LOCALES[0], mensajes, { env, extra }); } catch (e) { fallos.push(e.message); }
  throw Object.assign(new Error('RESPALDO_AGOTADO: ' + fallos.join(' | ')), { code: 'RESPALDO_AGOTADO' });
}

// que respaldos hay configurados (conteos, nunca valores): para /health y el auto-diagnostico
export function estadoRespaldo(env = process.env) {
  return { groq: claves('GROQ_API_KEY', env).length, nvidia: claves('NVIDIA_API_KEY', env).length, hf_local: [1, 2, 3].filter(n => env[`SWECODE_URL_S${n}`]).length };
}
