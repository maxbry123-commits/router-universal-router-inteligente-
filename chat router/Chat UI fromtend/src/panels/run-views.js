import { el, button } from "../dom.js";

export const RUN_VIEWS = Object.freeze([
  ["RUN-01", "CASCADE"], ["RUN-02", "TREN"], ["RUN-03", "AUDITOR"],
  ["RUN-04", "VENTANAS V-01…V-04"], ["RUN-05", "ORQUESTA"],
  ["RUN-06", "Sandbox"], ["RUN-07", "Código YAML"], ["RUN-08", "Nodo / IN / OUT"],
]);

export function renderRunViews() {
  const detail = el("p", { class: "panel-state pending", role: "status", text: "Selecciona una vista. El estado de DAG requiere T-05; no se simula." });
  return el("details", { class: "workspace-section", "aria-label": "Run · ocho vistas" },
    el("summary", { text: "Run · 8 vistas de referencia" }),
    el("div", { class: "workspace-grid" }, ...RUN_VIEWS.map(([id, label]) =>
      button(`${id} · ${label}`, () => {
        detail.className = "panel-state error";
        detail.textContent = `${label}: NOT_IMPLEMENTED · no hay lectura de DAG T-05; ningún paso se ejecutó.`;
      }, "workspace-item"))),
    detail);
}
