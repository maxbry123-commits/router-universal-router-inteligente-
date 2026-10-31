// memoria.js — OpenClaw usa la MISMA memoria del chat Yaiwes (bucket HF, scope chat-ui:hist:<sesion>) por memoria_hf.py (reutiliza mvp.memoria)
import { execFile } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { slug } from './proyectos.js';

const AQUI = path.dirname(fileURLToPath(import.meta.url));
const SCRIPT = path.resolve(AQUI, '../memoria_hf.py');

export const scopeDe = (sesion) => (sesion ? `chat-ui:hist:openclaw-${slug(sesion)}` : null);

function correr(args, stdin) {
  return new Promise((resolve) => {
    const cmd = process.env.RIU_MEMORIA_CMD;
    const [bin, argv] = cmd ? [cmd, args] : [process.env.RIU_PYTHON || 'python3', [SCRIPT, ...args]];
    const p = execFile(bin, argv, { timeout: 20000, env: process.env }, (err, out) => resolve(err ? null : String(out)));
    p.stdin.on('error', () => {}); p.stdin.end(stdin || '');
  });
}

// mejor esfuerzo: nunca rompe ni retrasa la respuesta (se llama sin await en el servidor)
export async function guardarTurno(sesion, pregunta, respuesta, modelo) {
  const scope = scopeDe(sesion);
  if (!scope || !process.env.HF_TOKEN) return false;
  const ts = Date.now();
  const okR = (o) => /"ok":\s*true/.test(String(o || ''));
  const a = okR(await correr(['save', scope, `m-${ts}-user`], JSON.stringify({ rol: 'user', texto: String(pregunta || '').slice(0, 20000), ts })));
  const b = okR(await correr(['save', scope, `m-${ts}-bot`], JSON.stringify({ rol: 'bot', texto: String(respuesta || '').slice(0, 50000), ts: ts + 1, modelo })));
  return a && b;
}

// historial de la sesion desde la misma memoria (accion search de mvp.memoria)
export async function leerTurnos(sesion, k = 200) {
  const scope = scopeDe(sesion);
  if (!scope || !process.env.HF_TOKEN) return [];
  const out = await correr(['search', scope, '', String(k)], '');
  try { return JSON.parse(out).results.sqlite || []; } catch { return []; }
}
