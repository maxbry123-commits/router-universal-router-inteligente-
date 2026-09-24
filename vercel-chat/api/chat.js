module.exports = async (req, res) => {
  if (req.method !== 'POST') {
    res.statusCode = 405;
    res.end('POST only');
    return;
  }
  const chunks = [];
  for await (const c of req) chunks.push(c);
  let body = {};
  try { body = JSON.parse(Buffer.concat(chunks).toString() || '{}'); } catch {}
  const message = String(body.message || '').slice(0, 4000);
  const base = (process.env.RIU_ROUTER_URL || '').replace(/\/$/, '');
  const token = process.env.HF_TOKEN || process.env.HF_TOKEN_1 || '';
  const key = process.env.RIU_ROUTER_API_KEY || '';
  if (!base || !token) {
    res.statusCode = 500;
    res.setHeader('content-type', 'application/json');
    res.end(JSON.stringify({ error: 'Falta RIU_ROUTER_URL o HF_TOKEN en Vercel' }));
    return;
  }
  try {
    const r = await fetch(base + '/chat/send', {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        Authorization: 'Bearer ' + token,
        ...(key ? { 'X-API-Key': key } : {})
      },
      body: JSON.stringify({
        message,
        provider: 'hf',
        model: 'deepseek-ai/DeepSeek-V4-Flash',
        max_tokens: 200
      })
    });
    const text = await r.text();
    let data; try { data = JSON.parse(text); } catch { data = { raw: text }; }
    const reply = data.reply || data.response || data.output || data.message || text;
    res.statusCode = r.ok ? 200 : r.status;
    res.setHeader('content-type', 'application/json');
    res.end(JSON.stringify({ reply, status: r.status }));
  } catch (e) {
    res.statusCode = 502;
    res.setHeader('content-type', 'application/json');
    res.end(JSON.stringify({ error: 'HF job no responde: ' + String(e.message || e) }));
  }
};
