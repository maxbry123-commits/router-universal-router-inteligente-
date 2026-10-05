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
  const fichas = window.RIU_CONFIG?.modelos || [];
  for (const m of fichas) { const o = node('option', m.etiqueta); o.value = m.id; root.querySelector('#ficha').append(o); }
  if (window.RIU_CONFIG?.defecto) root.querySelector('#ficha').value = window.RIU_CONFIG.defecto;
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
      const body = { message, ficha: root.querySelector('#ficha').value, provider, model, mode: agent ? "agent" : "direct", agent_id: agent || null, max_tokens };
      // con harnessUrl el mensaje va al harness DeepSeek (y este a la memoria por su plugin); si no, al Router como hoy
      const answer = window.RIU_CONFIG?.harnessUrl ? await window.RIU_HARNESS({ model: body.ficha, message, max_tokens, avisar: (t) => history.append(node('div', t, 'item message')) }) : await api("/chat/send", { method: "POST", body });
      history.append(node("div", answer.reply || "Sin respuesta", "item message"));
      if (answer.job_id) { window.__riuJob = answer.job_id; root.querySelector('#apagar-respaldo').hidden = false; }
      history.scrollTop = history.scrollHeight;
    } catch (error) { history.append(node("div", `GAP: ${error.message}`, "item message")); }
  });
  root.querySelectorAll("[data-control]").forEach(button => button.addEventListener("click", async () => {
    try { await api(`/control/${button.dataset.control}`, { method: "POST" }); tell(`${button.textContent}: ejecutado`); }
    catch (error) { tell(error.message); }
  }));
  const stop = root.querySelector('#apagar-respaldo');
  stop.addEventListener('click', async () => {
    const cfg = window.RIU_CONFIG || {};
    if (!window.__riuJob) { tell('No hay respaldo encendido'); return; }
    try {
      const r = await window.RIU_APAGAR();
      tell(r.ok ? 'Respaldo apagado' : 'No se pudo apagar (HTTP ' + r.status + ')');
      if (r.ok) { window.__riuJob = null; stop.hidden = true; }
    } catch (error) { tell(error.message); }
  });
}
