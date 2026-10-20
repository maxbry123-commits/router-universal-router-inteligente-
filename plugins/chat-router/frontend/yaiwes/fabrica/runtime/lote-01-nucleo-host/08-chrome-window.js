/* 08-chrome-window.js
 * 1 función: pintar UNA ventana con slots (toolbar/body/footer).
 * 1 ventana = este custom element instanciado. No agrupa otras ventanas.
 * Cablear: import { YaiwesWindow, createWindow } from "./08-chrome-window.js";
 */

import { slots } from "./02-slot-registry.js";

const css = `
:host {
  display: flex;
  flex-direction: column;
  background: var(--yaiwes-bg-elev);
  border: 1px solid var(--yaiwes-line);
  border-radius: var(--yaiwes-radius);
  box-shadow: var(--yaiwes-shadow);
  min-width: 280px;
  min-height: 160px;
  overflow: hidden;
}
.titlebar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: var(--yaiwes-bg-panel);
  border-bottom: 1px solid var(--yaiwes-line);
  font-size: 13px;
  font-weight: 600;
}
.toolbar, .body, .footer {
  display: flex;
  flex-wrap: wrap;
  gap: var(--yaiwes-gap);
}
.body {
  flex: 1;
  padding: var(--yaiwes-pad);
  background: var(--yaiwes-bg);
}
.footer {
  padding: var(--yaiwes-pad-sm) var(--yaiwes-pad);
  border-top: 1px solid var(--yaiwes-line);
  background: var(--yaiwes-bg-panel);
}
`;

export class YaiwesWindow extends HTMLElement {
  constructor() {
    super();
    this._root = this.attachShadow({ mode: "open" });
  }

  connectedCallback() {
    this.render();
    this._registerSlots();
  }

  applyManifest(m) {
    this.setAttribute("data-window-id", m.id);
    this.setAttribute("label", m.label);
    if (m.slotId) this.setAttribute("slot-id", m.slotId);
  }

  render() {
    const id = this.getAttribute("data-window-id") || "window.unnamed";
    const label = this.getAttribute("label") || id;
    this._root.innerHTML = "";
    const style = document.createElement("style");
    style.textContent = css;
    const title = document.createElement("div");
    title.className = "titlebar";
    title.textContent = label;
    const toolbar = document.createElement("div");
    toolbar.className = "toolbar yaiwes-slot";
    toolbar.setAttribute("data-slot-id", id + ".toolbar");
    toolbar.setAttribute("data-slot-kind", "toolbar");
    const body = document.createElement("div");
    body.className = "body yaiwes-slot";
    body.setAttribute("data-slot-id", id + ".body");
    body.setAttribute("data-slot-kind", "body");
    const footer = document.createElement("div");
    footer.className = "footer yaiwes-slot";
    footer.setAttribute("data-slot-id", id + ".footer");
    footer.setAttribute("data-slot-kind", "footer");
    this._root.appendChild(style);
    this._root.appendChild(title);
    this._root.appendChild(toolbar);
    this._root.appendChild(body);
    this._root.appendChild(footer);
  }

  _registerSlots() {
    this._root.querySelectorAll("[data-slot-id]").forEach((el) => {
      slots.register(el.getAttribute("data-slot-id"), el, el.getAttribute("data-slot-kind"));
    });
  }
}

if (!customElements.get("yaiwes-window")) {
  customElements.define("yaiwes-window", YaiwesWindow);
}

export function createWindow(manifest, host) {
  const el = document.createElement("yaiwes-window");
  el.applyManifest(manifest);
  if (host instanceof HTMLElement) host.appendChild(el);
  return el;
}
