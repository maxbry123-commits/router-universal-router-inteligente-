import { installSameOriginChatBridge } from "./plugins/same-origin-chat.js";
import { createChatContext } from "./context.js";
import { renderChat } from "./panels/chat.js";
import { renderFiles } from "./panels/files.js";
import { renderTracking } from "./panels/tracking.js";
import { renderCanvas } from "./panels/canvas.js";
import { el, button } from "./dom.js";

const panels = {
  chat: ["Chat", renderChat],
  files: ["Archivos", renderFiles],
  tracking: ["Seguimiento", renderTracking],
  canvas: ["Canvas", renderCanvas],
};
let active = "chat";
let currentPanel;
let context;
function navigate(id) {
  if (!panels[id]) return;
  active = id;
  context.refresh();
  document.querySelector(`[data-panel="${id}"]`)?.focus();
}
function renderShell() {
  currentPanel?.release?.();
  const nav = el("nav", { class: "workspace-nav", "aria-label": "Paneles" },
    ...Object.entries(panels).map(([id, [label]]) => {
      const control = button(label, () => navigate(id), "workspace-nav-item");
      control.dataset.panel = id;
      if (id === active) control.setAttribute("aria-current", "page");
      return control;
    }));
  currentPanel = panels[active][1](context);
  return el("div", { class: "workspace" },
    el("aside", { class: "workspace-sidebar" },
      el("div", { class: "workspace-title" }, el("strong", { text: "Y" }), el("span", { text: "YAIWES" })),
      nav,
      el("p", { class: "sub", text: "Los datos remotos requieren un bridge autenticado del host." })),
    el("div", { class: "workspace-content" }, currentPanel));
}

installSameOriginChatBridge();
context = createChatContext(document.getElementById("app"), document.getElementById("status"),
  { render: renderShell, onChat: () => navigate("chat") });
context.refresh();
