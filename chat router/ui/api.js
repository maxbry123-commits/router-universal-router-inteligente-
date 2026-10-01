let key = "";
export function setKey(value) { key = value.trim(); }
export async function api(path, options = {}) {
  if (!path.startsWith("/") || path.startsWith("//")) throw new Error("Ruta inválida");
  const headers = { "X-API-Key": key };
  if (options.body !== undefined) headers["Content-Type"] = "application/json";
  const response = await fetch(path, { method: options.method || "GET", headers,
    body: options.body === undefined ? undefined : JSON.stringify(options.body) });
  const payload = await response.json();
  if (!response.ok) throw new Error(typeof payload.detail === "string" ? payload.detail : `HTTP ${response.status}`);
  return payload;
}
export async function media(id) {
  if (!/^[a-f0-9]{24}$/.test(id)) throw new Error("ID de archivo inválido");
  const response = await fetch(`/chat/media/${id}`, { headers: { "X-API-Key": key } });
  if (!response.ok) throw new Error(`MEDIA_HTTP_${response.status}`);
  return response.blob();
}
export function node(tag, text, className = "") {
  const element = document.createElement(tag);
  element.textContent = String(text ?? "");
  if (className) element.className = className;
  return element;
}
