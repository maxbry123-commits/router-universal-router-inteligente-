import { api, harness, node } from "../api.js";
import { tell } from "./base.js";
import { activar, activo, agregar, crear, fijarConversacion, listar, mensajes } from "./chat-sesion.js";

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
    tab.addEventListener("click", () => { activar(chat.id); pintarChats(); });
    return tab;
  }));
  document.querySelector("#chat-id").textContent = `Sesión: ${actual.id}`;
  const history = document.querySelector("#history");
  history.replaceChildren(...mensajes(actual.id).map(m => node("div", m.texto, CLASES[m.rol] || CLASES.router)));
  history.scrollTop = history.scrollHeight;
}
function decir(id, rol, texto) {
  agregar(id, rol, texto);
  if (activo().id !== id) return;  // la respuesta llega a su chat aunque estés viendo otro
  const history = document.querySelector("#history");
  history.append(node("div", texto, CLASES[rol]));
  history.scrollTop = history.scrollHeight;
}

document.querySelector("#nuevo-chat").addEventListener("click", () => {
  crear();
  pintarChats();
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
      ? await harness({ model: document.querySelector("#ficha").value, message, max_tokens, sesion: chat.id,
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
void loadSelectors();
