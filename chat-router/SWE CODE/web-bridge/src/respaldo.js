// respaldo.js — si la web no responde: Groq -> NVIDIA -> HF local (S1..S3). Mismas claves del chat (GROQ_API_KEY, NVIDIA_API_KEY, *_1..N).
// Streaming real (stream:true) hacia Groq/NVIDIA cuando se pasa onDelta: fragmentos por callback, tool_calls reconstruidos por indice,
// conexiones keep-alive reutilizadas, TTFT y tokens/s medidos. Sin onDelta todo funciona como siempre (peticion completa, JSON).
import http from 'node:http';
import https from 'node:https';

export const BASES = { groq: 'https://api.groq.com/openai/v1', nvidia: 'https://integrate.api.nvidia.com/v1' };
// modelos autorizados del selector (Llama 3.3 de Groq y NVIDIA retirados). Muse Glimmer aparece una sola vez.
export const MODELOS_API = [
  { id: 'groq/qwen/qwen3.8-27b', nombre: 'Groq Qwen 3.8 27B' },
  { id: 'nvidia/minimaxai/minimax-m3.1-flash', nombre: 'NVIDIA MiniMax M3.1 Flash' },
  { id: 'nvidia/meta/muse-glimmer-30b', nombre: 'NVIDIA Muse Glimmer 30B' },
  { id: 'nvidia/nvidia/nemotron-3-ultra-550b-a55b', nombre: 'NVIDIA Nemotron 3 Ultra' },
  { id: 'nvidia/z-ai/glm-5.3', nombre: 'NVIDIA GLM 5.3' },
];
const MODELO = { groq: ['RIU_SWE_GROQ_MODELO', 'qwen/qwen3.8-27b'], nvidia: ['RIU_SWE_NVIDIA_MODELO', 'minimaxai/minimax-m3.1-flash'] };
export const modeloDefecto = (prov, env = process.env) => env[MODELO[prov][0]] || MODELO[prov][1];
// parametros de inferencia por modelo (id sin el prefijo del proveedor); los modelos locales y los no listados no mandan ninguno
export const AJUSTES = {
  'qwen/qwen3.8-27b': { temperature: 1.0, top_p: 0.95, max_tokens: 2048, reasoning_effort: 'medium', reasoning_format: 'hidden' },
  'minimaxai/minimax-m3.1-flash': { temperature: 1.0, top_p: 0.95, max_tokens: 4096 },
  'meta/muse-glimmer-30b': { temperature: 1.0, top_p: 0.95, max_tokens: 4096 },
  'nvidia/nemotron-3-ultra-550b-a55b': { temperature: 1.0, top_p: 0.95, max_tokens: 4096 },
  'z-ai/glm-5.3': { temperature: 0.5, top_p: 1.0, max_tokens: 4096 },
};
// descubrimiento de modelos (GET {base}/models): nada de ids inventados
const RE_GROQ = /qwen[-_]?3\.8/i;  // Qwen 3.8 (qwen3.8 / qwen-3.8); qwen3-8b NO es 3.8
const RE_NVIDIA_1 = /minimax|kimi|deepseek.?v4/i, RE_NVIDIA_2A = /muse|glimmer/i, RE_NVIDIA_2B = /nemotron.*3.*super|nemotron-3-super/i;
const PICK = {
  groq: (ids) => ids.find(i => RE_GROQ.test(i)),
  nvidia: (ids) => ids.find(i => RE_NVIDIA_1.test(i)) || ids.find(i => RE_NVIDIA_2A.test(i)) || ids.find(i => RE_NVIDIA_2B.test(i)),  // Muse/Glimmer (2A) y Nemotron-3-Super (2B) por separado
};
const autorizados = (prov) => MODELOS_API.filter(m => m.id.startsWith(prov + '/')).map(m => m.id.slice(prov.length + 1));
// del listado real del proveedor: el id exacto (env o defecto) > la regla de descubrimiento > otro id autorizado presente; null si nada sirve
const elegir = (prov, ids, env) => [env[MODELO[prov][0]], MODELO[prov][1]].filter(Boolean).find(x => ids.includes(x)) || PICK[prov](ids) || autorizados(prov).find(x => ids.includes(x)) || null;
const LOCALES = ['lfm2.5-350m', 'qwen2.5-coder-1.5b', 'qwen3.5-0.8b', 'qwen3-0.6b'];
// ---- R8: TABLA UNICA DE TIMEOUTS (la misma de compute.TIMEOUTS_MODELO_S en Python y de politicas_modelo.json; respaldo_a5.test.mjs las compara) ----
// Capas, de dentro a fuera: peticion al modelo (TIMEOUTS_DEFECTO, en stream = inactividad) < BRIDGE_RESPALDO_MS global (90 s) < plazo del bridge BRIDGE_DEADLINE_MS (100 s, server.js conDeadline: tope de TODA la respuesta)
// < proxy del Space (~100 s, se mantiene vivo con latidos SSE). Ningun valor POR DEFECTO supera el plazo del bridge (timeoutDe lo recorta); un valor explicito del operador
// (BRIDGE_RESPALDO_MS, RIU_SWE_TIMEOUTS, opts.timeoutsModelo) se respeta y el plazo del servidor sigue mandando por fuera. Harness: 600 s (RIU_HARNESS_TIMEOUT_S) en harness_client.py.
export const PLAZO_BRIDGE_MS = parseInt(process.env.BRIDGE_DEADLINE_MS || '100000', 10) || 100000;
export const TIMEOUT_DEFECTO_MS = 90000;
const TIMEOUT_MS = parseInt(process.env.BRIDGE_RESPALDO_MS || String(TIMEOUT_DEFECTO_MS), 10) || TIMEOUT_DEFECTO_MS;  // explicito = lo que el operador fije
const CONTINUAR = 'Continúa exactamente donde terminó, sin repetir';
const RED = { continuaciones: 8, cooldownMs: 60000, esperaMax: 2000, esperaDefecto: 500, backoffMs: 200, descubrirMs: 10000, cacheMs: 30 * 60000, cacheFalloMs: 60000, cortePorTokens: 15000 };
// parametros inyectables en tests: opts = { timeoutMs, timeoutsModelo, continuaciones, cooldownMs, esperaMax, backoffMs, jitter(), esperar(ms), ahora(), descubrirMs, cacheMs, signal }
const red = (o = {}) => ({ ...RED, timeoutMs: TIMEOUT_MS, esperar: (ms) => new Promise(r => setTimeout(r, ms)), ahora: Date.now, jitter: Math.random, ...o });
// timeout por modelo: opts.timeoutsModelo[<id>] > env RIU_SWE_TIMEOUTS ('{"<id>": ms}') > TIMEOUTS_DEFECTO (tabla, recortada al plazo del bridge) > global
export const TIMEOUTS_DEFECTO = { 'qwen/qwen3.8-27b': 60000, 'minimaxai/minimax-m3.1-flash': 90000, 'meta/muse-glimmer-30b': 180000, 'nvidia/nemotron-3-ultra-550b-a55b': 300000, 'z-ai/glm-5.3': 180000 };
export function timeoutDe(modelo, env, r) {
  let t = r.timeoutsModelo?.[modelo], defecto = false;
  if (t == null && env?.RIU_SWE_TIMEOUTS) { try { const o = JSON.parse(env.RIU_SWE_TIMEOUTS); if (o && typeof o === 'object') t = o[modelo]; } catch { /* env invalido: sigue el defecto */ } }
  if (t == null) { t = TIMEOUTS_DEFECTO[modelo]; defecto = t != null; }
  t = Number(t);
  if (!(Number.isFinite(t) && t > 0)) return r.timeoutMs;
  const tope = parseInt(env?.BRIDGE_DEADLINE_MS || PLAZO_BRIDGE_MS, 10) || PLAZO_BRIDGE_MS;
  return defecto ? Math.min(t, tope) : t;  // la tabla nunca supera el plazo del bridge; lo explicito del operador se respeta
}
const conTimeout = (r, modelo, env) => ({ ...r, timeoutMs: timeoutDe(modelo, env, r) });
const backoff = (n, r) => Math.round(Math.min(r.esperaMax, r.backoffMs * 2 ** n) * (0.5 + 0.5 * r.jitter()));  // exponencial con jitter (mitad a 100 % del valor)

