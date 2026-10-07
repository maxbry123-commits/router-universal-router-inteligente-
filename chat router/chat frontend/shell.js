import { api } from "./api.js";
import { mount as chat } from "./panel-chat.js";
import { mount as archivos } from "./panel-archivos.js";
import { mount as seguimiento } from "./panel-seguimiento.js";
import { mount as canvas } from "./panel-canvas.js";
import { mount as organization } from "./panel-org.js";

const panels = { chat, archivos, seguimiento, canvas, connectors: organization, templates: organization, engineering: organization };
const labels = { chat: "Chat", archivos: "Archivos", seguimiento: "Seguimiento", canvas: "Canvas",
  connectors: "Conectores", templates: "Plantillas", engineering: "Ingeniería" };
const panel = document.querySelector("#panel");
const notice = document.querySelector("#notice");
const tell = message => { notice.textContent = message || ""; };
let cleanup;
let requestId = 0;
const connection = document.querySelector("#connection");
document.querySelector("#connect").addEventListener("click", () => window.location.reload());
window.addEventListener("router-connection", event => {
  connection.textContent = event.detail;
});

async function show(view) {
  if (!panels[view]) return;
  const currentId = ++requestId;
  if (cleanup) cleanup();
  cleanup = undefined;
  document.querySelectorAll("[data-view]").forEach(button => {
    if (button.dataset.view === view) button.setAttribute("aria-current", "page");
    else button.removeAttribute("aria-current");
  });
  document.querySelector("#view-title").textContent = labels[view];
  tell("");
  try {
    const response = await fetch(`/chat/ui/panel-${["connectors", "templates", "engineering"].includes(view) ? "org" : view}.html`, { cache: "no-store" });
    if (!response.ok) throw new Error("PANEL_UNAVAILABLE");
    const html = await response.text();
    if (currentId !== requestId) return;
    panel.innerHTML = html;
    const dispose = await panels[view](panel, { api, tell, view });
    if (currentId === requestId) cleanup = dispose;
    else if (dispose) dispose();
  } catch (error) { if (currentId === requestId) tell(error.message); }
}
document.querySelector("#navigation").addEventListener("click", event => {
  const link = event.target.closest("a[data-view]");
  if (!link || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
  event.preventDefault();
  if (new URL(window.location.href).searchParams.get("view") !== link.dataset.view) {
    window.history.pushState({}, "", link.href);
  }
  show(link.dataset.view);
});
function currentView() {
  const view = new URL(window.location.href).searchParams.get("view");
  return Object.hasOwn(panels, view) ? view : "chat";
}
window.addEventListener("popstate", () => show(currentView()));
show(currentView());
const TEMAS = ["little", "matte", "crystal", "orange", "blue", "blanco", "gris"];
function aplicarTema(valor) {
  const tema = TEMAS.includes(valor) ? valor : "little";
  document.documentElement.dataset.theme = tema;
  try { localStorage.setItem("riu_tema", tema); } catch (error) { /* sin almacenamiento: vale solo en esta sesion */ }
  return tema;
}
let temaGuardado = "little";
try { temaGuardado = localStorage.getItem("riu_tema") || "little"; } catch (error) { /* sin almacenamiento */ }
const selectorTema = document.querySelector("#theme");
if (selectorTema) {
  selectorTema.value = aplicarTema(temaGuardado);
  selectorTema.addEventListener("change", () => { selectorTema.value = aplicarTema(selectorTema.value); });
}
