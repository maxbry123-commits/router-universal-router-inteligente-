import { node } from "./api.js";
// selects-secundarios.js — selects secundarios (dentro de «más»): proveedor, modelo, agente, grupo, cuenta GitHub
// Extraído de panel-chat.js sin cambiar la lógica: recibe lo que usa por ctx y devuelve lo que otros bloques necesitan.
export async function montarSelectsSecundarios(ctx) {
  const { q, api, tell } = ctx;

  // ---- selects secundarios (dentro de más) ----
  const select = (id, options, value, label) => {
    const target = q(id);
    for (const item of options) {
      const option = node("option", item[label]);
      option.value = item[value];
      target.append(option);
    }
  };
  try {
    const providers = await api("/chat/providers");
    select("#provider", (providers.providers || []).filter(item => item.id !== "auto"), "id", "label");
    select("#agent", (await api("/chat/agents")).agents || [], "id", "name");
    const accounts = await api("/chat/github/accounts");
    select("#github", accounts.accounts || [], "account", "account");
  } catch (error) { tell(error.message); }
  q("#provider").addEventListener("change", async event => {
    const model = q("#model");
    model.replaceChildren(node("option", "Router elige"));
    if (event.target.value === "auto") return;
    try { select("#model", (await api(`/chat/providers/${encodeURIComponent(event.target.value)}/models`)).models || [], "model_id", "label"); }
    catch (error) { tell(error.message); }
  });
}
