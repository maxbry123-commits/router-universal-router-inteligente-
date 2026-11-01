// bloques.js — partes + checkpoint: el modelo web nunca pierde el hilo
// Entrada grande -> bloques ~2500 chars con cabecera [BLOQUE n/N · MODO X]
// checkpoint.json por conversacion: si la pagina se reinicia se retoma
// desde el ultimo bloque confirmado, no desde cero.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import os from 'node:os';
import { fileURLToPath } from 'node:url';

// Carpeta de estado: SIEMPRE absoluta y leida del entorno en cada uso (no depende del cwd).
// Sin BRIDGE_STATE_DIR el defecto es <web-bridge>/state (relativo al modulo, no al cwd).
// En produccion BRIDGE_STATE_DIR apunta a /data (respaldado); estadoEfimero() avisa si cae en tmp.
const MODULO_DIR = path.dirname(fileURLToPath(import.meta.url));
export function estadoDir() { return path.resolve(process.env.BRIDGE_STATE_DIR || path.join(MODULO_DIR, '..', 'state')); }
export function estadoEfimero() {
  const d = estadoDir();
  return [os.tmpdir(), '/tmp', '/var/tmp'].some((t) => { const r = path.resolve(t); return d === r || d.startsWith(r + path.sep); });
}
const ckDir = () => path.join(estadoDir(), 'checkpoints');
const TAM = 2500;
const ESTADOS = ['CONTINUAR', 'WAIT_TOOLS', 'DONE', 'ERROR', 'RESPUESTA_COMPLETA'];  // RESPUESTA_COMPLETA: el modelo termino (stop) pero la tarea no esta confirmada

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
function ruta(convId) { return path.join(ckDir(), `${limpio(convId)}.json`); }

// huella de la tarea: un checkpoint solo se retoma si es de ESTA tarea y quedo a medias
// (antes un checkpoint completo con el mismo conv_id devolvia la respuesta vieja)
export function huella(texto, modo = '') { return crypto.createHash('sha256').update(String(modo) + '\u0000' + String(texto)).digest('hex').slice(0, 16); }

export function checkpointLeer(convId, h) {
  try {
    const ck = JSON.parse(fs.readFileSync(ruta(convId), 'utf8'));
    return ck.completo || ck.estado === 'DONE' || ck.huella !== h ? null : ck;
  } catch { return null; }
}

// checkpoint tal cual (sin comprobar huella): para retomar una seccion sola, con el texto y el modelo guardados
export function checkpointCrudo(convId) {
  try { return JSON.parse(fs.readFileSync(ruta(convId), 'utf8')); } catch { return null; }
}

// secciones conocidas (para que OpenClaw sepa cuales retomar): sin volcar contenido
const pendientesDe = (ck) => ck.pendientes?.tool_calls?.length || (ck.estado === 'WAIT_TOOLS' ? ck.lote?.assistant?.tool_calls?.length || 0 : 0);  // tool_calls entregados al cliente y aun sin resultado
export function listarCheckpoints(propietario) {  // con `propietario` (hash) se omiten las tareas de OTRO propietario; las sin dueño (web, previas) se listan
  const CK_DIR = ckDir();
  let archivos = [];
  try { archivos = fs.readdirSync(CK_DIR).filter(f => f.endsWith('.json')); } catch { return []; }
  const out = [];
  for (const f of archivos) {  // un archivo corrupto no esconde a los demas
    try {
      const ck = JSON.parse(fs.readFileSync(path.join(CK_DIR, f), 'utf8'));
      if (ck.vinculo && ck.vinculo.propietario && ck.vinculo.propietario !== propietario) continue;  // tarea ajena: ni siquiera se lista su id
      out.push({ conv_id: f.slice(0, -5), modo: ck.modo, modelo: ck.modelo, cuenta: ck.cuenta, url: ck.url, estado: ck.estado, paso: ck.paso, proveedor: ck.proveedor, enviados: ck.enviados, total: ck.total, completo: !!ck.completo || ck.estado === 'DONE', ts: ck.ts, ...(ck.fase ? { fase: ck.fase } : {}), ...(pendientesDe(ck) ? { herramientas_pendientes: pendientesDe(ck) } : {}) });
    } catch { /* ignorado */ }
  }
  return out;
}

