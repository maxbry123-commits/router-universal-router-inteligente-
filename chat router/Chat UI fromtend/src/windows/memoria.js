import { el, button, openWindow } from "../dom.js";
import { t, controlLabel } from "../i18n.js";

export function openMemoria(context) {
  const status = el("p", { class: "muted", role: "status", "aria-live": "polite" });
  const results = el("div", { class: "panel-results" });
  const scope = el("input", { class: "setting-input", value: "chat", "aria-label": "Scope de memoria" });
  const query = el("input", { class: "setting-input", placeholder: "Consulta en la memoria real del Router", "aria-label": "Consulta" });

  async function health() {
    status.className = "muted";
    status.textContent = t(context, "loading");
    try {
      const response = await context.execute("chat.memoria.health");
      status.textContent = "Memoria: " + JSON.stringify(response.health);
    } catch (error) { status.className = "error"; status.textContent = error.message; }
  }
  async function search() {
    status.className = "muted";
    status.textContent = t(context, "loading");
    try {
      const response = await context.execute("chat.memoria.search", { scope: scope.value, query: query.value });
      results.replaceChildren(...response.results.map((row, index) =>
        el("pre", { class: "resource-item", text: "#" + (index + 1) + " " + JSON.stringify(row) })));
      status.textContent = response.results.length + " resultados reales de /memoria/search";
    } catch (error) { status.className = "error"; status.textContent = error.message; }
  }

  const dialog = openWindow(controlLabel(context, "memoria"),
    el("div", { class: "window-body" },
      el("p", { class: "muted", text: "Consulta real a /memoria/* del Router. Sin resultados inventados." }),
      scope, query,
      el("div", { class: "chip-row" }, button(t(context, "search"), search, "primary"), button("Health", health)),
      status, results),
    t(context, "closeWindow"));
  health();
  return dialog;
}
