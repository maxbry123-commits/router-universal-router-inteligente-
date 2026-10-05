import { api, node } from "../api.js";
import { tell } from "./base.js";

export async function mount(root, { api }) {
  let disposed = false;
  let runRequest = 0;
  const read = async (path, statusId, listId, render) => {
    const status = root.querySelector(statusId);
    const list = root.querySelector(listId);
    status.textContent = "Consultando Router…";
    list.replaceChildren();
    try {
      const result = await api(path);
      if (disposed) return;
      render(result.data, list);
      if (!list.children.length) list.append(node("p", "Sin registros.", "muted"));
      status.textContent = "Consulta completada";
    } catch (error) {
      if (disposed) return;
      status.textContent = `No disponible: ${error.message}`;
      list.append(node("p", "No hay datos confirmados.", "muted"));
    }
  };
  const load = () => {
    root.querySelector("#template-selection").textContent = "Sin plantilla seleccionada.";
    return Promise.all([
    read("/chat/org/graph", "#wall-status", "#wall", (data, list) => {
      const graph = data.graph || {};
      list.append(node("div", `Grafo: ${(graph.nodes || []).length} nodos · ${(graph.edges || []).length} aristas`, "item"));
      const wall = data.crazy_wall || {};
      const state = data.state || {};
      for (const [project, item] of Object.entries(state.projects || {})) {
        list.append(node("div", `${project} · ${item.status || "sin estado"} · ${(item.active_tasks || []).length} tareas activas · ${(item.blocked_tasks || []).length} bloqueadas`, "item"));
      }
      for (const item of Object.values(wall.nodes || {})) {
        list.append(node("div", `${item.node_id || item.task} · ${item.status || "sin estado"} · ${item.phase || ""} · siguiente: ${item.next || "no publicado"}`, "item"));
      }
    }),
    read("/chat/org/queue", "#queue-status", "#queue", (data, list) => {
      for (const task of data.tasks || []) list.append(node("div",
        `${task.id || task.task || "Tarea"} · ${task.status || task.estado || "estado no publicado"}`, "item"));
      list.append(node("div", `Workers: ${(data.workers || []).length}`, "item"));
    }),
    read("/chat/org/templates", "#templates-status", "#templates", (data, list) => {
      for (const template of data.templates || []) {
        const button = node("button",
          `${template.id} · ${template.title} · ${template.locked ? "LOCKED" : "estado no publicado"}`, "secondary");
        button.type = "button";
        button.addEventListener("click", () => {
          for (const other of list.querySelectorAll("button")) other.setAttribute("aria-pressed", String(other === button));
          root.querySelector("#template-selection").textContent = `Seleccionada: ${template.id}. La selección no ejecuta el DAG.`;
        });
        button.setAttribute("aria-pressed", "false");
        list.append(button);
      }
    }),
    read("/chat/org/bitacora?limit=30", "#events-status", "#events", (data, list) => {
      const runIdPattern = /^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$/;
      for (const item of (data.events || []).slice().reverse()) {
        const text = `${item.task || item.id || "Evento"} · ${item.status || "sin estado"} · ${item.phase || ""} · ${item.summary || ""}`;
        const runId = typeof item.run_id === "string" ? item.run_id : typeof item.run === "string" ? item.run : "";
        if (runIdPattern.test(runId)) {
          const entry = node("button", `${text} · run: ${runId}`, "secondary item");
          entry.type = "button";
          entry.addEventListener("click", () => {
            root.querySelector("#run-id").value = runId;
            root.querySelector("#run-form").requestSubmit();
          });
          list.append(entry);
        } else {
          list.append(node("div", text, "item"));
        }
      }
    })
    ]);
  };
  root.querySelector("#tracking-reload").addEventListener("click", () => { void load(); });
  root.querySelector("#run-form").addEventListener("submit", async event => {
    event.preventDefault();
    const request = ++runRequest;
    const id = root.querySelector("#run-id").value.trim();
    const status = root.querySelector("#run-status");
    const list = root.querySelector("#ledger");
    list.replaceChildren();
    if (!/^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$/.test(id)) { status.textContent = "ID de run inválido."; return; }
    status.textContent = "Consultando ledger del Router…";
    try {
      const response = await api(`/chat/org/dag/${encodeURIComponent(id)}`);
      if (disposed || request !== runRequest) return;
      const run = response.data.run;
      status.textContent = `Run ${id} · ${run.status || "sin veredicto publicado"} · ledger ${run.ledger_valid === true ? "íntegro según Router" : "integridad no confirmada"}`;
      for (const [nodeId, entry] of Object.entries(run.nodes || {})) {
        list.append(node("div", `${nodeId} · ${entry.status || "sin estado"} · ${entry.state || ""}`, "item"));
      }
      for (const item of run.ledger || []) {
        list.append(node("div", `${item.node_id || item.node || item.id || "Nodo"} · ${item.status || item.verdict || "sin estado"} · ${item.phase || ""}`, "item"));
      }
      if (!list.children.length) list.append(node("p", "Sin entradas de ledger.", "muted"));
    } catch (error) { if (!disposed && request === runRequest) status.textContent = `No disponible: ${error.message}`; }
  });
  await load();
  return () => { disposed = true; runRequest++; };
}

void mount(document, { api }).catch(error => tell(error.message));
