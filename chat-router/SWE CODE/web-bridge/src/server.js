// server.js — endpoint OpenAI-compatible del puente web (SWEN CODE free)
// POST /v1/chat/completions {model, messages, modo?, conv_id?}
//   model: web-dsv4-flash | web-qwen37max | web-qwen38max | swecode-<modo>
//   swecode-consulta/plan -> fan-out 3 modelos + sintesis Qwen3.8Max
//   otros modos -> objetivo unico (qwen38max por defecto)
// Errores tipados: SESSION_EXPIRED | SELECTOR_BROKEN | CF_CHALLENGE | RATE_LIMITED
import express from 'express';
import { createRequire } from 'node:module';
import { consultarWeb, salud } from './motor.js';
import { consenso } from './consenso.js';
import { modoValido } from './modos.js';
import { estadoCuentas, estadoTabs, snapshotTab, cerrarPagina, cerrarTodo } from './browser.js';
import { MODELOS_WEB } from './sites.js';
import crypto from 'node:crypto';
import { pool, cuentaActual, setCuentas } from './cuentas.js';
import nodeFs from 'node:fs';
import { vigilarWorkspace, rutaWorkspace, configVigente, vigilarConfig, espejo } from './openclaw.js';
import { respaldo, externo, local, esExterno, esLocal, idsRespaldo, estadoRespaldo, setClaves, limpiarClaves } from './respaldo.js';
import { listarCheckpoints, registrarLeccion, proponerMejoras, checkpointCrudo } from './bloques.js';
import { retomarLocal, retomarPorId, TIPO as TIPO_LOCAL } from './retomar_local.js';
import { idValido as tareaIdValido } from './checkpoint_hf.js';
import { conFormato } from './formato.js';
import { guardarTurno, leerTurnos } from './memoria.js';
import { vigilarActualizacion } from './autoactualizar.js';
import { cargarDelBanco, guardarEnBanco, borrarDelBanco, vigilarBanco } from './clavesbanco.js';
import { publicarEnGithub, traerDeGithub } from './bancogithub.js';
import { guardarAsesoria, leerProyecto, listarProyectos } from './proyectos.js';
import { preambulo } from './modos.js';

// gramatica "SWEN CODE free ..." (SWE CODE free/activar.js): elige modelo, modo y seccion desde el propio mensaje
let activar = null;
try { activar = createRequire(import.meta.url)(process.env.RIU_ACTIVAR_PATH || '../../../SWE CODE free/activar.js').activar; } catch { console.warn('[bridge] sin activar.js: la gramatica SWEN CODE free queda desactivada (ruta o RIU_ACTIVAR_PATH)'); }
const IDS_DIRECTOS = (id) => /^(groq\/|nvidia\/|lfm2\.5|qwen2\.5-coder|qwen3\.5|qwen3-0\.6b|web-|swecode-)/.test(id);

// Groq/NVIDIA/locales con un modo (p. ej. despliega): reciben el preambulo de ese modo, como el agente que despliega
const conPreambulo = (msgs, m) => (m && modoValido(m) ? [{ role: 'system', content: preambulo(m) }, ...msgs] : msgs);

// acceso: con BRIDGE_TOKEN todas las rutas (salvo /health) piden Authorization: Bearer <token> o x-bridge-key
const TOKEN = process.env.BRIDGE_TOKEN || '';
const iguales = (a, b) => { const x = Buffer.from(String(a)), y = Buffer.from(String(b)); return x.length === y.length && crypto.timingSafeEqual(x, y); };
const sinCorreos = (o) => JSON.parse(JSON.stringify(o ?? null, (k, v) => (k === 'email' ? undefined : v)));
const textoDe = (c) => (typeof c === 'string' ? c : Array.isArray(c) ? c.map(p => (typeof p === 'string' ? p : p && typeof p.text === 'string' ? p.text : '')).filter(Boolean).join('\n') : '');
const MAX_PROMPT = parseInt(process.env.BRIDGE_MAX_PROMPT || '400000', 10), MAX_DOCS = 10;