// estado en memoria (nunca persiste ni se loguea): claves enfriadas por 429 y modelos descubiertos
const enfriadas = new Map();  // `${prov}\0${clave}` -> epoch ms hasta el que no se usa
const cacheModelos = new Map();  // `${prov}\0${base}` -> { id|null, hasta }
const metricas = new Map();  // `${prov}/${modelo}` -> acumulados de TTFT y tokens/s (solo numeros)
export function limpiarEstado() { enfriadas.clear(); cacheModelos.clear(); metricas.clear(); }


export const esLocal = (m) => LOCALES.includes(String(m || ''));
// solo ids del selector (MODELOS_API) o el que el operador fija por entorno (RIU_SWE_GROQ_MODELO / RIU_SWE_NVIDIA_MODELO): groq/llama-3.3-70b-versatile y demas ids inventados no entran
export const esExterno = (m, env = process.env) => typeof m === 'string' && (MODELOS_API.some(x => x.id === m) || ['groq', 'nvidia'].some(p => env[MODELO[p][0]] && m === `${p}/${env[MODELO[p][0]]}`));

// ids que el selector de OpenClaw ve ademas de los web-*: externos y locales
export function idsRespaldo() { return [...MODELOS_API.map(m => m.id), ...LOCALES]; }

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

// R7: parametros = defecto del modelo (AJUSTES) y DESPUES los explicitos validos del llamador (extra.params); limites REALES por proveedor en LIMITES.
// Fuente oficial (Firecrawl 2026-11-01): console.groq.com/docs/models y /docs/model/qwen/qwen3.8-27b -> MAX COMPLETION TOKENS 16,384; reasoning_effort default|none|low|medium|high; reasoning_format hidden|parsed.
// NVIDIA no publica un tope de max_tokens (solo ejemplos 8192/16384): sin tope local.
export const LIMITES = { 'qwen/qwen3.8-27b': { max_tokens: 16384, reasoning_effort: ['default', 'none', 'low', 'medium', 'high'], reasoning_format: ['hidden', 'parsed'] } };
const NUM = (v, lo, hi, abiertoLo) => typeof v === 'number' && Number.isFinite(v) && (abiertoLo ? v > lo : v >= lo) && v <= hi;
export function ajustesFinales(modelo, extra) {
  const ajustes = { ...(AJUSTES[modelo] || {}) }, lim = LIMITES[modelo] || {}, info = { ignorados: [], recortados: {} };
  const comp = AJUSTES[modelo] ? Object.keys(AJUSTES[modelo]) : null;  // con ajustes conocidos solo se admiten esos parametros
  for (const [n, v] of Object.entries(extra?.params && typeof extra.params === 'object' ? extra.params : {})) {
    if (!['temperature', 'top_p', 'max_tokens', 'reasoning_effort', 'reasoning_format'].includes(n)) continue;
    if (comp && !comp.includes(n)) { info.ignorados.push(n); continue; }
    const bien = n === 'temperature' ? NUM(v, 0, 2) : n === 'top_p' ? NUM(v, 0, 1, true) : n === 'max_tokens' ? Number.isInteger(v) && v > 0 : typeof v === 'string' && (!lim[n] || lim[n].includes(v));
    if (!bien) { info.ignorados.push(n); continue; }
    if (n === 'max_tokens' && lim.max_tokens && v > lim.max_tokens) { info.recortados.max_tokens = { pedido: v, aplicado: lim.max_tokens }; ajustes[n] = lim.max_tokens; continue; }
    ajustes[n] = v;
  }
  return { ajustes, info: info.ignorados.length || Object.keys(info.recortados).length ? Object.fromEntries(Object.entries(info).filter(([, x]) => (Array.isArray(x) ? x.length : Object.keys(x).length))) : null };
}
const cuerpo = (modelo, mensajes, extra, stream) => JSON.stringify({ model: modelo, messages: mensajes, ...ajustesFinales(modelo, extra).ajustes, ...(extra.tools && extra.tools.length ? { tools: extra.tools, tool_choice: extra.tool_choice || 'auto' } : {}), ...(stream ? { stream: true } : {}) });
const cabeceras = (clave) => ({ 'content-type': 'application/json', 'user-agent': 'riu-swe-code', ...(clave ? { authorization: `Bearer ${clave}` } : {}) });

