import { api, harness, node } from "../api.js";
import { tell } from "./base.js";

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

document.querySelector("#composer").addEventListener("submit", async event => {
  event.preventDefault();
  const input = document.querySelector("#message");
  const message = input.value.trim();
  if (!message) return;
  const button = document.querySelector("#composer button");
  const history = document.querySelector("#history");
  const agent = document.querySelector("#agent").value;
  const max_tokens = { fast: 512, balanced: 1024, think: 2048 }[document.querySelector("#mode").value];
  button.disabled = true;
  history.append(node("div", message, "item message user"));
  try {
    const answer = window.RIU_CONFIG?.harnessUrl
      ? await harness({ model: document.querySelector("#ficha").value, message, max_tokens,
          avisar: text => history.append(node("div", text, "item message")) })
      : await api("/chat/send", { method: "POST", body: {
          message, ficha: document.querySelector("#ficha").value,
          provider: document.querySelector("#provider").value,
          model: document.querySelector("#model").value,
          mode: agent ? "agent" : "direct", agent_id: agent || null, max_tokens
        } });
    history.append(node("div", answer.reply || "Respuesta vacía del Router.", "item message"));
    if (Array.isArray(answer.tools) && answer.tools.length)
      history.append(node("div", `Herramientas usadas: ${answer.tools.join(", ")}`, "item message muted"));
    input.value = "";
  } catch (error) {
    history.append(node("div", `No se pudo enviar: ${error.message}`, "item message"));
    tell(error.message);
  } finally {
    button.disabled = false;
    history.scrollTop = history.scrollHeight;
  }
});

void loadSelectors();
