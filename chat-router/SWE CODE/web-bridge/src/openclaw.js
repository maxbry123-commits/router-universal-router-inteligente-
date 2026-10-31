// openclaw.js — auto-reparacion del cableado de OpenClaw (sin tocar HF).
// openclaw.sh hace `rm -rf $OPENCLAW_HOME` en cada arranque y no recrea el workspace del agente:
// el gateway responde "This agent's workspace is missing on the gateway host". Aqui se recrea.
import nodeFs from 'node:fs';
import path from 'node:path';

export function asegurarWorkspace({ uid = process.getuid(), base = '/tmp', fs = nodeFs } = {}) {
  const ruta = process.env.OPENCLAW_WORKSPACE_DIR || path.join(base, `openclaw-home-${uid}`, '.openclaw', 'workspace');
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
