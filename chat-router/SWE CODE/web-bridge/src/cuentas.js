// cuentas.js — rotacion de cuentas web (5-9 correos, misma clave)
// credenciales: OpenClaw las inyecta por llamada (setCuentas) o env (respaldo)
import fs from 'node:fs';
import path from 'node:path';

const DATA = process.env.BRIDGE_STATE_DIR || './state';
const IDX_FILE = path.join(DATA, 'cuentas-index.json');

function limpiaSecreto(v) {
  return String(v || '').trim().replace(/^["']+|["']+$/g, '').trim();
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
  return true;
}

export function pool() {
  if (inyectadas) return inyectadas.mails;
  const mails = (process.env.WEB_ACCOUNTS || '').split(',').map(s => limpiaSecreto(s)).filter(Boolean);
  if (!mails.length) throw Object.assign(new Error('WEB_ACCOUNTS vacio: OpenClaw debe enviar cuentas y clave en el POST'), { code: 'CUENTAS_FALTAN' });
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
  return { email: mails[i % mails.length], index: i % mails.length, total: mails.length };
}

// rota al siguiente correo cuando la sesion cae (misma clave universal)
export function rotar() {
  const mails = pool();
  const { i } = idxRead();
  const ni = (i + 1) % mails.length;
  idxWrite({ i: ni, rotado_en: new Date().toISOString() });
  return { email: mails[ni], index: ni, total: mails.length };
}

// Vuelve al correo 0 (sin loguear el valor). repararSesion lo usa para no quedar atrapado en un índice quemado.
export function reiniciarIndice() {
  idxWrite({ i: 0, rotado_en: new Date().toISOString(), motivo: 'reparar' });
  return cuentaActual();
}
