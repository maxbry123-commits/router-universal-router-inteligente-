// swe_rutas.js — rutas /v1/swe/{iniciar,avanzar,estado,aprobar,reanudar} y GET /v1/swe/capacidades del bridge (backend de OpenClaw).
// OpenClaw UI -> (aqui) -> Harness DeepSeek (POST {RIU_DEEPSEEK_HARNESS_URL}/invoke) -> agentes/adaptadores. El bridge NO ejecuta herramientas ni adaptadores Python:
// solo valida y reenvia. RIU_API_KEY vive solo en este backend. Contrato de tarea: el mismo de YAIWES (chat-router/agentes/adaptadores/contrato.py, origen "openclaw").
// Autenticacion OBLIGATORIA: sin credencial configurada (BRIDGE_TOKEN, que es OPCIONAL, ni ninguna clave de acceso) estas rutas se rechazan (503); no heredan el acceso libre de las rutas publicas.
// Credencial valida: BRIDGE_TOKEN (Bearer / x-bridge-key) o una de las 4 clave de acceso (RIU_API_KEY, RIU_PUBLIC_CHAT_KEY, RIU_MCP_KEY, RIU_ROUTER_API_KEY) en Authorization: Bearer.
import crypto from 'node:crypto';
import { iguales } from './iguales.js';
import { clavesAcceso, esClaveAcceso, bearerDe } from './acceso.js';
import { catalogoTools, ACCESO_ROUTER, ROUTER_LOCAL, constitucionOficial, espacioDe, rutaArchivoChat, nombreArchivoValido, textoDeBase64, armarContextoFijo } from './openclaw.js';

export const OPERACIONES_SWE = { iniciar: 'swe_iniciar', avanzar: 'swe_avanzar', estado: 'swe_estado', aprobar: 'swe_aprobar', reanudar: 'swe_reanudar' };
const PERMITIDAS = new Set(Object.values(OPERACIONES_SWE));
export const TIMEOUT_HARNESS_MS = 60000;
export const TIMEOUT_AVANZAR_MS = 1800000;  // swe_avanzar / swe_reanudar corren el flujo entero en el Harness (minutos): RIU_SWE_AVANZAR_TIMEOUT_MS
const ORIGEN = 'openclaw';
const TASK_ID = /^[A-Za-z0-9_-]{1,64}$/, SEGMENTO = /^[A-Za-z0-9_-]{0,64}$/, OP_ID = /^[A-Za-z0-9_-]{1,80}$/, OPERADOR = /^[A-Za-z0-9_.@-]{2,64}$/, CODIGO = /^[A-Z][A-Z0-9_]{2,63}$/;
const CAMPOS = ['task_id', 'origen', 'mensaje', 'workflow', 'modelo_responde', 'modelo_lector', 'modelo_tool', 'modelo_revisor', 'agente_responde', 'agente_tool', 'agente_verificador', 'modo_agentico', 'aprobacion', 'sesion', 'proyecto'];
const OBLIGATORIOS = CAMPOS.slice(0, 11);
const MAX_MENSAJE = 200000;

