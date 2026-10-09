import { button, el } from "../dom.js";
import { controlLabel } from "../i18n.js";
import { icon } from "./icon.js";

export function selectionButton(context, name, value, onClick) {
  const node = button("", onClick, "selection-button");
  node.setAttribute("aria-haspopup", "dialog");
  node.setAttribute("aria-label", `${controlLabel(context, name)}: ${value}`);
  node.setAttribute("title", context.config.descriptions[name] || value);
  node.setAttribute("data-control", name);
  node.append(el("span", { class: "selection-label", text: value }), icon("chevron"));
  return node;
}