// R3: nombre completo de una herramienta que llega fragmentada. Tres formas reales: una vez; repetido entero en cada delta; acumulativo (git, github, github_leer)
// o en trozos disjuntos (github_ + leer). Solo en el ultimo caso se concatena. (Misma regla que compute.nombre_de_trozos del backend YAIWES.)
export function nombreDeTrozos(trozos) {
  const t = (trozos || []).filter(x => typeof x === 'string' && x);
  if (!t.length) return '';
  if (new Set(t).size === 1) return t[0];
  if (t.every((x, i) => i === 0 || x.startsWith(t[i - 1]))) return t[t.length - 1];
  return t.join('');
}
// nombres de herramientas declarados en la peticion (vacio: el nombre no se valida)
const declaradas = (extra) => new Set((extra?.tools || []).map(t => t?.function?.name).filter(n => typeof n === 'string' && n));
// llamadas que NO deben ejecutarse tal cual: nombre fuera de lo declarado o argumentos JSON incompletos. Se marcan, nunca se descartan (no se pierden llamadas pendientes).
export function validarTools(tools, nombres) {
  const malas = [];
  for (const t of tools) {
    const n = t?.function?.name, a = t?.function?.arguments;
    if (nombres?.size && !nombres.has(n)) { malas.push({ id: t.id, nombre: n, motivo: 'nombre_no_declarado' }); continue; }
    if (typeof a === 'string' && a.trim()) { let ok = false; try { const v = JSON.parse(a); ok = !!v && typeof v === 'object' && !Array.isArray(v); } catch { /* incompleto */ } if (!ok) malas.push({ id: t.id, nombre: n, motivo: 'argumentos_json_incompletos' }); }
  }
  return malas;
}

// respuesta completa (JSON de chat.completion) -> { texto, tool_calls, finish_reason, cortada }
function interpretar(j, r, nombres) {
  const c = j?.choices?.[0];
  const t = c?.message?.content, tc = c?.message?.tool_calls;
  if ((!t || !String(t).trim()) && !(Array.isArray(tc) && tc.length)) throw new Error('vacio');
  const tools = conIds(Array.isArray(tc) ? tc : []);
  const cortada = !tools.length && (c.finish_reason === 'length' || (!c.finish_reason && Number(j?.usage?.completion_tokens) >= r.cortePorTokens));
  return { texto: t ? String(t) : '', tool_calls: tools, tools_invalidas: validarTools(tools, nombres), finish_reason: c.finish_reason || (tools.length ? 'tool_calls' : cortada ? 'length' : 'stop'), cortada, usage: usoDe(j?.usage) };
}
// tool_calls sin id (algunos proveedores/locales lo omiten) -> call_<n>_<index>; n = contador de respuestas del proceso. Los que traen id lo conservan.
let secLlamadas = 0;
function conIds(tools) {
  const n = ++secLlamadas;
  return tools.map((t, i) => (t && typeof t === 'object' && !(typeof t.id === 'string' && t.id.trim()) ? { ...t, id: `call_${n}_${i}` } : t));
}
// usage del proveedor -> { p, c, t } (numeros) o null
function usoDe(u) {
  if (!u || typeof u !== 'object') return null;
  const p = Number(u.prompt_tokens), c = Number(u.completion_tokens), t = Number(u.total_tokens);
  if (!Number.isFinite(p) && !Number.isFinite(c) && !Number.isFinite(t)) return null;
  return { p: Number.isFinite(p) ? p : 0, c: Number.isFinite(c) ? c : 0, t: Number.isFinite(t) ? t : (Number.isFinite(p) ? p : 0) + (Number.isFinite(c) ? c : 0) };
}

