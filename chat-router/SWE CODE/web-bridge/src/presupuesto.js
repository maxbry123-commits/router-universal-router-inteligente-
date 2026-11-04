// presupuesto.js — listas A1 (budget80, GAP tipado, watchdog /retomar) + Code C1-C3, C5, C6, C8, C9, C11. Solo Groq/NVIDIA.
// Sin red propia salvo watchdogRetomar (cliente). Nunca loguea claves.
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';

// ---- GAP tipado (A1 propuestas-6) ----
export const GAP = Object.freeze({ RATE_LIMIT: 'RATE_LIMIT', TIMEOUT: 'TIMEOUT', LENGTH: 'LENGTH', HARNESS_DOWN: 'HARNESS_DOWN', BUDGET: 'BUDGET' });
export function tipoGap(e = {}, finish) {
  if (e.gap && GAP[e.gap]) return e.gap;
  if (finish === 'length') return GAP.LENGTH;
  const m = String(e.message || ''), c = String(e.code || '');
  if (e.status === 429 || /rate.?limit|429/i.test(m)) return GAP.RATE_LIMIT;
  if (e.status === 408 || e.status === 504 || /TIMEOUT|timed? ?out|ETIMEDOUT|plazo/i.test(m + c)) return GAP.TIMEOUT;
  if (/HARNESS|ECONNREFUSED|ENOTFOUND|checkpoint.*(no disponible|caido)/i.test(m + c) || (e.status >= 500 && e.status < 600)) return GAP.HARNESS_DOWN;
  return null;
}

// ---- C1 / A1-budget80 / C2: coste estimado vs remaining (TPM y RPM por separado) ----
export const FRACCION = Math.min(1, Math.max(0.1, parseFloat(process.env.RIU_CUPO_FRACCION || '0.8') || 0.8));
export function estimarCoste(mensajes = [], extra = {}) {
  const chars = (Array.isArray(mensajes) ? mensajes : []).reduce((a, m) => a + (typeof m?.content === 'string' ? m.content.length : JSON.stringify(m?.content ?? '').length), 0);
  const salida = Number(extra?.params?.max_tokens || extra?.max_tokens) || 1024;
  return { req: 1, tok: Math.ceil(chars / 4) + salida };
}
// cupo = { req, tok } leido de x-ratelimit-remaining-* (puede faltar uno). Solo se usa FRACCION (80%) del remaining.
export function alcanza(cupo, coste, fraccion = FRACCION) {
  if (!cupo) return { ok: true };
  const faltaReq = Number.isFinite(cupo.req) && cupo.req * fraccion < coste.req;
  const faltaTok = Number.isFinite(cupo.tok) && cupo.tok * fraccion < coste.tok;
  return { ok: !faltaReq && !faltaTok, faltaReq, faltaTok };
}
// C9: GAP BUDGET suave = pausa programada hasta el reset, no error duro
export const gapBudget = (prov, esperaMs) => Object.assign(new Error(`EXTERNO_${String(prov).toUpperCase()}: GAP BUDGET remaining < coste estimado; pausa programada ${Math.ceil((esperaMs || 0) / 1000)} s`), { code: 'EXTERNO_FALLO', tipo: 'limite_temporal', status: 429, gap: GAP.BUDGET, suave: true, reanudarEnMs: esperaMs || 0 });

// ---- C3: cola serial (1 llamada a la vez por clave) ----
const colas = new Map();
export function enCola(llave, fn) {
  const prev = colas.get(llave) || Promise.resolve();
  const sig = prev.catch(() => {}).then(fn);
  const fin = sig.catch(() => {}); colas.set(llave, fin);
  fin.then(() => { if (colas.get(llave) === fin) colas.delete(llave); });
  return sig;
}

// ---- C5: no comprimir historial al retomar si hay prompt-cache ----
export const conPromptCache = (env = process.env) => String(env.RIU_PROMPT_CACHE ?? '1') !== '0';
export function historialParaRetomar(conversacion, { env = process.env, comprimir } = {}) {
  if (conPromptCache(env) || typeof comprimir !== 'function') return conversacion;  // prefijo intacto = cache valido
  return comprimir(conversacion);
}

// ---- C6: idempotency key por tool (tarea + nombre + argumentos; el id del modelo cambia al retomar) ----
export const claveIdempotencia = (tareaId, t = {}) => crypto.createHash('sha256').update(JSON.stringify([String(tareaId), t.nombre ?? null, t.argumentos ?? null])).digest('hex').slice(0, 32);

// ---- C8: escritura incremental a disco (N lineas por vuelta + checkpoint) ----
export async function escribirIncremental(archivo, lineas, { porVuelta = 50, guardarCheckpoint, desde = 0 } = {}) {
  fs.mkdirSync(path.dirname(archivo), { recursive: true });
  let hechas = desde;
  for (let i = desde; i < lineas.length; i += porVuelta) {
    const trozo = lineas.slice(i, i + porVuelta);
    fs.appendFileSync(archivo, trozo.join('\n') + '\n');
    hechas = i + trozo.length;
    if (typeof guardarCheckpoint === 'function') await guardarCheckpoint({ archivo, lineas_escritas: hechas });
  }
  return hechas;
}

// ---- C11: chat corto vs tarea larga ----
export function esTareaLarga(mensajes = [], extra = {}) {
  if (extra.tarea_id || extra.larga === true) return true;
  const max = Number(extra?.params?.max_tokens || extra?.max_tokens) || 0;
  return max > parseInt(process.env.RIU_CHAT_CORTO_MAX_TOKENS || '4096', 10) || estimarCoste(mensajes, { max_tokens: 1 }).tok > parseInt(process.env.RIU_CHAT_CORTO_MAX_ENTRADA || '24000', 10);
}

// ---- A1 propuestas-8: watchdog cliente -> /retomar solo si la tarea larga se corto (GAP) ----
export async function watchdogRetomar(base, id, { headers = {}, intentos = 12, esperaMs = 5000, consultar = fetch, esperar = (ms) => new Promise((r) => setTimeout(r, ms)) } = {}) {
  let ultimo = null;
  for (let i = 0; i < intentos; i++) {
    const res = await consultar(`${String(base).replace(/\/$/, '')}/v1/secciones/${encodeURIComponent(id)}/retomar`, { method: 'POST', headers: { 'content-type': 'application/json', ...headers }, body: '{}' });
    const j = await res.json().catch(() => ({}));
    ultimo = j;
    const gap = j.gap || tipoGap({ status: res.status, message: j.error?.message || j.error || '' }, j.finish_reason);
    if (res.ok && !gap && j.finish_reason !== 'length') return j;  // completa: no se vuelve a llamar
    if (res.status === 401 || res.status === 403 || res.status === 404) return j;  // no es corte: no reintentar
    await esperar(Math.max(esperaMs, Number(j.reanudarEnMs) || 0));
  }
  return ultimo;
}
