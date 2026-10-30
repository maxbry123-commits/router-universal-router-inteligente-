// bloques.js — partes + checkpoint: el modelo web nunca pierde el hilo
// Entrada grande -> bloques ~2500 chars con cabecera [BLOQUE n/N · MODO X]
// checkpoint.json por conversacion: si la pagina se reinicia se retoma
// desde el ultimo bloque confirmado, no desde cero.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

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

// huella de la tarea: un checkpoint solo se retoma si es de ESTA tarea y quedo a medias
// (antes un checkpoint completo con el mismo conv_id devolvia la respuesta vieja)
export function huella(texto) { return crypto.createHash('sha256').update(String(texto)).digest('hex').slice(0, 16); }

export function checkpointLeer(convId, h) {
  try {
    const ck = JSON.parse(fs.readFileSync(ruta(convId), 'utf8'));
    return ck.completo || ck.huella !== h ? null : ck;
  } catch { return null; }
}

// secciones conocidas (para que OpenClaw sepa cuales retomar): sin volcar contenido
export function listarCheckpoints() {
  try {
    return fs.readdirSync(CK_DIR).filter(f => f.endsWith('.json')).map(f => {
      const ck = JSON.parse(fs.readFileSync(path.join(CK_DIR, f), 'utf8'));
      return { conv_id: f.slice(0, -5), modo: ck.modo, enviados: ck.enviados, total: ck.total, completo: !!ck.completo, ts: ck.ts };
    });
  } catch { return []; }
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

// auto-evolucion: el bridge anota cada arreglo propio (formato de SWE CODE free/evolucion.py); mejor esfuerzo, nunca rompe la peticion
export function registrarLeccion(l) {
  try {
    if (!l || !l.codigo || !l.accion) return false;
    const dir = path.join(DIR, 'evolucion');
    fs.mkdirSync(dir, { recursive: true });
    fs.appendFileSync(path.join(dir, 'lecciones.jsonl'), JSON.stringify({ ts: Math.floor(Date.now() / 1000), ...l }) + '\n');
    return true;
  } catch { return false; }
}
