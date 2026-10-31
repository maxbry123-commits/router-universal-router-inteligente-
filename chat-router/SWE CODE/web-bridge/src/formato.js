// formato.js — el formato de salida del chat Yaiwes (una sola copia: chat/backend/mvp/prompts/FORMATO_SALIDA.md) para los modelos que responden por el bridge.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const AQUI = path.dirname(fileURLToPath(import.meta.url));
let cache = null, rutaCache = null;

export function textoFormato() {
  const ruta = process.env.RIU_FORMATO_PATH || path.resolve(AQUI, '../../../chat/backend/mvp/prompts/FORMATO_SALIDA.md');
  if (cache === null || rutaCache !== ruta) {
    try { cache = fs.readFileSync(ruta, 'utf8').trim(); } catch { cache = ''; console.warn('[bridge] sin FORMATO_SALIDA.md: el formato de salida queda desactivado (ruta o RIU_FORMATO_PATH)'); }
    rutaCache = ruta;
  }
  return cache;
}

// antepone el formato salvo que ya venga (el Router MVP lo pone cuando el mensaje pasa por el)
export function conFormato(mensajes) {
  const f = textoFormato();
  if (!f || !Array.isArray(mensajes)) return mensajes;
  if (mensajes.some(m => m && m.role === 'system' && typeof m.content === 'string' && m.content.includes(f.slice(0, 60)))) return mensajes;
  return [{ role: 'system', content: f }, ...mensajes];
}
