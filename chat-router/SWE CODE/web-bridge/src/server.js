// server.js — endpoint OpenAI-compatible del puente web (SWEN CODE free)
// POST /v1/chat/completions {model, messages, modo?, conv_id?}
//   model: web-dsv4-flash | web-qwen37max | web-qwen38max | swecode-<modo>
//   swecode-consulta/plan -> fan-out 3 modelos + sintesis Qwen3.8Max
//   otros modos -> objetivo unico (qwen38max por defecto)
// Errores tipados: SESSION_EXPIRED | SELECTOR_BROKEN | CF_CHALLENGE | RATE_LIMITED
import express from 'express';
import { consultarWeb, salud } from './motor.js';
import { consenso } from './consenso.js';
import { modoValido } from './modos.js';
import { estadoCuentas, estadoTabs, snapshotTab } from './browser.js';
import { MODELOS_WEB } from './sites.js';
import { pool, cuentaActual, setCuentas } from './cuentas.js';
import { respaldo, externo, local, esExterno, esLocal, idsRespaldo } from './respaldo.js';
import { listarCheckpoints } from './bloques.js';

const app = express();
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
    catch (e) { ultimo = e; }
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
  res.json({ ok: true, pool: poolInfo, cuentas: estadoCuentas() });
});

app.get('/v1/queue', (_req, res) => {
  res.json({ ok: true, ...estadoTabs(), cuentas: estadoCuentas() });
});

// secciones (conv_id) con checkpoint: OpenClaw ve cuales retomar reenviando el mismo conv_id
app.get('/v1/secciones', (_req, res) => res.json({ ok: true, secciones: listarCheckpoints() }));

app.get('/v1/models', (_req, res) => {
  const base = Object.keys(MODELOS_WEB).map(m => `web-${m}`);
  const modos = ['revision','solucion','arquitectura','archivos','prompt_code','consulta','despliega'].map(m => `swecode-${m}`);
  res.json({ object: 'list', data: [...base, ...modos, ...idsRespaldo()].map(id => ({ id, object: 'model' })) });
});

// herramienta nativa: el agente la llama cuando ve SESSION_EXPIRED
app.post('/refresh_session', async (_req, res) => {
  try { const s = await salud(); res.json({ ok: true, sitios: s }); }
  catch (e) { res.status(503).json({ ok: false, error: e.code || e.message }); }
});

app.post('/v1/chat/completions', async (req, res) => {
  try {
    const { model = 'swecode-consulta', messages = [], modo, conv_id, documentos, cuentas, clave: claveReq } = req.body;
    // credenciales vienen de OpenClaw por llamada (vía plugins->harness); env solo respaldo
    if (cuentas) setCuentas(cuentas, claveReq);
    const ultimo = [...messages].reverse().find(m => m.role === 'user')?.content || '';
    const anterior = messages.filter(m => m.role !== 'user' || m !== messages[messages.length-1])
      .map(m => `${m.role}: ${m.content}`).join('\n');
    let prompt = anterior ? `${anterior}\nuser: ${ultimo}` : ultimo;
    // documentos: [{nombre, contenido}] o strings — se incrustan al prompt del modelo
    const docs = (Array.isArray(documentos) ? documentos : [])
      .map(d => typeof d === 'string' ? { nombre: 'doc', contenido: d } : d)
      .filter(d => d && d.contenido)
      .map(d => `[DOCUMENTO: ${d.nombre || 'doc'}]\n${String(d.contenido).slice(0, 100000)}`)
      .join('\n\n');
    if (docs) prompt = `${prompt}\n\n${docs}`;

    let modeloWeb, modoUso = modo || 'consulta', salida, usado = model;
    if (model.startsWith('web-')) {
      modeloWeb = model.slice(4);
    } else if (model.startsWith('swecode-')) {
      modoUso = model.slice(8);
      if (!modoValido(modoUso)) return res.status(400).json({ error: { code: 'MODO_INVALIDO', modo: modoUso } });
    } else if (!esExterno(model) && !esLocal(model)) {
      return res.status(400).json({ error: { code: 'MODELO_INVALIDO', model } });
    }
    let via = null;

    const ejecutar = async () => {
    if (esExterno(model)) {
      const r = await externo(model, messages); salida = r.salida; usado = r.usado; via = r.via;
    } else if (esLocal(model)) {
      const r = await local(model, messages); salida = r.salida; usado = r.usado; via = r.via;
    } else if (modeloWeb) {
      const r = await conFallback(modeloWeb, prompt, { modo: modoUso, convId: conv_id });
      salida = r.salida; usado = r.usado;
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
      if (!salida || !String(salida).trim()) throw Object.assign(new Error('respuesta vacia del modelo web'), { code: 'EMPTY_RESPONSE' });
    } catch (e) {
      if (e.code === 'MODO_INVALIDO') throw e;
      // auto-reparacion: sesion caida -> re-login/rotacion de correo y UN reintento; si sigue mal, respaldo Groq -> NVIDIA -> HF local
      if (e.code === 'SESSION_EXPIRED') {
        try { await salud(); salida = null; await conDeadline(ejecutar(), 50000); } catch { /* sigue al respaldo */ }
      }
      if (!salida || !String(salida).trim()) {
        const r = await respaldo(messages);
        salida = r.salida; usado = r.usado; via = r.via;
      }
    }
    res.setHeader('x-modelo-usado', usado);
    if (via) res.setHeader('x-via-respaldo', via);

    res.json({
      id: `webchat-${Date.now()}`, object: 'chat.completion', created: Math.floor(Date.now()/1000),
      model: `swecode:${model}`, modelo_usado: usado, via_respaldo: via,
      choices: [{ index: 0, finish_reason: 'stop', message: { role: 'assistant', content: salida || '' } }],
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

app.listen(PORT, () => console.log(`web-bridge escuchando :${PORT}`));
