// cuentas.js — rotacion de cuentas web (5-9 correos, misma clave)
// Vía 5+13: validar pool → pool.json; rotar solo índices ok; marcar fallos.
// G2: session-affinity con lease+TTL por conv_id (cuentaParaConv).
// credenciales: OpenClaw las inyecta por llamada (setCuentas) o env (respaldo)
import fs from 'node:fs';
import path from 'node:path';

const DATA = process.env.BRIDGE_STATE_DIR || './state';
const IDX_FILE = path.join(DATA, 'cuentas-index.json');
const POOL_FILE = path.join(DATA, 'pool.json');

function limpiaSecreto(v) {
  return String(v || '').trim().replace(/^["']+|["']+$/g, '').trim();
}

function emailOk(e) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(e || ''));
}

function escribirAtomico(destino, obj) {
  fs.mkdirSync(path.dirname(destino), { recursive: true });
  const tmp = destino + '.tmp.' + process.pid;
  fs.writeFileSync(tmp, JSON.stringify(obj, null, 2));
  fs.renameSync(tmp, destino);
}

// Fallidos por índice (persistidos en pool.json). Solo se rota entre ok.
function leerPoolMeta() {
  try { return JSON.parse(fs.readFileSync(POOL_FILE, 'utf8')); }
  catch { return { total: 0, indices: [], fallidos: {}, actualizado: null }; }
}

export function validarYGuardarPool(mails, pass) {
  const lista = (Array.isArray(mails) ? mails : String(mails || '').split(','))
    .map(s => limpiaSecreto(s)).filter(Boolean);
  const passL = limpiaSecreto(pass);
  const validos = lista.filter(emailOk);
  if (!validos.length) return { ok: false, code: 'POOL_SIN_EMAILS_VALIDOS', total: 0 };
  const meta = leerPoolMeta();
  const fallidos = meta.fallidos && typeof meta.fallidos === 'object' ? meta.fallidos : {};
  // No guardar secretos: solo conteos / índices / marcas de fallo.
  const out = {
    total: validos.length,
    indices: [...Array(validos.length).keys()],
    fallidos,
    tiene_pass: !!passL,
    actualizado: new Date().toISOString(),
  };
  try { escribirAtomico(POOL_FILE, out); } catch { /* disco opcional */ }
  return { ok: true, ...out };
}

export function marcarFallo(index, motivo = 'LOGIN_RECHAZADO') {
  const meta = leerPoolMeta();
  meta.fallidos = meta.fallidos || {};
  meta.fallidos[String(index)] = { motivo: String(motivo).slice(0, 80), ts: new Date().toISOString() };
  meta.actualizado = new Date().toISOString();
  try { escribirAtomico(POOL_FILE, meta); } catch { /* ignore */ }
  return meta;
}

export function limpiarFallos() {
  const meta = leerPoolMeta();
  meta.fallidos = {};
  meta.actualizado = new Date().toISOString();
  try { escribirAtomico(POOL_FILE, meta); } catch { /* ignore */ }
  return meta;
}

export function cuentasOk(index) {
  const meta = leerPoolMeta();
  const f = meta.fallidos || {};
  const enf = meta.enfriados || {};
  if (enf[String(index)] && Date.now() < enf[String(index)]) return false;
  return !f[String(index)];
}

// Backoff exponencial con jitter total ("full jitter"): espera aleatoria entre 0 y el tope
// base * 2^intento, con tope maximo. Fuente: AWS Architecture Blog (retry with jitter).
const BACKOFF_BASE_MS = parseInt(process.env.BRIDGE_BACKOFF_BASE_MS || '1000', 10);
const BACKOFF_CAP_MS = parseInt(process.env.BRIDGE_BACKOFF_CAP_MS || '300000', 10);
export function backoffMs(intento) {
  const tope = Math.min(BACKOFF_CAP_MS, BACKOFF_BASE_MS * 2 ** Math.max(0, intento));
  return Math.floor(Math.random() * tope);
}

// Enfria una cuenta tras un fallo transitorio (429/limite). retryAfterMs del servidor tiene prioridad.
export function enfriarCuenta(index, intento = 0, retryAfterMs = null) {
  const meta = leerPoolMeta();
  meta.enfriados = meta.enfriados || {};
  const espera = retryAfterMs != null ? Math.min(BACKOFF_CAP_MS, retryAfterMs) : backoffMs(intento);
  meta.enfriados[String(index)] = Date.now() + espera;
  meta.actualizado = new Date().toISOString();
  try { escribirAtomico(POOL_FILE, meta); } catch { /* ignore */ }
  return { index, espera_ms: espera };
}

