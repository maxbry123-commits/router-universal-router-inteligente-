// Router Universal NCT - Client (browser)
// Implementa los contratos del repo router-universal/red/

const RouterClient = {
  baseUrl: 'http://95.111.232.89:7000',
  secret: '',

  async send(to, payload, opts = {}) {
    const kind = opts.kind || 'text';
    const transport = opts.transport || 'http';
    const sandbox = opts.sandbox || 'none';
    const timeoutMs = opts.timeoutMs || 30000;

    const artifact = {
      artifact_id: 'art_' + Date.now().toString(16) + Math.random().toString(16).slice(2, 6),
      estado: 'pending',
      kind,
      transport,
      sandbox,
      timeout_ms: timeoutMs,
      payload,
      hash: await this.sha256(JSON.stringify(payload)),
      created_at: Date.now(),
      ttl_ms: 3600000,
    };

    if (this.secret) {
      artifact.signature = await this.hmacSign(artifact);
    }

    // Validar antes de enviar
    const validation = this.validate(artifact);
    if (!validation.ok) {
      return { ok: false, error: validation.error, artifact };
    }

    // HTTP POST
    try {
      const ctrl = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), timeoutMs);
      const url = `${to.url}/execute`;
      const r = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(artifact),
        signal: ctrl.signal,
      });
      clearTimeout(timer);
      const data = await r.json();
      return { ok: r.ok, status: r.status, result: data, artifact };
    } catch (e) {
      return { ok: false, error: e.message, artifact };
    }
  },

  async broadcast(payload, satellites, opts = {}) {
    const promises = satellites.map(s => this.send(s, payload, opts));
    return Promise.all(promises);
  },

  validate(art) {
    if (!/^art_[a-z0-9]{8,32}$/.test(art.artifact_id)) {
      return { ok: false, error: 'artifact_id inválido' };
    }
    if (!['pending', 'approved', 'rejected', 'completed'].includes(art.estado)) {
      return { ok: false, error: 'estado inválido' };
    }
    if (!['text', 'code', 'file', 'image', 'consensus', 'manifest'].includes(art.kind)) {
      return { ok: false, error: 'kind inválido' };
    }
    if (!['http', 'sse', 'ws', 'file', 'ipc'].includes(art.transport)) {
      return { ok: false, error: 'transport inválido' };
    }
    if (!['pyodide', 'wasm', 'native', 'none', 'docker'].includes(art.sandbox)) {
      return { ok: false, error: 'sandbox inválido' };
    }
    if (art.timeout_ms < 100 || art.timeout_ms > 600000) {
      return { ok: false, error: 'timeout_ms fuera de rango' };
    }
    if (!/^[a-f0-9]{64}$/.test(art.hash)) {
      return { ok: false, error: 'hash inválido (no SHA256)' };
    }
    return { ok: true };
  },

  async sha256(s) {
    const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s));
    return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, '0')).join('');
  },

  async hmacSign(art) {
    const msg = `${art.artifact_id}|${art.estado}|${art.kind}|${art.hash}`;
    const key = await crypto.subtle.importKey(
      'raw', new TextEncoder().encode(this.secret),
      { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']
    );
    const sig = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(msg));
    return Array.from(new Uint8Array(sig)).map(b => b.toString(16).padStart(2, '0')).join('');
  },

  async health(to) {
    try {
      const r = await fetch(`${to.url}/health`, { signal: AbortSignal.timeout(5000) });
      return r.ok;
    } catch { return false; }
  },
};
window.RouterClient = RouterClient;