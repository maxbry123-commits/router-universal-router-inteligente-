import { el } from "../dom.js";
// 05 proximity-sidebar: los iconos crecen según la cercanía del puntero.
export function proximitySidebar({ items = [] } = {}) {
  const nav = el("nav", { class: "rui-proximity", "aria-label": "proximity-sidebar" });
  for (const item of items) {
    const b = el("button", { type: "button", text: String(item.label ?? item), class: "rui-prox-item" });
    b.addEventListener("click", () => item.action?.());
    nav.append(b);
  }
  nav.addEventListener("pointermove", event => {
    for (const b of nav.children) {
      const r = b.getBoundingClientRect();
      const d = Math.abs(event.clientY - (r.top + r.height / 2));
      const s = Math.max(1, 1.6 - d / 120);
      b.style.transform = "scale(" + s.toFixed(2) + ")";
    }
  });
  nav.addEventListener("pointerleave", () => { for (const b of nav.children) b.style.transform = ""; });
  return nav;
}
