import { el } from "../dom.js";
// 04 family-drawer: un drawer padre con sub-opciones hijas.
export function familyDrawer({ groups = [] } = {}) {
  const root = el("div", { class: "rui-family" });
  for (const group of groups) {
    const detail = el("details", { class: "rui-family-group" },
      el("summary", { text: String(group.label ?? "") }));
    for (const child of group.children || []) {
      const b = el("button", { type: "button", text: String(child.label ?? child) });
      b.addEventListener("click", () => child.action?.());
      detail.append(b);
    }
    root.append(detail);
  }
  return root;
}
