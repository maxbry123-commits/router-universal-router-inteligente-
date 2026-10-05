import { api, node } from "../api.js";
import { tell } from "./base.js";

const key = "yaiwes-ui-preferences";
const defaults = { theme: "gris", scale: 100, reducedMotion: false };
const themes = ["gris", "little", "matte", "blanco"];

function validate(value) {
  if (!value || !themes.includes(value.theme) ||
    !Number.isInteger(value.scale) || value.scale < 85 || value.scale > 130 ||
    typeof value.reducedMotion !== "boolean") throw new Error("Ajustes no válidos.");
  return { theme: value.theme, scale: value.scale, reducedMotion: value.reducedMotion };
}

function stored() {
  try { return validate(JSON.parse(localStorage.getItem(key))); }
  catch { return { ...defaults }; }
}

function apply(preferences) {
  document.documentElement.dataset.theme = preferences.theme;
  document.documentElement.dataset.reducedMotion = String(preferences.reducedMotion);
  document.body.style.fontSize = `${preferences.scale * 0.15}px`;
}

apply(stored());

export async function mount(root, { api }) {
  let disposed = false;
  let exportUrl;
  let connectors = [];
  let preferences = stored();
  const status = root.querySelector("#preferences-status");
  const theme = root.querySelector("#ui-theme");
  const scale = root.querySelector("#ui-scale");
  const motion = root.querySelector("#ui-motion");
  const render = () => {
    apply(preferences);
    theme.value = preferences.theme;
    scale.value = preferences.scale;
    motion.checked = preferences.reducedMotion;
    root.querySelector("#scale-value").value = `${preferences.scale} %`;
  };
  const save = () => {
    preferences = validate({ theme: theme.value, scale: Number(scale.value), reducedMotion: motion.checked });
    render();
    try { localStorage.setItem(key, JSON.stringify(preferences)); status.textContent = "Ajustes visuales guardados en este navegador."; }
    catch { status.textContent = "Ajustes activos en esta pestaña; el navegador no permitió guardarlos."; }
  };
  theme.addEventListener("change", save);
  scale.addEventListener("input", save);
  motion.addEventListener("change", save);
  root.querySelector("#ui-reset").addEventListener("click", () => {
    preferences = { ...defaults };
    render();
    try { localStorage.removeItem(key); status.textContent = "Ajustes restablecidos."; }
    catch { status.textContent = "Ajustes restablecidos en esta pestaña."; }
  });
  root.querySelector("#ui-export").addEventListener("click", () => {
    if (exportUrl) URL.revokeObjectURL(exportUrl);
    exportUrl = URL.createObjectURL(new Blob([JSON.stringify(preferences, null, 2)], { type: "application/json" }));
    const link = document.createElement("a");
    link.href = exportUrl;
    link.download = "yaiwes-ui-preferences.json";
    link.click();
    status.textContent = "Descarga de preferencias solicitada.";
  });
  root.querySelector("#ui-import").addEventListener("change", async event => {
    const file = event.target.files[0];
    if (!file) return;
    try {
      if (file.size > 10240) throw new Error("Archivo JSON demasiado grande.");
      preferences = validate(JSON.parse(await file.text()));
      render();
      save();
    } catch (error) { status.textContent = error.message; }
    event.target.value = "";
  });
  const showConnectors = () => {
    const query = root.querySelector("#connectors-search").value.toLocaleLowerCase();
    const list = root.querySelector("#connectors-list");
    list.replaceChildren();
    for (const entry of connectors.filter(item =>
      `${item.id || ""} ${item.kind || ""}`.toLocaleLowerCase().includes(query))) {
      list.append(node("div", `${entry.id} · ${entry.status || "estado no publicado"} · ${entry.kind || "tipo no publicado"} · ${entry.ports?.role || "rol no publicado"}`, "item"));
    }
    if (!list.children.length) list.append(node("p", "Sin conectores para este filtro.", "muted"));
  };
  const read = async (path, field, targetId, statusId) => {
    const list = root.querySelector(targetId);
    const indicator = root.querySelector(statusId);
    indicator.textContent = "Consultando Router…";
    list.replaceChildren();
    try {
      const response = await api(path);
      if (disposed) return;
      const entries = response.data[field] || [];
      if (field === "connectors") {
        connectors = entries;
        showConnectors();
      } else {
        for (const entry of entries) list.append(node("div",
          `${entry.id || entry.name || "Control"} · ${entry.status || "sin estado publicado"}`, "item"));
        if (!entries.length) list.append(node("p", "Sin controles publicados.", "muted"));
      }
      indicator.textContent = `${entries.length} registros consultados · sólo lectura`;
    } catch (error) {
      if (disposed) return;
      if (field === "connectors") connectors = [];
      list.append(node("p", "No hay datos confirmados.", "muted"));
      indicator.textContent = `No disponible: ${error.message}`;
    }
  };
  const load = () => Promise.all([
    read("/chat/org/connectors", "connectors", "#connectors-list", "#connectors-status"),
    read("/chat/org/engineering", "toggles", "#engineering-list", "#engineering-status")
  ]);
  root.querySelector("#connectors-search").addEventListener("input", showConnectors);
  root.querySelector("#config-reload").addEventListener("click", () => { void load(); });
  render();
  await load();
  return () => { disposed = true; if (exportUrl) URL.revokeObjectURL(exportUrl); };
}

void mount(document, { api }).catch(error => tell(error.message));
