import { node } from "./api.js";

export async function mount(root, { api, tell }) {
  const select = (id, options, value, label) => {
    const target = root.querySelector(id);
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
  root.querySelector("#provider").addEventListener("change", async event => {
    const model = root.querySelector("#model");
    model.replaceChildren(node("option", "Router elige"));
    if (event.target.value === "auto") return;
    try { select("#model", (await api(`/chat/providers/${encodeURIComponent(event.target.value)}/models`)).models || [], "model_id", "label"); }
    catch (error) { tell(error.message); }
  });
  root.querySelector("#composer").addEventListener("submit", async event => {
    event.preventDefault();
    const input = root.querySelector("#message");
    const message = input.value.trim();
    if (!message) return;
    if (message === "/ayuda") { tell("Usa el selector de agente y envía tu mensaje. /ayuda no ejecuta modelos."); return; }
    const history = root.querySelector("#history");
    history.append(node("div", message, "item message user"));
    input.value = "";
    const agent = root.querySelector("#agent").value;
    const provider = root.querySelector("#provider").value;
    const model = root.querySelector("#model").value;
    const max_tokens = { fast: 512, balanced: 1024, think: 2048 }[root.querySelector("#mode").value];
    try {
      const answer = await api("/chat/send", { method: "POST", body: { message, provider, model,
        mode: agent ? "agent" : "direct", agent_id: agent || null, max_tokens } });
      history.append(node("div", answer.reply || "Sin respuesta", "item message"));
      history.scrollTop = history.scrollHeight;
    } catch (error) { history.append(node("div", `GAP: ${error.message}`, "item message")); }
  });
  root.querySelectorAll("[data-control]").forEach(button => button.addEventListener("click", async () => {
    try { await api(`/control/${button.dataset.control}`, { method: "POST" }); tell(`${button.textContent}: ejecutado`); }
    catch (error) { tell(error.message); }
  }));
}
