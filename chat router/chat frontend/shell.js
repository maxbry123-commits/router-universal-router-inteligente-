import { api } from "./api.js";
import { mount as chat } from "./panel-chat.js";
import { mount as archivos } from "./panel-archivos.js";
import { mount as seguimiento } from "./panel-seguimiento.js";
import { mount as canvas } from "./panel-canvas.js";
import { mount as organization } from "./panel-org.js";
import { mount as apariencia } from "./panel-apariencia.js";
import "./apariencia-aplicar.js";
import "./tools-ventana.js";  // MVP tools: ventana en el chat + bloque en Configuración  // aplica la apariencia guardada en todo el chat

const panels = { chat, archivos, seguimiento, canvas, connectors: organization, templates: organization, engineering: organization, apariencia };
const labels = { chat: "Chat", archivos: "Archivos", seguimiento: "Seguimiento", canvas: "Canvas",
  connectors: "Conectores", templates: "Plantillas", engineering: "Ingeniería", apariencia: "Configuración" };
const panel = document.querySelector("#panel");
const mmMovil = window.matchMedia("(max-width: 720px)");
const mvBar = document.querySelector("#movil-bar"), mvPanel = document.querySelector("#movil-panel"),
      mvToggle = document.querySelector("#movil-toggle"), mvStatus = document.querySelector("#movil-status");
function aplicarMovil() {
  const nav = document.querySelector("#navigation"), topbar = document.querySelector(".topbar"),
        navSlot = document.querySelector("#nav-slot"), topSlot = document.querySelector("#topbar-slot"),
        ctlInt = document.querySelector(".ctl-int"), ctlPanel = document.querySelector("#ctl-panel");
  if (mmMovil.matches) {  // reubicar los nodos EXISTENTES (no clonarlos): listeners y show(view) siguen intactos
    mvBar.hidden = false;
    if (nav) document.querySelector("#mv-nav").appendChild(nav);
    if (topbar) document.querySelector("#mv-top").appendChild(topbar);
    if (ctlInt) document.querySelector("#mv-ctl").appendChild(ctlInt);  // Controles entero: h1, chats, pills, selectores
    const h1 = document.querySelector("#panel h1");  // h1 de otras vistas (el del chat viaja dentro de ctl-int)
    if (h1) { h1._mvHome = h1.parentNode; h1._mvNext = h1.nextSibling; document.querySelector("#mv-title").appendChild(h1); }
  } else {
    mvBar.hidden = true; mvPanel.hidden = true;
    if (nav && navSlot) navSlot.after(nav);
    if (topbar && topSlot) topSlot.after(topbar);
    if (ctlInt && ctlPanel) ctlPanel.appendChild(ctlInt);
    const h1 = document.querySelector("#mv-title h1");
    if (h1 && h1._mvHome) h1._mvHome.insertBefore(h1, h1._mvNext);
  }
}
mvToggle.addEventListener("click", () => {
  mvPanel.hidden = !mvPanel.hidden;
  mvToggle.setAttribute("aria-expanded", String(!mvPanel.hidden));
  mvToggle.textContent = mvToggle.textContent.replace(/.$/, mvPanel.hidden ? "v" : "^");
});
mmMovil.addEventListener("change", aplicarMovil);
const notice = document.querySelector("#notice");
const tell = message => { notice.textContent = message || ""; };
let cleanup;
const connection = document.querySelector("#connection");
document.querySelector("#connect").addEventListener("click", () => window.location.reload());
window.addEventListener("router-connection", event => {
  connection.textContent = event.detail;
  mvStatus.textContent = "· " + (event.detail || "Router");
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
  mvToggle.textContent = labels[view] + (mvPanel.hidden ? " v" : " ^");
  tell("");
  try {
    const response = await fetch(`/chat/ui/panel-${["connectors", "templates", "engineering"].includes(view) ? "org" : view}.html`, { cache: "no-store" });
    if (!response.ok) throw new Error("PANEL_UNAVAILABLE");
    panel.innerHTML = await response.text();
    cleanup = await panels[view](panel, { api, tell, view });
    aplicarMovil();  // cada vista montada se reubica en la pestana si es movil
  } catch (error) { tell(error.message); }
}
document.querySelector("#navigation").addEventListener("click", event => {
  const button = event.target.closest("[data-view]");
  if (button) show(button.dataset.view);
});
aplicarMovil();
show("chat");
const TEMAS = ["gris", "little", "matte", "blanco", "crystal", "orange", "blue"];
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
