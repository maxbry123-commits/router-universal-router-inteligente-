/* 07-chrome-button.js
 * 1 función: pintar UN botón con tokens YAIWES.
 * No conoce ventanas. Recibe manifiesto + ActionBus.
 * Cablear: import { YaiwesButton } from "./07-chrome-button.js";
 */

import { actions } from "./03-action-bus.js";

const css = `
:host {
  display: inline-flex;
}
button {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  min-width: 36px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--yaiwes-text);
  font-family: var(--yaiwes-font);
  cursor: pointer;
  border-radius: var(--yaiwes-radius-sm);
}
button:hover { background: var(--yaiwes-bg-panel); border-color: var(--yaiwes-line); }
button:focus-visible { outline: none; box-shadow: var(--yaiwes-focus); }
button:disabled { opacity: 0.45; cursor: not-allowed; }
button.size-small { height: var(--yaiwes-btn-h-sm); padding: 0 8px; flex-direction: row; font-size: 12px; }
button.size-regular { height: var(--yaiwes-btn-h); padding: 0 10px; flex-direction: row; font-size: 13px; }
button.size-large { height: var(--yaiwes-btn-h-lg); min-width: 64px; padding: 6px 10px; font-size: 11px; }
.icon { font-size: 16px; line-height: 1; }
.size-large .icon { font-size: 22px; }
.label { white-space: nowrap; }
`;

export class YaiwesButton extends HTMLElement {
  static get observedAttributes() {
    return ["data-control-id", "label", "size", "icon", "action", "disabled"];
  }

  constructor() {
    super();
    this._root = this.attachShadow({ mode: "open" });
    this._onClick = this._onClick.bind(this);
  }

  connectedCallback() {
    this.render();
  }

  attributeChangedCallback() {
    if (this.isConnected) this.render();
  }

  applyManifest(m) {
    this.setAttribute("data-control-id", m.id);
    this.setAttribute("label", m.label);
    this.setAttribute("size", m.size || "regular");
    this.setAttribute("icon", m.icon || "");
    this.setAttribute("action", m.action || "");
    if (m.enabled === false) this.setAttribute("disabled", "");
    else this.removeAttribute("disabled");
  }

  render() {
    const label = this.getAttribute("label") || "";
    const size = this.getAttribute("size") || "regular";
    const icon = this.getAttribute("icon") || "";
    const disabled = this.hasAttribute("disabled");
    this._root.innerHTML = "";
    const style = document.createElement("style");
    style.textContent = css;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "size-" + size;
    btn.disabled = disabled;
    if (icon) {
      const ic = document.createElement("span");
      ic.className = "icon";
      ic.textContent = icon;
      btn.appendChild(ic);
    }
    const lb = document.createElement("span");
    lb.className = "label";
    lb.textContent = label;
    btn.appendChild(lb);
    btn.addEventListener("click", this._onClick);
    this._root.appendChild(style);
    this._root.appendChild(btn);
  }

  _onClick() {
    const action = this.getAttribute("action");
    if (!action) return;
    actions.dispatch(action, {
      controlId: this.getAttribute("data-control-id"),
      label: this.getAttribute("label")
    });
  }
}

if (!customElements.get("yaiwes-button")) {
  customElements.define("yaiwes-button", YaiwesButton);
}

export function createButton(manifest) {
  const el = document.createElement("yaiwes-button");
  el.applyManifest(manifest);
  return el;
}
