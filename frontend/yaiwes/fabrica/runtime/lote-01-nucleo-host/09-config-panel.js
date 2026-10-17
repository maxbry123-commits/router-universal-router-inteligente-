/* 09-config-panel.js
 * 1 función: panel Configuración UI (Office Customize Ribbon).
 * Con clave: añadir ventana o botón a un slot existente, mismo diseño.
 * Cablear: import { YaiwesConfigPanel } from "./09-config-panel.js";
 */

import { accessKey } from "./06-access-key.js";
import { slots } from "./02-slot-registry.js";
import { actions } from "./03-action-bus.js";
import { manifests } from "./05-manifest-store.js";
import { createButton } from "./07-chrome-button.js";
import { createWindow } from "./08-chrome-window.js";

const css = `
:host {
  position: fixed;
  top: 24px;
  right: 24px;
  width: 360px;
  z-index: var(--yaiwes-z-config);
  background: var(--yaiwes-bg-elev);
  border: 1px solid var(--yaiwes-line-strong);
  border-radius: var(--yaiwes-radius-lg);
  box-shadow: var(--yaiwes-shadow);
  display: none;
  font-size: 13px;
}
:host([open]) { display: block; }
header {
  padding: 12px 14px;
  border-bottom: 1px solid var(--yaiwes-line);
  font-weight: 700;
}
form, .body { padding: 12px 14px; display: grid; gap: 8px; }
label { display: grid; gap: 4px; color: var(--yaiwes-text-dim); }
input, select {
  height: 32px;
  border-radius: var(--yaiwes-radius-sm);
  border: 1px solid var(--yaiwes-line);
  background: var(--yaiwes-bg-input);
  color: var(--yaiwes-text);
  padding: 0 8px;
}
button.run {
  height: 36px;
  border: 0;
  border-radius: var(--yaiwes-radius-sm);
  background: var(--yaiwes-accent);
  color: #052014;
  font-weight: 700;
  cursor: pointer;
}
button.ghost {
  height: 32px;
  background: transparent;
  color: var(--yaiwes-text);
  border: 1px solid var(--yaiwes-line);
  border-radius: var(--yaiwes-radius-sm);
  cursor: pointer;
}
.msg { min-height: 1.2em; color: var(--yaiwes-accent-3); }
.err { color: var(--yaiwes-danger); }
.ok { color: var(--yaiwes-ok); }
`;

export class YaiwesConfigPanel extends HTMLElement {
  constructor() {
    super();
    this._root = this.attachShadow({ mode: "open" });
    this._host = null;
  }

  connectedCallback() {
    this.render();
  }

  attachHost(host) {
    this._host = host;
  }

  async open() {
    this.setAttribute("open", "");
    this.render();
  }

  close() {
    this.removeAttribute("open");
  }

  render() {
    this._root.innerHTML = "";
    const style = document.createElement("style");
    style.textContent = css;
    this._root.appendChild(style);
    const header = document.createElement("header");
    header.textContent = "Configuración UI YAIWES";
    this._root.appendChild(header);
    if (!accessKey.isUnlocked()) {
      this._root.appendChild(this._lockForm());
      return;
    }
    this._root.appendChild(this._editor());
  }

  _lockForm() {
    const form = document.createElement("form");
    const lab = document.createElement("label");
    lab.textContent = "Clave";
    const input = document.createElement("input");
    input.type = "password";
    input.autocomplete = "off";
    input.placeholder = "YAIWES-CONFIG";
    lab.appendChild(input);
    const btn = document.createElement("button");
    btn.className = "run";
    btn.type = "submit";
    btn.textContent = "Desbloquear";
    const msg = document.createElement("div");
    msg.className = "msg";
    form.appendChild(lab);
    form.appendChild(btn);
    form.appendChild(msg);
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const r = await accessKey.unlock(input.value);
      if (!r.ok) {
        msg.className = "msg err";
        msg.textContent = "clave incorrecta";
        return;
      }
      this.render();
    });
    return form;
  }

  _editor() {
    const wrap = document.createElement("div");
    wrap.className = "body";
    const kind = select("Tipo", ["button", "window"]);
    const id = field("id", "fn.nuevo-boton");
    const label = field("label", "Nuevo");
    const icon = field("icon", "+");
    const action = field("action", "fn.noop");
    const slot = select("targetSlot / slotId", slots.list().map((s) => s.id).concat(["window.nueva.toolbar"]));
    const msg = document.createElement("div");
    msg.className = "msg";
    const add = document.createElement("button");
    add.className = "run";
    add.type = "button";
    add.textContent = "Añadir al host";
    add.addEventListener("click", () => {
      const k = kind.querySelector("select").value;
      const raw = {
        id: id.querySelector("input").value.trim(),
        kind: k,
        label: label.querySelector("input").value.trim(),
        icon: icon.querySelector("input").value.trim(),
        action: action.querySelector("input").value.trim(),
        size: "regular"
      };
      if (k === "window") raw.slotId = slot.querySelector("select").value;
      else raw.targetSlot = slot.querySelector("select").value;
      const saved = manifests.add(raw);
      if (!saved.ok) {
        msg.className = "msg err";
        msg.textContent = JSON.stringify(saved);
        return;
      }
      const painted = paintManifest(saved.value, this._host);
      msg.className = painted.ok ? "msg ok" : "msg err";
      msg.textContent = painted.ok ? "añadido " + saved.value.id : painted.reason;
    });
    const exp = document.createElement("button");
    exp.className = "ghost";
    exp.type = "button";
    exp.textContent = "Descargar manifiestos JSON";
    exp.addEventListener("click", () => manifests.download());
    const lock = document.createElement("button");
    lock.className = "ghost";
    lock.type = "button";
    lock.textContent = "Cerrar sesión config";
    lock.addEventListener("click", () => {
      accessKey.lock();
      this.render();
    });
    [kind, id, label, icon, action, slot, add, exp, lock, msg].forEach((n) => wrap.appendChild(n));
    return wrap;
  }
}

function field(name, placeholder) {
  const lab = document.createElement("label");
  lab.appendChild(document.createTextNode(name));
  const input = document.createElement("input");
  input.placeholder = placeholder;
  input.value = placeholder;
  lab.appendChild(input);
  return lab;
}

function select(name, options) {
  const lab = document.createElement("label");
  lab.appendChild(document.createTextNode(name));
  const sel = document.createElement("select");
  (options.length ? options : ["(sin slots — cablea host)"]).forEach((o) => {
    const opt = document.createElement("option");
    opt.value = o;
    opt.textContent = o;
    sel.appendChild(opt);
  });
  lab.appendChild(sel);
  return lab;
}

export function paintManifest(m, host) {
  if (m.kind === "window") {
    const el = createWindow(m, host || document.body);
    return { ok: true, id: m.id, el };
  }
  if (m.kind === "button" || m.kind === "toggle") {
    if (!actions.has(m.action)) {
      return { ok: false, reason: "action_missing:" + m.action };
    }
    const el = createButton(m);
    const mounted = slots.mount(m.targetSlot, el);
    return mounted.ok ? { ok: true, id: m.id, el } : mounted;
  }
  return { ok: false, reason: "kind_unsupported" };
}

if (!customElements.get("yaiwes-config-panel")) {
  customElements.define("yaiwes-config-panel", YaiwesConfigPanel);
}
