import { el } from "../dom.js";
// 03 hook-sidebar: se engancha al borde y se despliega al activarse.
export function hookSidebar({ label = "···", items = [] } = {}) {
  const list = el("div", { class: "rui-hook-list" }, ...items.map(item =>
    el("button", { type: "button", text: String(item.label ?? item) })));
  const tab = el("button", { class: "rui-hook-tab", type: "button", text: label });
  const root = el("div", { class: "rui-hook" }, tab, list);
  tab.addEventListener("click", () => root.classList.toggle("open"));
  return root;
}
