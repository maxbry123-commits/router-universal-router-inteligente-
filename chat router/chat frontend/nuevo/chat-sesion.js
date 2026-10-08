// chat-sesion.js — Punto 1: chats aislados del panel "Chat nuevo".
// Cada chat tiene su propia sesion (id unico "web-…", mismo formato que el chat actual) y su propio historial.
// El id viaja al Router como `sesion` (puente_chat guarda la memoria en el scope chat:<sesion>);
// por la ruta /chat/send se guarda por chat el conversation_id que devuelve el servidor.
// Claves propias (no se mezclan con riu_chats_v1 del chat actual). El chat activo es por pestaña.
const INDICE = "riu_nuevo_chats_v1";
const HIST = "riu_nuevo_hist_v1:";
const ACTIVO = "riu_nuevo_chat_activo";
const MAX_MENSAJES = 200;
// Punto 5: un chat hijo es otra sesion "<padre>:ag:<agente>:<n>" (máx. 60, mismo límite que el Router).
const ID_RE = /^web-[a-z0-9]{8,56}(?::ag:[a-z0-9][a-z0-9_-]{1,63}:\d{1,6})*$/;
const ID_OK = { test: id => typeof id === "string" && id.length <= 60 && ID_RE.test(id) };

const leer = (clave, defecto) => {
  try { return JSON.parse(localStorage.getItem(clave)) ?? defecto; } catch { return defecto; }
};
const escribir = (clave, valor) => {
  try { localStorage.setItem(clave, JSON.stringify(valor)); return true; } catch { return false; }
};
const indice = () => {
  const lista = leer(INDICE, []);
  return Array.isArray(lista) ? lista.filter(c => c && ID_OK.test(c.id)) : [];
};

export function nuevoId() {
  const bytes = crypto.getRandomValues(new Uint8Array(8));
  return "web-" + Array.from(bytes, b => b.toString(16).padStart(2, "0")).join("");
}

export function listar() { return indice(); }

export function crear() {
  const chat = { id: nuevoId(), titulo: "", creado: Date.now(), conversation_id: null };
  escribir(INDICE, [...indice(), chat]);
  sessionStorage.setItem(ACTIVO, chat.id);
  return chat;
}

export function activar(id) {
  if (indice().some(c => c.id === id)) sessionStorage.setItem(ACTIVO, id);
}

export function activo() {
  const lista = indice();
  const id = sessionStorage.getItem(ACTIVO);
  return lista.find(c => c.id === id) || lista[lista.length - 1] || crear();
}

export function mensajes(id) {
  const lista = ID_OK.test(id) ? leer(HIST + id, []) : [];
  return Array.isArray(lista) ? lista : [];
}

export function agregar(id, rol, texto) {
  if (!ID_OK.test(id)) return;
  const lista = [...mensajes(id), { rol, texto: String(texto ?? ""), t: Date.now() }].slice(-MAX_MENSAJES);
  escribir(HIST + id, lista);
  if (rol === "user") actualizar(id, c => c.titulo ? c : { ...c, titulo: String(texto).slice(0, 28) });
}

export function fijarConversacion(id, conversationId) {
  if (typeof conversationId === "string" && conversationId)
    actualizar(id, c => ({ ...c, conversation_id: conversationId }));
}

// Punto 2: fusiona el historial del servidor (GET /chat/history/{sesion}, más antiguo primero) con el local.
// El servidor manda: sus mensajes quedan marcados srv; los locales ya confirmados que el servidor no tiene se descartan.
// Duplicados por rol+contenido+ts; un local sin confirmar se une a su copia del servidor si coincide rol+contenido
// dentro de VENTANA (el servidor guarda el turno al terminar la respuesta, el navegador al enviarlo).
const ROLES = { user: "user", assistant: "router" };
const VENTANA = 15 * 60 * 1000;
const aMs = ts => {
  const n = typeof ts === "number" ? ts : Number(ts);
  if (Number.isFinite(n)) return n < 1e12 ? Math.round(n * 1000) : n;
  const d = Date.parse(ts);
  return Number.isFinite(d) ? d : 0;
};
const clave = m => `${m.rol}\u0000${m.texto}\u0000${m.t}`;

export function fusionar(id, remotos) {
  if (!ID_OK.test(id) || !Array.isArray(remotos)) return null;
  const servidor = remotos.filter(m => m && m.content != null)
    .map(m => ({ rol: ROLES[m.role] || "nota", texto: String(m.content), t: aMs(m.ts), srv: true }));
  const exactas = new Set(servidor.map(clave));
  const usados = new Set();
  const locales = mensajes(id).filter(m => {
    if (exactas.has(clave(m)) || m.srv) return false;
    const i = servidor.findIndex((s, k) => !usados.has(k) && s.rol === m.rol && s.texto === m.texto && Math.abs(s.t - m.t) <= VENTANA);
    if (i >= 0) { usados.add(i); return false; }
    return true;
  });
  const lista = [...servidor, ...locales].sort((a, b) => a.t - b.t).slice(-MAX_MENSAJES);
  escribir(HIST + id, lista);
  const primera = servidor.find(m => m.rol === "user");
  if (primera) actualizar(id, c => c.titulo ? c : { ...c, titulo: primera.texto.slice(0, 28) });
  return { servidor: servidor.length, soloLocales: locales.length };
}

// Punto 4: nombres de archivos anclados por chat; viajan como `anclados` en cada mensaje de ese chat.
export function anclados(id) {
  const chat = indice().find(c => c.id === id);
  return Array.isArray(chat?.anclados) ? chat.anclados.filter(n => typeof n === "string") : [];
}

export function fijarAnclados(id, nombres) {
  actualizar(id, c => ({ ...c, anclados: [...new Set(nombres)] }));
}

// Punto 5: chats hijos (agente anclado). Se guardan en el mismo índice con `padre`; el Router manda la lista.
export function hijas(padre) { return indice().filter(c => c.padre === padre); }

export function registrarHijas(padre, lista, completa = false) {
  const nuevas = (Array.isArray(lista) ? lista : []).filter(h => h && ID_OK.test(h.sesion_hija) && h.padre === padre);
  const ids = new Set(nuevas.map(h => h.sesion_hija));
  const previas = new Map(indice().filter(c => c.padre === padre).map(c => [c.id, c]));
  const resto = indice().filter(c => c.padre !== padre || (!completa && !ids.has(c.id)));
  const hijasFinal = nuevas.map(h => ({ ...(previas.get(h.sesion_hija) || { titulo: "", conversation_id: null }),
    id: h.sesion_hija, padre, agente: h.agente, n: h.n, input_block_sha256: h.input_block_sha256,
    creado: previas.get(h.sesion_hija)?.creado || Date.now(), titulo: `${h.agente} #${h.n}`,
    ...(h.sha_enviado ? { sha_enviado: h.sha_enviado } : {}) }));
  escribir(INDICE, [...resto, ...hijasFinal]);
}

function actualizar(id, cambio) {
  escribir(INDICE, indice().map(c => c.id === id ? cambio(c) : c));
}
