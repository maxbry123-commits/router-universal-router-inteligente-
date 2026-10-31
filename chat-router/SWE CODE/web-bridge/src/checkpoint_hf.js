// checkpoint_hf.js — checkpoint universal de tarea (modelos locales HF, Groq, NVIDIA) sobre el almacen que YA existe:
// la herramienta `guardar`/`leer` del Harness DeepSeek (chat/backend/deepseek_harness/server.py), que escribe en el bucket HF por el Router MVP.
// Contrato REAL del Harness: POST {RIU_DEEPSEEK_HARNESS_URL}{RIU_DEEPSEEK_HARNESS_PATH||/invoke}, cabecera X-API-Key
// (RIU_DEEPSEEK_HARNESS_API_KEY || RIU_API_KEY, igual que plugins deepseek_harness/plugin.py), cuerpo
// {action:"invoke", tool:"guardar"|"leer", args:{nombre, valor}} -> {status:"ok", result:{...}} | {status:"error", error}.
// Ruta del dato: tareas/swe/<id>/checkpoint.json (misma convencion que tareas/<id>/diario.json del Harness); `valor` es un string JSON.
// Sin Harness configurado (o caido) el checkpoint se guarda igual en BRIDGE_STATE_DIR/checkpoints/<id>.json (escritura atomica);
// con Harness se guarda en ambos. Nunca se guardan claves ni cabeceras.
import fs from 'node:fs';
import path from 'node:path';
import { sanear as saneaBloques, estadoDir } from './bloques.js';

export const ID_RE = /^[a-zA-Z0-9_-]{1,64}$/;
export const TIMEOUT_MS = 30000;
export const idValido = (id) => typeof id === 'string' && ID_RE.test(id);

const falla = (code, message) => Object.assign(new Error(message), { code });

// ---------- sin claves ----------
// nombres de campo con pinta de clave: authorization, api_key, x-api-key, claves, token, access_token, secret, password, cookie... (max_tokens NO)
const CAMPO_SECRETO = /(?:authorization|api[_-]?key|apikey|clave|secret|password|passwd|cookie|bearer)s?$|token$/i;
// valores con forma de clave de Groq/NVIDIA/OpenAI/GitHub/HF, "Bearer xxx" y "api_key":"xxx" dentro de un JSON en texto
const VALOR_SECRETO = [
  /\bgsk[_-][A-Za-z0-9_-]{6,}/g, /\bnvapi-[A-Za-z0-9_-]{8,}/g, /\bsk-(?:sp-)?[A-Za-z0-9_-]{12,}/g,
  /\bgithub_pat_[A-Za-z0-9_]{12,}/g, /\bgh[pousr]_[A-Za-z0-9]{12,}/g, /\bhf_[A-Za-z0-9]{20,}/g,
  /\bBearer\s+[A-Za-z0-9._~+/=-]{8,}/gi,
];
const JSON_SECRETO = /("(?:[\w-]*(?:authorization|api[_-]?key|apikey|clave|secret|password|passwd|cookie|bearer|token))s?"\s*:\s*)"(?:[^"\\]|\\.)*"/gi;
const REDACTADO = '[REDACTADO]';

function limpiarTexto(s, secretos) {
  let t = s;
  for (const lit of secretos) if (lit) t = t.split(lit).join(REDACTADO);
  for (const re of VALOR_SECRETO) t = t.replace(re, REDACTADO);
  return t.replace(JSON_SECRETO, `$1"${REDACTADO}"`);
}

// copia profunda sin campos-clave y con los valores-clave tachados. `secretos`: claves literales conocidas (las del entorno). Idempotente.
function saneaPropio(valor, lits, prof = 0) {
  if (prof > 60) return null;
  if (typeof valor === 'string') return limpiarTexto(valor, lits);
  if (Array.isArray(valor)) return valor.map((v) => saneaPropio(v, lits, prof + 1));
  if (valor && typeof valor === 'object') {
    const out = {};
    for (const [k, v] of Object.entries(valor)) { if (CAMPO_SECRETO.test(k) || v === undefined || typeof v === 'function') continue; out[k] = saneaPropio(v, lits, prof + 1); }
    return out;
  }
  return valor;
}
// primero el sanear() de bloques.js (claves de objeto, cabeceras, patrones de secretos) y despues este (claves literales del entorno, JSON dentro de textos)
export function sanear(valor, secretos = []) {
  const lits = secretos.filter((s) => typeof s === 'string' && s.length >= 4);
  return saneaPropio(saneaBloques(valor), lits);
}

// ---------- almacenamiento local ----------
const dirLocal = (env) => path.join(env.BRIDGE_STATE_DIR ? path.resolve(env.BRIDGE_STATE_DIR) : estadoDir(), 'checkpoints');  // absoluta, igual que bloques.js
const rutaLocal = (id, env) => path.join(dirLocal(env), `${id}.json`);