// POST {RIU_DEEPSEEK_HARNESS_URL}/invoke con el cuerpo dado; devuelve cuerpo.result. Los mensajes de error son codigos fijos: jamas llevan la URL ni la clave.
async function postHarness(payload, { env, fetchFn }) {
  const largo = payload.action === 'invoke' && (payload.tool === 'swe_avanzar' || payload.tool === 'swe_reanudar');
  const base = String(env.RIU_DEEPSEEK_HARNESS_URL || '').trim().replace(/\/+$/, ''), clave = env.RIU_API_KEY;
  if (!base || !clave) throw new Error('HARNESS_NO_CONFIGURADO');
  const pos = (v) => (Number.parseInt(v, 10) > 0 ? Number.parseInt(v, 10) : 0);
  const ms = largo ? pos(env.RIU_SWE_AVANZAR_TIMEOUT_MS) || TIMEOUT_AVANZAR_MS : pos(env.RIU_SWE_HARNESS_TIMEOUT_MS) || TIMEOUT_HARNESS_MS;
  const ctl = new AbortController(), t = setTimeout(() => ctl.abort(), ms);
  let r;
  try {
    r = await fetchFn(`${base}/invoke`, { method: 'POST', headers: { 'content-type': 'application/json', 'X-API-Key': clave }, body: JSON.stringify(payload), signal: ctl.signal, redirect: 'error' });
    if (!r.ok) throw new Error(`HARNESS_HTTP_${r.status}`);
    let cuerpo = null;
    try { cuerpo = await r.json(); } catch { /* cuerpo no JSON: fallo de ejecucion */ }
    if (!cuerpo || cuerpo.status !== 'ok' || !cuerpo.result || typeof cuerpo.result !== 'object') {
      throw Object.assign(new Error('HARNESS_EJECUCION_FALLIDA'), typeof (cuerpo && cuerpo.error) === 'string' && CODIGO.test(cuerpo.error) ? { codigo: cuerpo.error } : {});  // solo un codigo estable; texto libre (rutas, trazas) se descarta
    }
    return cuerpo.result;
  } catch (e) {
    if (/^HARNESS_(HTTP_\d+|EJECUCION_FALLIDA)$/.test(e && e.message)) throw e;
    throw new Error(e && (e.name === 'AbortError' || e.name === 'TimeoutError') ? 'HARNESS_TIMEOUT' : 'HARNESS_NO_DISPONIBLE');
  } finally { clearTimeout(t); }
}

// Llama a una operacion SWE del Harness (solo las cinco permitidas).
export async function llamarHarness(operacion, datos, { env = process.env, fetchFn = fetch } = {}) {
  if (typeof operacion !== 'string' || !PERMITIDAS.has(operacion)) throw new Error('OPERACION_NO_PERMITIDA');
  return postHarness({ action: 'invoke', tool: operacion, args: datos }, { env, fetchFn });
}

// ---- capacidades (solo lectura): el `status` del Harness -> result.swe.{agentes,workflows,modelos}, saneado igual que GET /chat/swe/capacidades de YAIWES ----
// El catalogo vive en agentes/adaptadores/modelos.py y el Harness solo emite ids de ese catalogo; aqui no se copia: se descarta lo que no tenga la forma esperada.
const ID_CAP = /^[A-Za-z0-9][A-Za-z0-9._/-]{0,79}$/;
const SECRETO = /(?:sk-(?:sp-)?[A-Za-z0-9_-]{12,}|github_pat_[A-Za-z0-9_]{12,}|gh[pousr]_[A-Za-z0-9]{12,}|hf_[A-Za-z0-9]{20,}|gsk_[A-Za-z0-9]{12,}|nvapi-[A-Za-z0-9_-]{12,})/g;
const GRUPOS = ['agentes', 'workflows', 'modelos'];
// Los seis estados de la instruccion 37: los emite el Harness (agentes/adaptadores/disponibilidad.py ESTADOS); aqui solo se validan (test/swe_rutas.test.mjs comprueba que no hay deriva).
export const ESTADOS_DISPONIBILIDAD = ['DISPONIBLE', 'NO INSTALADO', 'NO CONFIGURADO', 'NO COMPATIBLE', 'NO DISPONIBLE EN PROVEEDOR', 'SIN VERIFICAR'];
const VEREDICTOS = ['DISPONIBLE', 'NO DISPONIBLE', 'SIN VERIFICAR'], CAUSA = /^[a-z][a-z0-9_]{1,63}$/;
function estadoSaneado(v, e, g) {
  if (typeof v.estado === 'string' && ESTADOS_DISPONIBILIDAD.includes(v.estado)) { e.estado = v.estado; if (v.estado !== 'DISPONIBLE') e.disponible = false; }  // desconocido jamas se presenta como verificado
  else if (v.estado !== undefined) e.disponible = false;  // estado fuera de los seis: no se da por verificado
  if (VEREDICTOS.includes(v.veredicto)) e.veredicto = v.veredicto;
  for (const k of ['verificado', 'intentable']) if (typeof v[k] === 'boolean') e[k] = v[k];
  if (typeof v.causa === 'string' && CAUSA.test(v.causa)) e.causa = v.causa;
  if (g === 'modelos') for (const [k, tope] of [['nombre', 80], ['proveedor', 40], ['nota', 200]]) if (typeof v[k] === 'string' && v[k]) e[k] = v[k].replace(SECRETO, '[REDACTADO]').slice(0, tope);
}
export function sanearCapacidades(result) {
  const swe = simple(result) && simple(result.swe) ? result.swe : {}, salida = {};
  for (const g of GRUPOS) {
    salida[g] = {};
    const entradas = simple(swe[g]) ? swe[g] : {};
    for (const [k, v] of Object.entries(entradas)) {
      if (!ID_CAP.test(k) || k.includes('..') || !simple(v) || typeof v.disponible !== 'boolean') continue;
      const e = { disponible: v.disponible };
      if (typeof v.motivo === 'string' && v.motivo) e.motivo = v.motivo.replace(SECRETO, '[REDACTADO]').slice(0, 200);
      if (g === 'agentes' && Array.isArray(v.modelos)) e.modelos = v.modelos.filter((m) => typeof m === 'string' && ID_CAP.test(m) && !m.includes('..'));
      estadoSaneado(v, e, g);
      salida[g][k] = e;
    }
  }
  return salida;
}
export async function consultarCapacidades({ env = process.env, fetchFn = fetch } = {}) {
  const vacio = { agentes: {}, workflows: {}, modelos: {} };
  if (!String(env.RIU_DEEPSEEK_HARNESS_URL || '').trim()) return { harness: 'no_configurado', ...vacio };
  if (!env.RIU_API_KEY) return { harness: 'sin_credencial', ...vacio };
  try { return { harness: 'ok', ...sanearCapacidades(await postHarness({ action: 'status' }, { env, fetchFn })) }; }
  catch { return { harness: 'no_disponible', ...vacio }; }
}

