import { el } from "../dom.js";
// 07 fluid-orb: esfera animada que reacciona al puntero.
export function fluidOrb() {
  const orb = el("div", { class: "rui-orb", role: "img", "aria-label": "fluid-orb" });
  orb.addEventListener("pointermove", event => {
    const r = orb.getBoundingClientRect();
    orb.style.setProperty("--ox", ((event.clientX - r.left) / r.width * 100).toFixed(1) + "%");
    orb.style.setProperty("--oy", ((event.clientY - r.top) / r.height * 100).toFixed(1) + "%");
  });
  return orb;
}
