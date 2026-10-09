import { el, button } from "../dom.js";
// 01 folder-component: carpeta que se abre revelando tarjetas; interacción real, sin datos falsos.
export function rareFolder({ label = "Carpeta", items = [] } = {}) {
  const body = el("div", { class: "rui-folder-body" });
  const root = el("div", { class: "rui-folder" },
    button(label, () => { root.classList.toggle("open"); body.hidden = !body.hidden; }, "rui-folder-tab"), body);
  for (const item of items) body.append(el("div", { class: "rui-folder-card", text: String(item) }));
  body.hidden = true;
  if (!items.length) body.append(el("p", { class: "muted", text: "—" }));
  return root;
}
