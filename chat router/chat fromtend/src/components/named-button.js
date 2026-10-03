import { button } from "../dom.js";
import { controlLabel } from "../i18n.js";

export function namedButton(context, name, onClick, style, label = controlLabel(context, name)) {
  const node = button(label, onClick, style);
  if (context.config.descriptions[name]) node.title = context.config.descriptions[name];
  return node;
}
