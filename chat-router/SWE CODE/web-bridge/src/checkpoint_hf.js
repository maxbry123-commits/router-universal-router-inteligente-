// checkpoint_hf.js — checkpoint universal de tarea (modelos locales HF, Groq, NVIDIA) sobre el almacen que YA existe:
// la herramienta `guardar`/`leer` del Harness DeepSeek (chat/backend/deepseek_harness/server.py), que escribe en el bucket HF por el Router MVP.
// Contrato REAL del Harness: POST {RIU_DEEPSEEK_HARNESS_URL}{RIU_DEEPSEEK_HARNESS_PATH||/invoke}, cabecera X-API-Key
// (RIU_DEEPSEEK_HARNESS_API_KEY || RIU_API_KEY, igual que plugins deepseek_harness/plugin.py), cuerpo
// {action:"invoke", tool:"guardar"|"leer", args:{nombre, valor}} -> {status:"ok", result:{...}} | {status:"error", error}.
// Ruta del dato: tareas/swe/<origen>/<id>/checkpoint.json con origen = yaiwes | openclaw (el del contrato de la tarea) o 'bridge'; los checkpoints previos sin origen
// (tareas/swe/<id>/checkpoint.json) se siguen leyendo. `valor` es un string JSON.
// Sin Harness configurado (o caido) el checkpoint se guarda igual en BRIDGE_STATE_DIR/checkpoints/<id>.json (escritura atomica);
// con Harness se guarda en ambos. Nunca se guardan claves ni cabeceras.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
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

// ---------- integridad, version y fragmentos (134-135) ----------
// Todo checkpoint lleva `integridad: {version:2, algoritmo:'sha256', sha256, bytes, partes}`; sha256 = hash del cuerpo (el checkpoint serializado SIN el campo `integridad`).
// Pequeno (<= RIU_CHECKPOINT_FRAGMENTO caracteres, defecto 200000): un solo documento con partes:0. Grande: el documento principal es el MANIFIESTO (metadatos + integridad.partes =
// [{n, nombre, bytes, sha256}]) y el cuerpo va en fragmentos <id>.<sha12>.<nnn>.frag (local) / tareas/swe/<origen>/<id>/checkpoint.<sha12>.<nnn>.frag (Harness; limite 1 MB por valor).
// Los fragmentos se escriben ANTES que el manifiesto (un corte deja el manifiesto anterior intacto); los de la version anterior se borran despues.
// Al leer se verifica cada fragmento y el total: si algo no coincide el checkpoint es CORRUPTO y no se usa (nunca se mezcla con otro). Sin `integridad` = formato previo (version 1), se acepta.
export const VERSION_CHECKPOINT = 2;
export const FRAGMENTO_DEFECTO = 200000;
const sha = (t) => crypto.createHash('sha256').update(t, 'utf8').digest('hex');
const maxFragmento = (env) => { const n = parseInt(env.RIU_CHECKPOINT_FRAGMENTO, 10); return Number.isFinite(n) && n >= 16 ? n : FRAGMENTO_DEFECTO; };
const META = ['tipo', 'tarea_id', 'estado', 'fase', 'completo', 'origen', 'huella', 'modelo', 'ts'];
const partirTexto = (t, max) => {
  const out = [];
  for (let i = 0; i < t.length;) { let f = Math.min(i + max, t.length); const c = t.charCodeAt(f - 1); if (f < t.length && c >= 0xD800 && c <= 0xDBFF) f--; out.push(t.slice(i, f)); i = f; }
  return out;
};
const nombreParte = (base, sha12, n) => `${base}.${sha12}.${String(n).padStart(3, '0')}.frag`;

// documento a guardar: { doc, partes:[{sufijo, nombre, texto}] } ; `base` = prefijo del nombre de los fragmentos
export function empaquetar(limpio, max, base) {
  const cuerpo = JSON.stringify(limpio), hash = sha(cuerpo), bytes = Buffer.byteLength(cuerpo);
  if (cuerpo.length <= max) return { doc: { ...limpio, integridad: { version: VERSION_CHECKPOINT, algoritmo: 'sha256', sha256: hash, bytes, partes: 0 } }, partes: [] };
  const trozos = partirTexto(cuerpo, max), h12 = hash.slice(0, 12);
  const partes = trozos.map((texto, i) => ({ n: i + 1, nombre: nombreParte(base, h12, i + 1), texto }));
  const meta = {}; for (const k of META) if (limpio[k] !== undefined && (limpio[k] === null || typeof limpio[k] !== 'object')) meta[k] = limpio[k];
  return { doc: { ...meta, fragmentado: true, integridad: { version: VERSION_CHECKPOINT, algoritmo: 'sha256', sha256: hash, bytes, partes: partes.map((p) => ({ n: p.n, nombre: p.nombre, bytes: Buffer.byteLength(p.texto), sha256: sha(p.texto) })) } }, partes };
}

