import { el, button } from "../dom.js";
import { renderRunViews } from "./run-views.js";
import { renderWallViews } from "./wall-views.js";

export function renderTracking(context) {
  const state = el("p", { class: "panel-state pending", role: "status", "aria-live": "polite", text: "Pendiente de consulta al Router" });
  const graph = el("div", { class: "panel-results" });
  const id = el("input", { class: "setting-input", placeholder: "ID de ejecución", "aria-label": "ID de ejecución" });
  const jobsInput = el("textarea", { class: "setting-input", placeholder: "JSON de jobs [{id,provider,model,instructions,…}] del Router", "aria-label": "JSON de jobs", rows: "3" });
  const dagInput = el("textarea", { class: "setting-input", placeholder: "JSON del DAG (plantilla del Router; no se inventa)", "aria-label": "JSON del DAG", rows: "3" });
  let revision = 0;
  const root = el("section", { class: "workspace-panel", "aria-label": "Seguimiento" },
    el("header", { class: "workspace-heading" }, el("h2", { text: "Seguimiento" }),
      el("p", { class: "sub", text: "El grafo de procedencia no equivale a un ledger de ejecución." })),
    el("div", { class: "workspace-toolbar" }, button("Actualizar procedencia", load),
      button("Uso del Router", usage), button("Conversaciones vivas", conversations), id, button("Consultar ledger", ledger),
      dagInput, button("Ejecutar DAG real", dagRun), button("Estado del Router", routerStatus),
      jobsInput, button("Lanzar jobs reales", jobsRun)),
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
  async function usage() {
    state.className = "panel-state pending progress";
    state.textContent = "Consultando uso del Router…";
    try {
      const response = await context.execute("chat.usage");
      if (!root.isConnected) return;
      graph.replaceChildren(el("h3", { text: "Uso del Router (real)" }),
        el("pre", { text: JSON.stringify(response.usage, null, 2) }));
      state.className = "panel-state";
      state.textContent = "Uso leído del Router.";
    } catch (error) {
      if (!root.isConnected) return;
      state.className = "panel-state error";
      state.textContent = "Uso no disponible: " + error.message;
    }
  }
  async function conversations() {
    state.className = "panel-state pending progress";
    state.textContent = "Consultando conversaciones…";
    try {
      const response = await context.execute("chat.conversations");
      if (!root.isConnected) return;
      graph.replaceChildren(el("h3", { text: "Conversaciones vivas: " + response.items.length }),
        ...response.items.map(item =>
          el("p", { class: "workspace-row", text: item.id + " · " + item.label + " · " + item.description })));
      state.className = "panel-state";
      state.textContent = "Conversaciones leídas del Router.";
    } catch (error) {
      if (!root.isConnected) return;
      state.className = "panel-state error";
      state.textContent = "Conversaciones no disponibles: " + error.message;
    }
  }
  async function dagRun() {
    let dag;
    try { dag = JSON.parse(dagInput.value); }
    catch { state.className = "panel-state error"; state.textContent = "DAG_JSON_INVALID: pega el JSON del DAG del Router."; return; }
    state.className = "panel-state pending progress";
    state.textContent = "Ejecutando DAG en el Router…";
    try {
      const response = await context.execute("chat.dagRun", { dag });
      if (!root.isConnected) return;
      graph.replaceChildren(el("h3", { text: "DAG ejecutado (respuesta real del Router)" }),
        el("pre", { text: JSON.stringify(response.dag, null, 2) }));
      state.className = "panel-state";
      state.textContent = "DAG confirmado por el Router.";
    } catch (error) {
      if (!root.isConnected) return;
      state.className = "panel-state error";
      state.textContent = "DAG no ejecutado: " + error.message;
    }
  }
  async function routerStatus() {
    state.className = "panel-state pending progress";
    state.textContent = "Consultando estado del Router…";
    try {
      const response = await context.execute("chat.routerStatus");
      if (!root.isConnected) return;
      graph.replaceChildren(el("h3", { text: "Estado del Router (real)" }),
        el("pre", { text: JSON.stringify(response.status, null, 2) }));
      state.className = "panel-state";
      state.textContent = "Estado leído del Router.";
    } catch (error) {
      if (!root.isConnected) return;
      state.className = "panel-state error";
      state.textContent = "Estado no disponible: " + error.message;
    }
  }
  async function jobsRun() {
    let jobs;
    try { jobs = JSON.parse(jobsInput.value); }
    catch { state.className = "panel-state error"; state.textContent = "JOBS_JSON_INVALID: pega la lista de jobs del Router."; return; }
    state.className = "panel-state pending progress";
    state.textContent = "Lanzando jobs en el Router…";
    try {
      const response = await context.execute("chat.jobs", { jobs });
      if (!root.isConnected) return;
      graph.replaceChildren(el("h3", { text: "Jobs: " + response.passed + "/" + response.total + " PASS (real)" }),
        el("pre", { text: JSON.stringify(response.jobs, null, 2) }));
      state.className = "panel-state";
      state.textContent = "Jobs confirmados por el Router.";
    } catch (error) {
      if (!root.isConnected) return;
      state.className = "panel-state error";
      state.textContent = "Jobs no ejecutados: " + error.message;
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
