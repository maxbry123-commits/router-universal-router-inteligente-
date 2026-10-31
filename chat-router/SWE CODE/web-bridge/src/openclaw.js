// openclaw.js — auto-reparacion del cableado de OpenClaw (sin tocar HF).
// openclaw.sh hace `rm -rf $OPENCLAW_HOME` en cada arranque y no recrea el workspace del agente:
// el gateway responde "This agent's workspace is missing on the gateway host". Aqui se recrea.
import nodeFs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';

export const rutaWorkspace = ({ uid = process.getuid(), base = '/tmp' } = {}) => process.env.OPENCLAW_WORKSPACE_DIR || path.join(base, `openclaw-home-${uid}`, '.openclaw', 'workspace');

export function asegurarWorkspace({ uid = process.getuid(), base = '/tmp', fs = nodeFs } = {}) {
  const ruta = rutaWorkspace({ uid, base });
  if (fs.existsSync(ruta)) return { ruta, creada: false };
  fs.mkdirSync(ruta, { recursive: true, mode: 0o700 });
  return { ruta, creada: true };
}

// comprueba al arrancar y cada intervaloMs (60 s); solo avisa cuando la crea
export function vigilarWorkspace(intervaloMs = 60000) {
  const paso = () => {
    try { const r = asegurarWorkspace(); if (r.creada) console.warn(`openclaw: workspace recreado en ${r.ruta}`); }
    catch (e) { console.warn(`openclaw: no se pudo asegurar el workspace: ${e.message}`); }
  };
  paso();
  return setInterval(paso, intervaloMs).unref();
}

// ---- configuracion vigente de OpenClaw (solo lectura, SIN secretos) ----
// La fuente es el repo (SWE CODE free/provider-openclaw.json + swen.json): el bridge la sirve en GET /v1/openclaw,
// que llega por Vercel (/web/v1/openclaw) y por el Space (proxy) sin tocar Hugging Face a mano. El vigilante de 60 s la mantiene al dia.
const DIR_POR_DEFECTO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../../SWE CODE free');

export function leerConfig({ dir = process.env.RIU_OPENCLAW_DIR || DIR_POR_DEFECTO, fs = nodeFs } = {}) {
  const leer = (n) => { try { return JSON.parse(fs.readFileSync(path.join(dir, n), 'utf8')); } catch { return null; } };
  const p = leer('provider-openclaw.json'), s = leer('swen.json');
  if (!p || typeof p !== 'object') return null;
  const { api_key: _fuera, ...provider } = p;  // el valor de api_key (aunque sea un marcador) no sale nunca
  const cfg = { provider, modos: Array.isArray(s?.modos) ? s.modos : [], aliases: s?.seleccion_modelo?.aliases || {} };
  return { ...cfg, version: crypto.createHash('sha256').update(JSON.stringify(cfg)).digest('hex').slice(0, 12) };
}

let vigente = null;
export function refrescarConfig(opts) { const c = leerConfig(opts); if (c) vigente = { ...c, leida: new Date().toISOString() }; return vigente; }
export const configVigente = (opts) => vigente || refrescarConfig(opts);

// lee al arrancar y cada intervaloMs (60 s)
export function vigilarConfig(intervaloMs = 60000, opts) {
  refrescarConfig(opts);
  return setInterval(() => refrescarConfig(opts), intervaloMs).unref();
}