const app = express();
app.use((req, res, next) => {
  if (!TOKEN || req.path === '/health') return next();
  const h = req.headers, t = String(h.authorization || '').replace(/^Bearer\s+/i, '') || String(h['x-bridge-key'] || '');
  return t && iguales(t, TOKEN) ? next() : res.status(401).json({ error: { code: 'NO_AUTORIZADO', message: 'falta o es invalido el token del bridge' } });
});
// panel de claves del chat (el proxy del Space reenvia /web/* aqui): ademas del BRIDGE_TOKEN exige la clave de acceso del chat en x-api-key
const ACCESO_VARS = ['RIU_API_KEY', 'RIU_PUBLIC_CHAT_KEY', 'RIU_MCP_KEY', 'RIU_ROUTER_API_KEY'];
app.use((req, res, next) => {
  if (req.path !== '/v1/claves' && req.path !== '/v1/openclaw') return next();
  const validas = ACCESO_VARS.map(v => process.env[v]).filter(Boolean);
  if (!validas.length) return res.status(503).json({ error: { code: 'SIN_CLAVE_DE_ACCESO', message: 'el bridge no tiene clave de acceso configurada (RIU_API_KEY)' } });
  const k = String(req.headers['x-api-key'] || '');
  return k && validas.some(v => iguales(k, v)) ? next() : res.status(401).json({ error: { code: 'NO_AUTORIZADO', message: 'falta o es invalida la clave de acceso (x-api-key)' } });
});
app.use(express.json({ limit: '10mb' }));
const PORT = process.env.BRIDGE_PORT || 7860;

const esConsenso = (modo) => ['consulta', 'plan'].includes(modo);
const OBJETIVO_UNICO = process.env.SWECODE_OBJETIVO || 'qwen38max';
// fallback dentro de la web antes de escalar a modelos locales
const WEB_FALLBACK = (process.env.WEB_FALLBACK || 'qwen38max,qwen37max,dsv4-flash').split(',');

// deadline duro por request: nunca colgar >120s (proxy/cliente). Devuelve 504 JSON.
const DEADLINE_MS = parseInt(process.env.BRIDGE_DEADLINE_MS || '100000', 10);
function conDeadline(p, ms) {
  let t;
  const to = new Promise((_, rej) => { t = setTimeout(() => rej(Object.assign(new Error(`sin respuesta en ${ms}ms`), { code: 'UPSTREAM_TIMEOUT' })), ms); });
  return Promise.race([p, to]).finally(() => clearTimeout(t));
}

async function conFallback(modelo, prompt, opts) {
  const orden = [modelo, ...WEB_FALLBACK.filter(m => m !== modelo)];
  let ultimo;
  for (const m of orden) {
    try { return { salida: await consultarWeb(m, prompt, opts), usado: m }; }
    catch (e) { if (e.code === 'SESSION_EXPIRED' || e.code === 'CUENTAS_FALTAN') throw e; ultimo = e; }  // un fallo de sesion/cuentas no se disfraza con el error del ultimo modelo
  }
  throw ultimo;
}

app.get('/health', async (_req, res) => {
  let poolInfo;
  try {
    const n = pool().length;
    let idx = null; try { idx = cuentaActual().index; } catch {}
    poolInfo = { total: n, loaded: true, indices: [...Array(n).keys()], actual: idx };
  } catch { poolInfo = { total: 0, loaded: false, error: 'WEB_ACCOUNTS_VACIO' }; }
  res.json({ ok: true, pool: poolInfo, cuentas: sinCorreos(estadoCuentas()), respaldo: estadoRespaldo(), state_dir: process.env.BRIDGE_STATE_DIR || './state' });
});

app.get('/v1/queue', (_req, res) => {
  res.json({ ok: true, ...estadoTabs(), cuentas: sinCorreos(estadoCuentas()) });
});

// secciones (conv_id) con checkpoint: OpenClaw ve cuales retomar reenviando el mismo conv_id
app.get('/v1/secciones', (_req, res) => res.json({ ok: true, secciones: listarCheckpoints() }));

