import { el } from "../dom.js";
// 19 animated-counter: número que anima hacia el valor real entregado.
export function animatedCounter({ value = 0, duration = 600 } = {}) {
  const out = el("span", { class: "rui-counter", text: "0" });
  const start = performance.now();
  const tick = now => {
    const p = Math.min(1, (now - start) / duration);
    out.textContent = String(Math.round(value * (1 - Math.pow(1 - p, 3))));
    if (p < 1) requestAnimationFrame(tick);
  };
  if (typeof requestAnimationFrame === "function") requestAnimationFrame(tick);
  else out.textContent = String(value);
  return out;
}