function guardarLocal(id, estado, env) {
  fs.mkdirSync(dirLocal(env), { recursive: true });
  const destino = rutaLocal(id, env), tmp = `${destino}.${process.pid}.${Math.random().toString(36).slice(2)}.tmp`;
  try { fs.writeFileSync(tmp, JSON.stringify(estado, null, 1)); fs.renameSync(tmp, destino); }  // atomico: un corte no deja un JSON a medias
  catch (e) { try { fs.rmSync(tmp, { force: true }); } catch { /* nada */ } throw e; }
}

function leerLocal(id, env) {
  try { const ck = JSON.parse(fs.readFileSync(rutaLocal(id, env), 'utf8')); return ck && typeof ck === 'object' ? ck : null; } catch { return null; }
}

// ---------- Harness ----------
function urlHarness(env) {
  const u = String(env.RIU_DEEPSEEK_HARNESS_URL || '').trim().replace(/\/+$/, '');
  if (!u) return '';
  try { const p = new URL(u); return (p.hostname && !p.username && !p.password && (p.protocol === 'https:' || (p.protocol === 'http:' && ['127.0.0.1', 'localhost'].includes(p.hostname)))) ? u : ''; } catch { return ''; }
}

async function invocar(herramienta, args, { env, fetch: f, timeoutMs, secretos }) {
  const base = urlHarness(env);
  if (!base) throw falla('HARNESS_NO_CONFIGURADO', 'sin RIU_DEEPSEEK_HARNESS_URL valida');
  const ruta = String(env.RIU_DEEPSEEK_HARNESS_PATH || '/invoke'), clave = env.RIU_DEEPSEEK_HARNESS_API_KEY || env.RIU_API_KEY;
  try {
    const resp = await f(base + (ruta.startsWith('/') ? ruta : '/invoke'), {
      method: 'POST', signal: AbortSignal.timeout(timeoutMs),
      headers: { 'content-type': 'application/json', ...(clave ? { 'x-api-key': clave } : {}) },
      body: JSON.stringify({ action: 'invoke', tool: herramienta, args }),
    });
    const j = await resp.json().catch(() => null);
    if (!resp.ok || !j || j.status !== 'ok') throw new Error(`HTTP ${resp.status}: ${String(j?.error || j?.detail || 'respuesta invalida').slice(0, 80)}`);
    return j.result;
  } catch (e) {
    throw falla('HARNESS_FALLO', limpiarTexto(`harness ${herramienta}: ${e.name === 'TimeoutError' ? 'timeout' : e.message}`, [...secretos, clave || '']));  // el error nunca repite una clave
  }
}

const nombreHarness = (id) => `tareas/swe/${id}/checkpoint.json`;
const opciones = (o = {}) => ({ env: o.env || process.env, fetch: o.fetch || globalThis.fetch, timeoutMs: o.timeoutMs ?? TIMEOUT_MS, secretos: Array.isArray(o.secretos) ? o.secretos : [] });

// Guarda el checkpoint: SIEMPRE en local (no se pierde) y, con Harness configurado, tambien en el Harness.
// Devuelve {local, harness, ts, harness_error?}. Solo lanza si no se pudo guardar en ningun sitio.
export async function guardarCheckpoint(id, estado, o = {}) {
  if (!idValido(id)) throw falla('CHECKPOINT_ID_INVALIDO', 'id: letras, numeros, - y _ (1 a 64)');
  const op = opciones(o), ts = new Date().toISOString();
  const limpio = { ...sanear(estado, op.secretos), ts };
  const r = { local: false, harness: false, ts };
  try { guardarLocal(id, limpio, op.env); r.local = true; } catch (e) { r.local_error = e.code || 'ESCRITURA'; }
  if (urlHarness(op.env)) {
    try { await invocar('guardar', { nombre: nombreHarness(id), valor: JSON.stringify(limpio) }, op); r.harness = true; } catch (e) { r.harness_error = e.message; }
  } else r.harness_error = 'HARNESS_NO_CONFIGURADO';
  if (!r.local && !r.harness) throw falla('CHECKPOINT_NO_GUARDADO', `no se pudo guardar el checkpoint ${id} (${r.local_error}; ${r.harness_error})`);
  return r;
}

// Lee el checkpoint mas reciente entre el local y el del Harness (tras un reinicio el disco local puede haberse perdido). null si no hay.
export async function leerCheckpoint(id, o = {}) {
  if (!idValido(id)) throw falla('CHECKPOINT_ID_INVALIDO', 'id: letras, numeros, - y _ (1 a 64)');
  const op = opciones(o), local = leerLocal(id, op.env);
  let remoto = null;
  if (urlHarness(op.env)) {
    try {
      const res = await invocar('leer', { nombre: nombreHarness(id) }, op), v = res?.valor;
      const ck = typeof v === 'string' ? JSON.parse(v) : v;
      remoto = ck && typeof ck === 'object' ? ck : null;
    } catch { remoto = null; }  // sin checkpoint en el Harness (o Harness caido): vale el local
  }
  if (local && remoto) return String(remoto.ts || '') > String(local.ts || '') ? remoto : local;
  return remoto || local || null;
}