export function estadoPool() {
  const meta = leerPoolMeta();
  let total = meta.total || 0;
  try { total = pool().length; } catch { /* sin mails */ }
  return {
    total,
    indices: [...Array(total).keys()],
    fallidos: meta.fallidos || {},
    ok: [...Array(total).keys()].filter(i => !meta.fallidos?.[String(i)]),
    actualizado: meta.actualizado || null,
    loaded: total > 0,
  };
}

// credenciales inyectadas por OpenClaw en tiempo de llamada (duenas: OpenClaw);
// env solo como respaldo. Nunca se loguean valores.
let inyectadas = null;
export function setCuentas(mails, pass) {
  const lista = Array.isArray(mails) ? mails : String(mails || '').split(',');
  const limpias = lista.map(s => limpiaSecreto(s)).filter(Boolean);
  const passL = limpiaSecreto(pass);
  if (!limpias.length || !passL) return false;
  inyectadas = { mails: limpias, pass: passL };
  validarYGuardarPool(limpias, passL);
  return true;
}

export function pool() {
  if (inyectadas) return inyectadas.mails;
  const mails = (process.env.WEB_ACCOUNTS || '').split(',').map(s => limpiaSecreto(s)).filter(Boolean);
  if (!mails.length) throw Object.assign(new Error('WEB_ACCOUNTS vacio: OpenClaw debe enviar cuentas y clave en el POST'), { code: 'CUENTAS_FALTAN' });
  // Validar/persistir meta sin secretos (una vez por proceso si falta).
  try {
    if (!fs.existsSync(POOL_FILE)) validarYGuardarPool(mails, process.env.WEB_PASS || '');
  } catch { /* ignore */ }
  return mails;
}

export function clave() {
  if (inyectadas) return inyectadas.pass;
  const p = process.env.WEB_PASS;
  if (!p) throw Object.assign(new Error('WEB_PASS no definido: OpenClaw debe enviar la clave en el POST'), { code: 'CUENTAS_FALTAN' });
  const out = limpiaSecreto(p);
  if (!out) throw Object.assign(new Error('WEB_PASS vacio tras normalizar'), { code: 'CUENTAS_FALTAN' });
  return out;
}

function idxRead() {
  try { return JSON.parse(fs.readFileSync(IDX_FILE, 'utf8')); } catch { return { i: 0 }; }
}
function idxWrite(v) {
  fs.mkdirSync(DATA, { recursive: true });
  fs.writeFileSync(IDX_FILE, JSON.stringify(v));
}

export function cuentaActual() {
  const mails = pool();
  const { i } = idxRead();
  // Preferir un índice ok.
  let idx = i % mails.length;
  for (let n = 0; n < mails.length; n++) {
    const j = (idx + n) % mails.length;
    if (cuentasOk(j)) { idx = j; break; }
  }
  return { email: mails[idx], index: idx, total: mails.length };
}

// G2 — session-affinity: la conversacion queda pegada a su cuenta hasta TTL
// (BRIDGE_LEASE_TTL_S, default 1800 s) o hasta que esa cuenta se marque fallida.
// Sin lease vigente toma la cuenta actual y la registra. Solo guarda índices, nunca secretos.
const LEASE_TTL_MS = parseInt(process.env.BRIDGE_LEASE_TTL_S || '1800', 10) * 1000;
const leases = new Map(); // convId -> {index, ts}
export function cuentaParaConv(convId) {
  const key = String(convId || '');
  const now = Date.now();
  const l = key ? leases.get(key) : null;
  if (l && now - l.ts < LEASE_TTL_MS && cuentasOk(l.index)) {
    l.ts = now; // renueva el lease mientras se use
    const mails = pool();
    return { email: mails[l.index], index: l.index, total: mails.length, lease: true };
  }
  const c = cuentaActual();
  if (key) {
    leases.delete(key);
    leases.set(key, { index: c.index, ts: now });
    if (leases.size > 500) leases.delete(leases.keys().next().value);
  }
  return { ...c, lease: false };
}
// Libera el lease de una conversacion (p. ej. tras 429 o fallo de cuenta).
export function soltarLease(convId) {
  leases.delete(String(convId || ''));
}

// Rota al siguiente correo OK (salta fallidos). Si todos fallaron → SIN_CUENTAS_OK.
export function rotar() {
  const mails = pool();
  const { i } = idxRead();
  for (let n = 1; n <= mails.length; n++) {
    const ni = (i + n) % mails.length;
    if (!cuentasOk(ni)) continue;
    idxWrite({ i: ni, rotado_en: new Date().toISOString() });
    return { email: mails[ni], index: ni, total: mails.length };
  }
  throw Object.assign(new Error('todas las cuentas marcadas fallidas'), { code: 'SIN_CUENTAS_OK' });
}

export function reiniciarIndice() {
  idxWrite({ i: 0, rotado_en: new Date().toISOString(), motivo: 'reparar' });
  return cuentaActual();
}