const cancelada = () => Object.assign(new Error('peticion cancelada por el cliente'), { code: 'ABORTADO' });
async function pedir(base, modelo, mensajes, clave, extra = {}, r = red()) {
  // Sin streaming (HF local, respuestas completas), Detener tambien debe cancelar la solicitud HTTP real.
  if (r.signal?.aborted) throw cancelada();
  const limite = AbortSignal.timeout(r.timeoutMs);
  const signal = r.signal ? AbortSignal.any([r.signal, limite]) : limite;
  try {
    const resp = await fetch(`${base.replace(/\/$/, '')}/chat/completions`, {
      method: 'POST', signal, headers: cabeceras(clave), body: cuerpo(modelo, mensajes, extra, false),
    });
    if (!resp.ok) throw errHttp(resp.status, resp.headers.get('retry-after'));
    return interpretar(await resp.json(), r, declaradas(extra));
  } catch (e) {
    if (r.signal?.aborted) throw cancelada();  // una cancelacion nunca rota claves ni activa el respaldo
    throw e;
  }
}

// ---- streaming real: node:http(s) con Agent keep-alive (las conexiones se reutilizan entre peticiones) ----
const AGENTES = { 'http:': new http.Agent({ keepAlive: true, keepAliveMsecs: 30000, maxSockets: 64 }), 'https:': new https.Agent({ keepAlive: true, keepAliveMsecs: 30000, maxSockets: 64 }) };
const ahoraMs = () => performance.now();

// POST con lectura incremental. h = { cabecera(res) -> 'sse' | 'json', evento(datos), json(texto) }. Inactividad > r.timeoutMs = TIMEOUT; r.signal = ABORTADO.
function peticionStream(url, headers, body, r, h) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    if (r.signal?.aborted) return reject(Object.assign(new Error('abortado'), { code: 'ABORTADO' }));
    let fin = false, timer = null, req = null;
    const cerrar = () => { fin = true; clearTimeout(timer); r.signal?.removeEventListener('abort', alAbortar); };
    const fallar = (e, drenar) => { if (fin) return; cerrar(); if (drenar) drenar(); else req?.destroy(); reject(e); };
    const alAbortar = () => fallar(Object.assign(new Error('abortado'), { code: 'ABORTADO' }));
    const tocar = () => { clearTimeout(timer); timer = setTimeout(() => fallar(Object.assign(new Error(`timeout ${r.timeoutMs}ms`), { code: 'TIMEOUT' })), r.timeoutMs); };
    r.signal?.addEventListener('abort', alAbortar, { once: true });
    req = (u.protocol === 'https:' ? https : http).request(u, { method: 'POST', agent: AGENTES[u.protocol], headers: { ...headers, 'content-length': Buffer.byteLength(body), accept: 'text/event-stream, application/json' } }, (res) => {
      let tipo;
      try { tipo = h.cabecera(res); } catch (e) { return fallar(e, () => res.resume()); }  // 4xx/5xx: se drena y el socket se reutiliza
      res.setEncoding('utf8');
      let buf = '', datos = [], todo = '';
      const despachar = () => { if (datos.length) { const d = datos.join('\n'); datos = []; h.evento(d); } };
      const linea = (l) => { if (l === '') despachar(); else if (l.startsWith('data:')) datos.push(l.slice(5).replace(/^ /, '')); };  // ':' = comentario, otros campos se ignoran
      res.on('data', (c) => {
        if (fin) return;
        tocar();
        try {
          if (tipo === 'json') { todo += c; return; }
          buf += c;
          let i;
          while ((i = buf.search(/\r\n|\n|\r/)) >= 0) {
            const l = buf.slice(0, i), salto = buf.startsWith('\r\n', i) ? 2 : 1;
            if (buf[i] === '\r' && i + 1 >= buf.length) break;  // '\r' final: puede ser la mitad de un \r\n
            buf = buf.slice(i + salto); linea(l);
          }
        } catch (e) { fallar(e); }
      });
      res.on('end', () => {
        if (fin) return;
        try { if (tipo === 'json') h.json(todo); else { if (buf) linea(buf.replace(/\r$/, '')); despachar(); } } catch (e) { return fallar(e); }
        cerrar(); resolve();
      });
      res.on('error', (e) => fallar(e));
      res.on('aborted', () => fallar(new Error('stream interrumpido')));
    });
    req.on('error', (e) => fallar(e));
    tocar();
    req.end(body);
  });
}

