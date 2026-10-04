import { el, button, openWindow } from "../dom.js";
import { t } from "../i18n.js";
import { v12Svg } from "../icons-v12.js";

export const PANELS = Object.freeze([
  { id: "chat", icon: "chat", label: "panelChat", desc: "panelChatDesc" },
  { id: "wall", icon: "folder", label: "panelWall", desc: "panelWallDesc" },
  { id: "run", icon: "rocket", label: "panelRun", desc: "panelRunDesc" },
  { id: "settings", icon: "settings", label: "panelSettings", desc: "panelSettingsDesc" },
]);

export function openPanels(context) {
  const list = el("div", { class: "option-list" });
  const dialog = openWindow(t(context, "panels"), el("div", { class: "window-body" }, list), t(context, "closeWindow"));
  for (const p of PANELS) {
    const node = button("", () => { dialog.close(); context.showPanel(p.id); }, "option");
    node.append(v12Svg(p.icon, "icon svg-icon"),
      el("span", { class: "option-copy" },
        el("span", { class: "name", text: t(context, p.label) }),
        el("span", { class: "sub", text: t(context, p.desc) })));
    if (context.panel === p.id) node.setAttribute("aria-pressed", "true");
    node.setAttribute("data-panel-target", p.id);
    list.append(node);
  }
  return dialog;
}
