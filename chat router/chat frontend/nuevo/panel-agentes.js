import { api, node } from "../api.js";
import { tell } from "./base.js";

export async function mount(root, { api }) {
  let disposed = false;
  let lastTasks;
  let lastAgents;
  const renderAgents = () => {
    const list = root.querySelector("#agents-list");
    list.replaceChildren();
    if (!lastAgents) { list.append(node("p", "No hay datos confirmados.", "muted")); return; }
    const query = root.querySelector("#agents-filter").value.toLocaleLowerCase();
    for (const agent of lastAgents) {
      if (!sections[0].format(agent).toLocaleLowerCase().includes(query)) continue;
      const item = node("div", sections[0].format(agent), "item");
      const publishedState = agent.status || agent.estado;
      if (publishedState) {
        const badge = node("span", `Estado: ${publishedState}`, "badge");
        badge.dataset.state = String(publishedState).toLowerCase();
        item.append(badge);
      }
      list.append(item);
    }
    if (!list.children.length) list.append(node("p", "Sin agentes para este filtro.", "muted"));
  };
  const renderTasks = () => {
    const list = root.querySelector("#agents-tasks");
    list.replaceChildren();
    if (!lastTasks) { list.append(node("p", "No hay datos confirmados.", "muted")); return; }
    const query = root.querySelector("#tasks-filter").value.toLocaleLowerCase();
    const matching = lastTasks.filter(entry =>
      `${entry.id || ""} ${entry.task || ""} ${entry.status || ""} ${entry.estado || ""}`.toLocaleLowerCase().includes(query));
    for (const entry of matching) {
      const item = node("div", sections[2].format(entry), "item");
      const subtasks = entry.subtasks || entry.subtareas;
      if (Array.isArray(subtasks)) {
        for (const subtask of subtasks) {
          item.append(node("div", `${subtask.id || subtask.task || "Subtarea"} · ${subtask.status || subtask.estado || "sin estado publicado"}`, "subtask"));
        }
      }
      list.append(item);
    }
    if (!list.children.length) list.append(node("p", "Sin tareas para este filtro.", "muted"));
    root.querySelector("#tasks-count").textContent =
      matching.length === lastTasks.length ? `${lastTasks.length} tareas.` : `${matching.length} de ${lastTasks.length} tareas coinciden con el filtro.`;
  };
  const sections = [
    { path: "/chat/agents", key: "agents", list: "#agents-list", status: "#agents-status",
      format: agent => {
        const models = Array.isArray(agent.models) && agent.models.length ? ` · modelos: ${agent.models.join(", ")}` : "";
        return `${agent.name || agent.id} · ${agent.description || agent.role || "sin descripción"}${models}`;
      } },
    { path: "/chat/org/graph", key: "graph", list: "#roles-list", status: "#roles-status",
      format: item => {
        const skills = Array.isArray(item.skills) ? item.skills : Array.isArray(item.habilidades) ? item.habilidades : [];
        const suffix = skills.length ? ` · habilidades: ${skills.join(", ")}` : "";
        return `${item.id} · ${item.rol || item.role || "sin rol"}${suffix}`;
      } },
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
      if (section.key === "agents") {
        lastAgents = entries || [];
        renderAgents();
      } else if (section.key === "tasks") {
        lastTasks = entries || [];
        renderTasks();
      } else {
        for (const entry of entries || []) {
          const item = node("div", section.format(entry), "item");
          const publishedState = entry.status || entry.estado;
          if (publishedState) {
            const badge = node("span", `Estado: ${publishedState}`, "badge");
            badge.dataset.state = String(publishedState).toLowerCase();
            item.append(badge);
          }
          list.append(item);
        }
      }
      if (!list.children.length) list.append(node("p", "Sin registros en el Router.", "muted"));
      status.textContent = `${(entries || []).length} registros consultados`;
    } catch (error) {
      if (disposed) return;
      if (section.key === "tasks") lastTasks = undefined;
      if (section.key === "agents") lastAgents = undefined;
      status.textContent = `No disponible: ${error.message}`;
      list.append(node("p", "No hay datos confirmados.", "muted"));
    }
  };
  root.querySelector("#tasks-filter").addEventListener("input", renderTasks);
  root.querySelector("#agents-filter").addEventListener("input", renderAgents);
  root.querySelector("#agents-reload").addEventListener("click", () => {
    sections.forEach(section => { void load(section); });
  });
  await Promise.all(sections.map(load));
  return () => { disposed = true; };
}

void mount(document, { api }).catch(error => tell(error.message));
