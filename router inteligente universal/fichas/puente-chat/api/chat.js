// Puente del chat = papel del harness DeepSeek para la UI (Vercel). Probado 2026-10-04.
// Copiar este archivo a la carpeta api/ del proyecto del chat en Vercel. harnessUrl = '/api/chat' (mismo dominio: sin CORS).
// Los tokens viven SOLO en variables de entorno del servidor (nunca en config.js ni en el navegador).
// Variables: RIU_ROUTER_URL (opcional), FICHA_KIMI_TOKEN, FICHA_GLM_TOKEN, FICHA_NEMOTRON_TOKEN, FICHA_GROQ_TOKEN, FICHA_LIGHTNING_TOKEN, HF_TOKEN
//
// GET  /api/chat?accion=modelos                      -> lista para el selector
// POST /api/chat {model, messages, max_tokens}       -> modelos de ficha: respuesta tipo OpenAI
//      respaldo (hf-1/hf-2) sin respaldo_url        -> 202 {estado:'encendiendo', job_id, url}   (enciende el L4)
//      respaldo con {respaldo_url}                   -> respuesta tipo OpenAI del L4
// GET  /api/chat?accion=estado&job=<id>&url=<url>    -> {etapa, listo}
// POST /api/chat?accion=apagar&job=<id>              -> boton de apagado remoto
const PUERTA = process.env.RIU_ROUTER_URL || 'https://comand-center-1-claude-github-mcp-backup.hf.space';
const NS = 'COMAND-CENTER-1';
const FICHAS = {
  'nv-kimi-k3': ['NV Kimi K3', 'FICHA_KIMI_TOKEN'],
  'nv-glm-5-3': ['NV GLM 5.3', 'FICHA_GLM_TOKEN'],
  'nv-nemotron-super': ['NV Nemotron 3 Super', 'FICHA_NEMOTRON_TOKEN'],
  'nv-nemotron-lightning': ['NV Nemotron 3.5 Lightning', 'FICHA_LIGHTNING_TOKEN'],
  'groq-qwen-3-8': ['GROQ Qwen 3.8', 'FICHA_GROQ_TOKEN'],
};
const RESPALDO = {
  'hf-1-qwen-3-8': ['HF 1 Qwen 3.8 (27B)', 'Qwen3.8-27B-UD-Q3_K_XL.gguf'],
  'hf-2-qwen-3-6': ['HF 2 Qwen 3.6 (35B)', 'Qwen3.6-35B-A3B-UD-Q3_K_XL.gguf'],
};
const ARRANQUE = '/app/llama-server --host 0.0.0.0 --port 8080 -m "/modelos/$ARCHIVO" --alias "$ALIAS" -ngl 999 -fa on -np 1 -b 128 -c 16384 --temp 0 --top-k 20 --top-p 0.95 --no-mmproj --reasoning-budget 0 --spec-type draft-mtp --spec-draft-n-max 2 --jinja > /tmp/l.log 2>&1 &\nP=$!\nwhile kill -0 $P 2>/dev/null; do\n  sleep 5\n  I=$(( $(date +%s) - $(stat -c %Y /tmp/l.log) ))\n  if grep -q print_timing /tmp/l.log && [ $I -ge 30 ]; then echo APAGADO_FIN_DE_SALIDA; kill $P; exit 0; fi\n  if [ $I -ge 300 ]; then echo APAGADO_5_MIN_SIN_USO; kill $P; exit 0; fi\ndone\n';

const hf = (path, method = 'GET', body) => fetch('https://huggingface.co' + path, {
  method, headers: { Authorization: 'Bearer ' + process.env.HF_TOKEN, 'Content-Type': 'application/json' },
  body: body ? JSON.stringify(body) : undefined,
});

async function encender(model) {
  const [, archivo] = RESPALDO[model];
  const r = await hf('/api/jobs/' + NS, 'POST', {
    dockerImage: 'ghcr.io/ggml-org/llama.cpp:server-cuda', command: ['bash', '-c', ARRANQUE], arguments: [],
    environment: { ARCHIVO: archivo, ALIAS: model }, flavor: 'l4x1', timeoutSeconds: 7200, labels: { name: 'router-respaldo-l4' },
    volumes: [{ type: 'bucket', source: NS + '/yaiwes-memoria-storage', mountPath: '/modelos', readOnly: true, path: 'router-respaldo/modelos' }],
    expose: { ports: [8080], portsPublic: [] },
  });
  const j = await r.json();
  if (!r.ok) return { error: j };
  return { estado: 'encendiendo', job_id: j.id, url: 'https://' + j.id + '--8080.hf.jobs', model };
}

module.exports = async function handler(req, res) {
  try {
    const q = req.query || {};
    const accion = q.accion;
    if (req.method === 'GET' && accion === 'modelos') {
      const lista = [...Object.entries(FICHAS), ...Object.entries(RESPALDO)].map(([id, v]) => ({ id, nombre: v[0], respaldo: id in RESPALDO }));
      return res.status(200).json({ modelos: lista });
    }
    if (req.method === 'GET' && accion === 'estado') {
      const r = await hf('/api/jobs/' + NS + '/' + q.job);
      const j = await r.json();
      const etapa = (j.status && j.status.stage) || 'DESCONOCIDA';
      let listo = false;
      if (etapa === 'RUNNING' && q.url) {
        try { const h = await fetch(q.url + '/health', { headers: { Authorization: 'Bearer ' + process.env.HF_TOKEN } }); listo = h.ok; } catch (e) { listo = false; }
      }
      return res.status(200).json({ etapa, listo });
    }
    if (req.method === 'POST' && accion === 'apagar') {
      const r = await hf('/api/jobs/' + NS + '/' + q.job + '/cancel', 'POST');
      return res.status(r.ok ? 200 : r.status).json({ job_id: q.job, apagado: r.ok });
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
      if (!b.respaldo_url) { const e = await encender(model); return res.status(e.error ? 502 : 202).json(e); }
      const r = await fetch(b.respaldo_url + '/v1/chat/completions', { method: 'POST', headers: { Authorization: 'Bearer ' + process.env.HF_TOKEN, 'Content-Type': 'application/json' }, body: JSON.stringify({ model, ...cuerpo }) });
      return res.status(r.status).json(await r.json());
    }
    return res.status(400).json({ error: 'modelo desconocido', validos: [...Object.keys(FICHAS), ...Object.keys(RESPALDO)] });
  } catch (e) {
    return res.status(500).json({ error: String(e).slice(0, 300) });
  }
};