const invalido = (code) => Object.assign(new Error(code), { http: 400 });
const simple = (o) => !!o && typeof o === 'object' && !Array.isArray(o);

// iniciar = el contrato TareaSWE exacto (la validacion de catalogo —modelos, agentes, workflow— la hace el contrato Python en el Harness, aqui no se copia el catalogo)
function argsIniciar(b) {
  if (!simple(b)) throw invalido('CONTRATO_INVALIDO');
  if (Object.keys(b).some((k) => !CAMPOS.includes(k))) throw invalido('CAMPOS_DESCONOCIDOS');
  if (typeof b.task_id !== 'string' || !TASK_ID.test(b.task_id)) throw invalido('TASK_ID_INVALIDO');
  if (b.origen !== ORIGEN) throw invalido('ORIGEN_INVALIDO');
  if (OBLIGATORIOS.some((k) => !(k in b))) throw invalido('CAMPOS_FALTANTES');
  if (OBLIGATORIOS.some((k) => typeof b[k] !== 'string')) throw invalido('CONTRATO_INVALIDO');
  if (!b.mensaje.trim()) throw invalido('MENSAJE_VACIO');
  if (b.mensaje.length > MAX_MENSAJE) throw invalido('MENSAJE_DEMASIADO_LARGO');
  if (['modo_agentico', 'aprobacion'].some((k) => k in b && typeof b[k] !== 'boolean')) throw invalido('CONTRATO_INVALIDO');
  if (['sesion', 'proyecto'].some((k) => k in b && (typeof b[k] !== 'string' || !SEGMENTO.test(b[k])))) throw invalido('CONTRATO_INVALIDO');
  const args = {}; for (const k of CAMPOS) if (k in b) args[k] = b[k];
  args.aprobacion = false;  // la aprobacion NO es un campo del cliente ni del modelo: solo swe_aprobar con operador identificado
  return args;
}
// avanzar/estado/reanudar/aprobar: solo la referencia de la tarea; el resto del cuerpo se descarta
function argsReferencia(b) {
  const x = simple(b) ? b : {};
  if (typeof x.task_id !== 'string' || !TASK_ID.test(x.task_id)) throw invalido('TASK_ID_INVALIDO');
  if (x.origen !== undefined && x.origen !== ORIGEN) throw invalido('ORIGEN_INVALIDO');
  const args = { task_id: x.task_id, origen: ORIGEN };
  for (const k of ['sesion', 'proyecto']) if (x[k] !== undefined && x[k] !== '') { if (typeof x[k] !== 'string' || !SEGMENTO.test(x[k])) throw invalido('CONTRATO_INVALIDO'); args[k] = x[k]; }
  return args;
}
const respuesta = (res, codigo, error) => res.status(codigo).json({ ok: false, error });

