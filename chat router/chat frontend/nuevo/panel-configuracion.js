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
  let connectorsLoaded = false;
  let connectorsRequest = 0;
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
  root.querySelector("#ui-copy").addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(preferences, null, 2));
      status.textContent = "Ajustes copiados al portapapeles.";
    } catch { status.textContent = "El navegador no permitió copiar al portapapeles."; }
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
    if (!connectorsLoaded) {
      list.append(node("p", "No hay datos confirmados.", "muted"));
      return;
    }
    for (const entry of connectors.filter(item =>
      `${item.id || ""} ${item.kind || ""}`.toLocaleLowerCase().includes(query))) {
      const fields = [
        entry.id || "conector",
        entry.status && `estado: ${entry.status}`,
        entry.kind && `tipo: ${entry.kind}`,
        entry.health && `salud: ${entry.health}`,
        entry.ports?.role && `rol: ${entry.ports.role}`
      ].filter(Boolean);
      list.append(node("div", fields.join(" · "), "item"));
    }
    if (!list.children.length) list.append(node("p", "Sin conectores para este filtro.", "muted"));
  };
  const read = async (path, field, targetId, statusId) => {
    const list = root.querySelector(targetId);
    const indicator = root.querySelector(statusId);
    indicator.textContent = "Consultando Router…";
    list.replaceChildren();
    const request = field === "connectors" ? ++connectorsRequest : 0;
    if (field === "connectors") connectorsLoaded = false;
    try {
      const response = await api(path);
      if (disposed || (field === "connectors" && request !== connectorsRequest)) return;
      const entries = response.data[field] || [];
      if (field === "connectors") {
        connectors = entries;
        connectorsLoaded = true;
        showConnectors();
      } else {
        for (const entry of entries) {
          const fields = [
            entry.id || entry.name || "Control",
            entry.status || "sin estado publicado",
            entry.enabled === true ? "habilitado" : entry.enabled === false ? "deshabilitado" : "",
            entry.description || entry.descripcion || ""
          ].filter(Boolean);
          list.append(node("div", fields.join(" · "), "item"));
        }
        if (!entries.length) list.append(node("p", "Sin controles publicados.", "muted"));
      }
      indicator.textContent = `${entries.length} registros consultados · sólo lectura`;
    } catch (error) {
      if (disposed || (field === "connectors" && request !== connectorsRequest)) return;
      if (field === "connectors") { connectors = []; connectorsLoaded = false; }
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