// una peticion stream:true: cada fragmento de texto va a ctx.emitir al llegar; los tool_calls se reconstruyen por indice y se devuelven completos
async function pedirStream(base, modelo, mensajes, clave, extra, r, ctx, metr) {
  const t0 = ahoraMs();
  let tPrimero = null, texto = '', fr = null, hecho = false, usoTokens = null, fragmentos = 0, usoCompleto = null;
  const acc = new Map();  // indice -> tool_call
  const primero = () => { if (tPrimero === null) { tPrimero = ahoraMs(); if (metr.ttft_ms === null) metr.ttft_ms = tPrimero - t0; } };
  const emitir = (t) => { if (!t) return; primero(); fragmentos++; texto += t; ctx.emitir(t); };
  const acumular = (d) => {
    for (const [pos, f] of (Array.isArray(d) ? d : []).entries()) {
      if (!f || typeof f !== 'object') continue;
      const k = Number.isInteger(f.index) ? f.index : pos;
      const t = acc.get(k) || { id: '', type: 'function', function: { name: '', arguments: '' }, trozos: [] };
      if (typeof f.id === 'string' && f.id) t.id = f.id;
      if (typeof f.type === 'string' && f.type) t.type = f.type;
      const n = f.function?.name, a = f.function?.arguments;
      if (typeof n === 'string' && n) { t.trozos.push(n); t.function.name = nombreDeTrozos(t.trozos); }  // R3: github_ + leer = github_leer; repetido o acumulativo no se duplica
      if (typeof a === 'string' && a) t.function.arguments += a;
      acc.set(k, t); primero(); fragmentos++;
    }
  };
  const procesar = (j) => {
    if (j?.error) { const c = Number(j.error.code ?? j.error.status); throw Object.assign(new Error('STREAM_ERROR'), { status: c >= 400 && c < 600 ? c : undefined }); }
    const u = j?.usage || j?.x_groq?.usage;
    if (u && Number.isFinite(Number(u.completion_tokens))) usoTokens = Number(u.completion_tokens);
    if (u) usoCompleto = usoDe(u) || usoCompleto;
    const c = j?.choices?.[0]; if (!c) return;
    const d = c.delta || {};
    if (typeof d.content === 'string') emitir(d.content);
    else if (!c.delta && typeof c.message?.content === 'string') emitir(c.message.content);
    if (d.tool_calls) acumular(d.tool_calls);
    if (c.finish_reason) fr = c.finish_reason;
  };
  let json = null;
  await peticionStream(`${base.replace(/\/$/, '')}/chat/completions`, cabeceras(clave), cuerpo(modelo, mensajes, extra, true), r, {
    cabecera: (res) => {
      if (res.statusCode < 200 || res.statusCode >= 300) throw errHttp(res.statusCode, res.headers['retry-after']);
      return /application\/json/i.test(String(res.headers['content-type'] || '')) ? 'json' : 'sse';
    },
    evento: (d) => { if (d.trim() === '[DONE]') { hecho = true; return; } let j; try { j = JSON.parse(d); } catch { return; } procesar(j); },
    json: (txt) => { json = JSON.parse(txt); },
  });
  const tFin = ahoraMs();
  if (json) {  // el proveedor ignoro stream y contesto JSON completo: se entrega entero
    const x = interpretar(json, r, declaradas(extra));
    if (x.texto) emitir(x.texto);
    const n = Number(json?.usage?.completion_tokens);
    metr.total_ms += tFin - t0; metr.peticiones++;
    if (Number.isFinite(n)) metr.tokens += n;
    return x;
  }
  if (!hecho && !fr) throw Object.assign(new Error('STREAM_CORTADO'), { code: 'STREAM_CORTADO' });
  const tools = conIds([...acc.entries()].sort((a, b) => a[0] - b[0]).map(([, t]) => t).filter(t => t.function.name).map(({ trozos, ...t }) => ({ ...t, function: { ...t.function, arguments: t.function.arguments || '{}' } })));
  if (!texto && !tools.length) throw new Error('vacio');
  metr.peticiones++; metr.total_ms += tFin - t0;
  if (usoTokens !== null) metr.tokens += usoTokens; else { metr.tokens += fragmentos; metr.tokens_estimado = true; }
  if (tPrimero !== null) metr.gen_ms += tFin - tPrimero;
  const cortada = !tools.length && (fr === 'length' || (!fr && usoTokens !== null && usoTokens >= r.cortePorTokens));
  return { texto, tool_calls: tools, tools_invalidas: validarTools(tools, declaradas(extra)), finish_reason: tools.length ? 'tool_calls' : fr || (cortada ? 'length' : 'stop'), cortada, usage: usoCompleto };
}