// BRIDGE_APROBADORES = "operador:sha256(token)" separados por coma: cada persona tiene SU token (en el entorno solo viaja el hash). Entradas mal formadas se ignoran.
// Sin esta variable NO hay aprobadores por defecto (es seguridad): aprobar responde 503 y dice como generarla.
const sha256 = (t) => crypto.createHash('sha256').update(String(t), 'utf8').digest('hex');
function aprobadores(env) {
  const salida = new Map();
  for (const par of String(env.BRIDGE_APROBADORES || '').split(',')) {
    const i = par.indexOf(':'), nombre = par.slice(0, i).trim(), huella = par.slice(i + 1).trim().toLowerCase();
    if (i > 0 && OPERADOR.test(nombre) && /^[0-9a-f]{64}$/.test(huella)) salida.set(nombre, huella);
  }
  return salida;
}
// Identifica al OPERADOR REAL (x-operador + su token individual en x-operator-token). El BRIDGE_TOKEN lo comparte todo el que habla con el bridge y NO identifica a nadie:
// sin aprobadores configurados 503; sin operador 403; operador no registrado 403; token ausente, de otro operador o el del bridge 401. Devuelve {operador} o {rechazo} ya enviado.
// El token de un operador tampoco puede coincidir con BRIDGE_TOKEN ni con una clave de acceso (esas las comparte quien habla con el bridge y no identifican a nadie): 503.
export const MSG_SIN_APROBADORES = 'falta la variable BRIDGE_APROBADORES (operador:sha256(token),...): genera la linea con chat-router/DEPLOY/generar-aprobadores.sh y pegala como secreto del Space';
function identificarOperador(req, res, env) {
  const reg = aprobadores(env), h = req.headers || {};
  if (!reg.size) return { rechazo: respuesta(res, 503, { code: 'APROBADORES_NO_CONFIGURADOS', message: MSG_SIN_APROBADORES }) };
  const compartidas = [env.BRIDGE_TOKEN || '', ...clavesAcceso(env)].map(sha256);
  if ([...reg.values()].some((x) => compartidas.map((c) => iguales(x, c)).some(Boolean))) return { rechazo: respuesta(res, 503, { code: 'APROBADORES_NO_CONFIGURADOS', message: 'BRIDGE_APROBADORES: el token de un operador debe ser SUYO (distinto de BRIDGE_TOKEN y de las claves de acceso); genera uno nuevo con chat-router/DEPLOY/generar-aprobadores.sh' }) };
  const op = h['x-operador'] !== undefined ? String(h['x-operador']) : '';
  if (!OPERADOR.test(op)) return { rechazo: respuesta(res, 403, { code: 'OPERADOR_REQUERIDO' }) };
  if (!reg.has(op)) return { rechazo: respuesta(res, 403, { code: 'OPERADOR_NO_AUTORIZADO' }) };
  const t = String(h['x-operator-token'] || '');
  if (!t || !iguales(sha256(t), reg.get(op))) return { rechazo: respuesta(res, 401, { code: 'OPERADOR_NO_AUTORIZADO' }) };
  return { operador: op };
}

// Autenticacion obligatoria compartida por todas las rutas /v1/swe/*: devuelve null si pasa, o la respuesta de rechazo ya enviada.
function exigirToken(req, res, env) {
  const token = env.BRIDGE_TOKEN || '';
  if (!token && !clavesAcceso(env).length) return respuesta(res, 503, { code: 'BRIDGE_TOKEN_NO_CONFIGURADO', message: 'las rutas /v1/swe/* exigen una credencial en el bridge: una clave de acceso (RIU_API_KEY) en Authorization: Bearer, o BRIDGE_TOKEN (opcional)' });
  const h = req.headers || {}, bearer = bearerDe(req), t = bearer || String(h['x-bridge-key'] || '');
  const esToken = !!token && !!t && iguales(t, token), esClave = esClaveAcceso(bearer, env);  // ambas comparaciones se evaluan siempre (tiempo constante)
  if (!esToken && !esClave) return respuesta(res, 401, { code: 'NO_AUTORIZADO' });
  return null;
}

