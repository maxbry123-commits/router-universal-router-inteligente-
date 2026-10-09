import { el } from "../dom.js";
// 20 matrix-orb: orbe de puntos que responde al puntero (canvas vacío sin datos falsos).
export function matrixOrb({ points = 24 } = {}) {
  const root = el("div", { class: "rui-matrix", role: "img", "aria-label": "matrix-orb" });
  for (let i = 0; i < points; i++) {
    const dot = el("span", { class: "rui-matrix-dot" });
    const a = (i / points) * Math.PI * 2;
    dot.style.left = (50 + Math.cos(a) * 40) + "%";
    dot.style.top = (50 + Math.sin(a) * 40) + "%";
    root.append(dot);
  }
  root.addEventListener("pointermove", e => {
    const r = root.getBoundingClientRect();
    root.style.setProperty("--mx", ((e.clientX - r.left) / r.width).toFixed(2));
    root.style.setProperty("--my", ((e.clientY - r.top) / r.height).toFixed(2));
  });
  return root;
}