// una peticion + continuacion automatica si la salida se corto por longitud (nunca con tool_calls).
// ctx = { onDelta, flujo }: con onDelta se hace streaming real y flujo.texto acumula lo YA ENTREGADO (un intento/proveedor posterior sigue desde ahi, sin repetirlo);
// solo con flujo (sin onDelta, p. ej. HF local) la peticion es normal pero parte del texto ya entregado.
async function completar(base, modelo, mensajes, clave, extra, r, ctx = {}) {
  const stream = typeof ctx.onDelta === 'function', flujo = ctx.flujo;
  const con = (t) => (t ? [...mensajes, { role: 'assistant', content: t }, { role: 'user', content: CONTINUAR }] : mensajes);
  const metr = { ttft_ms: null, tokens: 0, tokens_estimado: false, gen_ms: 0, total_ms: 0, peticiones: 0 };
  const ctxS = stream ? { emitir: (t) => { flujo.texto += t; try { ctx.onDelta(t); } catch { /* un fallo del consumidor no corta al modelo */ } } } : null;
  const t0 = ahoraMs();
  let texto = flujo ? flujo.texto : '';
  const uso = { visto: false, p: 0, c: 0, t: 0 };  // usage del proveedor sumado entre continuaciones
  const una = async (t) => {
    const x = await (stream ? pedirStream(base, modelo, con(t), clave, extra, r, ctxS, metr) : pedir(base, modelo, con(t), clave, extra, r));
    if (x.usage) { uso.visto = true; uso.p += x.usage.p; uso.c += x.usage.c; uso.t += x.usage.t; }
    return x;
  };
  let ultimo;
  try { ultimo = await una(texto); } catch (e) { if (texto && e.message === 'vacio') ultimo = { texto: '', tool_calls: [], finish_reason: 'stop', cortada: false }; else throw e; }
  texto += ultimo.texto;
  for (let i = 0; i < r.continuaciones && ultimo.cortada; i++) {
    let sig;
    try { sig = await una(texto); } catch (e) { if (stream) throw e; break; }  // sin stream se conserva lo ya recibido; en stream la siguiente clave/proveedor continua
    texto += sig.texto; ultimo = sig;
  }
  const total = ahoraMs() - t0;
  const tokNS = uso.visto && uso.c > 0 ? uso.c : null;  // sin stream: los tokens son SOLO los que informa el proveedor (usage); sin usage no se inventan
  const tps = stream ? (metr.tokens > 0 && metr.gen_ms > 0 ? Math.round((metr.tokens / (metr.gen_ms / 1000)) * 10) / 10 : null) : (tokNS && total > 0 ? Math.round((tokNS / (total / 1000)) * 10) / 10 : null);
  const tokensUso = uso.visto ? { prompt_tokens: uso.p, completion_tokens: uso.c, total_tokens: uso.t } : {};
  const metricas = stream
    ? { stream: true, ttft_ms: metr.ttft_ms === null ? null : Math.round(metr.ttft_ms), tokens: metr.tokens || null, tokens_estimado: metr.tokens_estimado, origen_tokens: metr.tokens ? (metr.tokens_estimado ? 'estimado' : 'proveedor') : null, tokens_s: tps, total_ms: Math.round(total), peticiones: metr.peticiones, ...tokensUso }
    : { stream: false, ttft_ms: null, tokens: tokNS, tokens_estimado: false, origen_tokens: tokNS ? 'proveedor' : null, tokens_s: tps, total_ms: Math.round(total), ...tokensUso };
  const invalidas = ultimo.tools_invalidas || [];
  if (invalidas.length) metricas.tools_invalidas = invalidas.length;
  const infoP = ajustesFinales(modelo, extra).info;
  if (infoP) metricas.parametros = infoP;
  return { texto, tool_calls: ultimo.tool_calls, tools_invalidas: invalidas, finish_reason: ultimo.cortada && !ultimo.tool_calls.length ? 'length' : ultimo.finish_reason, metricas };
}

// metricas internas por modelo (solo numeros): ultimo y promedio de TTFT y tokens/s
function anotarMetricas(clave, m) {
  const e = metricas.get(clave) || { llamadas: 0, n_ttft: 0, sum_ttft: 0, n_tps: 0, sum_tps: 0 };
  e.llamadas++; e.total_ms = m.total_ms;
  if (m.ttft_ms !== null && m.ttft_ms !== undefined) { e.ttft_ms = m.ttft_ms; e.n_ttft++; e.sum_ttft += m.ttft_ms; }
  if (m.tokens_s !== null && m.tokens_s !== undefined) { e.tokens_s = m.tokens_s; e.n_tps++; e.sum_tps += m.tokens_s; }
  metricas.set(clave, e);
}
export function estadoMetricas() {
  return Object.fromEntries([...metricas.entries()].map(([k, e]) => [k, {
    llamadas: e.llamadas, ttft_ms: e.ttft_ms ?? null, ttft_prom_ms: e.n_ttft ? Math.round(e.sum_ttft / e.n_ttft) : null,
    tokens_s: e.tokens_s ?? null, tokens_s_prom: e.n_tps ? Math.round((e.sum_tps / e.n_tps) * 10) / 10 : null, total_ms: e.total_ms,
  }]));
}

// GET {base}/models con la primera clave valida; cachea la lista de ids (o su ausencia)
async function listarIds(prov, base, ks, r) {
  const k = `${prov}\0${base}`, hit = cacheModelos.get(k);
  if (hit && hit.hasta > r.ahora()) return hit.ids;
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
  cacheModelos.set(k, { ids, hasta: r.ahora() + (ids ? r.cacheMs : r.cacheFalloMs) });
  return ids;
}

// id efectivo para un proveedor: NVIDIA = env > descubierto > defecto; Groq = descubierto (Qwen 3.8) > env > defecto
async function modeloDe(prov, env, r) {
  const [nombreEnv, defecto] = MODELO[prov];
  if (prov === 'nvidia' && env[nombreEnv]) return env[nombreEnv];
  const ks = libres(prov, env, r);
  const ids = ks.length ? await listarIds(prov, BASES[prov], ks, r) : null;
  return (ids && ids.length ? elegir(prov, ids, env) : null) || env[nombreEnv] || defecto;
}

