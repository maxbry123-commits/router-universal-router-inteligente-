import { MODELOS_API } from './respaldo.js';
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


// Sincronización del catálogo MODELO (NO de agentes): OpenClaw inicia desde
// /swecode_provider.json del Space, que puede estar desactualizado y tener
// apiKey:"local" (el bridge rechaza esa credencial). El Router SWE CODE ya lee el banco,
// por tanto OpenClaw necesita la CLAVE DE ACCESO a 127.0.0.1:7870, no las claves
// API privadas de NVIDIA/Groq. Solo se modifica la sección "swecode" y su
// allowlist de modelos de manera aditiva; se conserva el modelo predeterminado,
// pairing, workspace, gateway y demás providers.
const ORIGEN_OC = 'http://127.0.0.1:7861/plugins/deepseek_harness/modelos/v1';
export function sincronizarModelosOpenClaw(modelos, { key = process.env.RIU_API_KEY, dir = null, fs = nodeFs } = {}) {
  if (!key || !Array.isArray(modelos) || !modelos.length) return false;
  const home = process.env.OPENCLAW_HOME || path.join('/tmp', `openclaw-home-${process.getuid()}`);
  const target = path.join(dir || path.join(home, '.openclaw'), 'openclaw.json');
  let before, cfg;
  try {
    const stat = fs.lstatSync(target);
    if (!stat.isFile() || stat.isSymbolicLink()) return false; // no crear state ni seguir symlinks
    before = fs.readFileSync(target, 'utf8');
    cfg = JSON.parse(before); // configuración JSON5 desconocida: fallar cerrado sin sobreescribirla
  } catch { return false; }
  if (!cfg || typeof cfg !== 'object' || !cfg.models || !cfg.models.providers || !cfg.agents?.defaults?.models) return false;
  const safeIds = [...new Set(modelos)].filter(id => typeof id === 'string' &&
    /^(?:web-|swecode-|groq\/|nvidia\/|deepseek\/|minimax\/|openai\/|lfm2\.5|qwen2\.5|qwen3)/.test(id) &&
    id.length <= 100);
  if (!safeIds.length) return false;
  const nombres = new Map(MODELOS_API.map(m => [m.id, m.nombre]));
  for (const [id, nombre] of Object.entries({'lfm2.5-350m':'Liquid LFM2.5 350M','qwen2.5-coder-1.5b':'Qwen2.5 Coder 1.5B','qwen3.5-0.8b':'Qwen3.5 0.8B','qwen3-0.6b':'Qwen3 0.6B'})) nombres.set(id, nombre);
  cfg.agents.defaults.timeoutSeconds = Math.max(Number(cfg.agents.defaults.timeoutSeconds) || 0, 600);
  cfg.gateway ||= {};
  cfg.gateway.controlUi ||= {};
  cfg.gateway.controlUi.basePath = '/openclaw';
  const previo = cfg.models.providers.swecode || {};
  const previos = new Map((Array.isArray(previo.models) ? previo.models : []).filter(x => x && typeof x.id === 'string').map(x => [x.id, x]));
  cfg.models.providers.swecode = {
    ...previo, baseUrl: ORIGEN_OC, apiKey: key, api: 'openai-completions', timeoutSeconds: 480,
    models: safeIds.map(id => ({ ...{ name: id, reasoning: false, input: ['text'],
      cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
      contextWindow: 32768, maxTokens: 4096 }, ...(previos.get(id) || {}), id, name: nombres.get(id) || previos.get(id)?.name || id,
      ...(nombres.has(id) && !id.includes('/') ? { contextWindow: 16384 } : {}) })),
  };
  for (const id of safeIds) {
    const entry = cfg.agents.defaults.models['swecode/' + id] ||= {};
    if (nombres.has(id)) entry.alias = nombres.get(id);
  }
  const after = JSON.stringify(cfg, null, 2);
  if (after === JSON.stringify(JSON.parse(before), null, 2)) return false;
  const tmp = target + '.riu-' + process.pid + '.tmp';
  try {
    fs.writeFileSync(tmp, after, { encoding: 'utf8', mode: 0o600, flag: 'wx' });
    fs.renameSync(tmp, target);  // OpenClaw recarga models.providers en caliente
    return true;
  } catch { try { fs.unlinkSync(tmp); } catch {} return false; }
}
export function vigilarModelosOpenClaw(modelos, intervaloMs = 10000) {
  const paso = () => {
    try { if (sincronizarModelosOpenClaw(modelos())) console.warn('openclaw: catálogo de modelos SWE sincronizado desde GitHub'); }
    catch { /* OpenClaw opcional y sin alterar su funcionamiento */ }
  };
  paso();
  const timer = setInterval(paso, intervaloMs); timer.unref();
  return timer;
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

// ---- TOOLS de OpenClaw (UI3): las funciones del chat Yaiwes que el Router MVP YA expone por MCP/HTTP ----
// Una sola implementacion: el bridge NO ejecuta nada de esto, solo reenvia al Router (swe_rutas.js: GET /v1/swe/tools y POST /v1/swe/tools/:id) con la clave de acceso del ENTORNO del bridge;
// el navegador nunca la ve. El Router decide los permisos (Agentes/IA/Tools ON/OFF) igual que para el chat Yaiwes. Los ids, acciones y rutas se comprueban contra el codigo del Router en test/openclaw.test.mjs.
// `efectos`: lectura | efectos | por_accion (con `lectura` = acciones sin efectos). Lo que tiene efectos exige un operador identificado en el bridge.
const mcp = (id, tool, grupo, titulo, efectos, extra = {}) => ({ id, grupo, titulo, via: 'mcp', destino: { tool }, efectos, ...extra });
const plugin = (id, plugin_, grupo, titulo, acciones, lectura, extra = {}) => ({ id, grupo, titulo, via: 'plugin', destino: { plugin: plugin_, ruta: '/plugins/{plugin}/call/{accion}', metodo: 'POST' }, acciones, efectos: 'por_accion', lectura, ...extra });
const replica = (id, grupo, titulo, acciones, extra = {}) => ({ id, grupo, titulo, via: 'replica', destino: { local: true }, acciones, efectos: 'lectura', lectura: acciones, ...extra });
const TOOLS_OPENCLAW = [
  mcp('chat_router', 'chat', 'chat', 'Chat del Router (modelo + herramientas)', 'efectos'),
  mcp('almacen', 'almacen', 'almacen', 'Almacen autorizado (guardar/leer)', 'por_accion', { acciones: ['guardar', 'leer', 'computar', 'status'], lectura: ['leer', 'status'] }),
  mcp('memoria', 'memoria', 'almacen', 'Memoria del chat (save/load/search)', 'por_accion', { acciones: ['save', 'load', 'search'], lectura: ['load', 'search'] }),
  mcp('salud', 'salud', 'chat', 'Estado del Router, version y permisos (IA/Agentes)', 'lectura'),
  mcp('listar_fichas', 'listar_fichas', 'chat', 'Fichas disponibles', 'lectura'),
  mcp('resultado', 'resultado', 'chat', 'Resultado de un proceso de chat asincrono', 'lectura'),
  mcp('github_leer', 'github_leer', 'github', 'Leer archivo o carpeta de GitHub', 'lectura'),
  mcp('github_escribir', 'github_escribir', 'github', 'Escribir archivo con commit en GitHub', 'efectos'),
  mcp('github_api', 'github_api', 'github', 'API de GitHub con el token configurado', 'efectos'),
  mcp('pendientes', 'pendientes', 'chat', 'Checklist de pendientes', 'por_accion', { acciones: ['listar', 'agregar', 'marcar', 'ordenar', 'quitar'], lectura: ['listar'] }),
  mcp('sala', 'sala', 'chat', 'ROOM CONFERENCIAS', 'por_accion', { acciones: ['crear', 'listar', 'leer', 'enviar', 'contexto', 'permiso'], lectura: ['listar', 'leer'] }), // contexto ES escritura: Control._salas actualiza s['contexto']; requiere operador
  mcp('agente', 'agente', 'agentes', 'Delegar en un agente conectado (exige Agentes ON en el Router)', 'efectos'),
  mcp('llm', 'llm', 'agentes', 'Preguntar a otro modelo (exige IA ON en el Router)', 'efectos'),
  mcp('yaiwes_md', 'yaiwes_md', 'chat', 'yaiwes.md (informacion compartida del proyecto)', 'por_accion', { acciones: ['leer', 'escribir'], lectura: ['leer'] }),
  plugin('motor_archivos', 'motor_archivos', 'motores', 'Motor de descarga, extraccion, copia y busqueda de archivos (cola)', ['transferir', 'ejecutar', 'estado', 'cancelar', 'raiz', 'listar_raiz'], ['estado', 'raiz', 'listar_raiz'], { mcp_equivalente: 'archivos' }),
  plugin('loop', 'nct_loop', 'loop', 'LOOP gobernado (C0-C7, hasta 4 procesos en paralelo)', ['status', 'health', 'ejecutar', 'gobernar', 'estado', 'cancelar', 'motores', 'motor_fases', 'motor_ejecutar', 'motores_registro', 'agentes', 'fuente_listar', 'fuente_agregar', 'fuente_quitar', 'fuente_sync', 'paralelo', 'estado_paralelo'],
    ['status', 'health', 'estado', 'motores', 'motor_fases', 'motores_registro', 'agentes', 'fuente_listar', 'estado_paralelo'], { mcp_equivalente: 'loop', plugin_repo: 'nct_loop' }),
  plugin('cola', 'cola50', 'loop', 'Cola CIT-50', ['status', 'health', 'crear', 'listar', 'estado', 'eventos', 'tarea', 'orden', 'draft', 'aprobar', 'accion', 'worker'], ['status', 'health', 'listar', 'estado', 'eventos', 'tarea'], { plugin_repo: 'cola50' }),
  plugin('watchdog', 'watchdog48', 'loop', 'Watchdog 10 min - 48 h', ['status', 'health', 'crear', 'listar', 'estado', 'eventos', 'heartbeat', 'accion', 'tick', 'worker'], ['status', 'health', 'listar', 'estado', 'eventos'], { plugin_repo: 'watchdog48' }),
  plugin('puente_chat', 'puente_chat', 'chat', 'Puente del chat: procesos asincronos, cancelar, mantener encendido, mirrors', ['chat_async', 'resultado', 'cancelar', 'mantener_encendido', 'mirror_listar', 'mirror_configurar', 'mirror_agregar', 'mirror_quitar'], ['resultado', 'mirror_listar']),
  { id: 'chat_send', grupo: 'chat', titulo: 'Motor del chat (Harness + tools + constitucion + anclas + yaiwes.md)', via: 'http', destino: { metodo: 'POST', ruta: '/chat/send' }, efectos: 'efectos',
    campos: ['mensajes', 'messages', 'message', 'modelo', 'sesion', 'anclados', 'constitucion', 'tools', 'agente_tool', 'llm_tool', 'contexto_previo'] },
  { id: 'harness_status', grupo: 'agentes', titulo: 'Disponibilidad real de agentes, workflows y modelos (status del Harness)', via: 'harness', destino: { accion: 'status' }, efectos: 'lectura' },
  { id: 'workflows', grupo: 'agentes', titulo: 'Workflows SWE que reporta el Harness (individual, swe_code, liquid_mirror) y su disponibilidad', via: 'harness', destino: { accion: 'status', campo: 'workflows' }, efectos: 'lectura' },
  // REPLICAS (SWE CODE, solo lectura): el Router no sirve estas funciones como endpoint propio, pero SI expone los datos del servidor por HTTP/MCP;
  // el bridge los lee con la clave del entorno y arma aqui el mismo resultado. Nada de esto toca ni modifica el Router ni el chat.
  replica('anclaje', 'chat', 'Anclaje (lectura): archivos subidos al chat/constitucion/proyecto, anclas de proyectos y contenido de un archivo anclado', ['archivos', 'proyectos', 'leer_archivo'],
    { depende_de: 'almacen', usa: ['POST /plugins/puente_chat/call/archivos', 'POST /plugins/puente_chat/call/proyecto (op list|get)', 'POST /almacen (leer, destino hf)'] }),
  replica('constitucion', 'chat', 'Constitucion (lectura): la oficial YAIWES del repo y los archivos subidos a la constitucion', ['oficial', 'archivos', 'leer_archivo'],
    { usa: ['archivo local CONSTITUCION-YAIWES.json del repo (RIU_CONSTITUCION_PATH)', 'POST /plugins/puente_chat/call/archivos (destino constitucion)', 'POST /almacen (leer, destino hf)'] }),
  replica('contexto', 'chat', 'Contexto fijo del chat (lectura): constitucion oficial + yaiwes.md + sandbox + pendientes, como los antepone el Router a cada mensaje', ['fijo'],
    { depende_de: 'yaiwes_md', usa: ['constitucion oficial (archivo local)', 'MCP yaiwes_md leer', 'POST /plugins/puente_chat/call/sandbox (sin texto = lectura)', 'MCP pendientes listar'] }),
];
// Lo que existe en chat-router/plugins pero el Router no sirve por HTTP: GAP honesto (no se inventa un endpoint).
const NO_RUTEADO = 'el Router MVP no lo sirve: /plugins/{plugin}/call/{accion} responde 404 "plugin no disponible en mvp" para este plugin (solo puente_chat, fichas_qwen, almacen, motor_archivos, nct_loop, cola50 y watchdog48)';
const GAPS_TOOLS = [
  { id: 'anclados-navegador', motivo: 'los anclados de la pestana del chat actual viven en el navegador del Director (localStorage); el Router solo los recibe en el campo `anclados` de POST /chat/send. Lo que el servidor SI guarda (archivos subidos, anclas de proyectos) lo lee la tool anclaje', usar_con: 'chat_send' },
  { id: 'constitucion-propia-navegador', motivo: 'el texto propio de la constitucion y su interruptor viven en el navegador (riu_constitucion_v1); el Router solo los recibe como campo `constitucion` {texto, anclados} de POST /chat/send. La oficial y los archivos subidos los lee la tool constitucion', usar_con: 'chat_send' },
  { id: 'workflows-navegador', motivo: 'las definiciones de la ventana Workflow Loops code Yaiwes viven en el navegador (riu_workflows_v1); no hay endpoint. Los workflows SWE los da la tool workflows (Harness) y la ejecucion gobernada es la tool loop', usar_con: 'workflows' },
  { id: 'workflow-loop-yaiwes', plugin_repo: true, motivo: NO_RUTEADO },
  ...['agentes', 'chat', 'chat-router', 'connectivity', 'hf_compute', 'hf_datasets', 'hf_skills', 'hf_storage', 'lifeguard', 'orquestador', 'parallel', 'ssh_bridge'].map((id) => ({ id, plugin_repo: true, motivo: NO_RUTEADO })),
  ...['motores', 'motores-descarga'].map((id) => ({ id, plugin_repo: true, usar_con: 'motor_archivos', motivo: 'son los scripts fuente de los motores (HF/extraccion) sin endpoint HTTP; el motor servido por el Router es motor_archivos (mvp/archivos)' })),
];
const CUBIERTOS_TOOLS = [
  { plugin: 'memoria', por: 'memoria', nota: 'plugins/memoria es el almacen detras de la tool MCP memoria' },
  { plugin: 'deepseek_harness', por: 'harness_status', nota: 'el Harness montado en /plugins/deepseek_harness; el bridge lo usa por /v1/swe/*' },
  { plugin: 'swe_code', por: '/v1/swe/*', nota: 'SWE CODE ES este bridge: iniciar, avanzar, estado, aprobar, reanudar y capacidades' },
  { plugin: 'swen_code_free', por: '/v1/openclaw', nota: 'configuracion y modos de SWEN CODE free (solo lectura)' },
  { plugin: 'router_api_cliente.py', por: 'cliente interno', nota: 'cliente HTTP del Harness hacia el Router; no es una funcion para el usuario' },
];
export function catalogoTools() {
  return { version: 1, tools: TOOLS_OPENCLAW.map((t) => structuredClone(t)), gaps: structuredClone(GAPS_TOOLS), cubiertos: structuredClone(CUBIERTOS_TOOLS),
    nota: 'El Router decide que tools estan visibles (Agentes/IA/Tools ON/OFF); este catalogo solo enumera lo que existe en su codigo' };
}

// ---- REPLICAS de lectura (SWE CODE): calculos propios del bridge para las funciones del chat que el Router no sirve como endpoint ----
// Constitucion oficial YAIWES: el mismo archivo que carga el Harness (plugins/puente_chat/constitucion). Solo lectura; fail-closed como _gov_base (id, version y modo FAIL_CLOSED).
export const rutaConstitucion = (env = process.env) => String(env.RIU_CONSTITUCION_PATH || '').trim() || path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../../plugins/puente_chat/constitucion/CONSTITUCION-YAIWES.json');
export function constitucionOficial({ env = process.env, fs = nodeFs } = {}) {
  let texto; try { texto = fs.readFileSync(rutaConstitucion(env), 'utf8'); } catch { return { ok: false, codigo: 'CONSTITUCION_NO_ENCONTRADA' }; }
  let d; try { d = JSON.parse(texto); } catch { return { ok: false, codigo: 'CONSTITUCION_INVALIDA' }; }
  if (!d || typeof d !== 'object' || !d.id || !d.version || d.modo !== 'FAIL_CLOSED') return { ok: false, codigo: 'CONSTITUCION_INVALIDA' };
  return { ok: true, id: String(d.id), version: String(d.version), sha256: crypto.createHash('sha256').update(texto, 'utf8').digest('hex'), texto };
}
// Ubicacion de un archivo subido al chat: identica a control.clave_espacio / control.ruta_archivo del Router ("destino|project_id|sesion"[:160]; sha1[:12]).
export const ESPACIOS = ['chat', 'constitucion', 'proyecto'];
const SESION_OK = /^[A-Za-z0-9_.:@-]{1,60}$/, PROYECTO_OK = /^[A-Za-z0-9_-]{1,60}$/, NOMBRE_ARCHIVO_OK = /^[\p{L}\p{N}][\p{L}\p{N} ._()-]{0,119}$/u;
export const claveEspacio = ({ destino, project_id, sesion } = {}) => [destino || 'chat', project_id || '', sesion || 'web-general'].join('|').slice(0, 160);
export const rutaArchivoChat = (espacio, nombre) => `chat_archivos/${crypto.createHash('sha1').update(claveEspacio(espacio), 'utf8').digest('hex').slice(0, 12)}/${nombre}`;
// Valida los datos de un espacio (nunca deja pasar rutas ni separadores): {destino, project_id?, sesion?}
export function espacioDe(args = {}) {
  const destino = args.destino === undefined ? 'chat' : args.destino, sesion = args.sesion === undefined ? undefined : args.sesion, project_id = args.project_id === undefined ? undefined : args.project_id;
  if (!ESPACIOS.includes(destino)) return null;
  if (sesion !== undefined && (typeof sesion !== 'string' || !SESION_OK.test(sesion))) return null;
  if (project_id !== undefined && (typeof project_id !== 'string' || !PROYECTO_OK.test(project_id))) return null;
  return { destino, ...(project_id !== undefined ? { project_id } : {}), ...(sesion !== undefined ? { sesion } : {}) };
}
export const nombreArchivoValido = (n) => typeof n === 'string' && NOMBRE_ARCHIVO_OK.test(n) && !n.includes('..');
// base64 del almacen -> texto (si es binario solo se informa del tamano)
export function textoDeBase64(b64, max = 100000) {
  const buf = Buffer.from(String(b64 || ''), 'base64');
  if (buf.includes(0)) return { binario: true, bytes: buf.length };
  const t = buf.toString('utf8');
  return { binario: false, bytes: buf.length, texto: t.slice(0, max), truncado: t.length > max };
}
// Contexto fijo: las mismas capas que app._chat_ficha antepone como mensaje de sistema (CONSTITUCION, yaiwes.md, SANDBOX, PENDIENTES; "encendidos = con texto").
// La constitucion PROPIA del Director y los anclados de la pestana viven en el navegador: no entran (GAP anclados-navegador / constitucion-propia-navegador).
export function armarContextoFijo({ constitucion, yaiwes, sandbox, pendientes }) {
  const partes = [['CONSTITUCION OFICIAL YAIWES (solo lectura): es ley para este trabajo; respetala al programar y en lo que respondes', constitucion],
    ['yaiwes.md (informacion del proyecto; la herramienta yaiwes_md la lee y la escribe)', yaiwes], ['SANDBOX (system prompt de code)', sandbox],
    ['PENDIENTES (lista compartida; la herramienta pendientes la consulta y la actualiza)', pendientes]];
  const activas = partes.filter(([, t]) => typeof t === 'string' && t.trim());
  return { texto: activas.map(([n, t]) => `[${n}]\n${t}`).join('\n\n'), capas: partes.map(([n, t]) => ({ capa: n.split(' (')[0].split(':')[0], presente: typeof t === 'string' && !!t.trim() })) };
}
export { ACCESO_ROUTER, ROUTER_LOCAL };
