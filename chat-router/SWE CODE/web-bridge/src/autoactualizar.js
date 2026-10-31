// autoactualizar.js — el bridge se actualiza solo: el Space baja `main` al clon (autopull del Router) pero solo recarga el Router MVP.
// Si cambia algo de SWE CODE / SWE CODE free (o el formato de salida que lee el bridge), el bridge se relanza solo: sin reiniciar el Space.
import { execFile, spawn } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export const RUTAS = ['chat-router/SWE CODE/', 'chat-router/SWE CODE free/', 'chat-router/chat/backend/mvp/prompts/'];
const AQUI = path.dirname(fileURLToPath(import.meta.url));
const git = (repo, args) => new Promise((ok, no) => execFile('git', ['-C', repo, ...args], { timeout: 20000 }, (e, out) => (e ? no(e) : ok(String(out).trim()))));

// node --check de cada .js tocado (dentro de RUTAS y aun presente): se copia a .mjs para comprobar solo la sintaxis, sea CJS o ESM. Devuelve los nombres que no compilan.
async function rotos(repo, archivos) {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'bridge-check-')), malos = [];
  try {
    for (const [i, f] of archivos.filter(f => f.endsWith('.js') && RUTAS.some(r => f.startsWith(r))).entries()) {
      const origen = path.join(repo, f);
      if (!fs.existsSync(origen)) continue;  // borrado en este cambio
      const copia = path.join(tmp, `${i}.mjs`);
      fs.copyFileSync(origen, copia);
      if (!(await new Promise(ok => execFile(process.execPath, ['--check', copia], { timeout: 15000 }, e => ok(!e))))) malos.push(path.basename(f));
    }
  } finally { fs.rmSync(tmp, { recursive: true, force: true }); }
  return malos;
}
// npm install de las dependencias del bridge (solo si cambio package.json)
const instalarNpm = () => new Promise(ok => execFile('npm', ['install', '--omit=dev', '--no-audit', '--no-fund'], { cwd: path.resolve(AQUI, '..'), timeout: 300000 }, e => ok(!e)));

// una vuelta: compara la cabeza del repo con la que ya vio; si cambio algo del bridge, VERIFICA el codigo nuevo (node --check de los .js tocados y, si cambio
// package.json, npm install) y solo entonces relanza. Si la verificacion falla: git reset --hard a la cabeza previa y NO se relanza (queda el bridge sano que ya corre). Nunca lanza.
export async function revisar({ repo, estado, relanzar, instalar = instalarNpm }) {
  try {
    const ahora = await git(repo, ['rev-parse', 'HEAD']);
    if (!estado.cabeza) { estado.cabeza = ahora; return false; }
    if (ahora === estado.cabeza) return false;
    const archivos = (await git(repo, ['diff', '--name-only', estado.cabeza, ahora])).split('\n').filter(Boolean);
    const antes = estado.cabeza; estado.cabeza = ahora;
    if (!archivos.some(f => RUTAS.some(r => f.startsWith(r)))) return false;
    const deps = archivos.some(f => f.endsWith('web-bridge/package.json'));
    const malos = await rotos(repo, archivos);
    const fallo = malos.length ? `no compila ${malos.slice(0, 3).join(', ')}` : deps && !(await instalar()) ? 'npm install fallo' : null;
    if (fallo) {
      if (estado.rota !== ahora) console.warn(`[bridge] codigo nuevo ${ahora.slice(0, 7)} rechazado (${fallo}): se vuelve a ${antes.slice(0, 7)}, sin relanzar`);
      estado.rota = ahora;
      await git(repo, ['reset', '--hard', antes]).catch(() => {});
      estado.cabeza = antes;
      return false;
    }
    console.warn(`[bridge] codigo nuevo (${antes.slice(0, 7)} -> ${ahora.slice(0, 7)}): se relanza solo`);
    await relanzar({ deps });
    return true;
  } catch { return false; }
}

// relanzar: arrancar el mismo comando 2 s despues, cuando este proceso ya solto el puerto (las dependencias ya se instalaron en revisar)
export function relanzarMismoProceso() {
  const cmd = `sleep 2 && exec "${process.argv[0]}" ${process.argv.slice(1).map(a => `"${a}"`).join(' ')}`;
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
