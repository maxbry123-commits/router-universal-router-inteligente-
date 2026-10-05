import { api } from "./api.js";
import { mount as chat } from "./panel-chat.js";
import { mount as media } from "./panel-media.js";
import { mount as agentes } from "./panel-agentes.js";
import { mount as seguimiento } from "./panel-seguimiento.js";
import { mount as configuracion } from "./panel-configuracion.js";

const panels = { chat, media, agentes, seguimiento, configuracion };
const labels = { chat: "Chat", media: "Imágenes y videos", agentes: "Multiagente",
  seguimiento: "Seguimiento y planificación", configuracion: "Configuración de UI" };
const panel = document.querySelector("#panel");
const notice = document.querySelector("#notice");
const tell = message => { notice.textContent = message || ""; };
let cleanup;
let generation = 0;
const connection = document.querySelector("#connection");
document.querySelector("#connect").addEventListener("click", () => window.location.reload());
window.addEventListener("router-connection", event => {
  connection.textContent = event.detail;
});

async function show(view) {
  if (!panels[view]) return;
  const current = ++generation;
  if (cleanup) cleanup();
  cleanup = undefined;
  document.querySelectorAll("[data-view]").forEach(button => {
    if (button.dataset.view === view) button.setAttribute("aria-current", "page");
    else button.removeAttribute("aria-current");
  });
  document.querySelector("#view-title").textContent = labels[view];
  tell("");
  try {
    const response = await fetch(`/chat/ui/panel-${view}.html`);
    if (!response.ok) throw new Error("PANEL_UNAVAILABLE");
    const html = await response.text();
    if (current !== generation) return;
    const content = document.createElement("div");
    content.innerHTML = html;
    panel.replaceChildren(content);
    document.querySelector("#panel-style").href = `/chat/ui/panel-${view}.css`;
    const dispose = await panels[view](content, {
      api, tell: message => { if (current === generation) tell(message); }, view
    });
    if (current === generation) cleanup = dispose;
    else if (dispose) dispose();
  } catch (error) { if (current === generation) tell(error.message); }
}
document.querySelector("#navigation").addEventListener("click", event => {
  const button = event.target.closest("[data-view]");
  if (button) show(button.dataset.view);
});
show("chat");
