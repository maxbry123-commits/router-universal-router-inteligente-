// api.js — Cliente API del Router (chat UI)
// Cambios: trae util `copiar` al portador final; `chat` acepta flujo + historial + stop; manejo de errores de red
const CFG = window.RIU_CONFIG || {};
let BASE = "";  // sin base hardcodeada: la única fuente de verdad es LIVE_URL.json
let liveVerified = false;  // solo tras una resolución real de LIVE_URL se conserva BASE en la sesión

let liveCheckedAt = 0;
let liveRequest = null;
let PBASE = "";  // base de los plugins (chat_async, /resultado): mismo origen en Vercel (rewrites de vercel.json) o el Space directo
// fetch con tope: en movil (4G, pestaña en segundo plano) un fetch puede quedar colgado para siempre y el chat se queda en "Pensando" sin que el Router reciba nada
const vivos = new Set();
const fetchT = (url, opts, ms) => { const ac = typeof AbortController === 'function' ? new AbortController() : null; const reg = ac ? { ac, t0: Date.now() } : null; if (reg) vivos.add(reg); const t = setTimeout(() => ac && ac.abort(), ms); return fetch(url, Object.assign({}, opts || {}, ac ? { signal: ac.signal } : {})).finally(() => { clearTimeout(t); if (reg) vivos.delete(reg); }); };
// al volver a la pestaña: cortar los fetch que quedaron colgados en segundo plano; el polling sigue con el mismo proceso_id y un chat_async sin proceso_id se reintenta
try { document.addEventListener('visibilitychange', () => { if (document.visibilityState !== 'visible') return; for (const r of [...vivos]) if (Date.now() - r.t0 > 2000) { try { r.ac.abort(); } catch (e) {} } }); } catch (e) {}
const usarProxy = () => { try { return /\.vercel\.app$/.test(location.hostname) && localStorage.getItem('riu_proxy') !== '0' && !/[?&]proxy=0/.test(location.search); } catch (e) { return false; } };
function aplicarBase(url) {
  BASE = url;
  // mismo origen: en Vercel, si LIVE_URL es el Space al que apuntan los rewrites, los plugins van por location.origin (4G no corta *.hf.space). ?proxy=0 o localStorage riu_proxy=0 lo apaga
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
  if (!BASE) {  // no bloquear el envio esperando raw.githubusercontent: ultima direccion buena o el Space fijo de config.js
    let c = ''; try { c = localStorage.getItem('riu_live_url') || ''; } catch (e) {}
    if (!VALIDA(c)) c = CFG.proxyDestino || '';
    if (VALIDA(c)) aplicarBase(c);
  }
  if (Date.now() - liveCheckedAt >= 30000) { const pr = refrescarLive(); if (!BASE) return pr; pr.catch(() => {}); }  // con BASE: refresco en segundo plano
  return BASE;
}