// disponibilidad real de cada id de MODELOS_API segun GET /models de su proveedor. Sin clave o con el proveedor sin listar: SIN VERIFICAR (no se afirma nada).
// NO DISPONIBLE solo si el proveedor listo sus modelos y el id no esta: nunca se sustituye por otro en silencio.
export async function disponibilidad({ env = process.env, opts } = {}) {
  const r = red(opts), listas = {};
  for (const prov of ['groq', 'nvidia']) { const ks = libres(prov, env, r); listas[prov] = ks.length ? await listarIds(prov, BASES[prov], ks, r) : null; }
  return MODELOS_API.map((m) => {
    const prov = m.id.split('/')[0], mid = m.id.slice(prov.length + 1), l = listas[prov];
    const disponible = Array.isArray(l) && l.length ? l.includes(mid) : null;
    return { id: m.id, nombre: m.nombre, proveedor: prov, disponible, estado: disponible === true ? 'DISPONIBLE' : disponible === false ? 'NO DISPONIBLE' : 'SIN VERIFICAR' };
  });
}

// ---- 152: tabla de errores. Una politica DISTINTA por familia (misma que TABLA_ERRORES de externos.py) ----
export const TABLA_ERRORES = {
  limite_temporal:    { codigos: [429], reintentar: true,  rotarClave: true,  respetaRetryAfter: true,  enfriarClave: true,  texto: '429: limite de peticiones/tokens; se espera Retry-After (con tope) y se rota de clave' },
  credito_cuota:      { codigos: [402], reintentar: false, rotarClave: true,  respetaRetryAfter: false, enfriarClave: true,  texto: '402: sin credito/cuota en esa clave; se rota y la clave no se prueba primero durante 10 min' },
  credencial_permiso: { codigos: [401, 403], reintentar: false, rotarClave: true, respetaRetryAfter: false, enfriarClave: false, texto: '401/403: credencial invalida o sin permiso; se descarta esa clave' },
  timeout_red:        { codigos: [408], reintentar: true,  rotarClave: false, respetaRetryAfter: false, enfriarClave: false, texto: 'timeout/red: el proveedor entero se enfria y se pasa al siguiente (no se prueban sus demas claves)' },
  servidor_temporal:  { codigos: [500, 502, 503, 504, 529], reintentar: true, rotarClave: false, respetaRetryAfter: true, enfriarClave: false, texto: '5xx: backoff exponencial con jitter (o Retry-After) y siguiente clave; tope = numero de claves' },
  peticion_invalida:  { codigos: [400, 404, 422], reintentar: false, rotarClave: false, respetaRetryAfter: false, enfriarClave: false, texto: '400/404/422: modelo o peticion invalida; no se reintenta ni se cambia de modelo' },
};
export function clasificarError(status, { red = false } = {}) {
  if (red) return { tipo: 'timeout_red', ...TABLA_ERRORES.timeout_red };
  for (const [tipo, e] of Object.entries(TABLA_ERRORES)) if (e.codigos.includes(status)) return { tipo, ...e };
  const t = Number.isInteger(status) && status >= 400 && status < 500 ? 'peticion_invalida' : Number.isInteger(status) ? 'servidor_temporal' : 'timeout_red';
  return { tipo: t, ...TABLA_ERRORES[t] };
}
const tipoDe = (e) => clasificarError(Number.isInteger(e?.status) ? e.status : null, { red: !Number.isInteger(e?.status) }).tipo;
const COOLDOWN_CREDITO_MS = 10 * 60000;

// timeout (fetch TimeoutError, inactividad del stream o HTTP 408): el proveedor entero esta lento/caido -> no se prueban sus demas claves
const esTimeout = (e) => e?.name === 'TimeoutError' || e?.code === 'TIMEOUT' || e?.status === 408;
const esperaCorta = (e, r) => Math.min(e.retryAfterMs ?? r.esperaDefecto, r.esperaMax);

// modelo concreto groq/<id> o nvidia/<id>: va directo a su API; rota por todas las claves (429/402/408/5xx/timeout/red) y descarta las 401/403.
// onDelta(texto): streaming real; flujo = { texto } acumula lo entregado (compartido entre intentos/proveedores); onInicio({via, usado}) al empezar.
export async function externo(id, mensajes, { env = process.env, extra = {}, opts, onDelta, onInicio, flujo } = {}) {
  const [prov, ...resto] = id.split('/'), modelo = resto.join('/'), r = conTimeout(red(opts), modelo, env);
  const todas = claves(prov.toUpperCase() + '_API_KEY', env), ks = libres(prov, env, r);
  const ctx = onDelta ? { onDelta, flujo: flujo || { texto: '' } } : { flujo };
  let ultimo = new Error(todas.length ? 'claves enfriadas' : 'sin clave'), n = 0, fallos = 0;
  if (onInicio) { try { onInicio({ via: prov, usado: id }); } catch { /* informativo */ } }
  for (const [i, k] of ks.entries()) {
    if (n++ >= 20) break;
    try {
      const x = await completar(BASES[prov], modelo, mensajes, k, extra, r, ctx);
      anotarMetricas(`${prov}/${modelo}`, x.metricas);
      return { salida: x.texto, tool_calls: x.tool_calls, tools_invalidas: x.tools_invalidas, finish_reason: x.finish_reason, via: prov, usado: id, metricas: x.metricas };
    } catch (e) {
      ultimo = e;
      if (e.code === 'ABORTADO' || r.signal?.aborted) throw cancelada();  // Detener: ni otra clave ni otro proveedor
      if (esTimeout(e)) { for (const x of todas) enfriadas.set(`${prov}\0${x}`, r.ahora() + r.cooldownMs); break; }  // primer timeout: se enfria el proveedor (todas sus claves) y se corta; respaldo() no reentra
      if (e.status === 429) { enfriadas.set(`${prov}\0${k}`, r.ahora() + Math.max(r.cooldownMs, Math.min(e.retryAfterMs || 0, 600000))); await r.esperar(esperaCorta(e, r)); continue; }
      if (e.status === 402) { enfriadas.set(`${prov}\0${k}`, r.ahora() + COOLDOWN_CREDITO_MS); continue; }  // sin credito/cuota: otra clave puede servir; esta no se repite ni se prueba primero 10 min
      if (e.status === 401 || e.status === 403) continue;  // clave descartada
      if (e.status >= 400 && e.status < 500) break;  // 400/404/422...: no depende de la clave
      if (i < ks.length - 1) await r.esperar(Number.isFinite(e.retryAfterMs) && e.status >= 500 ? esperaCorta(e, r) : backoff(fallos++, r));  // 5xx/red: Retry-After (con tope) o backoff exponencial con jitter antes de la siguiente clave
    }
  }
  throw Object.assign(new Error(limpiar(`EXTERNO_${prov.toUpperCase()}: ${ultimo.message}`, todas)), { code: 'EXTERNO_FALLO', tipo: tipoDe(ultimo), ...(Number.isInteger(ultimo.status) ? { status: ultimo.status } : {}), ...(ctx.flujo?.texto ? { parcial: ctx.flujo.texto } : {}) });
}

