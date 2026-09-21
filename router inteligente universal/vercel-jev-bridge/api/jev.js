import { timingSafeEqual } from 'node:crypto';
import { experimental_evaluate as evaluate } from 'ai';

// Puente Router -> Jev (typesafe-ai/jev por Vercel AI Gateway). Falla cerrado: sin BRIDGE_KEY configurada no responde.
// Despliegue: proyecto Vercel `riu-jev-bridge` con package.json {"type":"module","dependencies":{"ai":"latest"}}, esta función en api/jev.js
// y api/health.js (GET -> {ok:true}). Variable BRIDGE_KEY (solo en Vercel y en el banco del Router). Estado: NO desplegado (Vercel 403).
function sameKey(a, b) {
  const x = Buffer.from(String(a || ''));
  const y = Buffer.from(String(b || ''));
  return x.length === y.length && timingSafeEqual(x, y);
}

export default async function handler(req, res) {
  const key = process.env.BRIDGE_KEY;
  if (!key) return res.status(503).json({ error: 'BRIDGE_KEY_NOT_CONFIGURED' });
  if (!sameKey(req.headers['x-bridge-key'], key)) return res.status(401).json({ error: 'UNAUTHORIZED' });
  if (req.method !== 'POST') return res.status(405).json({ error: 'POST_ONLY' });
  const { state, questions } = req.body || {};
  if (state === undefined || !questions || typeof questions !== 'object') {
    return res.status(400).json({ error: 'state y questions son obligatorios' });
  }
  try {
    const result = await evaluate({
      model: 'typesafe-ai/jev',
      state,
      questions,
      providerOptions: { gateway: { zeroDataRetention: true } },
    });
    const safe = JSON.parse(JSON.stringify(result, (k, v) => (typeof v === 'bigint' ? String(v) : v)));
    return res.status(200).json({ ok: true, result: safe });
  } catch (e) {
    return res.status(502).json({ error: 'JEV_CALL_FAILED', detail: String((e && e.message) || e).slice(0, 300) });
  }
}
