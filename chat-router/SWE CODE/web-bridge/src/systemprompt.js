// systemprompt.js — system-prompt de la ficha del Router MVP (router-mvp/fichas/system-prompt), aplicado a TODOS los modelos del bridge
// (Groq, NVIDIA, HF local, web-*), tanto para el chat directo (SWE CODE / SWEN CODE free) como para las tareas que llegan desde OpenClaw
// (mismo pipeline: server.js arma los mensajes finales una sola vez antes de llamar a externo()/local()/consultarWeb()).
// Toggle ON/OFF persistido en BRIDGE_STATE_DIR/system-prompt-on.flag ("1"/"0"); sin archivo se asume ON. Sin la ficha (o vacia), no rompe nada: string vacio.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const AQUI = path.dirname(fileURLToPath(import.meta.url));
const RELATIVA = ['router-mvp', 'fichas', 'system-prompt'];
let cacheTxt = null, cacheClave = null;

// 3 candidatos: RIU_REPO_ROOT (si existe) -> process.cwd()/../../../ (cwd = web-bridge) -> __dirname/../../../../ (desde src/)
function candidatos(env) {
  const out = [];
  if (env.RIU_REPO_ROOT) out.push(path.join(env.RIU_REPO_ROOT, ...RELATIVA));
  out.push(path.join(process.cwd(), '..', '..', '..', ...RELATIVA));
  out.push(path.resolve(AQUI, '..', '..', '..', '..', ...RELATIVA));
  return out;
}
// Misma composicion de mvp.prompt.sistema(): core parametrizado + bloque 3 + bloque 4.
// Los archivos originales viven SOLO en router-mvp/fichas/system-prompt; no copiar
// el texto de la ficha ni usar solamente el core (un prompt incompleto no es PASS).
const VARIABLES = Object.freeze({
  '[ROL_ESPECIALIZADO]': 'el ROL DEL NODO indicado más abajo',
  '[NIVEL / ESPECIALIDAD / PLATAFORMA]': 'senior / el que exija la tarea / la del repositorio',
  '[PROYECTO]': 'YAIWES',
  '[RUTA]': 'el repositorio y rutas indicados en la tarea',
  '[TAREA EXACTA]': 'la tarea del último mensaje del usuario',
  '[RESULTADO]': 'el resultado verificable que pide la tarea',
  '[EXISTENTE/AUTO-DETECT]': 'el existente (auto-detectar)',
  '[OBJETIVO_FINAL]': 'el objetivo de la tarea del usuario',
  '[CRITERIOS_DE_EXITO]': 'los criterios de la tarea y de la DEFINITION OF DONE',
  '[FORMATO_EXACTO]': 'el formato que pida la tarea (si no pide, el FORMATO DE SALIDA de la ficha)',
});
function leerCandidato(p) {
  try {
    const st = fs.statSync(p);
    if (!st.isDirectory()) return null; // la unica fuente autorizada es la ficha completa
    let core = fs.readFileSync(path.join(p, 'system_core.md'), 'utf8');
    for (const [k, v] of Object.entries(VARIABLES)) core = core.split(k).join(v);
    core = core.replace('[MODO]\n(ver bloque_1.md)\n', '').replace('\nEmpieza ahora.\n', '\n');
    core = core.replace(/\n=+ FIN INPUT BLOCK MAESTRO UNIFICADO =+\n/g, '\n');
    const bloque3 = fs.readFileSync(path.join(p, 'bloques', 'bloque_3.md'), 'utf8').trim();
    const bloque4 = fs.readFileSync(path.join(p, 'bloques', 'bloque_4.md'), 'utf8').trim();
    if (!core.trim() || !bloque3 || !bloque4) return null;
    return [core.trim(), bloque3, bloque4].join('\n\n');
  } catch { /* candidato ausente o incompleto: siguiente */ }
  return null;
}
export function textoSystemPrompt(env = process.env) {
  const lista = candidatos(env);
  const clave = lista.join('|') + '::' + (env.RIU_REPO_ROOT || '');
  if (cacheTxt === null || cacheClave !== clave) {
    let txt = '';
    for (const p of lista) { const t = leerCandidato(p); if (t !== null) { txt = t.trim(); break; } }
    cacheTxt = txt; cacheClave = clave;
  }
  return cacheTxt;
}

