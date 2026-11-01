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
// la ficha puede ser un archivo suelto o (como en este repo) una carpeta con system_core.md adentro
function leerCandidato(p) {
  try {
    const st = fs.statSync(p);
    if (st.isFile()) return fs.readFileSync(p, 'utf8');
    if (st.isDirectory()) {
      const core = path.join(p, 'system_core.md');
      if (fs.existsSync(core)) return fs.readFileSync(core, 'utf8');
    }
  } catch { /* candidato siguiente */ }
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

// antepone el system prompt de la ficha (si ON y con contenido) ANTES del primer mensaje; si ya hay un mensaje de sistema
// (p. ej. el preambulo de modo) se fusiona con el, en vez de agregar uno nuevo. OFF o sin contenido: no toca nada
export function conSystemPrompt(mensajes, env = process.env) {
  if (!systemPromptOn(env) || !Array.isArray(mensajes)) return mensajes;
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
export function conSystemPromptTexto(prompt, env = process.env) {
  if (!systemPromptOn(env)) return prompt;
  const txt = textoSystemPrompt(env);
  return txt ? `${txt}\n\n${prompt}` : prompt;
}
