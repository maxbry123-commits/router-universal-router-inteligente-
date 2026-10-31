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
import { vigilarWorkspace } from './openclaw.js';
import { respaldo, externo, local, esExterno, esLocal, idsRespaldo, estadoRespaldo, setClaves } from './respaldo.js';
import { listarCheckpoints, registrarLeccion, proponerMejoras, checkpointCrudo } from './bloques.js';
import { conFormato } from './formato.js';
import { guardarTurno, leerTurnos } from './memoria.js';
import { vigilarActualizacion } from './autoactualizar.js';
import { cargarDelBanco, guardarEnBanco, vigilarBanco } from './clavesbanco.js';
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
    res.json({ id: `retoma-${Date.now()}`, object: 'chat.completion', modelo_usado: r.modelo, choices: [{ index: 0, finish_reason: 'stop', message: { role: 'assistant', content: r.salida || '' } }] });
  } catch (e) { res.status(e.code === 'UPSTREAM_TIMEOUT' ? 504 : 502).json({ error: { code: e.code || 'BRIDGE_ERROR', message: String(e.message).slice(0, 200) } }); }
});

// auto-evolucion: mejoras propuestas por lo que el bridge reparo solo (OpenClaw las aplica con su commit)
app.get('/v1/evolucion', (_req, res) => res.json({ ok: true, propuestas: proponerMejoras() }));
// historial de una sesion/proyecto de OpenClaw, de la misma memoria del chat Yaiwes
app.get('/v1/memoria/:sesion', async (req, res) => {
  if (!process.env.HF_TOKEN) return res.status(503).json({ ok: false, error: { code: 'HF_TOKEN_FALTA', message: 'la memoria compartida necesita HF_TOKEN en el entorno del bridge' } });
  res.json({ ok: true, turnos: await leerTurnos(req.params.sesion) });
});

app.get('/v1/models', (_req, res) => {
  const base = Object.keys(MODELOS_WEB).map(m => `web-${m}`);
  const modos = ['revision','solucion','arquitectura','archivos','prompt_code','consulta','despliega','asesoria'].map(m => `swecode-${m}`);
  res.json({ object: 'list', data: [...base, ...modos, ...idsRespaldo()].map(id => ({ id, object: 'model' })) });
});

// herramienta nativa: el agente la llama cuando ve SESSION_EXPIRED
app.post('/refresh_session', async (_req, res) => {
  try { const s = await salud(); res.json({ ok: true, sitios: s }); }
  catch (e) { res.status(503).json({ ok: false, error: e.code || e.message }); }
});

app.post('/v1/chat/completions', async (req, res) => {
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
    let via = null, aviso = null, viaPrimaria = null, llamadas = [], fin = 'stop';
    const extra = { tools: Array.isArray(req.body.tools) ? req.body.tools : undefined, tool_choice: req.body.tool_choice };  // groq/nvidia/locales ejecutan tools: el Harness las corre

    const ejecutar = async () => {
    if (esExterno(model)) {
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
      res.setHeader('x-consenso-detalle', Buffer.from(JSON.stringify(r.por_modelo)).toString('base64').slice(0, 4000));
    } else {
      const r = await conFallback(OBJETIVO_UNICO, prompt, { modo: modoUso, convId: conv_id });
      salida = r.salida; usado = r.usado;
    }
    };
    try {
      await conDeadline(ejecutar(), DEADLINE_MS);
      if ((!salida || !String(salida).trim()) && !llamadas.length) throw Object.assign(new Error('respuesta vacia del modelo web'), { code: 'EMPTY_RESPONSE' });
    } catch (e) {
      if (e.code === 'MODO_INVALIDO') throw e;
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
    res.setHeader('x-modelo-usado', usado);
    if (via) res.setHeader('x-via-respaldo', via);

    res.json({
      id: `webchat-${Date.now()}`, object: 'chat.completion', created: Math.floor(Date.now()/1000),
      model: `swecode:${model}`, modelo_usado: usado, via_respaldo: via, via_primaria: viaPrimaria, aviso, archivo,
      choices: [{ index: 0, finish_reason: fin, message: { role: 'assistant', content: salida || '', ...(llamadas.length ? { tool_calls: llamadas } : {}) } }],
      usage: { prompt_tokens: 0, completion_tokens: 0, total_tokens: 0 },
    });
  } catch (e) {
    const code = e.code || 'BRIDGE_ERROR';
    if (res.headersSent) return;
    const st = code === 'SESSION_EXPIRED' ? 503 : code === 'UPSTREAM_TIMEOUT' ? 504 : code === 'EMPTY_RESPONSE' ? 502 : 500;
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
traerDeGithub().catch(() => false).then(() => cargarDelBanco()).then((n) => { if (n) console.warn(`[bridge] ${n} clave(s) de Groq/NVIDIA cargadas del banco`); }).catch(() => {});  // puente al banco: Router MVP (solo lectura) + banco propio

app.listen(PORT, () => console.log(`web-bridge escuchando :${PORT}`));
