import { el } from "../dom.js";
import { v12Svg } from "../icons-v12.js";
import { readTypography } from "../typography/state.js";

// Asigna los iconos V12 de la skill a los controles de producción;
// los que no tienen equivalente V12 conservan su trazo local.
const V12_MAP = {
  more: "menu", settings: "settings", voice: "mic", shield: "shield",
  send: "send", grid: "grid", controls: "sliders", file: "file",
  connectors: "plug", export: "download", attach: "link",
};

const paths = {
  plus: "M12 5v14M5 12h14",
  chevron: "m7 10 5 5 5-5",
  more: "M5 12h.01M12 12h.01M19 12h.01",
  settings: "M4 7h16M4 17h16M8 4v6M16 14v6",
  voice: "M9 5a3 3 0 0 1 6 0v7a3 3 0 0 1-6 0V5ZM5 10v2a7 7 0 0 0 14 0v-2M12 19v3M8 22h8",
  shield: "m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6l8-3Z",
  send: "M12 19V5m-6 6 6-6 6 6",
  grid: "M4 4h6v6H4V4ZM14 4h6v6h-6V4ZM4 14h6v6H4v-6ZM14 14h6v6h-6v-6Z",
  controls: "M4 6h16M4 12h16M4 18h16M8 3v6M16 9v6M10 15v6",
  attach: "m8 12 6-6a3 3 0 0 1 4 4l-8 8a5 5 0 0 1-7-7l8-8M8 12l-2 2a2 2 0 0 0 3 3l8-8",
  file: "M14 2H5v20h14V7l-5-5ZM14 2v5h5M8 12h8M8 16h8",
  connectors: "M8 3v5M16 3v5M5 8h14v3a7 7 0 0 1-14 0V8ZM12 18v4",
  export: "M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5",
};

const SLOT_OF = { send: "send", attach: "attach", more: "tools", chevron: "back" };

export function icon(name) {
  const slot = SLOT_OF[name];
  if (slot) {
    const custom = readTypography().icons?.[slot];
    if (custom) {
      const node = v12Svg(custom, "icon svg-icon");
      if (node.innerHTML) return node;
    }
  }
  const v12Id = V12_MAP[name];
  if (v12Id) {
    const node = v12Svg(v12Id, "icon svg-icon");
    if (node.innerHTML) return node;
  }
  return el("svg", { class: "icon", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": "1.7", "stroke-linecap": "round", "stroke-linejoin": "round", "aria-hidden": "true" }, el("path", { d: paths[name] }));
}
