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
export async function harness(body) {
  const headers = { "Content-Type": "application/json", [CFG.authHeader || "X-API-Key"]: clave() };
  const response = await fetch(CFG.harnessUrl, { method: "POST", headers, body: JSON.stringify(body) });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail || `HARNESS_HTTP_${response.status}`);
  return { reply: payload.reply || payload.respuesta || payload.answer || payload.text || "" };
}
window.RIU_HARNESS = harness;
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
