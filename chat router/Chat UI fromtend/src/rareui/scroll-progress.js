import { el } from "../dom.js";
// 08 scroll-progress: barra que refleja el desplazamiento real del contenedor.
export function scrollProgress(target) {
  const bar = el("div", { class: "rui-scroll-bar" });
  const root = el("div", { class: "rui-scroll" }, bar);
  const update = () => {
    const max = target.scrollHeight - target.clientHeight;
    bar.style.width = (max > 0 ? (target.scrollTop / max) * 100 : 0).toFixed(1) + "%";
  };
  target.addEventListener("scroll", update, { passive: true });
  update();
  return root;
}