// --- saneado: un checkpoint nunca lleva claves, cabeceras ni tokens de autenticacion ---
// Claves de objeto prohibidas (se descartan) y patrones de secretos dentro de textos (se tachan).
// Ojo: "tokens", "tokens_recibidos", "max_tokens" son contadores y SI se guardan.
const CLAVE_PROHIBIDA = /^(authorization|proxy-authorization|cookie|set-cookie|headers?|cabeceras?|password|passwd|pwd|secret|clave|claves|key|token|bearer|credentials?|credenciales)$|api[_-]?key|apikey|secret|password|authorization|cookie|bearer|(access|refresh|auth|id|session|csrf|bearer)[_-]?token|_key$|_claves?$/i;
const SECRETO_TEXTO = [
  /\b(Authorization\s*[:=]\s*)?Bearer\s+[A-Za-z0-9._~+\/=-]{8,}/gi,
  /\b(gsk_|nvapi-|sk-|sk_|ghp_|github_pat_|hf_|xox[abp]-|AIza)[A-Za-z0-9_-]{10,}/g,
  /\b(api[_-]?key|token|password|secret)\s*[:=]\s*["']?[A-Za-z0-9._~+\/=-]{8,}/gi,
];
const MAX_TEXTO = 200000, MAX_PROF = 12;
function saneaTexto(t) { let o = t.length > MAX_TEXTO ? t.slice(0, MAX_TEXTO) : t; for (const re of SECRETO_TEXTO) o = o.replace(re, '[REDACTED]'); return o; }
export function sanear(v, prof = 0) {
  if (typeof v === 'string') return saneaTexto(v);
  if (v === null || typeof v !== 'object') return typeof v === 'function' || typeof v === 'symbol' ? undefined : v;
  if (prof >= MAX_PROF) return undefined;
  if (Array.isArray(v)) return v.map((x) => sanear(x, prof + 1));
  const out = {};
  for (const [k, x] of Object.entries(v)) { if (CLAVE_PROHIBIDA.test(k)) continue; out[k] = sanear(x, prof + 1); }
  return out;
}

function leerCrudo(convId) { try { return JSON.parse(fs.readFileSync(ruta(convId), 'utf8')); } catch { return null; } }

// escritura atomica: tmp unico + fsync + rename; si algo falla el archivo previo queda intacto y no queda .tmp
function escribirAtomico(destino, obj) {
  fs.mkdirSync(path.dirname(destino), { recursive: true });
  const tmp = `${destino}.${process.pid}.${crypto.randomBytes(4).toString('hex')}.tmp`;
  try {
    const fd = fs.openSync(tmp, 'w');
    try { fs.writeSync(fd, JSON.stringify(obj, null, 1)); try { fs.fsyncSync(fd); } catch { /* fsync no soportado */ } } finally { fs.closeSync(fd); }
    fs.renameSync(tmp, destino);
  } catch (e) { try { fs.unlinkSync(tmp); } catch { /* ya no esta */ } throw e; }
}

// campos: modo, total, enviados, ultima_salida, huella, texto, modelo, cuenta, url (existentes) +
// tarea, paso, estado (CONTINUAR|WAIT_TOOLS|DONE|ERROR), proveedor, tokens_recibidos, secciones_recibidas,
// herramientas ({tool_call_id: {resultado, ts}}; se conservan las ya confirmadas de la MISMA tarea)
export function checkpointGuardar(convId, data) {
  const limpioData = sanear(data || {});
  const previo = leerCrudo(convId);
  if (previo && previo.integridad) return;  // checkpoint de tarea (checkpoint_hf.js: integridad SHA256 / fragmentos): lo gestiona retomar_local, aqui no se reescribe
  const mismaTarea = previo && (previo.huella === limpioData.huella || !previo.huella || !limpioData.huella);
  if (mismaTarea && previo.herramientas) limpioData.herramientas = { ...previo.herramientas, ...(limpioData.herramientas || {}) };
  const estado = String(limpioData.estado || '').toUpperCase();
  limpioData.estado = ESTADOS.includes(estado) ? estado : (limpioData.completo ? 'DONE' : 'CONTINUAR');
  escribirAtomico(ruta(convId), { ...limpioData, ts: new Date().toISOString() });
}

// --- idempotencia de herramientas por ID (tool_call id -> resultado) ---
const idTool = (id) => (typeof id === 'string' || typeof id === 'number') && String(id).trim() ? String(id).trim().slice(0, 200) : null;

export function herramientaEjecutada(convId, toolId) {
  const id = idTool(toolId); if (!id) return false;
  const ck = leerCrudo(convId);
  return !!(ck && ck.herramientas && Object.prototype.hasOwnProperty.call(ck.herramientas, id));
}

export function herramientaResultado(convId, toolId) {
  const id = idTool(toolId); if (!id) return undefined;
  const ck = leerCrudo(convId);
  return ck && ck.herramientas && Object.prototype.hasOwnProperty.call(ck.herramientas, id) ? ck.herramientas[id].resultado : undefined;
}

// marca la herramienta como confirmada; true si es nueva, false si ya estaba (se conserva el primer resultado)
export function herramientaConfirmar(convId, toolId, resultado) {
  const id = idTool(toolId); if (!id) return false;
  const previo = leerCrudo(convId) || {};
  if (previo.herramientas && Object.prototype.hasOwnProperty.call(previo.herramientas, id)) return false;
  const herramientas = { ...(previo.herramientas || {}), [id]: { resultado: sanear(resultado === undefined ? null : resultado), ts: new Date().toISOString() } };
  checkpointGuardar(convId, { ...previo, herramientas });
  return true;
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
    const dir = path.join(estadoDir(), 'evolucion');
    fs.mkdirSync(dir, { recursive: true });
    fs.appendFileSync(path.join(dir, 'lecciones.jsonl'), JSON.stringify({ ts: Math.floor(Date.now() / 1000), ...l }) + '\n');
    return true;
  } catch { return false; }
}

// mejoras propuestas a partir de las lecciones (misma regla que evolucion.py: 3 repeticiones); OpenClaw las lee y las aplica con su propio commit
const DESTINO = { promover_a_runbook: 'SWE CODE free/INSTRUCCIONES.md', cambiar_estrategia: 'SWE CODE/web-bridge/src/sites.js' };
export function proponerMejoras(minimo = 3) {
  let ls = [];
  try { ls = fs.readFileSync(path.join(estadoDir(), 'evolucion', 'lecciones.jsonl'), 'utf8').split('\n').filter(Boolean).slice(-5000).map(l => { try { return JSON.parse(l); } catch { return null; } }).filter(Boolean); } catch { return []; }
  const cuenta = new Map();
  for (const l of ls) { const k = JSON.stringify([l.codigo, l.accion, l.resultado === 'PASS']); cuenta.set(k, (cuenta.get(k) || 0) + 1); }
  return [...cuenta].filter(([, n]) => n >= minimo).map(([k, n]) => {
    const [codigo, accion, ok] = JSON.parse(k); const tipo = ok ? 'promover_a_runbook' : 'cambiar_estrategia';
    return { tipo, codigo, accion, veces: n, archivo: DESTINO[tipo] };
  });
}