// ---- TOOLS de OpenClaw (UI3): reenvio al Router MVP por MCP/HTTP con la clave de acceso del ENTORNO del bridge (jamas del navegador) ----
const TIMEOUT_TOOLS_MS = 120000, TIMEOUT_LISTA_MS = 15000, MAX_ARGS = 1000000;
const redactar = (texto, env) => {
  let t = String(texto == null ? '' : texto).replace(SECRETO, '[REDACTADO]');
  for (const v of ACCESO_ROUTER) { const k = String(env[v] || '').trim(); if (k.length >= 6) t = t.split(k).join('[REDACTADO]'); }
  return t.slice(0, 200);
};
function configRouter(env) {
  const base = String(env.RIU_ROUTER_URL || '').trim().replace(/\/+$/, '') || ROUTER_LOCAL;
  const clave = ACCESO_ROUTER.map((v) => String(env[v] || '').trim()).find(Boolean);
  if (!clave) return { error: 'ROUTER_NO_CONFIGURADO', estado: 'sin_credencial' };
  let ok = false; try { const u = new URL(base); ok = (u.protocol === 'https:' && !!u.hostname) || (u.protocol === 'http:' && ['127.0.0.1', 'localhost'].includes(u.hostname) && !u.username); } catch { ok = false; }
  return ok ? { base, clave } : { error: 'ROUTER_URL_INVALIDA', estado: 'no_configurado' };
}
// POST al Router; devuelve el cuerpo JSON. Errores = codigos fijos (nunca URL ni clave): ROUTER_BLOQUEADO (403, con el permiso apagado), ROUTER_HTTP_<n>, ROUTER_TIMEOUT, ROUTER_NO_DISPONIBLE.
async function postRouter(ruta, cuerpo, cfg, { env, fetchFn, ms }) {
  const ctl = new AbortController(), t = setTimeout(() => ctl.abort(), ms);
  try {
    const r = await fetchFn(cfg.base + ruta, { method: 'POST', headers: { 'content-type': 'application/json', 'X-API-Key': cfg.clave }, body: JSON.stringify(cuerpo), signal: ctl.signal, redirect: 'error' });
    if (r.status === 403) {
      let d = ''; try { d = String((await r.json()).detail || ''); } catch { /* sin detalle */ }
      const m = /(?<![\w])(?:tools|ia|agentes|agente_tool|llm_tool|herramienta|conexion)=false/.exec(d);
      throw Object.assign(new Error('ROUTER_BLOQUEADO'), { http: 403, permiso: m ? m[0] : undefined });
    }
    if (!r.ok) throw Object.assign(new Error(`ROUTER_HTTP_${r.status}`), { http: 502 });
    try { return await r.json(); } catch { throw Object.assign(new Error('ROUTER_RESPUESTA_INVALIDA'), { http: 502 }); }
  } catch (e) {
    if (/^ROUTER_(BLOQUEADO|HTTP_\d+|RESPUESTA_INVALIDA)$/.test(e && e.message)) throw e;
    throw Object.assign(new Error(e && (e.name === 'AbortError' || e.name === 'TimeoutError') ? 'ROUTER_TIMEOUT' : 'ROUTER_NO_DISPONIBLE'), { http: 502 });
  } finally { clearTimeout(t); }
}
async function visiblesDelRouter(env, fetchFn) {
  const cfg = configRouter(env); if (cfg.error) return { router: cfg.estado, visibles: null };
  try {
    const j = await postRouter('/mcp', { jsonrpc: '2.0', id: 1, method: 'tools/list' }, cfg, { env, fetchFn, ms: TIMEOUT_LISTA_MS });
    const lista = j && j.result && Array.isArray(j.result.tools) ? j.result.tools : null;
    return lista ? { router: 'ok', visibles: new Set(lista.map((x) => x && x.name).filter((n) => typeof n === 'string')) } : { router: 'no_disponible', visibles: null };
  } catch { return { router: 'no_disponible', visibles: null }; }
}
// Estado de cada tool segun lo que el Router DICE: el `tools/list` del Router solo trae las visibles (Agentes/IA/Tools ON y conexion activa).
function estadoTool(t, vivo, harness, env) {
  if (t.via === 'harness') return harness === 'ok' ? 'DISPONIBLE' : 'HARNESS_NO_DISPONIBLE';
  if (t.id === 'constitucion' && !constitucionOficial({ env }).ok) return 'CONSTITUCION_NO_ENCONTRADA';  // la replica local necesita el archivo del repo (RIU_CONSTITUCION_PATH)
  if (!vivo.visibles) return 'ROUTER_NO_DISPONIBLE';
  const mcp = t.via === 'mcp' ? t.destino.tool : t.mcp_equivalente || t.depende_de;
  if (mcp) return vivo.visibles.has(mcp) ? 'DISPONIBLE' : 'BLOQUEADA_POR_ROUTER';
  return 'SIN_VERIFICAR';  // plugin/ruta HTTP sin tool MCP equivalente: existe en el codigo del Router pero no hay forma de listarla sin ejecutarla
}
const hayHarness = (env) => !!(String(env.RIU_DEEPSEEK_HARNESS_URL || '').trim() && env.RIU_API_KEY);
export async function listarTools({ env = process.env, fetchFn = fetch } = {}) {
  const vivo = await visiblesDelRouter(env, fetchFn), cat = catalogoTools();
  const tools = cat.tools.map((t) => ({ ...t, estado: estadoTool(t, vivo, hayHarness(env) ? 'ok' : 'no', env) }));
  return { ok: true, vivo: { router: vivo.router }, tools, gaps: cat.gaps, cubiertos: cat.cubiertos, nota: cat.nota };
}
const sinEfectos = (t, accion) => t.efectos === 'lectura' || (t.efectos === 'por_accion' && Array.isArray(t.lectura) && t.lectura.includes(accion));
export async function planificarTool(id, cuerpo, { env = process.env, fetchFn = fetch } = {}) {
  const t = catalogoTools().tools.find((x) => x.id === id);
  if (!t) throw Object.assign(new Error('TOOL_DESCONOCIDA'), { http: 404 });
  const x = simple(cuerpo) ? cuerpo : {}, args = x.args === undefined ? {} : x.args;
  if (!simple(args)) throw invalido('CONTRATO_INVALIDO');
  if (JSON.stringify(args).length > MAX_ARGS) throw invalido('ARGS_DEMASIADO_GRANDES');
  let accion;
  if (t.acciones) {
    accion = x.accion;
    if (typeof accion !== 'string' || !accion) throw invalido('ACCION_REQUERIDA');
    if (!t.acciones.includes(accion)) throw invalido('ACCION_NO_PERMITIDA');
  }
  if (t.via === 'http' && Object.keys(args).some((k) => !t.campos.includes(k))) throw invalido('CAMPOS_DESCONOCIDOS');
  return { t, args, accion, efectos: !sinEfectos(t, accion) };
}
// tools/call del Router por MCP: devuelve el contenido estructurado o lanza un codigo fijo
async function llamarMcp(nombre, argumentos, cfg, op) {
  const j = await postRouter('/mcp', { jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name: nombre, arguments: argumentos } }, cfg, op);
  if (j && j.error) throw Object.assign(new Error('ROUTER_RPC_ERROR'), { http: 502, mensaje: redactar(j.error.message, op.env) });
  const r = j && j.result;
  if (!r) throw Object.assign(new Error('ROUTER_RESPUESTA_INVALIDA'), { http: 502 });
  if (r.isError) throw Object.assign(new Error('ROUTER_TOOL_ERROR'), { http: 502, mensaje: redactar((r.content && r.content[0] && r.content[0].text) || '', op.env) });
  return r.structuredContent !== undefined ? r.structuredContent : r;
}
const resultadoPlugin = (j) => (j && typeof j === 'object' && j.status === 'ok' && 'result' in j ? j.result : j);
const POR_REPLICA_MAX = 100000;