// asesorias guardadas por proyecto (un ASESORIA.md cada uno): OpenClaw las lee antes de ejecutar
app.get('/v1/proyectos', (_req, res) => res.json({ ok: true, proyectos: listarProyectos() }));
app.get('/v1/proyectos/:nombre', (req, res) => {
  const p = leerProyecto(req.params.nombre);
  p ? res.json({ ok: true, ...p }) : res.status(404).json({ ok: false, error: 'PROYECTO_NO_ENCONTRADO' });
});

// retomar una seccion a medias SIN que el cliente reenvie el texto: usa el texto y el modelo guardados en el checkpoint
async function retomarSeccion(id) {
  const ck = checkpointCrudo(id);
  if (!ck || ck.tipo === TIPO_LOCAL) {  // checkpoint de un modelo local HF / Groq / NVIDIA (retomar_local.js): puede estar solo en el Harness si el disco se perdio
    const l = await conDeadline(retomarPorId(id, { hasta: Date.now() + DEADLINE_MS * 0.8 }), DEADLINE_MS);
    if (l && l.yaCompleto) return { status: 409, error: { code: 'SECCION_YA_COMPLETA' } };
    if (l) return { status: 200, salida: l.salida, modelo: l.usado, local: l };
  }
  if (!ck || !ck.texto || !ck.modelo) return { status: 404, error: { code: 'SECCION_NO_ENCONTRADA' } };
  if (ck.completo || (ck.enviados >= ck.total)) return { status: 409, error: { code: 'SECCION_YA_COMPLETA' } };
  const salida = await conDeadline(consultarWeb(ck.modelo, ck.texto, { modo: ck.modo, convId: id }), DEADLINE_MS);
  return { status: 200, salida, modelo: ck.modelo };
}
app.post('/v1/secciones/:id/retomar', async (req, res) => {
  if (!/^[\w-]{1,80}$/.test(req.params.id)) return res.status(400).json({ error: { code: 'CONV_ID_INVALIDO' } });
  try {
    const r = await retomarSeccion(req.params.id);
    if (r.error) return res.status(r.status).json({ error: r.error });
    const l = r.local;
    res.json({ id: `retoma-${Date.now()}`, object: 'chat.completion', modelo_usado: r.modelo, ...(l ? { via_respaldo: l.via, tarea: { id: l.tarea_id, estado: l.estado, secciones: l.secciones } } : {}), choices: [{ index: 0, finish_reason: l ? l.finish_reason : 'stop', message: { role: 'assistant', content: r.salida || '', ...(l && l.tool_calls.length ? { tool_calls: l.tool_calls } : {}) } }] });
  } catch (e) { res.status(e.code === 'UPSTREAM_TIMEOUT' ? 504 : 502).json({ error: { code: e.code || 'BRIDGE_ERROR', message: String(e.message).slice(0, 200) } }); }
});

// auto-evolucion: mejoras propuestas por lo que el bridge reparo solo (OpenClaw las aplica con su commit)
app.get('/v1/evolucion', (_req, res) => res.json({ ok: true, propuestas: proponerMejoras() }));
// historial de una sesion/proyecto de OpenClaw, de la misma memoria del chat Yaiwes
app.get('/v1/memoria/:sesion', async (req, res) => {
  if (!process.env.HF_TOKEN) return res.status(503).json({ ok: false, error: { code: 'HF_TOKEN_FALTA', message: 'la memoria compartida necesita HF_TOKEN en el entorno del bridge' } });
  res.json({ ok: true, turnos: await leerTurnos(req.params.sesion) });
});

