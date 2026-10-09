import { api, node } from "../api.js";
import { tell } from "./base.js";

export async function mount(root, { api }) {
  let disposed = false;
  let lastTasks;
  let lastAgents;
  let lastRoles;
  const query = () => root.querySelector("#multi-search").value.toLocaleLowerCase();
  const renderAgents = () => {
    const list = root.querySelector("#agents-list");
    list.replaceChildren();
    if (!lastAgents) { list.append(node("p", "No hay datos confirmados.", "muted")); return; }
    for (const agent of lastAgents) {
      if (!sections[0].format(agent).toLocaleLowerCase().includes(query())) continue;
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
  const renderRoles = () => {
    const list = root.querySelector("#roles-list");
    list.replaceChildren();
    if (!lastRoles) { list.append(node("p", "No hay datos confirmados.", "muted")); return; }
    for (const entry of lastRoles) {
      if (!sections[1].format(entry).toLocaleLowerCase().includes(query())) continue;
      const item = node("div", sections[1].format(entry), "item");
      const publishedState = entry.status || entry.estado;
      if (publishedState) {
        const badge = node("span", `Estado: ${publishedState}`, "badge");
        badge.dataset.state = String(publishedState).toLowerCase();
        item.append(badge);
      }
      list.append(item);
    }
    if (!list.children.length) list.append(node("p", "Sin roles para este filtro.", "muted"));
  };
  const renderTasks = () => {
    const list = root.querySelector("#agents-tasks");
    list.replaceChildren();
    if (!lastTasks) { list.append(node("p", "No hay datos confirmados.", "muted")); return; }
    const matching = lastTasks.filter(entry =>
      `${entry.id || ""} ${entry.task || ""} ${entry.status || ""} ${entry.estado || ""}`.toLocaleLowerCase().includes(query()));
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
  const renderSummary = () => {
    const parts = [
      lastAgents ? `${root.querySelector("#agents-list").querySelectorAll(".item").length} agentes` : null,
      lastRoles ? `${root.querySelector("#roles-list").querySelectorAll(".item").length} roles` : null,
      lastTasks ? `${root.querySelector("#agents-tasks").querySelectorAll(".item").length} tareas` : null
    ].filter(Boolean);
    root.querySelector("#multi-summary").textContent = parts.length ? `Visibles: ${parts.join(" · ")}` : "Sin datos confirmados.";
  };
  const renderAll = () => { renderAgents(); renderRoles(); renderTasks(); renderSummary(); };
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
    status.dataset.state = "loading";
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
      } else if (section.key === "graph") {
        lastRoles = entries || [];
        renderRoles();
      } else if (section.key === "tasks") {
        lastTasks = entries || [];
        renderTasks();
      }
      if (!list.children.length) list.append(node("p", "Sin registros en el Router.", "muted"));
      status.textContent = `${(entries || []).length} registros consultados`;
      status.dataset.state = "ok";
      renderSummary();
    } catch (error) {
      if (disposed) return;
      if (section.key === "tasks") lastTasks = undefined;
      if (section.key === "agents") lastAgents = undefined;
      if (section.key === "graph") lastRoles = undefined;
      status.textContent = `No disponible: ${error.message}`;
      status.dataset.state = "error";
      list.append(node("p", "No hay datos confirmados.", "muted"));
      renderSummary();
    }
  };
  root.querySelector("#multi-search").addEventListener("input", renderAll);
  root.querySelector("#multi-clear").addEventListener("click", () => {
    root.querySelector("#multi-search").value = "";
    renderAll();
  });
  root.querySelector("#agents-reload").addEventListener("click", () => {
    sections.forEach(section => { void load(section); });
  });
  await Promise.all(sections.map(load));
  return () => { disposed = true; };
}

void mount(document, { api }).catch(error => tell(error.message));
