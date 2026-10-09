import { el } from "../dom.js";
// 16 grid-reveal: tarjetas que aparecen escalonadas al entrar en vista.
export function gridReveal({ items = [] } = {}) {
  const grid = el("div", { class: "rui-grid-reveal" });
  items.forEach((item, i) => {
    const cell = el("div", { class: "rui-grid-cell", text: String(item) });
    cell.style.transitionDelay = (i * 35) + "ms";
    grid.append(cell);
  });
  const reveal = () => grid.classList.add("shown");
  if (typeof IntersectionObserver === "function") {
    new IntersectionObserver(entries => { if (entries.some(e => e.isIntersecting)) reveal(); }).observe(grid);
  } else reveal();
  return grid;
}
