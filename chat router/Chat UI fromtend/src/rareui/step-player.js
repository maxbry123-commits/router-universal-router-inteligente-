import { el, button } from "../dom.js";
// 15 step-player: reproductor de pasos con posición real.
export function stepPlayer({ steps = [] } = {}) {
  let index = 0;
  const label = el("p", { class: "rui-step-label" });
  const prev = button("←", () => { index = Math.max(0, index - 1); paint(); });
  const next = button("→", () => { index = Math.min(steps.length - 1, index + 1); paint(); });
  function paint() {
    label.textContent = steps.length ? (index + 1) + "/" + steps.length + " · " + steps[index] : "—";
    prev.disabled = index === 0;
    next.disabled = index >= steps.length - 1;
  }
  paint();
  return el("div", { class: "rui-steps" }, prev, label, next);
}
