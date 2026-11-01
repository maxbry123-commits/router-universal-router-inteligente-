// acceso.js — credenciales del bridge. BRIDGE_TOKEN es OPCIONAL: basta cualquiera de las 4 claves de acceso (RIU_API_KEY, RIU_PUBLIC_CHAT_KEY, RIU_MCP_KEY, RIU_ROUTER_API_KEY),
// en `x-api-key` o en `Authorization: Bearer <clave>` (asi el provider de OpenClaw usa api_key = clave de acceso sin BRIDGE_TOKEN). Comparacion en tiempo constante (sha256 + timingSafeEqual).
import { iguales } from './iguales.js';

export const ACCESO_VARS = ['RIU_API_KEY', 'RIU_PUBLIC_CHAT_KEY', 'RIU_MCP_KEY', 'RIU_ROUTER_API_KEY'];
export const clavesAcceso = (env = process.env) => ACCESO_VARS.map((v) => env[v]).filter(Boolean);
const cab = (req, n) => String((req && req.headers && req.headers[n]) || '');
export const bearerDe = (req) => { const m = /^Bearer\s+(.+)$/i.exec(cab(req, 'authorization').trim()); return m ? m[1].trim() : ''; };

// ¿`valor` es una de las claves de acceso configuradas? Se comparan TODAS (sin retorno temprano)
export const esClaveAcceso = (valor, env = process.env) => !!valor && clavesAcceso(env).map((v) => iguales(valor, v)).some(Boolean);

// la clave de acceso que trae la peticion ('' si ninguna): x-api-key o Authorization: Bearer. `solo` limita las cabeceras admitidas
export function claveAccesoDe(req, env = process.env, { solo } = {}) {
  const candidatas = [['x-api-key', cab(req, 'x-api-key')], ['bearer', bearerDe(req)]].filter(([n]) => !solo || solo.includes(n));
  for (const [, v] of candidatas) if (esClaveAcceso(v, env)) return v;
  return '';
}
