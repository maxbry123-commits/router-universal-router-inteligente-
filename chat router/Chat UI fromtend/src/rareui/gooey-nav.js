import { el, button } from "../dom.js";
// 17 gooey-nav: pestañas con indicador que se desliza a la activa.
export function gooeyNav({ items = [], onPick } = {}) {
  const marker = el("span", { class: "rui-gooey-marker" });
  const nav = el("nav", { class: "rui-gooey" }, marker);
  for (const item of items) {
    const b = button(String(item.label ?? item), () => {
      nav.querySelectorAll("button").forEach(x => x.setAttribute("aria-pressed", "false"));
      b.setAttribute("aria-pressed", "true");
      marker.style.transform = "translateX(" + b.offsetLeft + "px)";
      marker.style.width = b.offsetWidth + "px";
      onPick?.(item);
    });
    nav.append(b);
  }
  return nav;
}
