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

// el conv_id viene del cliente: se sanea para no salir de checkpoints/ (../ y similares)
const limpio = (c) => String(c).replace(/[^\w.-]/g, '_').replace(/\.{2,}/g, '_').slice(0, 100) || 'sin-id';
function ruta(convId) { return path.join(CK_DIR, `${limpio(convId)}.json`); }

// huella de la tarea: un checkpoint solo se retoma si es de ESTA tarea y quedo a medias
// (antes un checkpoint completo con el mismo conv_id devolvia la respuesta vieja)
export function huella(texto, modo = '') { return crypto.createHash('sha256').update(String(modo) + '\u0000' + String(texto)).digest('hex').slice(0, 16); }

export function checkpointLeer(convId, h) {
  try {
    const ck = JSON.parse(fs.readFileSync(ruta(convId), 'utf8'));
    return ck.completo || ck.huella !== h ? null : ck;
  } catch { return null; }
}

// checkpoint tal cual (sin comprobar huella): para retomar una seccion sola, con el texto y el modelo guardados
export function checkpointCrudo(convId) {
  try { return JSON.parse(fs.readFileSync(ruta(convId), 'utf8')); } catch { return null; }
}

// secciones conocidas (para que OpenClaw sepa cuales retomar): sin volcar contenido
export function listarCheckpoints() {
  let archivos = [];
  try { archivos = fs.readdirSync(CK_DIR).filter(f => f.endsWith('.json')); } catch { return []; }
  const out = [];
  for (const f of archivos) {  // un archivo corrupto no esconde a los demas
    try {
      const ck = JSON.parse(fs.readFileSync(path.join(CK_DIR, f), 'utf8'));
      out.push({ conv_id: f.slice(0, -5), modo: ck.modo, modelo: ck.modelo, cuenta: ck.cuenta, url: ck.url, enviados: ck.enviados, total: ck.total, completo: !!ck.completo, ts: ck.ts });
    } catch { /* ignorado */ }
  }
  return out;
}

export function checkpointGuardar(convId, data) {
  fs.mkdirSync(CK_DIR, { recursive: true });
  const destino = ruta(convId), tmp = destino + '.tmp';  // escritura atomica: un corte no deja un JSON a medias
  fs.writeFileSync(tmp, JSON.stringify({ ...data, ts: new Date().toISOString() }, null, 1));
  fs.renameSync(tmp, destino);
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

// mejoras propuestas a partir de las lecciones (misma regla que evolucion.py: 3 repeticiones); OpenClaw las lee y las aplica con su propio commit
const DESTINO = { promover_a_runbook: 'SWE CODE free/INSTRUCCIONES.md', cambiar_estrategia: 'SWE CODE/web-bridge/src/sites.js' };
export function proponerMejoras(minimo = 3) {
  let ls = [];
  try { ls = fs.readFileSync(path.join(DIR, 'evolucion', 'lecciones.jsonl'), 'utf8').split('\n').filter(Boolean).slice(-5000).map(l => { try { return JSON.parse(l); } catch { return null; } }).filter(Boolean); } catch { return []; }
  const cuenta = new Map();
  for (const l of ls) { const k = JSON.stringify([l.codigo, l.accion, l.resultado === 'PASS']); cuenta.set(k, (cuenta.get(k) || 0) + 1); }
  return [...cuenta].filter(([, n]) => n >= minimo).map(([k, n]) => {
    const [codigo, accion, ok] = JSON.parse(k); const tipo = ok ? 'promover_a_runbook' : 'cambiar_estrategia';
    return { tipo, codigo, accion, veces: n, archivo: DESTINO[tipo] };
  });
}
