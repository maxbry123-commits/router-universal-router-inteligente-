// clavesbanco.js — puente al banco de claves: al arrancar toma las claves de Groq/NVIDIA del banco del Router MVP (solo lectura) y del banco propio;
// las que pegan en Configuracion se guardan en el banco propio (cifrado, respaldado en /data). Sin variables de Hugging Face y sin tocar el Router.
import { execFile } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { setClaves } from './respaldo.js';
import { traerDeGithub } from './bancogithub.js';

const SCRIPT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../claves_banco.py');
const entorno = () => Object.fromEntries(['PATH', 'HOME', 'PYTHONPATH', 'LANG', 'BRIDGE_STATE_DIR', 'RIU_API_KEY', 'RIU_PUBLIC_CHAT_KEY', 'RIU_MCP_KEY', 'RIU_ROUTER_API_KEY', 'RIU_BANCO_ROUTER']
  .filter(k => process.env[k] !== undefined).map(k => [k, process.env[k]]));

function correr(args, stdin) {
  return new Promise((resolve) => {
    const cmd = process.env.RIU_CLAVES_CMD;
    const [bin, argv] = cmd ? [cmd, args] : [process.env.RIU_PYTHON || 'python3', [SCRIPT, ...args]];
    const p = execFile(bin, argv, { timeout: 15000, env: cmd ? process.env : entorno() }, (err, out) => resolve(err ? null : String(out)));
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

// el banco se vuelve a leer cada 60 s: una clave que entre al banco del Router MVP llega al bridge sin reiniciar nada
// y si el banco local aun no existe, lo trae de GitHub (rama banco-claves; sin red cuando ya existe) antes de leerlo
export function vigilarBanco(intervaloMs = 60000, { traer = traerDeGithub, cargar = cargarDelBanco } = {}) {
  const vuelta = async () => {
    await traer().catch(() => false);
    if ((await cargar()) === 0 && await traer({ forzar: true }).catch(() => false)) await cargar();  // banco local vacio o ilegible: el de GitHub manda
  };
  const t = setInterval(() => { vuelta().catch(() => {}); }, intervaloMs); t.unref();
  return t;
}
