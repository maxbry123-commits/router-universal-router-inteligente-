import { el } from "../dom.js";

export function brandMark(className) {
  return el("svg", { class: className, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": "1.7", "stroke-linecap": "round", "aria-hidden": "true" },
    el("path", { d: "M12 2v20M2 12h20M5 5l14 14M19 5 5 19" }));
}
