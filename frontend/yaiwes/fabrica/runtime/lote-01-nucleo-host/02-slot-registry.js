/* 02-slot-registry.js
 * 1 función: registrar y resolver slots de ventanas existentes.
 * Fail-closed: slot desconocido => null, no se pinta.
 * Cablear: import { SlotRegistry } from "./02-slot-registry.js";
 */

export const SLOT_KIND = Object.freeze({
  toolbar: "toolbar",
  group: "group",
  body: "body",
  footer: "footer",
  qat: "qat"
});

export class SlotRegistry {
  constructor() {
    this._slots = new Map();
  }

  register(slotId, element, kind) {
    if (typeof slotId !== "string" || !slotId.trim()) {
      throw new Error("SlotRegistry.register: slotId vacío");
    }
    if (!(element instanceof HTMLElement)) {
      throw new Error("SlotRegistry.register: element no es HTMLElement");
    }
    const k = kind || element.getAttribute("data-slot-kind") || SLOT_KIND.toolbar;
    if (!SLOT_KIND[k]) {
      throw new Error("SlotRegistry.register: kind inválido " + k);
    }
    element.setAttribute("data-slot-id", slotId);
    element.setAttribute("data-slot-kind", k);
    element.classList.add("yaiwes-slot");
    this._slots.set(slotId, { id: slotId, kind: k, element });
    return this._slots.get(slotId);
  }

  get(slotId) {
    return this._slots.get(slotId) || null;
  }

  has(slotId) {
    return this._slots.has(slotId);
  }

  list() {
    return Array.from(this._slots.values()).map((s) => ({
      id: s.id,
      kind: s.kind
    }));
  }

  mount(slotId, node) {
    const slot = this.get(slotId);
    if (!slot) {
      return { ok: false, reason: "slot_missing", slotId };
    }
    if (!(node instanceof Node)) {
      return { ok: false, reason: "node_invalid", slotId };
    }
    slot.element.appendChild(node);
    return { ok: true, slotId };
  }

  unmountByControlId(controlId) {
    for (const s of this._slots.values()) {
      const found = s.element.querySelector('[data-control-id="' + cssEscape(controlId) + '"]');
      if (found) found.remove();
    }
  }

  scan(root) {
    const scope = root || document;
    const nodes = scope.querySelectorAll("[data-slot-id]");
    const out = [];
    nodes.forEach((el) => {
      out.push(this.register(el.getAttribute("data-slot-id"), el, el.getAttribute("data-slot-kind")));
    });
    return out;
  }
}

function cssEscape(value) {
  if (typeof CSS !== "undefined" && typeof CSS.escape === "function") {
    return CSS.escape(value);
  }
  return String(value).replace(/[^a-zA-Z0-9_\-]/g, "\\$&");
}

export const slots = new SlotRegistry();
