const { timingSafeEqual, randomUUID } = require('node:crypto');

const DATASET = 'COMAND-CENTER-1/yaiwes-hf-memoria';
const COMMIT_URL = `https://huggingface.co/api/datasets/${DATASET}/commit/main`;
const MAX_FILE_BYTES = 2.8 * 1024 * 1024;

function authorized(req) {
  const expected = process.env.RIU_ROUTER_API_KEY || '';
  const supplied = req.headers['x-api-key'] || '';
  const a = Buffer.from(String(expected));
  const b = Buffer.from(String(supplied));
  return !!expected && a.length === b.length && timingSafeEqual(a, b);
}

function safe(value, fallback = 'item') {
  const result = String(value || '').normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^A-Za-z0-9._-]+/g, '-')
    .replace(/^-+|-+$/g, '').slice(0, 100);
  return result || fallback;
}

function json(res, status, body) {
  res.statusCode = status;
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store, private');
  res.end(JSON.stringify(body));
}

async function commit(token, files, summary) {
  const lines = [
    JSON.stringify({ key: 'header', value: { summary, description: 'Chat RIU: datos privados del usuario' } }),
    ...files.map(file => JSON.stringify({ key: 'file', value: { path: file.path, encoding: 'base64', content: Buffer.from(file.contents).toString('base64') } })),
  ].join('\n') + '\n';
  const response = await fetch(COMMIT_URL, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/x-ndjson' },
    body: lines,
    cache: 'no-store',
    signal: AbortSignal.timeout(25000),
  });
  if (!response.ok) {
    const error = new Error(`HF_DATASET_HTTP_${response.status}`);
    error.status = response.status;
    throw error;
  }
  return response.json().catch(() => ({}));
}

module.exports = async (req, res) => {
  res.setHeader('Cache-Control', 'no-store, private');
  if (req.method !== 'POST') return json(res, 405, { ok: false, error: 'POST_ONLY' });
  if (!authorized(req)) return json(res, 401, { ok: false, error: 'UNAUTHORIZED' });
  const token = process.env.HF_TOKEN_1 || '';
  if (!token) return json(res, 503, { ok: false, error: 'DATASET_TOKEN_NOT_CONFIGURED' });
  const body = typeof req.body === 'string' ? (() => { try { return JSON.parse(req.body); } catch { return {}; } })() : (req.body || {});
  const conversation = safe(body.conversation_id, 'principal');
  const time = new Date().toISOString().replace(/[:.]/g, '-') + '-' + randomUUID();

  try {
    let path, contents, summary;
    if (body.kind === 'turn') {
      if (!body.user_message && !body.assistant_message) return json(res, 400, { ok: false, error: 'EMPTY_TURN' });
      path = `chat-data/conversations/${conversation}/events/${time}.json`;
      contents = JSON.stringify({
        format: 'riu-chat-turn-v1', created_at: new Date().toISOString(), conversation_id: conversation,
        user_message: String(body.user_message || ''), assistant_message: String(body.assistant_message || ''),
        model: String(body.model || '').slice(0, 200), agent_id: String(body.agent_id || '').slice(0, 100),
      });
      summary = 'Chat RIU: guardar turno';
    } else if (body.kind === 'document') {
      if (typeof body.data_b64 !== 'string' || !body.data_b64) return json(res, 400, { ok: false, error: 'DOCUMENT_DATA_REQUIRED' });
      const binary = Buffer.from(body.data_b64, 'base64');
      if (!binary.length || binary.length > MAX_FILE_BYTES) return json(res, 413, { ok: false, error: 'DOCUMENT_SIZE_LIMIT_3MB' });
      const name = safe(String(body.name || 'documento').split(/[\\/]/).pop(), 'documento');
      const id = randomUUID();
      const dir = `chat-data/documents/${conversation}/${id}`;
      const meta = JSON.stringify({ format: 'riu-chat-document-v1', created_at: new Date().toISOString(), conversation_id: conversation, name, mime: String(body.mime || 'application/octet-stream'), size: binary.length });
      const metadataPath = `${dir}/metadata.json`;
      const filePath = `${dir}/${name}`;
      await commit(token, [{ path: filePath, contents: binary }, { path: metadataPath, contents: meta }], 'Chat RIU: guardar adjunto');
      return json(res, 200, { ok: true, saved: true, dataset: DATASET, path: filePath });
    } else if (body.kind === 'snapshot') {
      const snapshot = { format: 'riu-chat-snapshot-v1', created_at: new Date().toISOString(), conversation_id: conversation, messages: Array.isArray(body.messages) ? body.messages.slice(-200) : [] };
      path = `chat-data/snapshots/${conversation}/${time}.json`;
      contents = JSON.stringify(snapshot);
      summary = 'Chat RIU: snapshot de conversación';
    } else {
      return json(res, 400, { ok: false, error: 'KIND_MUST_BE_turn_document_or_snapshot' });
    }
    await commit(token, [{ path, contents }], summary);
    return json(res, 200, { ok: true, saved: true, dataset: DATASET, path });
  } catch (error) {
    return json(res, 502, { ok: false, error: error.status ? `HF_DATASET_HTTP_${error.status}` : 'DATASET_WRITE_FAILED' });
  }
};

module.exports.config = { api: { bodyParser: { sizeLimit: '4mb' } } };
