// autoactualizar.js — el bridge se actualiza solo: el Space baja `main` al clon (autopull del Router) pero solo recarga el Router MVP.
// Si cambia algo de SWE CODE / SWE CODE free (o el formato de salida que lee el bridge), el bridge se relanza solo: sin reiniciar el Space.
import { execFile, spawn } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export const RUTAS = ['chat-router/SWE CODE/', 'chat-router/SWE CODE free/', 'chat-router/chat/backend/mvp/prompts/'];
const AQUI = path.dirname(fileURLToPath(import.meta.url));
const git = (repo, args) => new Promise((ok, no) => execFile('git', ['-C', repo, ...args], { timeout: 20000 }, (e, out) => (e ? no(e) : ok(String(out).trim()))));

// una vuelta: compara la cabeza del repo con la que ya vio; relanza solo si cambio algo del bridge. Nunca lanza.
export async function revisar({ repo, estado, relanzar }) {
  try {
    const ahora = await git(repo, ['rev-parse', 'HEAD']);
    if (!estado.cabeza) { estado.cabeza = ahora; return false; }
    if (ahora === estado.cabeza) return false;
    const archivos = (await git(repo, ['diff', '--name-only', estado.cabeza, ahora])).split('\n').filter(Boolean);
    const antes = estado.cabeza; estado.cabeza = ahora;
    if (!archivos.some(f => RUTAS.some(r => f.startsWith(r)))) return false;
    console.warn(`[bridge] codigo nuevo (${antes.slice(0, 7)} -> ${ahora.slice(0, 7)}): se relanza solo`);
    await relanzar({ deps: archivos.some(f => f.endsWith('web-bridge/package.json')) });
    return true;
  } catch { return false; }
}

// relanzar: (npm install si cambiaron las dependencias) y arrancar el mismo comando 2 s despues, cuando este proceso ya solto el puerto
export function relanzarMismoProceso({ deps } = {}) {
  const cmd = `${deps ? 'npm install --omit=dev --no-audit --no-fund && ' : ''}sleep 2 && exec "${process.argv[0]}" ${process.argv.slice(1).map(a => `"${a}"`).join(' ')}`;
  spawn('sh', ['-c', cmd], { cwd: process.cwd(), env: process.env, detached: true, stdio: 'inherit' }).unref();
  setTimeout(() => process.exit(0), 200);
}

export function vigilarActualizacion({ intervaloMs = 60000, repo = process.env.BRIDGE_REPO || path.resolve(AQUI, '../../../..') } = {}) {
  if (process.env.BRIDGE_AUTOACTUALIZAR === '0') return null;
  const estado = {};
  revisar({ repo, estado, relanzar: relanzarMismoProceso });  // fija la cabeza con la que arranco
  const t = setInterval(() => revisar({ repo, estado, relanzar: relanzarMismoProceso }), intervaloMs); t.unref();
  return t;
}
