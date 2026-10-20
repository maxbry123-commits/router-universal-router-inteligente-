import { node } from "./api.js";

const config = {
  connectors: { title: "Conectores Fables", field: "connectors", empty: "Sin conectores", description: "Estado real del bus de fichas." },
  templates: { title: "Plantillas DAG", field: "templates", empty: "Sin plantillas", description: "Plantillas bloqueadas: selección y consulta. La ejecución requiere autorización y un DAG ejecutable." },
  engineering: { title: "Engineering Control", field: "toggles", empty: "No hay controles de ingeniería configurados", description: "Solo lectura; no se inventan valores para controles inexistentes." }
};

export async function mount(root, { api, tell, view }) {
  const current = config[view];
  root.querySelector("#org-title").textContent = current.title;
  root.querySelector("#org-description").textContent = current.description;
  try {
    const data = (await api(`/chat/org/${view}`)).data[current.field];
    const list = root.querySelector("#org-list");
    for (const entry of data) {
      const text = view === "connectors" ? `${entry.id} · ${entry.status} · ${JSON.stringify(entry.health)}`
        : view === "templates" ? `${entry.id} · ${entry.title} · LOCKED` : JSON.stringify(entry);
      list.append(node("div", text, "item"));
    }
    if (!list.children.length) list.append(node("p", current.empty, "muted"));
  } catch (error) { tell(error.message); }
}
