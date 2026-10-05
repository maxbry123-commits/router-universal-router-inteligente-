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
const connection = document.querySelector("#connection");
document.querySelector("#connect").addEventListener("click", () => window.location.reload());
window.addEventListener("router-connection", event => {
  connection.textContent = event.detail;
});

async function show(view) {
  if (!panels[view]) return;
  if (cleanup) cleanup();
  cleanup = undefined;
  document.querySelectorAll("[data-view]").forEach(button => {
    if (button.dataset.view === view) button.setAttribute("aria-current", "page");
    else button.removeAttribute("aria-current");
  });
  document.querySelector("#view-title").textContent = labels[view];
  tell("");
  try {
    const response = await fetch(`/chat/ui/panel-${["connectors", "templates", "engineering"].includes(view) ? "org" : view}.html`);
    if (!response.ok) throw new Error("PANEL_UNAVAILABLE");
    panel.innerHTML = await response.text();
    cleanup = await panels[view](panel, { api, tell, view });
  } catch (error) { tell(error.message); }
}
document.querySelector("#navigation").addEventListener("click", event => {
  const button = event.target.closest("[data-view]");
  if (button) show(button.dataset.view);
});
show("chat");
const TEMAS = ["gris", "little", "matte", "blanco"];
function aplicarTema(valor) {
  const tema = TEMAS.includes(valor) ? valor : "gris";
  document.documentElement.dataset.theme = tema;
  try { localStorage.setItem("riu_tema", tema); } catch (error) { /* sin almacenamiento: vale solo en esta sesion */ }
  return tema;
}
let temaGuardado = "gris";
try { temaGuardado = localStorage.getItem("riu_tema") || "gris"; } catch (error) { /* sin almacenamiento */ }
const selectorTema = document.querySelector("#theme");
if (selectorTema) {
  selectorTema.value = aplicarTema(temaGuardado);
  selectorTema.addEventListener("change", () => { selectorTema.value = aplicarTema(selectorTema.value); });
}
