import { timingSafeEqual } from 'node:crypto';

const FLAG_URL =
  'https://raw.githubusercontent.com/maxbry123-commits/router-universal-router-inteligente-/main/router%20inteligente%20universal/agents-yaiwes/ROUTER_JOB_PAUSE.flag';

const ROUTER_GET = new Set([
  '/health',
  '/chat/router/status',
  '/chat/models',
  '/chat/github/accounts',
  '/chat/github/whoami',
  '/chat/github/repos',
  '/chat/github/file',
  '/control/hf/status',
  '/control/hf/workers',
  '/plugins'
]);

const ROUTER_POST_PREFIXES = [
  '/chat/send',
  '/chat/github/commit',
  '/control/hf/workers/ensure',
  '/control/hf/invoke',
  '/plugins/'
];

const MCP_TOOLS = new Set([
  'connection_status',
  'list_repositories',
  'get_file',
  'create_or_update_file',
  'delete_file',
  'create_branch',
  'delete_branch',
  'create_issue',
  'create_pull_request',
  'delete_repository',
  'github_api',
  'storage_write',
  'storage_read',
  'storage_list'
]);

let routerCache = { url: '', at: 0 };
const CACHE_MS = 15000;

function sameKey(a, b) {
  const x = Buffer.from(String(a || ''));
  const y = Buffer.from(String(b || ''));
  return x.length === y.length && timingSafeEqual(x, y);
}

function bridgeKey() {
  return process.env.RIU_DIRECT_BRIDGE_KEY ||
    process.env.RIU_CHAT_PASSWORD ||
    process.env.BRIDGE_KEY ||
    '';
}

function hfToken() {
  return process.env.HF_CONTROL_JOBS_TOKEN ||
    process.env.HF_TOKEN ||
    process.env.HF_TOKEN_1 ||
    '';
}

async function resolveRouterUrl() {
  if (routerCache.url && Date.now() - routerCache.at < CACHE_MS) return routerCache.url;
  try {
    const r = await fetch(FLAG_URL, { cache: 'no-store', signal: AbortSignal.timeout(8000) });
    if (r.ok) {
      const text = await r.text();
      const line = text.split(/\r?\n/).find((v) => v.startsWith('LIVE_URL='));
      const url = line ? line.slice('LIVE_URL='.length).trim().replace(/\/$/, '') : '';
      if (/^https:\/\/[a-z0-9-]+--8000\.hf\.jobs$/i.test(url)) {
        routerCache = { url, at: Date.now() };
        return url;
      }
    }
  } catch {}
  const fallback = String(process.env.RIU_ROUTER_URL || '').trim().replace(/\/$/, '');
  if (!fallback) throw new Error('ROUTER_URL_UNAVAILABLE');
  return fallback;
}

function routerPathAllowed(method, path) {
  if (method === 'GET') return ROUTER_GET.has(path);
  if (method === 'POST') {
    return ROUTER_POST_PREFIXES.some((prefix) =>
      prefix.endsWith('/') ? path.startsWith(prefix) : path === prefix
    );
  }
  return false;
}

async function callRouter(input) {
  const method = String(input.method || 'GET').toUpperCase();
  const path = String(input.path || '');
  if (!path.startsWith('/') || !routerPathAllowed(method, path)) {
    return { ok: false, status: 400, error: 'ROUTE_NOT_ALLOWED' };
  }

  const base = await resolveRouterUrl();
  const token = hfToken();
  const apiKey = process.env.RIU_ROUTER_API_KEY || '';
  if (!token || !apiKey) {
    return { ok: false, status: 503, error: 'ROUTER_AUTH_NOT_CONFIGURED' };
  }

  const q = input.query && typeof input.query === 'object'
    ? '?' + new URLSearchParams(Object.entries(input.query).map(([k, v]) => [k, String(v)])).toString()
    : '';

  const headers = {
    Authorization: 'Bearer ' + token,
    'X-API-Key': apiKey,
    Accept: 'application/json'
  };
  const init = {
    method,
    headers,
    signal: AbortSignal.timeout(120000)
  };
  if (method !== 'GET') {
    headers['Content-Type'] = 'application/json';
    init.body = JSON.stringify(input.body && typeof input.body === 'object' ? input.body : {});
  }

  const r = await fetch(base + path + q, init);
  const text = await r.text();
  let data;
  try { data = JSON.parse(text); } catch { data = { raw: text }; }
  return { ok: r.ok, status: r.status, via: 'vercel->hf-router', data };
}

async function mcpRpc(url, body) {
  const r = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json, text/event-stream',
      'MCP-Protocol-Version': '2025-03-26'
    },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(120000)
  });
  const text = await r.text();
  const lines = text.split(/\r?\n/);
  const dataLine = lines.find((line) => line.startsWith('data: '));
  let payload = text;
  if (dataLine) payload = dataLine.slice(6);
  let data;
  try { data = JSON.parse(payload); } catch { data = { raw: text }; }
  return { status: r.status, ok: r.ok, data };
}

async function callMcp(input) {
  const url = String(process.env.HF_MCP_DIRECT_URL || '').trim();
  if (!url) return { ok: false, status: 503, error: 'HF_MCP_DIRECT_URL_NOT_CONFIGURED' };

  const tool = String(input.tool || '');
  if (!MCP_TOOLS.has(tool)) return { ok: false, status: 400, error: 'MCP_TOOL_NOT_ALLOWED' };

  const init = await mcpRpc(url, {
    jsonrpc: '2.0',
    id: 'init',
    method: 'initialize',
    params: {
      protocolVersion: '2025-03-26',
      capabilities: {},
      clientInfo: { name: 'yaiwes-vercel-direct', version: '1.0.0' }
    }
  });
  if (!init.ok) return { ...init, phase: 'initialize' };

  const out = await mcpRpc(url, {
    jsonrpc: '2.0',
    id: 'call',
    method: 'tools/call',
    params: {
      name: tool,
      arguments: input.arguments && typeof input.arguments === 'object' ? input.arguments : {}
    }
  });
  return { ...out, via: 'vercel->hf-mcp->github', tool };
}

export default async function handler(req, res) {
  const want = bridgeKey();
  if (!want) return res.status(503).json({ error: 'DIRECT_BRIDGE_KEY_NOT_CONFIGURED' });
  if (!sameKey(req.headers['x-bridge-key'], want)) {
    return res.status(401).json({ error: 'UNAUTHORIZED' });
  }
  if (req.method !== 'POST') return res.status(405).json({ error: 'POST_ONLY' });

  const input = req.body && typeof req.body === 'object' ? req.body : {};
  try {
    if (input.mode === 'router') {
      const out = await callRouter(input);
      return res.status(out.status || (out.ok ? 200 : 502)).json(out);
    }
    if (input.mode === 'mcp') {
      const out = await callMcp(input);
      return res.status(out.status || (out.ok ? 200 : 502)).json(out);
    }
    return res.status(400).json({ error: 'MODE_REQUIRED', allowed: ['router', 'mcp'] });
  } catch (e) {
    return res.status(502).json({
      error: 'DIRECT_BRIDGE_FAILED',
      detail: String((e && e.message) || e).slice(0, 300)
    });
  }
}
