import { api, node } from "../api.js";
import { tell } from "./base.js";

export async function mount(root, { api }) {
  let disposed = false;
  const sections = [
    { path: "/chat/agents", key: "agents", list: "#agents-list", status: "#agents-status",
      format: agent => `${agent.name || agent.id} · ${agent.description || agent.role || "sin descripción"}` },
    { path: "/chat/org/graph", key: "graph", list: "#roles-list", status: "#roles-status",
      format: item => `${item.id} · ${item.rol || item.role || "sin rol"}` },
    { path: "/chat/org/queue", key: "tasks", list: "#agents-tasks", status: "#tasks-status",
      format: item => `${item.id || item.task || "Tarea"} · ${item.status || item.estado || "sin estado publicado"}` }
  ];
  const load = async section => {
    const status = root.querySelector(section.status);
    const list = root.querySelector(section.list);
    status.textContent = "Consultando Router…";
    list.replaceChildren();
    try {
      let response;
      try { response = await api(section.path); }
      catch (error) {
        if (section.key !== "graph" || !["Not Found", "HTTP 404"].includes(error.message)) throw error;
        response = { data: { graph: await api("/chat/graph") } };
      }
      if (disposed) return;
      const data = section.key === "agents" ? response.agents : response.data[section.key];
      const entries = section.key === "graph" ? data.nodes : data;
      for (const entry of entries || []) {
        const item = node("div", section.format(entry), "item");
        if (section.key === "tasks") {
          const subtasks = entry.subtasks || entry.subtareas;
          if (Array.isArray(subtasks)) {
            for (const subtask of subtasks) {
              item.append(node("div", `${subtask.id || subtask.task || "Subtarea"} · ${subtask.status || subtask.estado || "sin estado publicado"}`, "subtask"));
            }
          }
        }
        list.append(item);
      }
      if (!list.children.length) list.append(node("p", "Sin registros en el Router.", "muted"));
      status.textContent = `${(entries || []).length} registros consultados`;
    } catch (error) {
      if (disposed) return;
      status.textContent = `No disponible: ${error.message}`;
      list.append(node("p", "No hay datos confirmados.", "muted"));
    }
  };
  root.querySelector("#agents-reload").addEventListener("click", () => {
    sections.forEach(section => { void load(section); });
  });
  await Promise.all(sections.map(load));
  return () => { disposed = true; };
}

void mount(document, { api }).catch(error => tell(error.message));