// REPLICAS de lectura (anclaje, constitucion, contexto): el Router no las sirve como endpoint, pero si los datos del servidor; aqui se piden y se arma el resultado. Solo lectura: ningun cuerpo lleva texto, op de escritura ni accion con efectos.
async function listarArchivosChat(espacio, cfg, op) {
  const r = resultadoPlugin(await postRouter('/plugins/puente_chat/call/archivos', espacio, cfg, op));
  return Array.isArray(r && r.archivos) ? r.archivos.filter((n) => typeof n === 'string') : [];
}
async function leerArchivoChat(args, cfg, op) {
  const espacio = espacioDe(args);
  if (!espacio) throw invalido('ESPACIO_INVALIDO');
  if (!nombreArchivoValido(args.nombre)) throw invalido('NOMBRE_INVALIDO');
  if (!(await listarArchivosChat(espacio, cfg, op)).includes(args.nombre)) throw Object.assign(new Error('ARCHIVO_NO_ENCONTRADO'), { http: 404 });  // solo lo que el indice del Router declara (como control.ruta_de)
  const a = await postRouter('/almacen', { accion: 'leer', destino: 'hf', nombre: rutaArchivoChat(espacio, args.nombre) }, cfg, op);
  return { nombre: args.nombre, ...espacio, ...textoDeBase64(a && a.valor, POR_REPLICA_MAX) };
}
async function ejecutarReplica({ t, args, accion }, { env, fetchFn, ms }, cfg) {
  const op = { env, fetchFn, ms };
  if (t.id === 'constitucion' && accion === 'oficial') {
    const c = constitucionOficial({ env });
    if (!c.ok) throw Object.assign(new Error(c.codigo), { http: 404 });
    return { id: c.id, version: c.version, sha256: c.sha256, texto: c.texto };
  }
  if (accion === 'archivos' || accion === 'leer_archivo') {
    const a = t.id === 'constitucion' ? { ...args, destino: 'constitucion', sesion: args.sesion === undefined ? 'constitucion' : args.sesion } : args;
    if (accion === 'leer_archivo') return leerArchivoChat(a, cfg, op);
    const espacio = espacioDe(a); if (!espacio) throw invalido('ESPACIO_INVALIDO');
    return { ...espacio, archivos: await listarArchivosChat(espacio, cfg, op) };
  }
  if (t.id === 'anclaje' && accion === 'proyectos') {
    const id = args.project_id;
    if (id !== undefined && (typeof id !== 'string' || !/^[A-Za-z0-9_-]{1,60}$/.test(id))) throw invalido('PROYECTO_INVALIDO');
    return resultadoPlugin(await postRouter('/plugins/puente_chat/call/proyecto', id === undefined ? { op: 'list' } : { op: 'get', project_id: id }, cfg, op));  // op fijo: list|get, nunca upsert/delete
  }
  if (t.id === 'contexto' && accion === 'fijo') {
    const ses = args.sesion === undefined ? 'web-general' : args.sesion;
    if (typeof ses !== 'string' || !/^[A-Za-z0-9_.:@-]{1,60}$/.test(ses)) throw invalido('ESPACIO_INVALIDO');
    const salto = async (f) => { try { return await f(); } catch { return null; } };  // una capa caida no tira las demas: queda marcada como ausente
    const of = constitucionOficial({ env }), [yaiwes, sandbox, pend] = await Promise.all([
      salto(async () => (await llamarMcp('yaiwes_md', { accion: 'leer' }, cfg, op)).texto),
      salto(async () => resultadoPlugin(await postRouter('/plugins/puente_chat/call/sandbox', { sesion: ses }, cfg, op)).sandbox),  // sin `texto` = solo lectura
      salto(async () => (await llamarMcp('pendientes', { accion: 'listar' }, cfg, op)).pendientes)]);
    const lista = Array.isArray(pend) ? pend.slice(0, 30).map((p) => `- [${p && p.hecho ? 'x' : ' '}] ${String((p && p.texto) || '').slice(0, 300)}`).join('\n') : '';
    return { sesion: ses, ...armarContextoFijo({ constitucion: of.ok ? of.texto : '', yaiwes, sandbox, pendientes: lista }), constitucion: of.ok ? { id: of.id, version: of.version, sha256: of.sha256 } : { error: of.codigo } };
  }
  throw invalido('ACCION_NO_PERMITIDA');
}
async function ejecutarTool({ t, args, accion }, { env, fetchFn }) {
  if (t.via === 'harness') { const c = await consultarCapacidades({ env, fetchFn }); return t.destino.campo ? { harness: c.harness, [t.destino.campo]: c[t.destino.campo] } : c; }
  if (t.via === 'replica' && t.id === 'constitucion' && accion === 'oficial') return ejecutarReplica({ t, args, accion }, { env, fetchFn, ms: 0 }, null);  // local: no necesita Router
  const cfg = configRouter(env);
  if (cfg.error) throw Object.assign(new Error(cfg.error), { http: 503 });
  const ms = Number.parseInt(env.RIU_SWE_TOOLS_TIMEOUT_MS, 10) > 0 ? Number.parseInt(env.RIU_SWE_TOOLS_TIMEOUT_MS, 10) : TIMEOUT_TOOLS_MS, op = { env, fetchFn, ms };
  if (t.via === 'replica') return ejecutarReplica({ t, args, accion }, op, cfg);
  if (t.via === 'mcp') return llamarMcp(t.destino.tool, accion ? { ...args, accion } : args, cfg, op);
  return resultadoPlugin(t.via === 'plugin' ? await postRouter(`/plugins/${t.destino.plugin}/call/${accion}`, args, cfg, op) : await postRouter(t.destino.ruta, args, cfg, op));
}

