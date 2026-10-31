// clavesbanco.js — puente al banco de claves: al arrancar toma las claves de Groq/NVIDIA del banco del Router MVP (solo lectura) y del banco propio;
// las que pegan en Configuracion se guardan en el banco propio (cifrado, respaldado en /data). Sin variables de Hugging Face y sin tocar el Router.
import { execFile } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { setClaves } from './respaldo.js';
import fs from 'node:fs';
import { traerDeGithub, diagTraer } from './bancogithub.js';

const SCRIPT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../claves_banco.py');
const entorno = () => Object.fromEntries(['PATH', 'HOME', 'PYTHONPATH', 'LANG', 'BRIDGE_STATE_DIR', 'RIU_API_KEY', 'RIU_PUBLIC_CHAT_KEY', 'RIU_MCP_KEY', 'RIU_ROUTER_API_KEY', 'RIU_BANCO_ROUTER']
  .filter(k => process.env[k] !== undefined).map(k => [k, process.env[k]]));

// estado para diagnosticar (nunca valores): ultima llamada al helper python y si el banco local existe
const diagPy = { accion: null, ok: null, err: null, detalle: null };
export function diagnosticoBanco(env = process.env) {
  const ruta = require_ruta(env); let local = null;
  try { local = fs.statSync(ruta).size; } catch { /* no existe */ }
  return { local_bytes: local, github: { ...diagTraer }, python: { ...diagPy }, accesos: ['RIU_API_KEY', 'RIU_PUBLIC_CHAT_KEY', 'RIU_MCP_KEY', 'RIU_ROUTER_API_KEY'].filter((k) => env[k]).length };
}
const require_ruta = (env) => path.join(env.BRIDGE_STATE_DIR || './state', 'banco-swe.bin');

function correr(args, stdin) {
  return new Promise((resolve) => {
    const cmd = process.env.RIU_CLAVES_CMD;
    const [bin, argv] = cmd ? [cmd, args] : [process.env.RIU_PYTHON || 'python3', [SCRIPT, ...args]];
    const p = execFile(bin, argv, { timeout: 15000, env: cmd ? process.env : entorno() }, (err, out, errout) => {
      if (args[0] !== 'diagnostico') diagPy.accion = args[0]; if (args[0] !== 'diagnostico') diagPy.ok = !err; if (args[0] !== 'diagnostico') diagPy.err = err ? String(errout || err.message || err.code || '').trim().split('\n').slice(-1)[0].slice(0, 160) : null;
      resolve(err ? null : String(out));
    });
    p.stdin.on('error', () => {}); p.stdin.end(stdin || '');
  });
}

// devuelve cuantas claves cargo (0 si no hay banco, clave de acceso o python)
export async function cargarDelBanco() {
  const out = await correr(['leer']);
  try {
    const c = JSON.parse(out);
    const nuevas = {};  // un banco vacio no borra lo que ya estaba en memoria
    if ((c.groq || []).length) nuevas.groq = c.groq;
    if ((c.nvidia || []).length) nuevas.nvidia = c.nvidia;
    if (Object.keys(nuevas).length) setClaves(nuevas);
    return (c.groq || []).length + (c.nvidia || []).length;
  } catch { return 0; }
}

export async function guardarEnBanco(claves) {
  const out = await correr(['guardar'], JSON.stringify(claves || {}));
  return /"ok":\s*true/.test(String(out || ''));
}

// vacia el banco PROPIO (el del Router MVP nunca se toca)
export async function borrarDelBanco() {
  const out = await correr(['borrar']);
  return /"ok":\s*true/.test(String(out || ''));
}

// el banco se vuelve a leer cada 60 s: una clave que entre al banco del Router MVP llega al bridge sin reiniciar nada.
// Si el banco local aun no existe, lo trae de GitHub (rama banco-claves). El traer FORZADO (pisa el local) solo si el local no existe o NO abre
// (diagnostico propio.existe && abre_con === null); un local que abre y esta vacio (DELETE a proposito) se respeta: el borrado es persistente.
export function vigilarBanco(intervaloMs = 60000, { traer = traerDeGithub, cargar = cargarDelBanco, diagnosticar = diagnosticarPython, existe = () => fs.existsSync(require_ruta(process.env)) } = {}) {
  const vuelta = async () => {
    await traer().catch(() => false);
    if ((await cargar()) === 0) {
      const d = await diagnosticar().catch(() => null), propio = d && d.propio;
      const inservible = !existe() || !!(propio && propio.existe && propio.abre_con === null);
      if (inservible && await traer({ forzar: true }).catch(() => false)) await cargar();
    }
    try { diagPy.detalle = await diagnosticar(); } catch { /* solo diagnostico */ }
  };
  const t = setInterval(() => { vuelta().catch(() => {}); }, intervaloMs); t.unref();
  return t;
}
async function diagnosticarPython() { return JSON.parse(await correr(['diagnostico'])); }