// verifica un documento (y sus fragmentos con leerParte(nombre) -> string|null). Devuelve {ck} valido o {corrupto:motivo}
export async function desempaquetar(doc, leerParte) {
  if (!doc || typeof doc !== 'object' || Array.isArray(doc)) return { corrupto: 'DOCUMENTO_INVALIDO' };
  const ig = doc.integridad;
  if (ig === undefined) return { ck: doc };  // formato previo (version 1): sin integridad que verificar
  if (!ig || typeof ig !== 'object' || ig.version !== VERSION_CHECKPOINT || ig.algoritmo !== 'sha256' || typeof ig.sha256 !== 'string') return { corrupto: 'VERSION_NO_SOPORTADA' };
  let cuerpo;
  if (Array.isArray(ig.partes)) {
    const trozos = [];
    for (const p of ig.partes) {
      const t = p && typeof p.nombre === 'string' ? await leerParte(p.nombre) : null;
      if (typeof t !== 'string') return { corrupto: `FRAGMENTO_FALTA:${p?.n}` };
      if (Buffer.byteLength(t) !== p.bytes || sha(t) !== p.sha256) return { corrupto: `FRAGMENTO_SHA:${p.n}` };
      trozos.push(t);
    }
    cuerpo = trozos.join('');
  } else {
    const { integridad, ...resto } = doc;
    cuerpo = JSON.stringify(resto);
  }
  if (sha(cuerpo) !== ig.sha256 || Buffer.byteLength(cuerpo) !== ig.bytes) return { corrupto: 'SHA256_NO_COINCIDE' };
  try { const ck = JSON.parse(cuerpo); return ck && typeof ck === 'object' ? { ck } : { corrupto: 'CUERPO_INVALIDO' }; } catch { return { corrupto: 'CUERPO_INVALIDO' }; }
}

// ---------- almacenamiento local ----------
const dirLocal = (env) => path.join(env.BRIDGE_STATE_DIR ? path.resolve(env.BRIDGE_STATE_DIR) : estadoDir(), 'checkpoints');  // absoluta, igual que bloques.js
const rutaLocal = (id, env) => path.join(dirLocal(env), `${id}.json`);

function escribirAtomico(destino, texto) {
  const tmp = `${destino}.${process.pid}.${Math.random().toString(36).slice(2)}.tmp`;
  try { fs.writeFileSync(tmp, texto); fs.renameSync(tmp, destino); }  // atomico: un corte no deja un JSON a medias
  catch (e) { try { fs.rmSync(tmp, { force: true }); } catch { /* nada */ } throw e; }
}

function guardarLocal(id, empaque, env) {
  fs.mkdirSync(dirLocal(env), { recursive: true });
  const previo = leerDocLocal(id, env);
  for (const p of empaque.partes) escribirAtomico(path.join(dirLocal(env), p.nombre), p.texto);  // fragmentos primero
  escribirAtomico(rutaLocal(id, env), JSON.stringify(empaque.doc, null, 1));  // manifiesto/documento despues
  const vivos = new Set(empaque.partes.map((p) => p.nombre));
  for (const p of (Array.isArray(previo?.integridad?.partes) ? previo.integridad.partes : [])) if (!vivos.has(p.nombre) && /^[\w.-]+\.frag$/.test(String(p.nombre))) { try { fs.rmSync(path.join(dirLocal(env), p.nombre), { force: true }); } catch { /* nada */ } }
}

function leerDocLocal(id, env) {
  try { const d = JSON.parse(fs.readFileSync(rutaLocal(id, env), 'utf8')); return d && typeof d === 'object' ? d : null; } catch { return null; }
}
const leerParteLocal = (env) => (nombre) => { if (!/^[\w.-]+\.frag$/.test(String(nombre))) return null; try { return fs.readFileSync(path.join(dirLocal(env), nombre), 'utf8'); } catch { return null; } };