// claves de Groq/NVIDIA desde el panel del chat: SOLO conteos en las respuestas, jamas valores
const conteo = () => { const { groq, nvidia } = estadoRespaldo(); return { groq, nvidia }; };
const claveOk = (k) => typeof k === 'string' && k.length >= 8 && k.length <= 300 && !/\s/.test(k);
app.get('/v1/claves', (_req, res) => res.json({ ok: true, ...conteo() }));
app.post('/v1/claves', async (req, res) => {
  const b = req.body && typeof req.body === 'object' ? req.body : {}, nuevas = {};
  for (const prov of ['groq', 'nvidia']) {
    if (b[prov] === undefined) continue;
    const lista = Array.isArray(b[prov]) ? b[prov] : [b[prov]];
    if (lista.length > 20 || !lista.every(claveOk)) return res.status(400).json({ error: { code: 'CLAVE_INVALIDA', message: `${prov}: maximo 20 claves, cada una de 8 a 300 caracteres sin espacios ni saltos de linea` } });
    nuevas[prov] = b[prov];
  }
  if (!Object.keys(nuevas).length) return res.status(400).json({ error: { code: 'CLAVE_INVALIDA', message: 'envia groq y/o nvidia (string o lista de strings)' } });
  setClaves(nuevas);
  const persistido = await guardarEnBanco(nuevas).catch(() => false);
  if (persistido) await publicarEnGithub().catch(() => false);
  res.json({ ok: true, ...conteo(), persistido });
});
app.delete('/v1/claves', async (_req, res) => {
  limpiarClaves();
  const persistido = await borrarDelBanco().catch(() => false);
  if (persistido) await publicarEnGithub().catch(() => false);  // se publica el banco ya vacio
  res.json({ ok: true, ...conteo(), persistido });
});

const idsModelos = () => {
  const base = Object.keys(MODELOS_WEB).map(m => `web-${m}`);
  const modos = ['revision','solucion','arquitectura','archivos','prompt_code','consulta','despliega','asesoria'].map(m => `swecode-${m}`);
  return [...base, ...modos, ...idsRespaldo()];
};
app.get('/v1/models', (_req, res) => res.json({ object: 'list', data: idsModelos().map(id => ({ id, object: 'model' })) }));

// configuracion vigente de OpenClaw (providers, modelos, modos, workspace): solo lectura, sin secretos (conteos de claves, jamas valores)
app.get('/v1/openclaw', (_req, res) => {
  const c = configVigente();
  if (!c) return res.status(404).json({ ok: false, error: { code: 'CONFIG_NO_ENCONTRADA', message: 'falta SWE CODE free/provider-openclaw.json (RIU_OPENCLAW_DIR)' } });
  const ruta = rutaWorkspace();
  res.json({ ok: true, ...c, vivo: { modelos: idsModelos(), ...conteo() }, workspace: { ruta, existe: nodeFs.existsSync(ruta) }, espejo: espejo() });  // espejo de emergencia: catalogo del Router para OpenClaw (solo nombres)
});

// herramienta nativa: el agente la llama cuando ve SESSION_EXPIRED
app.post('/refresh_session', async (_req, res) => {
  try { const s = await salud(); res.json({ ok: true, sitios: s }); }
  catch (e) { res.status(503).json({ ok: false, error: e.code || e.message }); }
});

// SSE (stream:true): la respuesta se calcula completa y se emite como chat.completion.chunk (role -> content en trozos -> tool_calls -> finish_reason -> [DONE]).
// Mientras se espera, cada SSE_KEEPALIVE_MS se abre el stream y se envia ": keepalive" para que ningun proxy corte la conexion; antes de abrirlo los errores siguen siendo JSON.
const SSE_KEEPALIVE_MS = parseInt(process.env.BRIDGE_SSE_KEEPALIVE_MS || '15000', 10), SSE_TROZO = 200;
function trozosDe(texto, max = SSE_TROZO) {
  const t = String(texto || ''), out = [];
  for (let i = 0; i < t.length;) {
    let f = Math.min(i + max, t.length);
    const c = t.charCodeAt(f - 1);
    if (f < t.length && c >= 0xD800 && c <= 0xDBFF) f--;  // no partir un par sustituto (emoji)
    out.push(t.slice(i, f)); i = f;
  }
  return out;
}
function crearSse(req, res) {
  const pide = !!req.body && req.body.stream === true;
  const s = { pide, activo: false, id: `webchat-${Date.now()}`, created: Math.floor(Date.now() / 1000), model: `swecode:${pide ? req.body.model : ''}`, extra: {}, timer: null };
  s.abrir = () => { if (!s.activo && !res.headersSent) { s.activo = true; res.writeHead(200, { 'content-type': 'text/event-stream; charset=utf-8', 'cache-control': 'no-cache', connection: 'keep-alive' }); } };
  s.vigilar = () => { if (pide && !s.timer) { s.timer = setInterval(() => { s.abrir(); if (s.activo) res.write(': keepalive\n\n'); }, SSE_KEEPALIVE_MS); res.on('close', s.parar); } };
  s.parar = () => { clearInterval(s.timer); s.timer = null; };
  s.chunk = (delta, finish_reason = null, extra = {}) => res.write(`data: ${JSON.stringify({ id: s.id, object: 'chat.completion.chunk', created: s.created, model: s.model, ...s.extra, choices: [{ index: 0, delta, finish_reason }], ...extra })}\n\n`);
  s.error = (code, message, detail) => { s.abrir(); s.chunk({}, 'error', { error: { code, message, detail } }); res.end('data: [DONE]\n\n'); };
  return s;
}

