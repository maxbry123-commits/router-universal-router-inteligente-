// Puente del chat = papel del harness DeepSeek para la UI (Vercel). Probado 2026-10-04.
// Copiar este archivo a la carpeta api/ del proyecto del chat en Vercel. harnessUrl = '/api/chat' (mismo dominio: sin CORS).
// Los tokens viven SOLO en variables de entorno del servidor (nunca en config.js ni en el navegador).
// Variables: RIU_ROUTER_URL (opcional), FICHA_KIMI_TOKEN, FICHA_GLM_TOKEN, FICHA_NEMOTRON_TOKEN, FICHA_GROQ_TOKEN, FICHA_LIGHTNING_TOKEN
//
// GET  /api/chat?accion=modelos                      -> lista para el selector
// POST /api/chat {model, messages, max_tokens}       -> modelos de ficha: respuesta tipo OpenAI
// Modelos hf-1/hf-2: L4/HF Jobs RETIRADO (2026-10-16) -> GAP_NO_EXECUTOR, sin fallback silencioso.
const PUERTA = process.env.RIU_ROUTER_URL || 'https://comand-center-1-claude-github-mcp-backup.hf.space';
const FICHAS = {
  'nv-kimi-k3': ['NV Kimi K3', 'FICHA_KIMI_TOKEN'],
  'nv-glm-5-3': ['NV GLM 5.3', 'FICHA_GLM_TOKEN'],
  'nv-nemotron-super': ['NV Nemotron 3 Super', 'FICHA_NEMOTRON_TOKEN'],
  'nv-nemotron-lightning': ['NV Nemotron 3.5 Lightning', 'FICHA_LIGHTNING_TOKEN'],
  'groq-qwen-3-8': ['GROQ Qwen 3.8', 'FICHA_GROQ_TOKEN'],
};
// Identidad conservada (las fichas/selector la referencian) pero sin ejecutor: jamas se lanza un Job.
const RESPALDO = {
  'hf-1-qwen-3-8': ['HF 1 Qwen 3.8 (27B)', 'Qwen3.8-27B-UD-Q3_K_XL.gguf'],
  'hf-2-qwen-3-6': ['HF 2 Qwen 3.6 (35B)', 'Qwen3.6-35B-A3B-UD-Q3_K_XL.gguf'],
};

module.exports = async function handler(req, res) {
  try {
    const q = req.query || {};
    const accion = q.accion;
    if (req.method === 'GET' && accion === 'modelos') {
      const lista = [...Object.entries(FICHAS), ...Object.entries(RESPALDO)].map(([id, v]) => ({ id, nombre: v[0], respaldo: false, gap: id in RESPALDO ? 'GAP_NO_EXECUTOR' : undefined }));
      return res.status(200).json({ modelos: lista });
    }
    if (accion === 'estado' || accion === 'apagar' || accion === 'apagar_todo') {
      return res.status(410).json({ error: 'L4_RETIRADO: ya no hay Jobs L4 que consultar ni apagar' });
    }
    if (req.method !== 'POST') return res.status(405).json({ error: 'usa POST' });
    const b = typeof req.body === 'string' ? JSON.parse(req.body) : (req.body || {});
    const model = b.model;
    const cuerpo = { messages: b.messages || [], max_tokens: b.max_tokens || 2048 };
    if (model in FICHAS) {
      const token = process.env[FICHAS[model][1]];
      const r = await fetch(PUERTA + '/v1/router/chat/completions', { method: 'POST', headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' }, body: JSON.stringify({ model: 'auto', ...cuerpo }) });
      return res.status(r.status).json(await r.json());
    }
    if (model in RESPALDO) {
      return res.status(501).json({ error: 'GAP_NO_EXECUTOR', detalle: 'modelo HF sin ejecutor: L4/HF Jobs retirados del Router', model });
    }
    return res.status(400).json({ error: 'modelo desconocido', validos: [...Object.keys(FICHAS), ...Object.keys(RESPALDO)] });
  } catch (e) {
    return res.status(500).json({ error: String(e).slice(0, 300) });
  }
};
