async function liveRouterUrl() {
  const fallback = String(process.env.RIU_ROUTER_URL || '').trim().replace(/\/$/, '');
  try {
    const r = await fetch(
      'https://raw.githubusercontent.com/maxbry123-commits/router-universal-router-inteligente-/main/router%20inteligente%20universal/agents-yaiwes/ROUTER_JOB_PAUSE.flag',
      { cache: 'no-store', signal: AbortSignal.timeout(5000) }
    );
    const text = r.ok ? await r.text() : '';
    const line = text.split(/\r?\n/).find((v) => v.startsWith('LIVE_URL='));
    return (line ? line.slice('LIVE_URL='.length).trim() : '') || fallback;
  } catch {
    return fallback;
  }
}

export default async function handler(_req, res) {
  const routerUrl = await liveRouterUrl();
  return res.status(200).json({
    ok: true,
    service: 'yaiwes-vercel-direct',
    primary_path: 'vercel',
    router_url_resolved: Boolean(routerUrl),
    router_api_key_present: Boolean(process.env.RIU_ROUTER_API_KEY),
    hf_router_token_present: Boolean(
      process.env.HF_CONTROL_JOBS_TOKEN || process.env.HF_TOKEN || process.env.HF_TOKEN_1
    ),
    mcp_direct_url_present: Boolean(process.env.HF_MCP_DIRECT_URL),
    bridge_key_present: Boolean(
      process.env.RIU_DIRECT_BRIDGE_KEY || process.env.RIU_CHAT_PASSWORD || process.env.BRIDGE_KEY
    )
  });
}