app.post('/v1/chat/completions', async (req, res) => {
  const sse = crearSse(req, res);
  try {
    let { model = 'swecode-consulta', messages: mensajesIn = [], modo, conv_id, proyecto, documentos, cuentas, clave: claveReq, claves: clavesReq } = req.body;
    if (typeof model !== 'string' || !/^[\w.\/:-]{1,100}$/.test(model)) return res.status(400).json({ error: { code: 'MODELO_INVALIDO', model: String(model).slice(0, 50) } });
    if (!Array.isArray(mensajesIn)) return res.status(400).json({ error: { code: 'MENSAJES_INVALIDOS', message: 'messages debe ser una lista' } });
    mensajesIn = mensajesIn.filter(m => m && typeof m === 'object').map(m => ({ ...m, content: textoDe(m.content) }));
    const iUlt = mensajesIn.map(m => m.role).lastIndexOf('user');
    const act = activar && iUlt >= 0 ? activar(mensajesIn[iUlt].content) : null;
    if (act && act.error) return res.status(400).json({ error: { code: 'ACTIVACION_INVALIDA', message: act.error } });
    if (act) {  // "SWEN CODE free [modo m] [solo modelo] [chat n] texto": el mensaje manda sobre el modelo/modo/seccion del POST
      model = act.modelo === 'consenso' ? `swecode-${act.modo}` : (IDS_DIRECTOS(act.modelo) ? act.modelo : model);
      if (act.modo === 'asesoria') model = 'swecode-asesoria';  // la asesoria por gramatica tambien va primero a Groq
      modo = act.modo; conv_id = act.conv_id || conv_id;
      mensajesIn = mensajesIn.map((m, i) => (i === iUlt ? { ...m, content: act.prompt } : m));
    }
    if (conv_id != null && !/^[\w-]{1,80}$/.test(String(conv_id))) return res.status(400).json({ error: { code: 'CONV_ID_INVALIDO', message: 'conv_id: letras, numeros, - y _ (max 80)' } });
    if (model.startsWith('web-') && !MODELOS_WEB[model.slice(4)]) return res.status(400).json({ error: { code: 'MODELO_INVALIDO', model } });
    if (Array.isArray(documentos) && documentos.length > MAX_DOCS) return res.status(413).json({ error: { code: 'DEMASIADOS_DOCUMENTOS', max: MAX_DOCS } });
    const messages = conFormato(mensajesIn);  // formato de salida del chat Yaiwes tambien para OpenClaw
    // credenciales vienen de OpenClaw por llamada (vía plugins->harness); env solo respaldo
    if (cuentas) setCuentas(cuentas, claveReq);
    if (clavesReq && typeof clavesReq === 'object') { setClaves(clavesReq); guardarEnBanco(clavesReq).then((ok) => ok && publicarEnGithub()).catch(() => {}); }  // claves de Groq/NVIDIA por llamada: en memoria y en el banco propio cifrado (sobreviven reinicios)
    const iU = messages.map(m => m.role).lastIndexOf('user');
    const ultimo = iU >= 0 ? messages[iU].content : '';
    const anterior = messages.filter((m, i) => i !== iU).map(m => `${m.role}: ${m.content}`).join('\n');
    let prompt = anterior ? `${anterior}\nuser: ${ultimo}` : ultimo;
    // documentos: [{nombre, contenido}] o strings — se incrustan al prompt y tambien llegan a Groq/NVIDIA/locales como mensaje
    const docs = (Array.isArray(documentos) ? documentos : [])
      .map(d => typeof d === 'string' ? { nombre: 'doc', contenido: d } : d)
      .filter(d => d && d.contenido)
      .map(d => `[DOCUMENTO: ${d.nombre || 'doc'}]\n${String(d.contenido).slice(0, 100000)}`)
      .join('\n\n');
    if (docs) prompt = `${prompt}\n\n${docs}`;
    if (prompt.length > MAX_PROMPT) return res.status(413).json({ error: { code: 'PROMPT_DEMASIADO_GRANDE', max: MAX_PROMPT } });
    const mensajesM = docs ? [...messages, { role: 'user', content: docs }] : messages;

    let modeloWeb, modoUso = modo || 'consulta', salida, usado = model;
    if (model.startsWith('web-')) {
      modeloWeb = model.slice(4);
    } else if (model.startsWith('swecode-')) {
      modoUso = model.slice(8);
      if (!modoValido(modoUso)) return res.status(400).json({ error: { code: 'MODO_INVALIDO', modo: modoUso } });
    } else if (!esExterno(model) && !esLocal(model)) {
      return res.status(400).json({ error: { code: 'MODELO_INVALIDO', model } });
    }
    let via = null, aviso = null, viaPrimaria = null, llamadas = [], fin = 'stop', tarea = null;
    // tarea_id (cuerpo o cabecera x-tarea-id): modelos locales/Groq/NVIDIA con checkpoint universal (retomar_local.js); sin tarea_id nada cambia
    const tareaId = req.body.tarea_id != null ? req.body.tarea_id : req.headers['x-tarea-id'];
    const usaTarea = tareaId != null && tareaId !== '' && (esExterno(model) || esLocal(model));
    if (usaTarea && !tareaIdValido(String(tareaId))) return res.status(400).json({ error: { code: 'TAREA_ID_INVALIDO', message: 'tarea_id: letras, numeros, - y _ (max 64)' } });
    const extra = { tools: Array.isArray(req.body.tools) ? req.body.tools : undefined, tool_choice: req.body.tool_choice };  // groq/nvidia/locales ejecutan tools: el Harness las corre

    const ejecutar = async () => {
    if (usaTarea) {
      const r = await retomarLocal(String(tareaId), model, conPreambulo(mensajesM, modo), { ...extra, hasta: Date.now() + DEADLINE_MS * 0.8 }); salida = r.salida; usado = r.usado || model; via = r.via; llamadas = r.tool_calls || []; fin = r.finish_reason || 'stop';
      tarea = { id: r.tarea_id, estado: r.estado, secciones: r.secciones, reanudado: r.reanudado, desde_checkpoint: r.desde_checkpoint };
    } else if (esExterno(model)) {
      const r = await externo(model, conPreambulo(mensajesM, modo), { extra }); salida = r.salida; usado = r.usado; via = r.via; llamadas = r.tool_calls || []; fin = r.finish_reason || 'stop';
    } else if (esLocal(model)) {
      const r = await local(model, conPreambulo(mensajesM, modo), { extra }); salida = r.salida; usado = r.usado; via = r.via; llamadas = r.tool_calls || []; fin = r.finish_reason || 'stop';
    } else if (modeloWeb) {
      const r = await conFallback(modeloWeb, prompt, { modo: modoUso, convId: conv_id });
      salida = r.salida; usado = r.usado;
    } else if (modoUso === 'asesoria') {
      // asesoria previa a ejecutar: primero Groq (las claves del chat Yaiwes), si no responde la web de SWE CODE free
      try {
        const r = await externo(`groq/${process.env.RIU_SWE_GROQ_MODELO || 'llama-3.3-70b-versatile'}`, [{ role: 'system', content: preambulo('asesoria') }, ...mensajesM]);
        salida = r.salida; usado = r.usado; viaPrimaria = 'groq';
      } catch {
        const r = await conFallback(OBJETIVO_UNICO, prompt, { modo: modoUso, convId: conv_id });
        salida = r.salida; usado = r.usado;
      }
    } else if (esConsenso(modoUso)) {
      const r = await consenso(prompt, { modo: modoUso, convId: conv_id });
      salida = r.final; usado = 'consenso';
      if (!res.headersSent) res.setHeader('x-consenso-detalle', Buffer.from(JSON.stringify(r.por_modelo)).toString('base64').slice(0, 4000));
    } else {
      const r = await conFallback(OBJETIVO_UNICO, prompt, { modo: modoUso, convId: conv_id });
      salida = r.salida; usado = r.usado;
    }
    };
    sse.vigilar();
    try {
      await conDeadline(ejecutar(), DEADLINE_MS);
      if ((!salida || !String(salida).trim()) && !llamadas.length) throw Object.assign(new Error('respuesta vacia del modelo web'), { code: 'EMPTY_RESPONSE' });
    } catch (e) {
      if (e.code === 'MODO_INVALIDO' || usaTarea) throw e;  // con tarea_id retomarLocal ya probo local/Groq/NVIDIA y guardo el checkpoint: el cliente reintenta con el mismo tarea_id
      if (e.code === 'UPSTREAM_TIMEOUT' && conv_id) await cerrarPagina(conv_id).catch(() => {});  // la tab colgada liberaba su slot solo al cerrarse
      // auto-reparacion: sesion caida -> re-login/rotacion de correo y UN reintento; si sigue mal, respaldo Groq -> NVIDIA -> HF local
      if (e.code === 'SESSION_EXPIRED') {
        try { await salud(); salida = null; await conDeadline(ejecutar(), 50000); registrarLeccion({ codigo: 'SESSION_EXPIRED', accion: 'salud() + reintento', resultado: 'PASS', modelo: model }); } catch { registrarLeccion({ codigo: 'SESSION_EXPIRED', accion: 'salud() + reintento', resultado: 'FAIL', modelo: model }); }
      }
      if ((!salida || !String(salida).trim()) && !llamadas.length) {
        const r = await respaldo(conPreambulo(mensajesM, model.startsWith('swecode-') ? modoUso : modo), { extra });
        llamadas = r.tool_calls || []; fin = r.finish_reason || 'stop';
        salida = r.salida; usado = r.usado; via = r.via; aviso = e.code || null;
        registrarLeccion({ codigo: e.code || 'WEB_FALLO', accion: 'respaldo ' + r.via, resultado: 'PASS', modelo: model });  // p. ej. CUENTAS_FALTAN: OpenClaw sabe que debe reenviar cuentas y clave
      }
    }
    let archivo = null;
    if (modoUso === 'asesoria') { try { archivo = guardarAsesoria(proyecto || conv_id, { texto: salida, via: via || viaPrimaria || 'web', modelo: usado }); } catch { /* guardar es mejor esfuerzo */ } }
    if (proyecto || conv_id) guardarTurno(proyecto || conv_id, ultimo, salida, usado).catch(() => {});  // misma memoria del chat Yaiwes (mejor esfuerzo)
    if (!res.headersSent) { res.setHeader('x-modelo-usado', usado); if (via) res.setHeader('x-via-respaldo', via); }

    if (sse.pide) {  // OpenClaw (openai-completions) pide SSE: la respuesta ya esta completa, se emite como chunks estandar + [DONE]
      sse.parar(); sse.model = `swecode:${model}`; sse.extra = { modelo_usado: usado, via_respaldo: via, ...(tarea ? { tarea } : {}) };
      sse.abrir();
      sse.chunk({ role: 'assistant', content: '' });
      for (const t of trozosDe(salida)) sse.chunk({ content: t });
      if (llamadas.length) sse.chunk({ tool_calls: llamadas.map((t, i) => ({ index: i, ...t })) });
      sse.chunk({}, fin);
      return res.end('data: [DONE]\n\n');
    }
    res.json({
      id: `webchat-${Date.now()}`, object: 'chat.completion', created: Math.floor(Date.now()/1000),
      model: `swecode:${model}`, modelo_usado: usado, via_respaldo: via, via_primaria: viaPrimaria, aviso, archivo, ...(tarea ? { tarea } : {}),
      choices: [{ index: 0, finish_reason: fin, message: { role: 'assistant', content: salida || '', ...(llamadas.length ? { tool_calls: llamadas } : {}) } }],
      usage: { prompt_tokens: 0, completion_tokens: 0, total_tokens: 0 },
    });
  } catch (e) {
    const code = e.code || 'BRIDGE_ERROR';
    sse.parar();
    if (sse.activo) return res.writableEnded ? undefined : sse.error(code, e.message, e.detail);  // error tras abrir el stream: chunk con el error + [DONE]
    if (res.headersSent) return;
    const st = code === 'SESSION_EXPIRED' ? 503 : code === 'UPSTREAM_TIMEOUT' ? 504 : code === 'EMPTY_RESPONSE' ? 502 : ['CHECKPOINT_OTRA_TAREA', 'VERIFICAR_HERRAMIENTAS_PENDIENTES'].includes(code) ? 409 : 500;
    res.status(st).json({ error: { code, message: e.message, detail: e.detail } });
  }
});


