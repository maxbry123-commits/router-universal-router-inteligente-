import { el } from "../dom.js";
// 02 bounce-sidebar: raíl lateral con rebote al abrir.
export function bounceSidebar({ items = [], onPick } = {}) {
  const nav = el("nav", { class: "rui-bounce", "aria-label": "bounce-sidebar" });
  const paint = () => {
    nav.replaceChildren(...items.map((item, i) => {
      const b = el("button", { type: "button", text: String(item.label ?? item) });
      b.style.transitionDelay = (i * 30) + "ms";
      b.addEventListener("click", () => onPick?.(item));
      return b;
    }));
  };
  paint();
  nav.open = () => { nav.classList.add("open"); paint(); };
  nav.close = () => nav.classList.remove("open");
  return nav;
}
