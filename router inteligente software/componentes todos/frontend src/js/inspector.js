// Inspector · visualiza contract + topology + logs

const Inspector = {
  selectedSat: null,
  selectedResp: null,

  renderTopology(satellites) {
    const svg = document.getElementById('topologySvg');
    if (!svg) return;
    const W = svg.clientWidth || 280;
    const H = 280;
    const cx = W / 2, cy = H / 2;
    const r = Math.min(W, H) * 0.35;
    let html = `<svg width="${W}" height="${H}" xmlns="http://www.w3.org/2000/svg">`;
    // router center
    html += `<circle cx="${cx}" cy="${cy}" r="22" fill="#00b8ff" opacity="0.9"/>`;
    html += `<text x="${cx}" y="${cy+4}" text-anchor="middle" fill="#000" font-size="10" font-weight="bold">Router</text>`;
    // satellites around
    satellites.forEach((s, i) => {
      const angle = (i / satellites.length) * Math.PI * 2 - Math.PI / 2;
      const x = cx + Math.cos(angle) * r;
      const y = cy + Math.sin(angle) * r;
      const color = s.online ? '#00d4aa' : '#ff6b6b';
      html += `<line x1="${cx}" y1="${cy}" x2="${x}" y2="${y}" stroke="rgba(0,184,255,0.3)" stroke-width="1"/>`;
      html += `<g class="graph-node" onclick="selectSatellite('${s.name}')" style="cursor:pointer">`;
      html += `<circle cx="${x}" cy="${y}" r="14" fill="${color}"/>`;
      html += `<text x="${x}" y="${y+4}" text-anchor="middle" fill="#000" font-size="9" font-weight="bold">${s.name.slice(0,8)}</text>`;
      html += `</g>`;
    });
    html += `</svg>`;
    svg.innerHTML = html;
  },

  renderInspector(sat) {
    const c = document.getElementById('inspectorContent');
    if (!c) return;
    if (!sat) {
      c.innerHTML = '<p class="hint">Selecciona un satélite del sidebar para inspeccionar.</p>';
      return;
    }
    c.innerHTML = `
      <div class="insp-row"><b>Nombre</b><span>${sat.name}</span></div>
      <div class="insp-row"><b>URL</b><code>${sat.url}</code></div>
      <div class="insp-row"><b>Capability</b><span class="badge">${sat.cap || '—'}</span></div>
      <div class="insp-row"><b>Transport</b><span>${sat.transport || 'http'}</span></div>
      <div class="insp-row"><b>Sandbox</b><span>${sat.sandbox || 'none'}</span></div>
      <div class="insp-row"><b>Estado</b><span style="color:${sat.online ? '#00d4aa' : '#ff6b6b'}">${sat.online ? '● online' : '○ offline'}</span></div>
      <hr>
      <h4 style="font-size:11px;color:var(--azure);margin:8px 0 4px">Acciones</h4>
      <button class="btn-secondary" onclick="testSatellite('${sat.name}')">🔬 Test health</button>
      <button class="btn-secondary" onclick="deleteSatellite('${sat.name}')">🗑 Eliminar</button>
      <hr>
      <h4 style="font-size:11px;color:var(--azure);margin:8px 0 4px">Schema artifact</h4>
      <pre style="font-size:9px;color:var(--model-color);background:var(--bg);padding:6px;border-radius:4px;max-height:160px;overflow:auto">{
  "artifact_id": "art_xxx",
  "estado": "pending|approved|rejected|completed",
  "kind": "text|code|file|image|consensus|manifest",
  "transport": "http|sse|ws|file|ipc",
  "sandbox": "pyodide|wasm|native|none|docker",
  "timeout_ms": 100..600000,
  "payload": { ... },
  "hash": "sha256 del payload",
  "signature": "hmac opcional"
}</pre>
    `;
    this.selectedSat = sat;
  },

  renderContract() {
    const el = document.getElementById('contractPre');
    if (!el) return;
    el.textContent = `# Router Universal · Contrato

## Artifact schema
artifact_id  := ^art_[a-z0-9]{8,32}$
estado       := pending | approved | rejected | completed | expired
kind         := text | code | file | image | consensus | manifest
transport    := http | sse | ws | file | ipc
sandbox      := pyodide | wasm | native | none | docker
timeout_ms   := 100..600000
hash         := SHA256 del payload
signature    := HMAC-SHA256(artifact_id|estado|kind|hash, secret)

## Endpoints
POST /execute  → ejecuta artifact
GET  /health   → { ok: bool, latency_ms }
GET  /sse      → Server-Sent Events (transporte sse)
WS   /ws       → WebSocket (transporte ws)

## Flujo
1. Crear artifact con payload
2. Calcular hash = SHA256(json(payload))
3. (opcional) Firmar = HMAC-SHA256
4. Validar contrato (regex, kinds, transports)
5. POST a ${'{SATELLITE_URL}'}/execute
6. Esperar respuesta o timeout
`;
  },

  selectResponse(resp) {
    this.selectedResp = resp;
    document.getElementById('inspectorContent').innerHTML = `
      <h4 style="font-size:11px;color:var(--azure);margin-bottom:6px">Artifact enviado</h4>
      <pre style="font-size:9px;color:var(--model-color);background:var(--bg);padding:6px;border-radius:4px;max-height:200px;overflow:auto">${JSON.stringify(resp.artifact, null, 2)}</pre>
      <h4 style="font-size:11px;color:var(--azure);margin:8px 0 4px">Respuesta</h4>
      <pre style="font-size:9px;color:var(--model-color);background:var(--bg);padding:6px;border-radius:4px;max-height:160px;overflow:auto">${JSON.stringify(resp.result || { error: resp.error }, null, 2)}</pre>
      <p style="font-size:10px;color:var(--fg-dim);margin-top:6px">
        ${resp.ok ? '✅ OK' : '❌ ' + (resp.error || 'fail')} · status: ${resp.status || '—'}
      </p>
    `;
  },
};
window.Inspector = Inspector;