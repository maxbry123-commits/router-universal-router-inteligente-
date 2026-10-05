const CFG = window.RIU_CONFIG || {};
const BASE = (CFG.apiBase || "").replace(/[/]+$/, "");
function clave() {
  let k = sessionStorage.getItem("riu_clave");
  if (!k) { k = prompt("Clave de acceso") || ""; sessionStorage.setItem("riu_clave", k); }
  return k;
}
function remoto(headers) {
  if (BASE) headers[CFG.authHeader || "X-API-Key"] = clave();
  return BASE ? "include" : "same-origin";
}
const L4 = { job: null, url: null };
async function puente(base, body, qs, method, headers) {
  const r = await fetch(base + (qs || ''), { method: method || 'POST', headers, body: method === 'GET' ? undefined : JSON.stringify(body) });
  const p = await r.json().catch(() => ({}));
  return { status: r.status, ok: r.ok, p };
}
export async function harness({ model, message, max_tokens, avisar }) {
  const base = (window.RIU_CONFIG || {}).harnessUrl;
  const headers = { 'Content-Type': 'application/json' };
  const pw = sessionStorage.getItem('riu_clave');
  if (pw) headers['X-Chat-Password'] = pw;
  const messages = [{ role: 'user', content: message }];
  const esHF = model.startsWith('hf-');
  let r;
  if (esHF && L4.url) {
    r = await puente(base, { model, messages, max_tokens, respaldo_url: L4.url }, '', 'POST', headers);
    if (!r.ok) { L4.job = L4.url = null; r = null; }
  }
  if (!r) r = await puente(base, { model, messages, max_tokens }, '', 'POST', headers);
  if (r.status === 401) {
    const k = prompt('Contrasena del chat');
    if (k) { sessionStorage.setItem('riu_clave', k); return harness({ model, message, max_tokens, avisar }); }
  }
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
    r = await puente(base, { model, messages, max_tokens, respaldo_url: L4.url }, '', 'POST', headers);
  }
  if (!r.ok) throw new Error(r.p.error || r.p.detail || ('HTTP ' + r.status));
  return { reply: (r.p.choices && r.p.choices[0] && r.p.choices[0].message && r.p.choices[0].message.content) || '', job_id: L4.job };
}
window.RIU_HARNESS = harness;
export async function apagarRespaldo() {
  const base = (window.RIU_CONFIG || {}).harnessUrl;
  const job = L4.job || window.__riuJob;
  const headers = { 'Content-Type': 'application/json' };
  const pw = sessionStorage.getItem('riu_clave');
  if (pw) headers['X-Chat-Password'] = pw;
  const r = await puente(base, null, '?accion=apagar&job=' + encodeURIComponent(job), 'POST', headers);
  if (r.ok) { L4.job = L4.url = null; window.__riuJob = null; }
  return r;
}
window.RIU_APAGAR = apagarRespaldo;
export async function api(path, options = {}) {
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
