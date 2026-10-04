import { el, button } from "../dom.js";

export const WALL_VIEWS = Object.freeze([
  ["WALL-01", "Bloques"], ["WALL-02", "Árbol"], ["WALL-03", "Archivos"],
  ["WALL-04", "Preguntar"], ["WALL-05", "Tap archivo"], ["WALL-06", "Tap bloque"],
  ["WALL-07", "Seis raíces"], ["WALL-08", "Grid 00–25 (26 claves)"],
  ["WALL-09", "Lista de archivos"], ["WALL-10", "Sheet bloque"],
  ["WALL-11", "Sheet archivo"], ["WALL-12", "Sheet raíz"],
  ["WALL-13", "Sheet extra"], ["WALL-14", "Añadir raíz"],
  ["WALL-15", "Guardar / compartir"], ["WALL-16", "State JSON"],
]);

export function renderWallViews() {
  const detail = el("p", { class: "panel-state pending", role: "status", text: "Las superficies de referencia no son estado verificado." });
  return el("details", { class: "workspace-section", "aria-label": "Crazy Wall · dieciséis superficies" },
    el("summary", { text: "Crazy Wall · 16 superficies de referencia" }),
    el("div", { class: "workspace-grid" }, ...WALL_VIEWS.map(([id, label]) =>
      button(`${id} · ${label}`, () => {
        detail.className = "panel-state error";
        detail.textContent = `${label}: NOT_IMPLEMENTED · falta STATE.json/CRAZY_WALL.json servido con read-back.`;
      }, "workspace-item"))),
    detail);
}
