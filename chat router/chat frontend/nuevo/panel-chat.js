import { api, harness, node } from "../api.js";
import { tell } from "./base.js";
import { activar, activo, agregar, anclados, crear, fijarConversacion, fusionar, hijas, listar, mensajes } from "./chat-sesion.js";
import { montarArchivos } from "./chat-archivos.js";
import { montarHijos } from "./chat-hijos.js";
import { enviarOrquestado, montarOrquestador } from "./chat-orquestador.js";

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
function pestana(chat, texto, seleccionada) {
  const tab = node("button", texto, "chat-tab");
  tab.type = "button";
  tab.title = `Sesión ${chat.id}`;
  tab.setAttribute("role", "tab");
  tab.setAttribute("aria-selected", String(seleccionada));
  tab.addEventListener("click", () => abrir(chat.id));
  return tab;
}
function pintarChats() {
  const actual = activo();
  const raiz = actual.padre || actual.id;  // Punto 5: los hijos van como sub-pestañas bajo su padre
  document.querySelector("#chat-tabs").replaceChildren(...listar().filter(c => !c.padre).map((chat, i) => {
    const tab = pestana(chat, chat.titulo || `Chat ${i + 1}`, chat.id === actual.id);
    if (chat.id === raiz && actual.padre) tab.dataset.padreActivo = "true";
    return tab;
  }));
  const subtabs = document.querySelector("#chat-subtabs");
  subtabs.replaceChildren(...hijas(raiz).map(h => pestana(h, `↳ ${h.titulo || h.id}`, h.id === actual.id)));
  subtabs.hidden = !subtabs.childElementCount;
  document.querySelector("#chat-id").textContent = `Sesión: ${actual.id}`;
  const history = document.querySelector("#history");
  history.replaceChildren(...mensajes(actual.id).flatMap(m => burbujas(m, actual.id)));
  history.scrollTop = history.scrollHeight;
}
// Punto 6: bajo una respuesta orquestada va la tarjeta del run (guardada con el mensaje).
function burbujas(m, id) {
  const div = node("div", m.texto, CLASES[m.rol] || CLASES.router);
  return m.run ? [div, orq.tarjeta(m.run, id)] : [div];
}
function abrir(id) {
  activar(id);
  pintarChats();
  void sincronizar(id);
}
// Punto 2: al abrir un chat o recargar, trae su historial del Router y lo fusiona con el local.
function origen(texto, tipo, detalle = "") {
  const marca = document.querySelector("#historial-origen");
  marca.textContent = texto;
  marca.dataset.origen = tipo;
  marca.title = detalle;
}
const archivos = montarArchivos({ activoId: () => activo().id });  // Punto 4: archivos del chat activo
const hijosUI = montarHijos({ activo, abrir, repintar: () => pintarChats() });  // Punto 5: agente anclado → chat hijo
const orq = montarOrquestador({ activo, abrirHija: abrir, refrescarHijas: id => hijosUI.refrescar(id) });  // Punto 6
async function sincronizar(id) {
  void archivos.cargar(id);  // al abrir/crear/recargar un chat también se recargan sus archivos
  void hijosUI.cargar(id);  // y sus chats hijos (o, si es hijo, su ficha e INPUT_BLOCK)
  void orq.cargar(id);  // y el estado del orquestador (solo chats raíz)
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
function decir(id, rol, texto, extra = null) {
  agregar(id, rol, texto, extra);
  if (activo().id !== id) return;  // la respuesta llega a su chat aunque estés viendo otro
  const history = document.querySelector("#history");
  history.append(...burbujas({ rol, texto, ...(extra || {}) }, id));
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
  const nodos = orq.nodosPara(chat.id);  // Punto 6: ON → chat_async con orquestador_nodos; OFF → camino normal
  try {
    if (nodos) {
      const r = await enviarOrquestado({ model: document.querySelector("#ficha").value, message, max_tokens, sesion: chat.id, anclados: anclados(chat.id), nodos });
      decir(chat.id, "router", r.reply || "Respuesta vacía del orquestador.", r.orquestador ? { run: r.orquestador } : null);
      input.value = "";
      void hijosUI.refrescar(chat.id).catch(() => {});
      void orq.cargarRuns(chat.id);
      return;
    }
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