// ---- toggle ON/OFF ----
const flagPath = (env = process.env) => path.join(env.BRIDGE_STATE_DIR || './state', 'system-prompt-on.flag');
export function systemPromptOn(env = process.env) {
  try { return fs.readFileSync(flagPath(env), 'utf8').trim() !== '0'; } catch { return true; }  // sin archivo: ON por defecto
}
export function setSystemPromptOn(on, env = process.env) {
  const p = flagPath(env);
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, on ? '1' : '0');
  return systemPromptOn(env);
}

// El boton de YAIWES debe gobernar el estado REAL del Router MVP, no un toggle
// paralelo del bridge. Sin credencial/Router, no se afirma que el cambio se aplico.
// OpenClaw mantiene su prompt ON por origen y no requiere este boton.
export async function consultarPromptRouter(on = null, { env = process.env, fetchFn = fetch } = {}) {
  const clave = String(env.RIU_API_KEY || '').trim();
  if (!clave) throw new Error('ROUTER_SIN_CREDENCIAL');
  const puerto = Number(env.PORT);
  const base = String(env.RIU_ROUTER_URL || `http://127.0.0.1:${Number.isInteger(puerto) && puerto > 0 && puerto < 65536 ? puerto : 7861}`).replace(/\\/+$/, '');
  const url = new URL(base);
  if (!(url.protocol === 'https:' || (url.protocol === 'http:' && ['127.0.0.1', 'localhost'].includes(url.hostname))) || url.username || url.password)
    throw new Error('ROUTER_URL_INVALIDA');
  const ctrl = new AbortController(), timer = setTimeout(() => ctrl.abort(), 6000);
  try {
    const r = await fetchFn(base + '/plugins/puente_chat/call/agent_access_lock', {
      method:'POST', redirect:'error', signal:ctrl.signal,
      headers:{'content-type':'application/json','x-api-key':clave},
      body:JSON.stringify(on === null ? {} : {quien:'prompt',locked:!on}),
    });
    if (!r.ok) throw new Error('ROUTER_HTTP_' + r.status);
    const j = await r.json();
    const locked = j?.result?.prompt_locked;
    if (j?.status !== 'ok' || typeof locked !== 'boolean')
      throw new Error('ROUTER_PROMPT_ESTADO_INVALIDO');
    const confirmado = !locked;
    if (on !== null && confirmado !== on) throw new Error('ROUTER_PROMPT_NO_CONFIRMADO');
    setSystemPromptOn(confirmado,env); // solo se cambia el espejo tras CONFIRMACION del Router.
    return confirmado;
  } finally {clearTimeout(timer);}
}

// antepone el system prompt de la ficha (si ON y con contenido) ANTES del primer mensaje; si ya hay un mensaje de sistema
// (p. ej. el preambulo de modo) se fusiona con el, en vez de agregar uno nuevo. OFF o sin contenido: no toca nada
export function conSystemPrompt(mensajes, env = process.env, { forzarOn = false } = {}) {
  if ((!forzarOn && !systemPromptOn(env)) || !Array.isArray(mensajes)) return mensajes;
  const txt = textoSystemPrompt(env);
  if (!txt) return mensajes;
  const primero = mensajes[0];
  if (primero && primero.role === 'system' && typeof primero.content === 'string') {
    if (primero.content.includes(txt.slice(0, 60))) return mensajes;  // ya esta (no duplicar)
    return [{ role: 'system', content: `${txt}\n\n${primero.content}` }, ...mensajes.slice(1)];
  }
  return [{ role: 'system', content: txt }, ...mensajes];
}

// version para los modelos web-* / consenso, que reciben un prompt de texto plano (no un arreglo de mensajes)
export function conSystemPromptTexto(prompt, env = process.env, { forzarOn = false } = {}) {
  if (!forzarOn && !systemPromptOn(env)) return prompt;
  const txt = textoSystemPrompt(env);
  return txt ? `${txt}\n\n${prompt}` : prompt;
}