// {ck, corrupto}: ck valido | corrupto con motivo | nada (ni archivo)
async function leerLocal(id, env) {
  const doc = leerDocLocal(id, env);
  return doc ? desempaquetar(doc, leerParteLocal(env)) : {};
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
      method: 'POST', redirect: 'error', signal: AbortSignal.timeout(timeoutMs),
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

export const ORIGEN_RE = /^[A-Za-z0-9_-]{1,32}$/;
export const ORIGENES = ['bridge', 'openclaw', 'yaiwes'];
export const origenValido = (o) => (typeof o === 'string' && ORIGEN_RE.test(o) ? o : null);
const nombreHarness = (id, origen) => (origen ? `tareas/swe/${origen}/${id}/checkpoint.json` : `tareas/swe/${id}/checkpoint.json`);  // sin origen = ruta previa (solo lectura)
const opciones = (o = {}) => ({ origen: origenValido(o.origen), env: o.env || process.env, fetch: o.fetch || globalThis.fetch, timeoutMs: o.timeoutMs ?? TIMEOUT_MS, secretos: Array.isArray(o.secretos) ? o.secretos : [] });

const origenDe = (estado, op) => origenValido(estado?.origen) || op.origen || 'bridge';

// Guarda el checkpoint: SIEMPRE en local (no se pierde) y, con Harness configurado, tambien en el Harness. Grande -> fragmentos + manifiesto (ver arriba).
// Devuelve {local, harness, ts, partes, harness_error?}. Solo lanza si no se pudo guardar en ningun sitio.
export async function guardarCheckpoint(id, estado, o = {}) {
  if (!idValido(id)) throw falla('CHECKPOINT_ID_INVALIDO', 'id: letras, numeros, - y _ (1 a 64)');
  const op = opciones(o), ts = new Date().toISOString(), max = maxFragmento(op.env);
  const limpio = { ...sanear(estado, op.secretos), ts }; delete limpio.integridad;
  const r = { local: false, harness: false, ts };
  const loc = empaquetar(limpio, max, id);
  r.partes = loc.partes.length;
  try { guardarLocal(id, loc, op.env); r.local = true; } catch (e) { r.local_error = e.code || 'ESCRITURA'; }
  if (urlHarness(op.env)) {
    try {
      const nombre = nombreHarness(id, origenDe(estado, op)), base = nombre.replace(/\.json$/, '');
      const rem = empaquetar(limpio, max, base);
      for (const p of rem.partes) await invocar('guardar', { nombre: p.nombre, valor: p.texto }, op);  // fragmentos antes que el manifiesto
      await invocar('guardar', { nombre, valor: JSON.stringify(rem.doc) }, op); r.harness = true;
    } catch (e) { r.harness_error = e.message; }
  } else r.harness_error = 'HARNESS_NO_CONFIGURADO';
  if (!r.local && !r.harness) throw falla('CHECKPOINT_NO_GUARDADO', `no se pudo guardar el checkpoint ${id} (${r.local_error}; ${r.harness_error})`);
  return r;
}

// Lee el checkpoint mas reciente entre el local y el del Harness (tras un reinicio el disco local puede haberse perdido). null si no hay.
// En el Harness busca en tareas/swe/<origen>/<id> (origen = el pedido, el del checkpoint local o 'bridge') y en la ruta previa sin origen; si no hay nada y el origen no se
// conoce, prueba los demas origenes. Entre varios gana el de `ts` mas reciente. Cada copia se VERIFICA (SHA256/fragmentos): una copia corrupta no se usa; si solo hay copias
// corruptas lanza CHECKPOINT_CORRUPTO (no se arranca de cero en silencio: podria repetir operaciones ya hechas).
export async function leerCheckpoint(id, o = {}) {
  if (!idValido(id)) throw falla('CHECKPOINT_ID_INVALIDO', 'id: letras, numeros, - y _ (1 a 64)');
  const op = opciones(o), { ck: local, corrupto: corruptoLocal } = await leerLocal(id, op.env);
  const origen = op.origen || origenValido(local?.origen) || 'bridge', conocido = !!(op.origen || origenValido(local?.origen));
  const corruptos = corruptoLocal ? [`local:${corruptoLocal}`] : [];
  let remoto = null;
  if (urlHarness(op.env)) {
    const leerRaw = async (nombre) => { try { const res = await invocar('leer', { nombre }, op); return typeof res?.valor === 'string' ? res.valor : null; } catch { return null; } };  // sin dato (o Harness caido)
    const leer = async (nombre) => {
      const v = await leerRaw(nombre); if (v === null) return null;
      let doc; try { doc = JSON.parse(v); } catch { return null; }
      const x = await desempaquetar(doc, leerRaw);
      if (x.corrupto) { corruptos.push(`harness:${x.corrupto}`); return null; }
      return x.ck;
    };
    const masNuevo = (a, b) => (a && b ? (String(b.ts || '') > String(a.ts || '') ? b : a) : a || b);
    for (const nombre of [nombreHarness(id, origen), nombreHarness(id)]) remoto = masNuevo(remoto, await leer(nombre));
    if (!remoto && !conocido) for (const otro of ORIGENES.filter((x) => x !== origen)) { remoto = await leer(nombreHarness(id, otro)); if (remoto) break; }
  }
  if (local && remoto) return String(remoto.ts || '') > String(local.ts || '') ? remoto : local;
  const ck = remoto || local || null;
  if (!ck && corruptos.length) throw falla('CHECKPOINT_CORRUPTO', `el checkpoint ${id} no pasa la verificacion de integridad (${corruptos.join(', ').slice(0, 160)}) y no se usa`);
  return ck;
}
