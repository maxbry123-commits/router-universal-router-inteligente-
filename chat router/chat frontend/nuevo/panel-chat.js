import { api, harness, node } from "../api.js";
import { tell } from "./base.js";
import { activar, activo, agregar, anclados, crear, fijarConversacion, fusionar, listar, mensajes } from "./chat-sesion.js";
import { montarArchivos } from "./chat-archivos.js";

const select = (id, entries, value, label) => {
  const target = document.querySelector(id);
  for (const entry of entries) {
    const option = node("option", entry[label]);
    option.value = entry[value];
    target.append(option);
  }
};

const fichas = window.RIU_CONFIG?.modelos || [];
select("#ficha", fichas, "id", "etiqueta");
if (window.RIU_CONFIG?.defecto) document.querySelector("#ficha").value = window.RIU_CONFIG.defecto;

async function loadSelectors() {
  try {
    const [providers, agents] = await Promise.all([api("/chat/providers"), api("/chat/agents")]);
    select("#provider", (providers.providers || []).filter(item => item.id !== "auto"), "id", "label");
    select("#agent", agents.agents || [], "id", "name");
  } catch (error) { tell(`Opciones no disponibles: ${error.message}`); }
}

document.querySelector("#provider").addEventListener("change", async event => {
  const model = document.querySelector("#model");
  model.replaceChildren(node("option", "Router elige"));
  if (event.target.value === "auto") return;
  try {
    const result = await api(`/chat/providers/${encodeURIComponent(event.target.value)}/models`);
    if (event.target.value === document.querySelector("#provider").value)
      select("#model", result.models || [], "model_id", "label");
  } catch (error) { tell(error.message); }
});

// Chats aislados: cada chat tiene su sesion y su historial; cambiar de chat muestra solo los suyos.
const CLASES = { user: "item message user", router: "item message", nota: "item message muted", error: "item message" };
function pintarChats() {
  const actual = activo();
  document.querySelector("#chat-tabs").replaceChildren(...listar().map((chat, i) => {
    const tab = node("button", chat.titulo || `Chat ${i + 1}`, "chat-tab");
    tab.type = "button";
    tab.title = `Sesión ${chat.id}`;
    tab.setAttribute("role", "tab");
    tab.setAttribute("aria-selected", String(chat.id === actual.id));
    tab.addEventListener("click", () => { activar(chat.id); pintarChats(); void sincronizar(chat.id); });
    return tab;
  }));
  document.querySelector("#chat-id").textContent = `Sesión: ${actual.id}`;
  const history = document.querySelector("#history");
  history.replaceChildren(...mensajes(actual.id).map(m => node("div", m.texto, CLASES[m.rol] || CLASES.router)));
  history.scrollTop = history.scrollHeight;
}
// Punto 2: al abrir un chat o recargar, trae su historial del Router y lo fusiona con el local.
function origen(texto, tipo, detalle = "") {
  const marca = document.querySelector("#historial-origen");
  marca.textContent = texto;
  marca.dataset.origen = tipo;
  marca.title = detalle;
}
const archivos = montarArchivos({ activoId: () => activo().id });  // Punto 4: archivos del chat activo
async function sincronizar(id) {
  void archivos.cargar(id);  // al abrir/crear/recargar un chat también se recargan sus archivos
  if (activo().id === id) origen("Historial: consultando servidor…", "cargando");
  try {
    const respuesta = await api(`/chat/history/${encodeURIComponent(id)}?limit=200`);
    const resultado = fusionar(id, respuesta?.messages);
    if (!resultado) throw new Error("respuesta sin messages");
    if (activo().id !== id) return;
    pintarChats();
    origen(resultado.soloLocales ? `Historial: servidor + ${resultado.soloLocales} solo local` : "Historial: servidor",
      "servidor", `${resultado.servidor} mensajes del Router`);
  } catch (error) {
    if (activo().id === id) origen("Historial: solo local", "local", `Servidor no disponible: ${error.message}`);
  }
}
function decir(id, rol, texto) {
  agregar(id, rol, texto);
  if (activo().id !== id) return;  // la respuesta llega a su chat aunque estés viendo otro
  const history = document.querySelector("#history");
  history.append(node("div", texto, CLASES[rol]));
  history.scrollTop = history.scrollHeight;
}

document.querySelector("#nuevo-chat").addEventListener("click", () => {
  const chat = crear();
  pintarChats();
  void sincronizar(chat.id);
  document.querySelector("#message").focus();
});

document.querySelector("#composer").addEventListener("submit", async event => {
  event.preventDefault();
  const input = document.querySelector("#message");
  const message = input.value.trim();
  if (!message) return;
  const chat = activo();
  const button = document.querySelector("#composer button");
  const agent = document.querySelector("#agent").value;
  const max_tokens = { fast: 512, balanced: 1024, think: 2048 }[document.querySelector("#mode").value];
  button.disabled = true;
  decir(chat.id, "user", message);
  try {
    const answer = window.RIU_CONFIG?.harnessUrl
      ? await harness({ model: document.querySelector("#ficha").value, message, max_tokens, sesion: chat.id, anclados: anclados(chat.id),
          avisar: text => { if (activo().id === chat.id) document.querySelector("#history").append(node("div", text, "item message")); } })
      : await api("/chat/send", { method: "POST", body: {
          message, ficha: document.querySelector("#ficha").value,
          provider: document.querySelector("#provider").value,
          model: document.querySelector("#model").value,
          mode: agent ? "agent" : "direct", agent_id: agent || null, max_tokens,
          conversation_id: chat.conversation_id || null
        } });
    fijarConversacion(chat.id, answer.conversation_id);
    decir(chat.id, "router", answer.reply || "Respuesta vacía del Router.");
    if (Array.isArray(answer.tools) && answer.tools.length)
      decir(chat.id, "nota", `Herramientas usadas: ${answer.tools.map(t => t?.nombre || t).join(", ")}`);
    input.value = "";
  } catch (error) {
    decir(chat.id, "error", `No se pudo enviar: ${error.message}`);
    tell(error.message);
  } finally {
    button.disabled = false;
  }
});

pintarChats();
void sincronizar(activo().id);
void loadSelectors();