function clave() {
  return sessionStorage.getItem("riu_clave") || "";
}
function remoto(headers) {
  if (BASE) headers[CFG.authHeader || "X-API-Key"] = clave();
  return BASE ? "omit" : "same-origin";
}
const L4 = { job: null, url: null };
// ---- procesos en curso: una recarga NO relanza la tarea; se retoma por su proceso_id (sesion, proceso_id, direccion exacta del Router, hora) ----
const CP = 'riu_proc_v1';
const procs = () => { try { return JSON.parse(localStorage.getItem(CP) || '{}'); } catch (e) { return {}; } };
const guardaProc = (ses, v) => { try { const t = procs(); if (v) t[ses] = v; else delete t[ses]; localStorage.setItem(CP, JSON.stringify(t)); } catch (e) {} };
const hdrs = () => { const k = sessionStorage.getItem('riu_clave'); const h = { 'Content-Type': 'application/json' }; if (k) { h['X-API-Key'] = k; h.Authorization = 'Bearer ' + k; } return h; };
window.RIU_PENDIENTE = (ses) => procs()[ses] || null;
window.RIU_CANCELAR = async (ses) => {  // Detener: en cola se cancela antes de ejecutar; si ya corre, el Router no lanza los pasos siguientes
  const v = procs()[ses]; if (!v) return false; guardaProc(ses, null);
  try { await fetch(v.base.replace(/[/]+$/, '') + '/cancelar', { method: 'POST', headers: hdrs(), body: JSON.stringify({ proceso_id: v.pid }) }); } catch (e) {}
  return true;
};
window.RIU_RETOMAR = async (ses) => {
  const v = procs()[ses]; if (!v) return null; const fin = Date.now() + 560000; let malos = 0;
  while (Date.now() < fin) {
    if (!procs()[ses]) return { error: 'PROCESO_DETENIDO' };  // Detener sobre una tarea retomada: RIU_CANCELAR ya borro el registro y aviso al Router

    try {
      const r = await fetchT(v.base.replace(/[/]+$/, '') + '/resultado', { method: 'POST', headers: hdrs(), body: JSON.stringify({ proceso_id: v.pid }) }, 10000);
      const e = await r.json().catch(() => ({})); const p = e.result || {};
      if (!r.ok || e.status !== 'ok') { if (++malos >= 8) { guardaProc(ses, null); return { error: e.reason || e.detail || ('HTTP ' + r.status) }; } }  // respuesta invalida repetida: cortar, no girar 560 s
      else if (p.error) { guardaProc(ses, null); return p; }  // error real del proceso (PROCESO_NO_EXISTE tras reinicio): borrar PID y devolver ya
      else if (p.estado && p.estado !== 'procesando') { guardaProc(ses, null); return p; }
      else if (!p.estado) { if (++malos >= 8) { guardaProc(ses, null); return { error: 'RESULTADO_VACIO' }; } }
      else malos = 0;
    } catch (x) { if (++malos >= 40) { guardaProc(ses, null); return { error: 'ROUTER_SIN_RESPUESTA' }; } }  // red caida ~20 s seguidos: cortar con aviso
    await new Promise((ok) => setTimeout(ok, 500));
  }
  return { error: 'TIEMPO_TOTAL_AGOTADO', detalle: 'sigue en el Router' };
};
async function puenteRouter(base, body, qs, headers) {
  await liveRouter();
  const baseDe = () => (body && body.plugin ? PBASE + '/plugins/' + body.plugin + '/call' : CFG.harnessUrl);  // plugin del Router elegido por el selector
  base = baseDe();
  // Puente dentro del Router (plugin puente_chat, puerta fija): POST <base>/<accion>, respuesta {status, result}.
  const q = new URLSearchParams((qs || '').replace(/^[?]/, ''));
  const accion = q.get('accion') || 'chat';
  let payload = accion === 'chat' ? Object.assign({}, body || {}) : { job: q.get('job'), url: q.get('url') };
  if (accion === 'chat') {
    // sesion por estancia de chat (pestaña): cada chat lleva la suya
    let s = (body && body.sesion) || sessionStorage.getItem('riu_sesion');
    if (!s) { s = 'web-' + Math.random().toString(36).slice(2, 10); sessionStorage.setItem('riu_sesion', s); }
    payload.sesion = s;
  }
  const h = { 'Content-Type': 'application/json' };
  const pw = headers['X-Chat-Password'] || sessionStorage.getItem('riu_clave');
  if (pw) h['X-API-Key'] = pw;
  for (let intento = 0; intento < 2; intento++) {
    let r;
    try {
      r = await fetchT(base.replace(/[/]+$/, '') + '/' + (accion === 'chat' ? 'chat_async' : accion), { method: 'POST', headers: h, body: JSON.stringify(payload) }, 30000);
    } catch (e) {
      // job en cambio de direccion: releer LIVE_URL y reintentar una vez
      liveCheckedAt = 0;
      await liveRouter();
      base = baseDe();  // sin proceso_id todavia: reintenta el POST una vez (misma u otra direccion)
      r = await fetchT(base.replace(/[/]+$/, '') + '/' + (accion === 'chat' ? 'chat_async' : accion), { method: 'POST', headers: h, body: JSON.stringify(payload) }, 30000);
    }
    const env = await r.json().catch(() => ({}));
    if (r.status === 401 || r.status === 403) return { status: 401, ok: false, p: env };
    if (!r.ok || env.status !== 'ok') return { status: r.ok ? 502 : r.status, ok: false, p: { error: env.reason || env.detail || ('HTTP ' + r.status) } };
    let p = env.result || {};
    let cortado = false;
    if (p.estado === 'procesando' && p.proceso_id) {
      const deadline = Date.now() + 560000;
      const proceso = p.proceso_id;
      try { window.dispatchEvent(new CustomEvent('riu-progreso', { detail: { sesion: payload.sesion, proceso_id: proceso, texto: 'En cola…' } })); } catch (e) {}  // process_id != modelo corriendo: el backend informa el estado real; sesion+pid aíslan el progreso entre chats
      if (payload && payload.sesion) guardaProc(payload.sesion, { pid: proceso, base, ts: Date.now() });
      let primera = true;  // primera consulta inmediata, luego cada 250 ms (tope total sigue en deadline 560 s)
      let fallosRed = 0;  // fix 5: la red caida ya no se oculta para siempre
      while (p.estado === 'procesando') {
        if (Date.now() > deadline) { cortado = true; break; }
        if (!primera) await new Promise(resolve => setTimeout(resolve, 250)); primera = false;
        try {
          const poll = await fetchT(base.replace(/[/]+$/, '') + '/resultado', { method: 'POST', headers: h, body: JSON.stringify({ proceso_id: proceso }) }, 15000);
          const envelope = await poll.json().catch(() => ({}));
          if (!poll.ok || envelope.status !== 'ok') return { status: poll.status, ok: false, p: { error: envelope.reason || envelope.detail || 'Error al consultar la respuesta' } };
          p = envelope.result || {}; fallosRed = 0; if (p.progreso) { try { window.dispatchEvent(new CustomEvent('riu-progreso', { detail: { sesion: payload.sesion, proceso_id: proceso, texto: p.progreso } })); } catch (e) {} }
        } catch (e) {  // red/job en cambio: seguir esperando, pero avisar y cortar tras 80 fallos seguidos (~20 s a 250 ms)
          fallosRed++;
          try { window.dispatchEvent(new CustomEvent('riu-progreso', { detail: { sesion: payload.sesion, proceso_id: proceso, texto: 'Sin conexión con el Router (' + fallosRed + ')…' } })); } catch (x) {}
          if (fallosRed >= 80) return { status: 503, ok: false, p: { error: 'ROUTER_SIN_RESPUESTA', detalle: String(e && e.message || e).slice(0, 200), proceso_id: proceso } };
          continue;
        }
      }
    }
    if (!cortado && payload && payload.sesion) guardaProc(payload.sesion, null);  // termino: ya no hay nada que retomar
    if (cortado) { return { status: 504, ok: false, p: { error: 'TIEMPO_TOTAL_AGOTADO', detalle: 'El proceso sigue en el Router; no se relanza la tarea', proceso_id: p.proceso_id } }; }
    if (p.estado === 'encendiendo') return { status: 202, ok: true, p };
    if (p.error) return { status: 502, ok: false, p };  // proceso terminado en error: NO se relanza otro chat_async (el reintento de red de LIVE_URL solo vale antes de obtener proceso_id)
    return { status: 200, ok: true, p };
  }
}
async function puente(base, body, qs, method, headers) {
  if (String(base).includes('/plugins/puente_chat')) return puenteRouter(base, body, qs, headers);
  const r = await fetch(base + (qs || ''), { method: method || 'POST', headers, body: method === 'GET' ? undefined : JSON.stringify(body) });
  const p = await r.json().catch(() => ({}));
  return { status: r.status, ok: r.ok, p };
}
export async function accion(acc, payload) {
  // cualquier accion del puente (subir, archivos, xray, auditor_code, handoff, sandbox, ...)
  await liveRouter();
  const h = { 'Content-Type': 'application/json' };
  const pw = sessionStorage.getItem('riu_clave');
  if (pw) h['X-API-Key'] = pw;
  payload = Object.assign({ sesion: sessionStorage.getItem('riu_sesion') || 'web-general' }, payload || {});
  const r = await fetch(CFG.harnessUrl.replace(/[/]+$/, '') + '/' + acc, { method: 'POST', headers: h, body: JSON.stringify(payload) });
  const env = await r.json().catch(() => ({}));
  if (!r.ok || env.status !== 'ok') throw new Error(env.reason || env.detail || ('HTTP ' + r.status));
  return env.result || {};
}
window.RIU_ACCION = accion;
export async function harness({ model, message, max_tokens, avisar, anclados, sesion, qwen, gobernanza, constitucion, fast_reply, contexto_previo, motor, project_id }) {
  const base = (window.RIU_CONFIG || {}).harnessUrl;
  const headers = { 'Content-Type': 'application/json' };
  const pw = sessionStorage.getItem('riu_clave');
  if (pw) headers['X-Chat-Password'] = pw;
  const messages = [{ role: 'user', content: message }];
  const esHF = model.startsWith('hf-');
  const extra = Object.assign((anclados && anclados.length) ? { anclados } : {}, sesion ? { sesion } : {}, gobernanza ? { gobernanza } : {}, constitucion ? { constitucion } : {}, typeof fast_reply === "boolean" ? { fast_reply } : {}, motor ? { motor: true } : {}, project_id ? { project_id } : {}, Array.isArray(contexto_previo) && contexto_previo.length ? { contexto_previo } : {}, qwen || {});  // qwen: selector Qwen -> plugin fichas_qwen
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
  const prueba = Array.isArray(r.p.traza) && r.p.traza.length ? '\n\n— Prueba de ejecución —\n' + r.p.traza.filter((t) => t.modelo !== 'goals').map((t) => t.nodo + ' · ' + String(t.modelo).replace('ficha-', '') + ' · ' + (t.rol || '') + (t.ok ? ' ✔' : ' ✘')).join('\n') : '';
  return { reply: ((r.p.choices && r.p.choices[0] && r.p.choices[0].message && r.p.choices[0].message.content) || ''), traza: r.p.traza, job_id: L4.job, tools: (r.p.herramientas || []).map((x) => ({ nombre: x.herramienta, ok: !!x.ok })), fast_lane: !!r.p.fast_lane, fast_consult: !!r.p.fast_consult, execution_path: r.p.execution_path || "HEAVY", ms: Number(r.p.ms || 0) };
}
window.RIU_HARNESS = harness;
export async function apagarRespaldo() {
  const base = (window.RIU_CONFIG || {}).harnessUrl;
  // apaga TODOS los L4 de respaldo (el Router solo apaga los suyos), haya o no un job conocido
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
    response = await fetch(BASE + path, { method: options.method || "GET", headers, credentials,
      body: options.body === undefined ? undefined : JSON.stringify(options.body) });
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
export async function media(id) {
  await liveRouter();
  if (!/^[a-f0-9]{24}$/.test(id)) throw new Error("ID de archivo inválido");
  const headers = {};
  const credentials = remoto(headers);
  const response = await fetch(`${BASE}/chat/media/${id}`, { headers, credentials });
  if (!response.ok) throw new Error(`MEDIA_HTTP_${response.status}`);
  return response.blob();
}
export function node(tag, text, className = "") {
  const element = document.createElement(tag);
  element.textContent = String(text ?? "");
  if (className) element.className = className;
  return element;
}