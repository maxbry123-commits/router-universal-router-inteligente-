// Sidecar de AgentDB (v3 alpha, Node): runtime REAL del motor, compilado desde el codigo ya bajado
// (Componentes del Router/.../componentes descargados/AgentDB). Cada memoria = un Episode de ReflexionMemory
// (sessionId = scope, task = key, output = JSON de los datos). Busqueda con retrieveRelevant (vectores).
// Embeddings: los calcula el EmbeddingService local de AgentDB (sin clave ni LLM). Contrato: sidecar_http.py.
// Uso: node agentdb_sidecar.mjs --port 9104 --dist <AgentDB>/dist/src/index.js --db /tmp/riu-motores/agentdb.sqlite
import http from 'node:http';

const argv = process.argv.slice(2);
const arg = (n, d) => { const i = argv.indexOf('--' + n); return i >= 0 ? argv[i + 1] : d; };
const PORT = Number(arg('port', '9104'));
const { AgentDB } = await import(arg('dist'));
const db = new AgentDB({ dbPath: arg('db', '/tmp/riu-motores/agentdb.sqlite') });
await db.initialize();
const mem = db.getController('reflexion');

const rec = (e) => {
  let data = null;
  try { data = JSON.parse(e.output ?? 'null'); } catch { data = e.output ?? null; }
  return { scope: e.sessionId, key: e.task, data, id: e.id };
};
const send = (res, code, obj) => {
  const b = JSON.stringify(obj);
  res.writeHead(code, { 'Content-Type': 'application/json; charset=utf-8', 'Content-Length': Buffer.byteLength(b) });
  res.end(b);
};

http.createServer(async (req, res) => {
  const u = new URL(req.url, 'http://x');
  try {
    if (req.method === 'GET' && (u.pathname === '/' || u.pathname === '/health'))
      return send(res, 200, { status: 'ok', engine: 'agentdb', version: '3.0.0-alpha.20', store: 'sql.js (WASM SQLite)', memoria: 'ReflexionMemory', busqueda: 'vectorial (retrieveRelevant) con respaldo por texto' });
    if (req.method === 'GET' && u.pathname === '/load') {
      const eps = await mem.getRecentEpisodes(u.searchParams.get('scope') || '', 500);
      return send(res, 200, { records: eps.filter((e) => e.task === u.searchParams.get('key')).map(rec) });
    }
    if (req.method === 'GET' && u.pathname === '/search') {
      const k = Number(u.searchParams.get('k') || 10), scope = u.searchParams.get('scope') || '';
      const query = u.searchParams.get('query') || '';
      let hits = [];
      try { hits = (await mem.retrieveRelevant({ task: query, k: k * 5 })).filter((e) => e.sessionId === scope); } catch { hits = []; }
      if (!hits.length) {  // respaldo: texto sobre los episodios que AgentDB guardo en ese scope
        const q = query.toLowerCase();
        hits = (await mem.getRecentEpisodes(scope, 500)).filter((e) => (String(e.task) + ' ' + String(e.output ?? '')).toLowerCase().includes(q));
      }
      return send(res, 200, { records: hits.slice(0, k).map(rec) });
    }
    if (req.method === 'POST' && u.pathname === '/save') {
      let raw = ''; for await (const c of req) raw += c;
      const b = JSON.parse(raw || '{}');
      const id = await mem.storeEpisode({ sessionId: b.scope, task: b.key, output: JSON.stringify(b.data ?? null), reward: 1, success: true, metadata: { origen: 'riu-memoria' } });
      return send(res, 200, { id });
    }
    return send(res, 404, { error: 'ruta desconocida' });
  } catch (e) {
    return send(res, 500, { error: e?.name || 'Error', detalle: String(e?.message || e).slice(0, 200) });
  }
}).listen(PORT, '127.0.0.1');
