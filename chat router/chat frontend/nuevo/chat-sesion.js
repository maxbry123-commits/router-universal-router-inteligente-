// chat-sesion.js — Punto 1: chats aislados del panel "Chat nuevo".
// Cada chat tiene su propia sesion (id unico "web-…", mismo formato que el chat actual) y su propio historial.
// El id viaja al Router como `sesion` (puente_chat guarda la memoria en el scope chat:<sesion>);
// por la ruta /chat/send se guarda por chat el conversation_id que devuelve el servidor.
// Claves propias (no se mezclan con riu_chats_v1 del chat actual). El chat activo es por pestaña.
const INDICE = "riu_nuevo_chats_v1";
const HIST = "riu_nuevo_hist_v1:";
const ACTIVO = "riu_nuevo_chat_activo";
const MAX_MENSAJES = 200;
const ID_OK = /^web-[a-z0-9]{8,56}$/;

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

function actualizar(id, cambio) {
  escribir(INDICE, indice().map(c => c.id === id ? cambio(c) : c));
}
