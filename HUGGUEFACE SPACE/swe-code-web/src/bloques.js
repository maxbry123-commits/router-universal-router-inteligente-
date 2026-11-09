// bloques.js — partes + checkpoint: el modelo web nunca pierde el hilo
// Entrada grande -> bloques ~2500 chars con cabecera [BLOQUE n/N · MODO X]
// checkpoint.json por conversacion: si la pagina se reinicia se retoma
// desde el ultimo bloque confirmado, no desde cero.
import fs from 'node:fs';
import path from 'node:path';

const DIR = process.env.BRIDGE_STATE_DIR || './state';
const CK_DIR = path.join(DIR, 'checkpoints');
const TAM = 2500;

export function partir(texto) {
  const out = [];
  for (let i = 0; i < texto.length; i += TAM) out.push(texto.slice(i, i + TAM));
  return out.length ? out : [''];
}

export function cabecera(n, total, modo) {
  return `[BLOQUE ${n}/${total} · MODO ${modo.toUpperCase()}]\n`;
}

function ruta(convId) { return path.join(CK_DIR, `${convId}.json`); }

export function checkpointLeer(convId) {
  try { return JSON.parse(fs.readFileSync(ruta(convId), 'utf8')); } catch { return null; }
}

export function checkpointGuardar(convId, data) {
  fs.mkdirSync(CK_DIR, { recursive: true });
  fs.writeFileSync(ruta(convId), JSON.stringify({ ...data, ts: new Date().toISOString() }, null, 1));
}

// resume-card: contexto minimo para que el modelo retome sin releer todo
export function resumeCard(ck) {
  return `[RETOMO] modo=${ck.modo} bloques_enviados=${ck.enviados}/${ck.total} ` +
    `ultima_salida=${(ck.ultima_salida || '').slice(0, 400)}`;
}
