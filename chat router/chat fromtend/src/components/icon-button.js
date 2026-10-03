import { button } from "../dom.js";
import { controlLabel } from "../i18n.js";
import { icon } from "./icon.js";

export function iconButton(context, name, glyph, onClick, style = "") {
  const label = controlLabel(context, name);
  const node = button("", onClick, `icon-btn ${style}`.trim());
  node.setAttribute("aria-label", label);
  node.setAttribute("title", context.config.descriptions[name] || label);
  node.setAttribute("data-control", name);
  node.append(icon(glyph));
  return node;
}
