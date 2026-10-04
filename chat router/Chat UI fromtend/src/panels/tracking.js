import { el, button } from "../dom.js";
import { renderRunViews } from "./run-views.js";
import { renderWallViews } from "./wall-views.js";

export function renderTracking(context) {
  const state = el("p", { class: "panel-state pending", role: "status", "aria-live": "polite", text: "Pendiente de consulta al Router" });
  const graph = el("div", { class: "panel-results" });
  const id = el("input", { class: "setting-input", placeholder: "ID de ejecución", "aria-label": "ID de ejecución" });
  let revision = 0;
  const root = el("section", { class: "workspace-panel", "aria-label": "Seguimiento" },
    el("header", { class: "workspace-heading" }, el("h2", { text: "Seguimiento" }),
      el("p", { class: "sub", text: "El grafo de procedencia no equivale a un ledger de ejecución." })),
    el("div", { class: "workspace-toolbar" }, button("Actualizar procedencia", load), id, button("Consultar ledger", ledger)),
    state, graph, renderRunViews(), renderWallViews());
  async function load() {
    const current = ++revision;
    state.className = "panel-state pending progress";
    state.textContent = "Consultando procedencia…";
    graph.replaceChildren();
    try {
      const response = await context.execute("chat.graph");
      if (current !== revision || !root.isConnected) return;
      if (!Array.isArray(response.nodes) || !Array.isArray(response.edges)) throw new Error("INVALID_GRAPH_RESPONSE");
      graph.append(el("h3", { text: `Procedencia: ${response.nodes.length} nodos · ${response.edges.length} aristas` }));
      for (const edge of response.edges) {
        graph.append(el("p", { class: "workspace-row", text: `${String(edge.src)} → ${String(edge.rel)} → ${String(edge.dst)}` }));
      }
      if (!response.edges.length) graph.append(el("p", { class: "muted", text: "Sin aristas registradas." }));
      state.className = "panel-state";
      state.textContent = "Procedencia leída del Router; estado de ejecución no disponible";
    } catch (error) {
      if (current !== revision || !root.isConnected) return;
      state.className = "panel-state error";
      state.textContent = `No se pudo leer procedencia: ${error.message}`;
    }
  }
  async function ledger() {
    if (!/^[a-zA-Z0-9_-]{1,128}$/.test(id.value.trim())) {
      state.className = "panel-state error"; state.textContent = "ID de ejecución inválido."; return;
    }
    state.className = "panel-state pending progress";
    state.textContent = "Consultando ledger…";
    try {
      const response = await context.execute("run.ledger", { id: id.value.trim() });
      if (!root.isConnected) return;
      if (!response.ledger || typeof response.ledger !== "object") throw new Error("INVALID_LEDGER_RESPONSE");
      graph.replaceChildren(el("pre", { text: JSON.stringify(response.ledger, null, 2) }));
      state.className = "panel-state";
      state.textContent = "Ledger confirmado por el bridge del host";
    } catch (error) {
      if (!root.isConnected) return;
      state.className = "panel-state error";
      state.textContent = `Ledger no disponible: ${error.message}`;
    }
  }
  queueMicrotask(load);
  return root;
}