// modelo local de la cola HF: entra por S1 y salta a S2/S3 si no responde (sin stream: la cola HF no lo recibe; con flujo previo continua sin repetirlo)
export async function local(id, mensajes, { env = process.env, extra = {}, opts, onInicio, flujo } = {}) {
  const fallos = [], r = conTimeout(red(opts), id, env);
  if (onInicio) { try { onInicio({ via: 'hf-local', usado: id }); } catch { /* informativo */ } }
  for (const n of [1, 2, 3]) {
    const u = env[`SWECODE_URL_S${n}`]; if (!u) continue;
    try { const x = await completar(u, id, mensajes, null, extra, r, { flujo }); anotarMetricas(`hf-local/${id}`, x.metricas); return { salida: x.texto, tool_calls: x.tool_calls, tools_invalidas: x.tools_invalidas, finish_reason: x.finish_reason, via: 'hf-local', usado: id, servidor: `S${n}`, metricas: x.metricas }; } catch (e) { if (e.code === 'ABORTADO' || r.signal?.aborted) throw cancelada(); fallos.push(`S${n}: ${e.message}`); }
  }
  throw Object.assign(new Error('HF_LOCAL: ' + (fallos.join(' | ') || 'sin SWECODE_URL_S1..S3')), { code: 'HF_LOCAL_FALLO' });
}

export async function respaldo(mensajes, { env = process.env, extra = {}, opts, onDelta, onInicio, flujo } = {}) {
  const fallos = [], r = red(opts), f = onDelta ? (flujo || { texto: '' }) : flujo;
  const intentos = [];  // 156-161: rastro (sin credenciales) de cada proveedor intentado; el cambio de proveedor/modelo NUNCA se oculta
  for (const prov of ['groq', 'nvidia']) {
    const todas = claves(prov.toUpperCase() + '_API_KEY', env);
    if (!todas.length) { fallos.push(`${prov}: sin clave`); continue; }
    if (!libres(prov, env, r).length) { fallos.push(`${prov}: enfriado (timeout/429 reciente)`); continue; }  // no se reentra en un proveedor ya enfriado
    let id = `${prov}/${modeloDefecto(prov, env)}`;
    try { id = `${prov}/${await modeloDe(prov, env, r)}`; const x = await externo(id, mensajes, { env, extra, opts, onDelta, onInicio, flujo: f }); intentos.push({ via: prov, usado: id, ok: true }); return { ...x, intentos }; }
    catch (e) { if (e.code === 'ABORTADO' || r.signal?.aborted) throw cancelada(); intentos.push({ via: prov, usado: id, ok: false, tipo: e.tipo || tipoDe(e), ...(Number.isInteger(e.status) ? { status: e.status } : {}) }); fallos.push(limpiar(`${prov}: ${e.message}`, todas)); }
  }
  try { const x = await local(LOCALES[0], mensajes, { env, extra, opts, onInicio, flujo: f }); intentos.push({ via: 'hf-local', usado: LOCALES[0], ok: true }); return { ...x, intentos }; }
  catch (e) { if (e.code === 'ABORTADO' || r.signal?.aborted) throw cancelada(); intentos.push({ via: 'hf-local', usado: LOCALES[0], ok: false, tipo: 'timeout_red' }); fallos.push(e.message); }
  throw Object.assign(new Error('RESPALDO_AGOTADO: ' + fallos.join(' | ')), { code: 'RESPALDO_AGOTADO', intentos, ...(f?.texto ? { parcial: f.texto } : {}) });
}

// que respaldos hay configurados (conteos, nunca valores): para /health y el auto-diagnostico
export function estadoRespaldo(env = process.env) {
  return { groq: claves('GROQ_API_KEY', env).length, nvidia: claves('NVIDIA_API_KEY', env).length, hf_local: [1, 2, 3].filter(n => env[`SWECODE_URL_S${n}`]).length };
}