// Diagnóstico (Centinela): GET /debug/tab?conv_id=&shot=0|1 → url, title, screenshot_png_base64
// Acceso vía proxy: GET /web/debug/tab (sin cambiar proxy.py)
app.get('/debug/tab', async (req, res) => {
  try {
    const convId = req.query.conv_id || null;
    const shot = String(req.query.shot ?? '1') !== '0';
    const out = await snapshotTab(convId, { shot });
    if (out.ok === false) return res.status(404).json(out);
    res.json(out);
  } catch (e) {
    res.status(500).json({ ok: false, error: e.message });
  }
});

// errores de express (JSON malformado, body enorme): siempre JSON tipado
app.use((err, _req, res, _next) => res.status(err.status || 400).json({ error: { code: err.type === 'entity.too.large' ? 'BODY_DEMASIADO_GRANDE' : 'BAD_REQUEST', message: String(err.message || err).slice(0, 200) } }));

// cierre limpio: sin esto un reinicio del Space deja el perfil de Chromium bloqueado
for (const sig of ['SIGTERM', 'SIGINT']) process.on(sig, async () => { try { await cerrarTodo(); } catch { /* sigue */ } process.exit(0); });

// BRIDGE_AUTORETOMAR=1: al arrancar, retoma una a una las secciones que quedaron a medias (si hay cuentas en el entorno)
if (process.env.BRIDGE_AUTORETOMAR === '1') {
  setTimeout(async () => {
    for (const sec of listarCheckpoints().filter(c => !c.completo)) {
      try { await retomarSeccion(sec.conv_id); registrarLeccion({ codigo: 'REINICIO', accion: 'retoma automatica ' + sec.conv_id, resultado: 'PASS' }); }
      catch { registrarLeccion({ codigo: 'REINICIO', accion: 'retoma automatica ' + sec.conv_id, resultado: 'FAIL' }); }
    }
  }, 3000);
}

// auto-reparacion de cableado de OpenClaw: openclaw.sh borra su home en cada arranque y no recrea el workspace del agente
if (process.env.OPENCLAW_ENABLE === '1' || process.env.BRIDGE_REPARAR_OPENCLAW === '1') vigilarWorkspace();

// el bridge se actualiza solo cuando llega codigo nuevo de SWE CODE / SWE CODE free (sin reiniciar el Space); BRIDGE_AUTOACTUALIZAR=0 lo apaga
vigilarActualizacion();
vigilarBanco();  // y cada 60 s
vigilarConfig();  // config de OpenClaw (GET /v1/openclaw) al dia cada 60 s
traerDeGithub().catch(() => false).then(() => cargarDelBanco()).then((n) => { if (n) console.warn(`[bridge] ${n} clave(s) de Groq/NVIDIA cargadas del banco`); }).catch(() => {});  // puente al banco: Router MVP (solo lectura) + banco propio

app.listen(PORT, () => console.log(`web-bridge escuchando :${PORT}`));
