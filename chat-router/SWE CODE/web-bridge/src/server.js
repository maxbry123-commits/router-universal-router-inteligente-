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

const app = express();
app.use(express.json({ limit: '10mb' }));
const PORT = process.env.BRIDGE_PORT || 7860;

const esConsenso = (modo) => ['consulta', 'plan'].includes(modo);
const OBJETIVO_UNICO = process.env.SWECODE_OBJETIVO || 'qwen38max';
// fallback dentro de la web antes de escalar a modelos locales
const WEB_FALLBACK = (process.env.WEB_FALLBACK || 'qwen38max,qwen37max,dsv4-flash').split(',');

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
  res.json({ ok: true, cuentas: estadoCuentas() });
});

app.get('/v1/queue', (_req, res) => {
  res.json({ ok: true, ...estadoTabs(), cuentas: estadoCuentas() });
});

app.get('/v1/models', (_req, res) => {
  const base = Object.keys(MODELOS_WEB).map(m => `web-${m}`);
  const modos = ['revision','solucion','arquitectura','archivos','prompt_code','consulta','despliega'].map(m => `swecode-${m}`);
  res.json({ object: 'list', data: [...base, ...modos].map(id => ({ id, object: 'model' })) });
});

// herramienta nativa: el agente la llama cuando ve SESSION_EXPIRED
app.post('/refresh_session', async (_req, res) => {
  try { const s = await salud(); res.json({ ok: true, sitios: s }); }
  catch (e) { res.status(503).json({ ok: false, error: e.code || e.message }); }
});

app.post('/v1/chat/completions', async (req, res) => {
  try {
    const { model = 'swecode-consulta', messages = [], modo, conv_id } = req.body;
    const ultimo = [...messages].reverse().find(m => m.role === 'user')?.content || '';
    const anterior = messages.filter(m => m.role !== 'user' || m !== messages[messages.length-1])
      .map(m => `${m.role}: ${m.content}`).join('\n');
    const prompt = anterior ? `${anterior}\nuser: ${ultimo}` : ultimo;

    let modeloWeb, modoUso = modo || 'consulta', salida, usado = model;
    if (model.startsWith('web-')) {
      modeloWeb = model.slice(4);
    } else if (model.startsWith('swecode-')) {
      modoUso = model.slice(8);
      if (!modoValido(modoUso)) return res.status(400).json({ error: { code: 'MODO_INVALIDO', modo: modoUso } });
    } else {
      return res.status(400).json({ error: { code: 'MODELO_INVALIDO', model } });
    }

    if (modeloWeb) {
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
    res.setHeader('x-modelo-usado', usado);

    res.json({
      id: `webchat-${Date.now()}`, object: 'chat.completion', created: Math.floor(Date.now()/1000),
      model: `swecode:${model}`, modelo_usado: usado,
      choices: [{ index: 0, finish_reason: 'stop', message: { role: 'assistant', content: salida || '' } }],
      usage: { prompt_tokens: 0, completion_tokens: 0, total_tokens: 0 },
    });
  } catch (e) {
    const code = e.code || 'BRIDGE_ERROR';
    res.status(code === 'SESSION_EXPIRED' ? 503 : 500).json({ error: { code, message: e.message, detail: e.detail } });
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
