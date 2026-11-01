// defaults.js — el bridge debe funcionar SIN que el Director configure variables nuevas en Hugging Face. Solo se completa lo que NO esta definido
// (una variable definida pero VACIA cuenta como definida: es la forma de desactivar un default a proposito). Nunca se inventan claves ni aprobadores.
//  - SWECODE_URL_S1..S3: las URLs publicas de los servidores de modelos locales (sin secreto).
//  - RIU_DEEPSEEK_HARNESS_URL: el plugin del Harness montado en el MISMO Space (http://127.0.0.1:$PORT/plugins/deepseek_harness; PORT=7861 en el Space). Solo con RIU_API_KEY
//    (el Harness solo se autentica con ella) y SIEMPRE local: si algo no cuadra se usa 7861.
export const SWECODE_URLS_PUBLICAS = Object.freeze({
  S1: 'https://comand-center-1-swe-code-s1.hf.space/v1',
  S2: 'https://comand-center-1-swe-code-s2.hf.space/v1',
  S3: 'https://comand-center-1-swe-code-s3.hf.space/v1',
});
export const PUERTO_ROUTER = 7861, RUTA_HARNESS = '/plugins/deepseek_harness';

// http en loopback (127.0.0.1 / localhost), sin credenciales en la URL
export function esUrlLocal(u) {
  try { const p = new URL(String(u)); return p.protocol === 'http:' && ['127.0.0.1', 'localhost'].includes(p.hostname) && !p.username && !p.password; } catch { return false; }
}
export function urlHarnessLocal(env = process.env) {
  const crudo = String(env.PORT == null ? '' : env.PORT).trim();
  const n = /^\d{1,5}$/.test(crudo) ? Number(crudo) : 0;
  const url = `http://127.0.0.1:${n >= 1 && n <= 65535 ? n : PUERTO_ROUTER}${RUTA_HARNESS}`;
  return esUrlLocal(url) ? url : `http://127.0.0.1:${PUERTO_ROUTER}${RUTA_HARNESS}`;
}
export function aplicarDefectos(env = process.env) {
  for (const [s, url] of Object.entries(SWECODE_URLS_PUBLICAS)) if (env[`SWECODE_URL_${s}`] === undefined) env[`SWECODE_URL_${s}`] = url;
  if (env.RIU_DEEPSEEK_HARNESS_URL === undefined && String(env.RIU_API_KEY || '').trim()) env.RIU_DEEPSEEK_HARNESS_URL = urlHarnessLocal(env);
  return env;
}
