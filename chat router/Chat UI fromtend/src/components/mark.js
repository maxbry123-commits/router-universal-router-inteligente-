import { el } from "../dom.js";

export function brandMark(className) {
  return el("svg", { class: className, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": "1.7", "stroke-linecap": "round", "aria-hidden": "true" },
    el("path", { d: "m5 4 7 8 7-8M12 12v8" }));
}
