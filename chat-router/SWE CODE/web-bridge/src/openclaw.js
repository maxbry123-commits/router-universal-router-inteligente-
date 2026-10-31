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

// ---- ejecutor de las tools: quien ejecuta los tool_calls de una peticion (campo `ejecutor_tools` del POST /v1/chat/completions) ----
// 'swe' (defecto) = como hoy: el bridge devuelve los tool_calls y el Harness/Router los ejecuta. 'openclaw' = passthrough: el bridge los
// devuelve tal cual al cliente OpenClaw (finish_reason 'tool_calls') y marca la seccion WAIT_TOOLS hasta que OpenClaw responda con los resultados.
export const EJECUTORES_TOOLS = ['swe', 'openclaw'];
export const normalizarEjecutor = (v) => { const x = typeof v === 'string' ? v.trim().toLowerCase() : ''; return EJECUTORES_TOOLS.includes(x) ? x : 'swe'; };

// ---- ESPEJO de emergencia (solo lectura, SIN secretos) ----
// El chat Yaiwes es la fuente principal; la UI de chat de OpenClaw es el mirror de emergencia. Si el chat de Vercel/Space no funciona, OpenClaw usa el
// mismo codigo del Router MVP (chat/backend/mvp): motor (/chat/send), constitucion, tools MCP, plugins, almacen y memoria. Aqui solo van NOMBRES
// de cabeceras y variables, nunca valores. Las rutas y tools se comprueban contra el codigo del Router en test/openclaw.test.mjs.
const ROUTER_LOCAL = 'http://127.0.0.1:7861';
const ACCESO_ROUTER = ['RIU_API_KEY', 'RIU_PUBLIC_CHAT_KEY', 'RIU_MCP_KEY', 'RIU_ROUTER_API_KEY'];
const TOOLS_MCP = ['chat', 'almacen', 'memoria', 'salud', 'listar_fichas', 'resultado', 'github_leer', 'github_escribir', 'github_api', 'pendientes', 'sala', 'agente', 'llm', 'yaiwes_md', 'loop', 'archivos'];
const PLUGINS_ROUTER = ['puente_chat', 'motor_archivos', 'nct_loop', 'cola50', 'watchdog48', 'fichas_qwen', 'deepseek_harness'];

export function espejo({ env = process.env } = {}) {
  const url = String(env.RIU_ROUTER_URL || '').trim().replace(/\/+$/, '');
  return {
    router_url: url || ROUTER_LOCAL, router_url_origen: url ? 'env' : 'defecto', router_url_env: 'RIU_ROUTER_URL',
    auth: { cabecera: 'X-API-Key', alternativa: 'Authorization: Bearer', query: 'key', variables: ACCESO_ROUTER, configuradas: ACCESO_ROUTER.filter(v => env[v]), nota: 'OpenClaw manda el valor de RIU_API_KEY (o la clave de acceso del chat) en la cabecera; este endpoint nunca lo devuelve' },
    endpoints: {
      mcp: { metodo: 'POST', ruta: '/mcp', protocolo: 'MCP JSON-RPC 2.0 (initialize, tools/list, tools/call)' },
      plugins: { metodo: 'POST', ruta: '/plugins/{plugin}/call/{accion}' },
      almacen: { metodo: 'POST', ruta: '/almacen', acciones: ['guardar', 'leer', 'computar', 'status'] },
      memoria: { guardar: { metodo: 'POST', ruta: '/memoria/save' }, leer: { metodo: 'GET', ruta: '/memoria/load' }, buscar: { metodo: 'GET', ruta: '/memoria/search' } },
      constitucion: { metodo: 'POST', ruta: '/chat/send', campo: 'constitucion', forma: '{texto, anclados}', archivos: 'POST /plugins/motor_archivos/call/<accion> (destino constitucion)' },
      tools: { metodo: 'POST', ruta: '/mcp', metodo_rpc: 'tools/list | tools/call', nota: 'mismas tools que ve el chat; el Router decide cuales son visibles' },
      chat: { metodo: 'POST', ruta: '/chat/send', nota: 'motor del chat: Harness + tools + constitucion + yaiwes.md' },
      health: { metodo: 'GET', ruta: '/health' },
      ui: { metodo: 'GET', ruta: '/chat/ui/{archivo}', nota: 'el Router sirve el propio chat Yaiwes (GET /) aunque Vercel no despliegue' },
    },
    tools: { mcp: TOOLS_MCP },
    plugins: PLUGINS_ROUTER,
    ejecutor_tools: { campo: 'ejecutor_tools', defecto: 'swe', valores: EJECUTORES_TOOLS,
      swe: { descripcion: 'el bridge devuelve los tool_calls y el Harness/Router los ejecuta (comportamiento actual)' },
      openclaw: { descripcion: 'passthrough: tool_calls tal cual al cliente OpenClaw; la seccion queda en WAIT_TOOLS', estado: 'WAIT_TOOLS' } },
  };
}
