// api.js — Cliente API del Router (chat UI)
// Cambio: cuando el Space HF no responde, el error dice explícitamente "Space caído — reinicia en Hugging Face" en lugar de GAP network error genérico.
const CFG = window.RIU_CONFIG || {};
let BASE = "";
let liveVerified = false;

let liveCheckedAt = 0;
let liveRequest = null;
let PBASE = "";
const vivos = new Set();
const fetchT = (url, opts, ms) => { const ac = typeof AbortController === 'function' ? new AbortController() : null; const reg = ac ? { ac, t0: Date.now() } : null; if (reg) vivos.add(reg); const t = setTimeout(() => ac && ac.abort(), ms); return fetch(url, Object.assign({}, opts || {}, ac ? { signal: ac.signal } : {})).finally(() => { clearTimeout(t); if (reg) vivos.delete(reg); }); };
try { const cortarColgados = () => { for (const r of [...vivos]) if (Date.now() - r.t0 > 2000) { try { r.ac.abort(); } catch (e) {} } }; document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') cortarColgados(); }); window.addEventListener('online', cortarColgados); window.addEventListener('pageshow', (e) => { if (e.persisted) cortarColgados(); }); } catch (e) {}
const usarProxy = () => { try { return /\.vercel\.app$/.test(location.hostname) && localStorage.getItem('riu_proxy') !== '0' && !/[?&]proxy=0/.test(location.search); } catch (e) { return false; } };
function aplicarBase(url) {
  BASE = url;
  PBASE = (url === CFG.proxyDestino && usarProxy()) ? location.origin : url;
  CFG.apiBase = BASE;
  CFG.harnessUrl = PBASE + '/plugins/puente_chat/call';
  try { localStorage.setItem('riu_live_url', url); } catch (e) {}
}
const VALIDA = (u) => /^https:\/\/[a-z0-9-]+\.hf\.space$/.test(u || '');
function refrescarLive() {
  if (!liveRequest) liveRequest = (async () => {
    try {
      const flag = await fetchT(CFG.liveUrl + '?t=' + Date.now(), { cache: 'no-store', credentials: 'omit' }, 8000);
      if (!flag.ok) throw new Error('Dirección HF no disponible');
      const info = await flag.json();
      if (!VALIDA(info.LIVE_URL)) throw new Error('Dirección HF inválida');
      aplicarBase(info.LIVE_URL);
      liveCheckedAt = Date.now();
      liveVerified = true;
    } catch (error) {
      if (!liveVerified && !BASE) throw new Error('ROUTER_LIVE_URL_NO_RESUELTO');
    } finally { liveRequest = null; }
    return BASE;
  })();
  return liveRequest;
}
async function liveRouter() {
  if (CFG.routerStopped) throw new Error('Router detenido por orden del Director');
  if (!BASE) {
    let c = ''; try { c = localStorage.getItem('riu_live_url') || ''; } catch (e) {}
    if (!VALIDA(c)) c = CFG.proxyDestino || '';
    if (VALIDA(c)) aplicarBase(c);
  }
  if (Date.now() - liveCheckedAt >= 30000) { const pr = refrescarLive(); if (!BASE) return pr; pr.catch(() => {}); }
  return BASE;
}

function clave() { return sessionStorage.getItem("riu_clave") || ""; }
function remoto(headers) {
  if (BASE) headers[CFG.authHeader || "X-API-Key"] = clave();
  return BASE ? "omit" : "same-origin";
}
const L4 = { job: null, url: null };
const CP = 'riu_proc_v1';
const procs = () => { try { return JSON.parse(localStorage.getItem(CP) || '{}'); } catch (e) { return {}; } };
const guardaProc = (ses, v) => { try { const t = procs(); if (v) t[ses] = v; else delete t[ses]; localStorage.setItem(CP, JSON.stringify(t)); } catch (e) {} };
const hdrs = () => { const k = sessionStorage.getItem('riu_clave'); const h = { 'Content-Type': 'application/json' }; if (k) { h['X-API-Key'] = k; h.Authorization = 'Bearer ' + k; } return h; };
window.RIU_PENDIENTE = (ses) => procs()[ses] || null;
window.RIU_CANCELAR = async (ses) => {
  const v = procs()[ses]; if (!v) return false; guardaProc(ses, null);
  try { await fetchT(v.base.replace(/[/]+$/, '') + '/cancelar', { method: 'POST', headers: hdrs(), body: JSON.stringify({ proceso_id: v.pid }) }, 8000); } catch (e) {}
  return true;
};
window.RIU_RETOMAR = async (ses) => {
  const v = procs()[ses]; if (!v) return null; const fin = Date.now() + 560000; let malos = 0;
  while (Date.now() < fin) {
    if (!procs()[ses]) return { error: 'PROCESO_DETENIDO' };
    try {
      const r = await fetchT(v.base.replace(/[/]+$/, '') + '/resultado', { method: 'POST', headers: hdrs(), body: JSON.stringify({ proceso_id: v.pid, espera: 8 }) }, 16000);
      const e = await r.json().catch(() => ({})); const p = e.result || {};
      if (!r.ok || e.status !== 'ok') { if (++malos >= 8) return { estado: 'reanudable', proceso_id: v.pid, error: 'GAP_ROUTER_ESTADO_NO_CONFIRMADO', detalle: e.reason || e.detail || ('HTTP ' + r.status) }; }
      else if (p.error) { guardaProc(ses, null); return p; }
      else if (p.estado && p.estado !== 'procesando') { guardaProc(ses, null); return p; }
      else if (!p.estado) { if (++malos >= 8) return { estado: 'reanudable', proceso_id: v.pid, error: 'GAP_RESULTADO_TEMPORALMENTE_VACIO', detalle: 'Reconsultar el mismo PID; no relanzar el trabajo' }; }
      else malos = 0;
    } catch (x) { if (++malos >= 12) { return { estado: 'reanudable', proceso_id: v.pid, error: 'ROUTER_SIN_RESPUESTA' }; } }
    await new Promise((ok) => setTimeout(ok, 500));
  }
  return { estado: 'reanudable', proceso_id: v.pid, error: 'TIEMPO_TOTAL_AGOTADO', detalle: 'sigue en el Router' };
};
try { liveRouter().catch(() => {}); } catch (e) {}
async function puenteRouter(base, body, qs, headers) {
  await liveRouter();
  const baseDe = () => (body && body.plugin ? PBASE + '/plugins/' + body.plugin + '/call' : CFG.harnessUrl);
  base = baseDe();
  const q = new URLSearchParams((qs || '').replace(/^[?]/, ''));
  const accion = q.get('accion') || 'chat';
  let payload = accion === 'chat' ? Object.assign({}, body || {}) : { job: q.get('job'), url: q.get('url') };
  if (accion === 'chat') {
    let s = (body && body.sesion) || sessionStorage.getItem('riu_sesion');
    if (!s) { s = 'web-' + Math.random().toString(36).slice(2, 10); sessionStorage.setItem('riu_sesion', s); }
    payload.sesion = s;
    payload.request_id = payload.request_id || ('rq-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 10));
  }
  const h = { 'Content-Type': 'application/json' };
  const pw = headers['X-Chat-Password'] || sessionStorage.getItem('riu_clave');
  if (pw) h['X-API-Key'] = pw;
  for (let intento = 0; intento < 2; intento++) {
    let r;
    for (let k = 0; k < 3; k++) {
      try { r = await fetchT(base.replace(/[/]+$/, '') + '/' + (accion === 'chat' ? 'chat_async' : accion), { method: 'POST', headers: h, body: JSON.stringify(payload) }, k ? 20000 : 15000); break; }
      catch (e) {
        if (k === 2) {
          const msg = String(e && e.message || e);
          if (/failed to fetch|networkerror|abort|timeout/i.test(msg)) {
            throw new Error('GAP: Space HF caído o dormido. Ve a Hugging Face → Space comand-center-1-riu-router → Restart.');
          }
          throw e;
        }
        liveCheckedAt = 0; await liveRouter(); base = baseDe();
        await new Promise(ok => setTimeout(ok, 800 * (k + 1)));
      }
    }
    const env = await r.json().catch(() => ({}));
    if (r.status === 401 || r.status === 403) return { status: 401, ok: false, p: env };
    if (!r.ok || env.status !== 'ok') return { status: r.ok ? 502 : r.status, ok: false, p: { error: env.reason || env.detail || ('HTTP ' + r.status) } };
    let p = env.result || {};
    let cortado = false;
    let proceso = p.proceso_id || null;
    if (p.estado === 'procesando' && p.proceso_id) {
      const deadline = Date.now() + 560000;
      try { window.dispatchEvent(new CustomEvent('riu-progreso', { detail: { sesion: payload.sesion, proceso_id: proceso, texto: 'En cola…' } })); } catch (e) {}
      if (payload && payload.sesion) guardaProc(payload.sesion, { pid: proceso, base, ts: Date.now() });
      let primera = true;
      let fallosRed = 0;
      let vaciosEstado = 0;
      while (p.estado === 'procesando' || !p.estado) {
        if (Date.now() > deadline) { cortado = true; break; }
        if (!primera) await new Promise(resolve => setTimeout(resolve, 250)); primera = false;
        try {
          const poll = await fetchT(base.replace(/[/]+$/, '') + '/resultado', { method: 'POST', headers: h, body: JSON.stringify({ proceso_id: proceso, espera: 8 }) }, 16000);
          const envelope = await poll.json().catch(() => ({}));
          if (poll.status === 401 || poll.status === 403) return { status: 401, ok: false, p: envelope };
          if (!poll.ok || envelope.status !== 'ok') throw new Error(envelope.reason || envelope.detail || ('HTTP ' + poll.status));
          p = envelope.result || {}; fallosRed = 0;
          if (!p.estado && !p.error && ++vaciosEstado >= 8) {
            return { status: 503, ok: false, p: { estado: 'reanudable', error: 'GAP_RESULTADO_TEMPORALMENTE_VACIO', detalle: 'El trabajo sigue asociado al mismo PID; usar Retomar', proceso_id: proceso } };
          }
          if (p.estado) vaciosEstado = 0;
          if (p.error && !p.estado) break;
          if (p.progreso || p.parcial) { try { window.dispatchEvent(new CustomEvent('riu-progreso', { detail: { sesion: payload.sesion, proceso_id: proceso, texto: p.progreso || '', parcial: p.parcial || '' } })); } catch (e) {} }
        } catch (e) {
          fallosRed++;
          try { window.dispatchEvent(new CustomEvent('riu-progreso', { detail: { sesion: payload.sesion, proceso_id: proceso, texto: 'Sin conexión con el Router (' + fallosRed + ')…' } })); } catch (x) {}
          if (fallosRed >= 12) return { status: 503, ok: false, p: { error: 'ROUTER_SIN_RESPUESTA', detalle: String(e && e.message || e).slice(0, 200), proceso_id: proceso } };
          continue;
        }
      }
    }
    if (!cortado && payload && payload.sesion) guardaProc(payload.sesion, null);
    if (cortado) { return { status: 504, ok: false, p: { estado: 'reanudable', error: 'TIEMPO_TOTAL_AGOTADO', detalle: 'El proceso sigue en el Router; no se relanza la tarea', proceso_id: proceso || p.proceso_id } }; }
    if (p.estado === 'encendiendo') return { status: 202, ok: true, p };
    if (p.error) return { status: 502, ok: false, p };
    return { status: 200, ok: true, p };
  }
}
async function puente(base, body, qs, method, headers) {
  if (String(base).includes('/plugins/puente_chat')) return puenteRouter(base, body, qs, headers);
  const r = await fetchT(base + (qs || ''), { method: method || 'POST', headers, body: method === 'GET' ? undefined : JSON.stringify(body) }, 15000);
  const p = await r.json().catch(() => ({}));
  return { status: r.status, ok: r.ok, p };
}
export async function accion(acc, payload) {
  await liveRouter();
  const h = { 'Content-Type': 'application/json' };
  const pw = sessionStorage.getItem('riu_clave');
  if (pw) h['X-API-Key'] = pw;
  payload = Object.assign({ sesion: sessionStorage.getItem('riu_sesion') || 'web-general' }, payload || {});
  const r = await fetchT(CFG.harnessUrl.replace(/[/]+$/, '') + '/' + acc, { method: 'POST', headers: h, body: JSON.stringify(payload) }, acc === 'subir' ? 60000 : acc === 'recurso_probar' ? 120000 : 15000);
  const env = await r.json().catch(() => ({}));
  if (!r.ok || env.status !== 'ok') throw new Error(env.reason || env.detail || ('HTTP ' + r.status));
  return env.result || {};
}
window.RIU_ACCION = accion;
export async function harness({ model, message, max_tokens, avisar, anclados, sesion, qwen, gobernanza, constitucion, fast_reply, contexto_previo, motor, project_id, instrucciones_fijas, mode_request, thinking_mode }) {
  const base = (window.RIU_CONFIG || {}).harnessUrl;
  const headers = { 'Content-Type': 'application/json' };
  const pw = sessionStorage.getItem('riu_clave');
  if (pw) headers['X-Chat-Password'] = pw;
  const messages = [{ role: 'user', content: message }];
  const extra = Object.assign(
    { active_anchors_v1: true },
    { sesion: sesion || undefined, anclados: anclados || [] },
    gobernanza !== undefined ? { gobernanza } : {},
    constitucion !== undefined ? { constitucion } : {},
    instrucciones_fijas ? { instrucciones_fijas } : {},
    fast_reply ? { fast_reply } : {},
    motor ? { motor } : {},
    project_id ? { project_id } : {},
    contexto_previo ? { contexto_previo } : {},
    mode_request ? { mode_request } : {},
    thinking_mode !== undefined ? { thinking_mode } : {},
    qwen ? { qwen: mode_request ? { ...qwen, mode_request } : qwen } : {}
  );
  const esHF = model.startsWith('hf-');
  let r;
  if (esHF && L4.url) {
    r = await puente(base, { model, messages, max_tokens, respaldo_url: L4.url, ...extra }, '', 'POST', headers);
    if (!r.ok) { L4.job = L4.url = null; r = null; }
  }
  if (!r) r = await puente(base, { model, messages, max_tokens, ...extra }, '', 'POST', headers);
  if (r.status === 202 && r.p.job_id) {
    L4.job = r.p.job_id; L4.url = null;
    window.__riuJob = r.p.job_id;
    if (avisar) avisar('Encendiendo modelo (aprox. 1 a 4 min)...');
    let listo = false;
    for (let i = 0; i < 80 && !listo; i++) {
      await new Promise((ok) => setTimeout(ok, 5000));
      const e = await puente(base, null, '?accion=estado&job=' + encodeURIComponent(r.p.job_id) + '&url=' + encodeURIComponent(r.p.url || ''), 'GET', headers);
      if (e.ok && e.p.listo) listo = true;
      else if (e.ok && ['ERROR', 'CANCELED', 'COMPLETED', 'DELETED'].includes(e.p.etapa)) { L4.job = null; throw new Error('El modelo se apago: ' + e.p.etapa); }
    }
    if (!listo) throw new Error('El modelo no encendio a tiempo');
    L4.url = r.p.url;
    r = await puente(base, { model, messages, max_tokens, respaldo_url: L4.url, ...extra }, '', 'POST', headers);
  }
  if (!r.ok) throw new Error(r.p.error || r.p.detail || ('HTTP ' + r.status));
  if (r.p && r.p.error) throw new Error(String(r.p.error));
  return { reply: ((r.p.choices && r.p.choices[0] && r.p.choices[0].message && r.p.choices[0].message.content) || ''), traza: r.p.traza, job_id: L4.job, tools: (r.p.herramientas || []).map((x) => ({ nombre: x.herramienta, ok: !!x.ok })), fast_lane: !!r.p.fast_lane, fast_consult: !!r.p.fast_consult, execution_path: r.p.execution_path || "HEAVY", ms: Number(r.p.ms || 0) };
}
window.RIU_HARNESS = harness;
export async function apagarRespaldo() {
  const base = (window.RIU_CONFIG || {}).harnessUrl;
  const headers = { 'Content-Type': 'application/json' };
  const pw = sessionStorage.getItem('riu_clave');
  if (pw) headers['X-Chat-Password'] = pw;
  const r = await puente(base, null, '?accion=apagar_todo', 'POST', headers);
  if (r.ok) { L4.job = L4.url = null; window.__riuJob = null; }
  return r;
}
window.RIU_APAGAR = apagarRespaldo;
export async function api(path, options = {}) {
  await liveRouter();
  if (!path.startsWith("/") || path.startsWith("//")) throw new Error("Ruta inválida");
  const headers = {};
  if (options.body !== undefined) headers["Content-Type"] = "application/json";
  let response;
  try {
    const credentials = remoto(headers);
    response = await fetchT(BASE + path, { method: options.method || "GET", headers, credentials,
      body: options.body === undefined ? undefined : JSON.stringify(options.body) }, path === "/chat/send" ? 120000 : 15000);
  } catch (error) {
    window.dispatchEvent(new CustomEvent("router-connection", { detail: "Sin conexión" }));
    throw error;
  }
  const status = response.status === 401 || response.status === 403 ? "Acceso requerido"
    : response.status >= 500 ? "Error de Router" : "Router disponible";
  window.dispatchEvent(new CustomEvent("router-connection", { detail: status }));
  const payload = response.headers.get("content-type")?.includes("application/json")
    ? await response.json() : { detail: `HTTP ${response.status}` };
  if (!response.ok) throw new Error(typeof payload.detail === "string" ? payload.detail : `HTTP ${response.status}`);
  return payload;
}