export function montarRutasSwe(app, { env = process.env, fetchFn = fetch } = {}) {
  // GET /v1/swe/capacidades: solo lectura, sin secretos, misma autenticacion obligatoria. La UI de OpenClaw marca NO DISPONIBLE lo que no figura conectado.
  app.get('/v1/swe/capacidades', async (req, res) => exigirToken(req, res, env) || res.json(await consultarCapacidades({ env, fetchFn })));
  // TOOLS de OpenClaw: catalogo (con el estado real que da el Router) y reenvio al Router. Misma autenticacion obligatoria; lo que tiene efectos pide ademas un operador identificado.
  app.get('/v1/swe/tools', async (req, res) => exigirToken(req, res, env) || res.json(await listarTools({ env, fetchFn })));
  app.post('/v1/swe/tools/:id', async (req, res) => {
    const rechazo = exigirToken(req, res, env); if (rechazo) return rechazo;
    let plan;
    try { plan = await planificarTool(String((req.params || {}).id || ''), req.body, { env, fetchFn }); }
    catch (e) { return respuesta(res, e.http || 400, { code: e.message }); }
    if (plan.efectos) { const id = identificarOperador(req, res, env); if (id.rechazo) return id.rechazo; }
    try { return res.json({ ok: true, tool: plan.t.id, resultado: await ejecutarTool(plan, { env, fetchFn }) }); }
    catch (e) { return respuesta(res, e.http || 502, { code: e.message, ...(e.permiso ? { permiso: e.permiso } : {}), ...(e.mensaje ? { message: e.mensaje } : {}) }); }
  });
  for (const [ruta, operacion] of Object.entries(OPERACIONES_SWE)) {
    app.post(`/v1/swe/${ruta}`, async (req, res) => {
      const rechazo = exigirToken(req, res, env); if (rechazo) return rechazo;
      let operador = null;
      if (operacion === 'swe_aprobar') { const id = identificarOperador(req, res, env); if (id.rechazo) return id.rechazo; operador = id.operador; }  // primero QUIEN es; solo entonces se mira el resto
      let args;
      try {
        args = operacion === 'swe_iniciar' ? argsIniciar(req.body) : argsReferencia(req.body);
        if (operacion === 'swe_aprobar') {
          const op_id = simple(req.body) ? req.body.op_id : undefined;
          if (typeof op_id !== 'string' || !OP_ID.test(op_id)) throw invalido('OP_ID_INVALIDO');
          args = { ...args, op_id, operador };  // operador = el identificado por el servidor con su token individual; `aprobacion`/`operador` del cuerpo no cuentan
        }
      } catch (e) { return respuesta(res, e.http || 400, { code: e.message }); }
      try { return res.json({ ok: true, resultado: await llamarHarness(operacion, args, { env, fetchFn }) }); }
      catch (e) { return respuesta(res, 502, { code: 'SWE_HARNESS_ERROR', causa: String(e.message).slice(0, 60), ...(e.codigo ? { codigo_harness: e.codigo } : {}) }); }
    });
  }
}
