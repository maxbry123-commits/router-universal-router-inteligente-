import { el, button } from "../dom.js";

export function renderFiles(context) {
  const state = el("p", { class: "panel-state pending", role: "status", "aria-live": "polite", text: "Pendiente de consulta al Router" });
  const results = el("div", { class: "panel-results" });
  const search = el("input", { type: "search", placeholder: "Buscar documentos", "aria-label": "Buscar documentos", class: "setting-input" });
  const file = el("input", { type: "file", "aria-label": "Seleccionar archivo" });
  let documents = [];
  let loaded = false;
  let revision = 0;
  const root = el("section", { class: "workspace-panel", "aria-label": "Archivos" },
    el("header", { class: "workspace-heading" }, el("h2", { text: "Archivos" }), el("p", { class: "sub", text: "Documentos del Router; ningún archivo aparece sin respuesta real." })),
    el("div", { class: "workspace-toolbar" }, search, button("Actualizar", load), file, button("Subir", upload)),
    state, results);

  function display() {
    results.replaceChildren();
    if (!loaded) return;
    const filtered = documents.filter(item => String(item.name || "").toLocaleLowerCase().includes(search.value.toLocaleLowerCase()));
    if (!filtered.length) { results.append(el("p", { class: "muted", text: "Sin documentos coincidentes." })); return; }
    for (const item of filtered) {
      if (!item || typeof item.id !== "string") continue;
      results.append(el("div", { class: "workspace-row" },
        el("span", { text: String(item.name || item.id) }),
        el("small", { class: "sub", text: `${Number(item.size) || 0} bytes · ${String(item.mime || "desconocido")}` })));
    }
  }
  async function load() {
    const current = ++revision;
    state.className = "panel-state pending progress";
    state.textContent = "Consultando documentos…";
    results.replaceChildren();
    loaded = false;
    try {
      const response = await context.execute("chat.documents");
      if (current !== revision || !root.isConnected) return;
      if (!Array.isArray(response.documents)) throw new Error("INVALID_DOCUMENTS_RESPONSE");
      documents = response.documents;
      loaded = true;
      state.className = "panel-state";
      state.textContent = `${documents.length} documento(s) confirmados por el Router`;
      display();
    } catch (error) {
      if (current !== revision || !root.isConnected) return;
      state.className = "panel-state error";
      state.textContent = `No se pudo cargar: ${error.message}`;
    }
  }
  async function upload() {
    const chosen = file.files?.[0];
    if (!chosen) { state.className = "panel-state error"; state.textContent = "Selecciona un archivo real antes de subir."; return; }
    state.className = "panel-state pending progress";
    state.textContent = "Subida pendiente de confirmación…";
    try {
      const result = await context.execute("chat.attach", { file: chosen, name: chosen.name });
      if (!root.isConnected) return;
      if (!result.attachmentId) throw new Error("INVALID_ATTACHMENT_RESPONSE");
      file.value = "";
      await load();
    } catch (error) {
      if (!root.isConnected) return;
      state.className = "panel-state error";
      state.textContent = `Subida no confirmada: ${error.message}`;
    }
  }
  search.addEventListener("input", display);
  queueMicrotask(load);
  return root;
}
