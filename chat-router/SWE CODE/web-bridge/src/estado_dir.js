// estado_dir.js — B1: resuelve BRIDGE_STATE_DIR ANTES de que otros módulos lo lean (primer import de server.js).
// En HF Space /data es el disco persistente: si existe y es escribible, BRIDGE_STATE_DIR=/data
// cuando no está definida o apunta a un tmp efímero (p.ej. /tmp/state del boot.sh). Si no, se respeta lo definido / ./state.
// Migración no destructiva: copia de /tmp/state a /data solo los archivos que aún no existen en /data.
// BRIDGE_STATE_DIR_FIJO=1 desactiva el ajuste (respeta el valor tal cual).
import fs from 'node:fs';
import path from 'node:path';

export const DATA_PERSIST = process.env.BRIDGE_DATA_PERSIST || '/data';

function escribible(d) {
  try { if (!fs.statSync(d).isDirectory()) return false; fs.accessSync(d, fs.constants.W_OK); return true; } catch { return false; }
}
const esTmp = (d) => { const r = path.resolve(d); return r === '/tmp' || r.startsWith('/tmp/') || r.startsWith('/dev/shm'); };

function copiarFaltantes(src, dst) {
  let n = 0;
  for (const e of fs.readdirSync(src, { withFileTypes: true })) {
    const a = path.join(src, e.name), b = path.join(dst, e.name);
    try {
      if (e.isDirectory()) { fs.mkdirSync(b, { recursive: true }); n += copiarFaltantes(a, b); }
      else if (e.isFile() && !fs.existsSync(b)) { fs.copyFileSync(a, b); n++; }
    } catch {}
  }
  return n;
}

export function resolverEstadoDir(env = process.env) {
  const actual = env.BRIDGE_STATE_DIR;
  if (env.BRIDGE_STATE_DIR_FIJO === '1') return { dir: actual || './state', origen: 'fijo' };
  if (escribible(DATA_PERSIST) && (!actual || esTmp(actual))) {
    let migrados = 0;
    if (actual && actual !== DATA_PERSIST && fs.existsSync(actual)) { try { migrados = copiarFaltantes(actual, DATA_PERSIST); } catch {} }
    env.BRIDGE_STATE_DIR = DATA_PERSIST;
    env.BRIDGE_STATE_DIR_ANTERIOR = actual || '';
    return { dir: DATA_PERSIST, origen: 'hf_persist', anterior: actual || null, migrados };
  }
  return { dir: actual || './state', origen: actual ? 'env' : 'defecto' };
}

export const ESTADO_DIR_INFO = resolverEstadoDir();
