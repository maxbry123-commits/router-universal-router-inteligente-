// api.js — Cliente API del Router (chat UI)
// Cambios: trae util `copiar` al portador final; `chat` acepta flujo + historial + stop; manejo de errores de red
const CFG = window.RIU_CONFIG || {};
let BASE = (CFG.apiBase || "").replace(/[/]+$/, "");

let liveCheckedAt = 0;
let liveRequest = null;
async function liveRouter() {
  if (CFG.routerStopped) throw new Error('Router detenido por orden del Director');
  if (Date.now() - liveCheckedAt < 30000) return BASE;
  if (!liveRequest) liveRequest = (async () => {
    try {
      const flag = await fetch(CFG.liveUrl + '?t=' + Date.now(), { cache: 'no-store', credentials: 'omit' });
      if (!flag.ok) throw new Error('Dirección HF no disponible');
      const info = await flag.json();
      if (!/^https:\/\/[a-f0-9]{24}--8000\.hf\.jobs$/.test(info.LIVE_URL || '')) throw new Error('Dirección HF inválida');
      BASE = info.LIVE_URL;
      CFG.apiBase = BASE;
      CFG.harnessUrl = BASE + '/plugins/puente_chat/call';
      liveCheckedAt = Date.now();
    } catch (error) {
      if (!BASE) throw error;
    } finally { liveRequest = null; }
    return BASE;
  })();
  return liveRequest;
}

function clave() {
  return sessionStorage.getItem("riu_clave") || "";
}
function remoto(headers) {
  if (BASE) headers[CFG.authHeader || "X-API-Key"] = clave();
  return BASE ? "omit" : "same-origin";
}
const L4 = { job: null, url: null };
function espera(ms, signal) {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) { reject(new DOMException("Detenido", "AbortError")); return; }
    const terminar = () => { signal?.removeEventListener("abort", detener); resolve(); };
    const timer = setTimeout(terminar, ms);
    function detener() {
      clearTimeout(timer);
      signal.removeEventListener("abort", detener);
      reject(new DOMException("Detenido", "AbortError"));
    }
    signal?.addEventListener("abort", detener, { once: true });
  });
}
async function puenteRouter(base, body, qs, headers, signal) {
  await liveRouter();
  base = CFG.harnessUrl;
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
  {
    // No reenviar chat_async: una respuesta de red perdida no implica que el job no se inició.
    const r = await fetch(base.replace(/[/]+$/, '') + '/' + (accion === 'chat' ? 'chat_async' : accion), { method: 'POST', headers: h, body: JSON.stringify(payload), signal });
    const env = await r.json().catch(() => ({}));
    if (r.status === 401 || r.status === 403) return { status: 401, ok: false, p: env };
    if (!r.ok || env.status !== 'ok') return { status: r.ok ? 502 : r.status, ok: false, p: { error: env.reason || env.detail || ('HTTP ' + r.status) } };
    let p = env.result || {};
    let cortado = false;
    if (p.estado === 'procesando' && p.proceso_id) {
      const deadline = Date.now() + 930000;
      const proceso = p.proceso_id;
      while (p.estado === 'procesando') {
        if (Date.now() > deadline) { cortado = true; break; }
        await espera(1000, signal);
        try {
          const poll = await fetch(base.replace(/[/]+$/, '') + '/resultado', { method: 'POST', headers: h, body: JSON.stringify({ proceso_id: proceso }), signal });
          const envelope = await poll.json().catch(() => ({}));
          if (!poll.ok || envelope.status !== 'ok') return { status: poll.status, ok: false, p: { error: envelope.reason || envelope.detail || 'Error al consultar la respuesta' } };
          p = envelope.result || {};
        } catch (e) { if (signal?.aborted) throw e; continue; }
      }
    }
    if (cortado) return { status: 504, ok: false, p: { error: 'La espera local terminó; el job remoto puede continuar' } };
    if (p.estado === 'encendiendo') return { status: 202, ok: true, p };
    if (p.error) {
      return { status: 502, ok: false, p };
    }
    return { status: 200, ok: true, p };
  }
}
async function puente(base, body, qs, method, headers, signal) {
  if (String(base).includes('/plugins/puente_chat')) return puenteRouter(base, body, qs, headers, signal);
  const r = await fetch(base + (qs || ''), { method: method || 'POST', headers, body: method === 'GET' ? undefined : JSON.stringify(body), signal });
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
  if (!env.result || env.result.error || env.result.ok === false)
    throw new Error(env.result?.error || "ACCION_SIN_CONFIRMACION");
  return env.result;
}
window.RIU_ACCION = accion;
window.YAIWES_PLUGIN_BRIDGE = Object.freeze({
  execute(actionId, payload) {
    if (actionId === "chat.send") return harness(payload);
    return accion(actionId, payload);
  }
});
export async function harness({ model, message, max_tokens, avisar, anclados, sesion, task_id, signal }) {
  const base = (window.RIU_CONFIG || {}).harnessUrl;
  const headers = { 'Content-Type': 'application/json' };
  const pw = sessionStorage.getItem('riu_clave');
  if (pw) headers['X-Chat-Password'] = pw;
  const messages = [{ role: 'user', content: message }];
  const esHF = model.startsWith('hf-');
  const extra = Object.assign((anclados && anclados.length) ? { anclados } : {}, sesion ? { sesion } : {}, task_id ? { task_id } : {});
  let r;
  if (esHF && L4.url) {
    r = await puente(base, { model, messages, max_tokens, respaldo_url: L4.url, ...extra }, '', 'POST', headers, signal);
    if (!r.ok) { L4.job = L4.url = null; r = null; }
  }
  if (!r) r = await puente(base, { model, messages, max_tokens, ...extra }, '', 'POST', headers, signal);
  if (r.status === 202 && r.p.job_id) {
    L4.job = r.p.job_id; L4.url = null;
    window.__riuJob = r.p.job_id;
    if (avisar) avisar('Encendiendo modelo (aprox. 1 a 4 min)...');
    let listo = false;
    for (let i = 0; i < 80 && !listo; i++) {
      await espera(5000, signal);
      const e = await puente(base, null, '?accion=estado&job=' + encodeURIComponent(r.p.job) + '&url=' + encodeURIComponent(r.p.url || ''), 'GET', headers, signal);
      if (e.ok && e.p.listo) listo = true;
      else if (e.ok && ['ERROR', 'CANCELED', 'COMPLETED', 'DELETED'].includes(e.p.etapa)) { L4.job = null; throw new Error('El modelo se apago: ' + e.p.etapa); }
    }
    if (!listo) throw new Error('El modelo no encendio a tiempo');
    L4.url = r.p.url;
    r = await puente(base, { model, messages, max_tokens, respaldo_url: L4.url, ...extra }, '', 'POST', headers, signal);
  }
  if (!r.ok) throw new Error(r.p.error || r.p.detail || ('HTTP ' + r.status));
  return { reply: (r.p.choices && r.p.choices[0] && r.p.choices[0].message && r.p.choices[0].message.content) || '', job_id: L4.job, tools: (r.p.herramientas || []).map((x) => ({ nombre: x.herramienta, ok: !!x.ok })) };
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
      body: options.body === undefined ? undefined : JSON.stringify(options.body), signal: options.signal });
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